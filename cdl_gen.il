; -----------------------------------------------------------------------------
; File          : cdl_gen.il
; Author        : Kwantae Kim <kwantae.kim@aalto.fi>
; Group         : TSirc Group, Aalto University
; Created       : 26.Jun.2026
; -----------------------------------------------------------------------------

; cdlgenRefresh() : full Library Manager refresh from the CIW.
(defun cdlgenRefresh ()
    (ddUpdateLibList)
    (ddsRefresh ?cellview t ?cdf t ?property t ?constraint t ?techfile t)
    (printf "[CDL Gen]: Library Manager refreshed.\n")
    t
)

; cdlgenDumpSym(lib cell [view]) : print a symbol's shapes/points/pins.
(defun cdlgenDumpSym (lib cell @optional (view "symbol"))
    (let (cv ty)
        (setq cv (dbOpenCellViewByType lib cell view "" "r"))
        (unless cv
            (error "[CDL Gen]: cannot open %s/%s %s" lib cell view))
        (printf "=== %s/%s %s ===\n" lib cell view)
        (foreach shape cv~>shapes
            (setq ty shape~>objType)
            (printf "%s layer=%L purpose=%L" ty shape~>layerName shape~>purpose)
            (cond
                ((equal ty "path")
                    (printf " width=%L points=%L" shape~>width shape~>points))
                ((or (equal ty "line") (equal ty "polygon"))
                    (printf " points=%L" shape~>points))
                ((or (equal ty "rect") (equal ty "ellipse"))
                    (printf " bBox=%L" shape~>bBox))
                ((equal ty "label")
                    (printf " orig=%L text=%L justify=%L orient=%L font=%L height=%L type=%L"
                        shape~>xy shape~>theLabel shape~>justify shape~>orient shape~>font shape~>height shape~>labelType))
                ((equal ty "arc")
                    (printf " ellipseBBox=%L %L %L" shape~>ellipseBBox shape~>startAngle shape~>stopAngle))
            )
            (printf "\n")
        )
        (foreach term cv~>terminals
            (printf "pin %L\n" term~>name)
        )
        (dbClose cv)
        t
    )
)

; cdlgenDumpCDF(lib cell [full]) : print a cell's CDF parameters (name/type/value/prompt).
(defun cdlgenDumpCDF (lib cell @optional full)
    (let ((cdf (cdfGetBaseCellCDF (ddGetObj lib cell))))
        (unless cdf (error "[CDL Gen]: no CDF on %s/%s" lib cell))
        (printf "=== %s/%s CDF ===\n" lib cell)
        (foreach p cdf~>parameters
            (if full
                (progn
                    (printf "--- %L ---\n" p~>name)
                    (foreach slot p~>?
                        (printf "  %s = %L\n" slot (get p slot))))
                (printf "%-16s type=%-8s value=%-12L prompt=%L\n"
                    p~>name p~>paramType p~>value p~>prompt)))
        t
    )
)

; cdlgenCheckTech(lib) : report the technology library bound to lib, compared with techmap.
(defun cdlgenCheckTech (lib)
    (let (obj tf nm want)
        (setq obj (ddGetObj lib))
        (unless obj (error "[CDL Gen]: no library %s" lib))
        (setq tf   (car (errset (techGetTechFile obj))))
        (setq nm   (and tf (car (errset tf~>libName))))
        (setq want (cdlgenTechParam "lib"))
        (cond
            ((null want)
                (printf "[CDL Gen]: *** cannot read \"lib\" from techmap.json ***\n")
                (printf "[CDL Gen]: set up techmap.json first (see README, Step 1).\n"))
            ((null (ddGetObj want))
                (printf "[CDL Gen]: *** techmap.json names PDK library '%s', which does not exist ***\n" want)
                (printf "[CDL Gen]: fix \"lib\" in techmap.json, then delete and recreate '%s'.\n" lib))
            ((null tf)
                (printf "[CDL Gen]: *** '%s' has NO technology bound ***\n" lib)
                (printf "[CDL Gen]: CDF parameters will not display. Delete '%s' and recreate it\n" lib)
                (printf "[CDL Gen]: with 'python3 cdl_gen/newlib.py %s' to bind '%s'.\n" lib want))
            ((null nm) (printf "[CDL Gen]: '%s' has a technology bound, name unavailable (techmap: %L)\n" lib want))
            ((equal nm want) (printf "[CDL Gen]: '%s' -> %s  OK\n" lib nm))
            (t
                (printf "[CDL Gen]: *** '%s' is bound to '%s' but techmap.json says '%s' ***\n" lib nm want)
                (printf "[CDL Gen]: fix \"lib\" in techmap.json, or rebind the library.\n")))
        t
    )
)

; cdlgenDumpNets(lib cell [view]) : print each net, its terminals and whether it is a pin.
(defun cdlgenDumpNets (lib cell @optional (view "schematic"))
    (let (cv)
        (setq cv (dbOpenCellViewByType lib cell view "" "r"))
        (unless cv (error "[CDL Gen]: cannot open %s/%s %s" lib cell view))
        (printf "=== %s/%s nets ===\n" lib cell)
        (foreach net cv~>nets
            (printf "net %L pin=%L conn=" net~>name (if net~>term "yes" "no"))
            (foreach it net~>instTerms
                (printf "%s.%s " it~>inst~>name it~>name))
            (printf "\n"))
        (dbClose cv)
        t
    )
)

; cdlgenDumpSch(lib cell [view]) : print a schematic's instances, wires and pins.
(defun cdlgenDumpSch (lib cell @optional (view "schematic"))
    (let (cv)
        (setq cv (dbOpenCellViewByType lib cell view "" "r"))
        (unless cv
            (error "[CDL Gen]: cannot open %s/%s %s" lib cell view))
        (printf "=== %s/%s %s ===\n" lib cell view)
        (foreach inst cv~>instances
            (if (equal inst~>libName "basic")
                (let ((it (car inst~>instTerms)))
                    (printf "pin %L xy=%L orient=%L\n"
                        (if it it~>net~>name inst~>name) inst~>xy inst~>orient))
                (printf "inst %L %s/%s xy=%L orient=%L\n"
                    inst~>name inst~>libName inst~>cellName inst~>xy inst~>orient)))
        (foreach shape cv~>shapes
            (when (member shape~>objType (list "line" "path"))
                (printf "wire points=%L\n" shape~>points)))
        (dbClose cv)
        t
    )
)

; cdlgenTechParam(key [path]) : PDK name for a general key, read from techmap.json (single source).
(defun cdlgenTechParam (key @optional (path "./cdl_gen/techmap.json"))
    (let (port (txt "") line val)
        (setq port (infile path))
        (unless port (error "[CDL Gen]: cannot read %s" path))
        (while (gets line port) (setq txt (strcat txt line)))
        (close port)
        (when (and (rexCompile (sprintf nil "\"%s\"[ \t]*:[ \t]*\"\\([^\"]+\\)\"" key))
                   (rexExecute txt))
            (setq val (rexSubstitute "\\1")))
        val
    )
)

; cdlgenSetFingers(lib cell [fparam]) : CIW-only. For every instance, toggle its finger-count param
; (n+1 -> n), firing the PDK callback so total width recomputes. fparam defaults to techmap n_f.
; Needs a GUI session (do NOT run in batch).
(defun cdlgenSetFingers (lib cell @optional fparam)
    (let (cv cdf p cb n)
        (unless fparam (setq fparam (cdlgenTechParam "n_f")))
        (setq cv (dbOpenCellViewByType lib cell "schematic" "schematic" "a"))
        (unless cv (error "[CDL Gen]: cannot open %s/%s schematic" lib cell))
        (foreach inst cv~>instances
            (when (and (setq cdf (cdfGetInstCDF inst))
                       (setq p (cdfFindParamByName cdf fparam)))
                (setq cdfgData cdf)
                (setq cb p~>callback)
                (setq n p~>value)
                (setq n (if (stringp n) (atoi n) (fix n)))
                (foreach v (list (plus n 1) n)
                    (p~>value = (sprintf nil "%d" v))
                    (when (and cb (nequal cb "")) (errset (evalstring cb))))))
        (schCheck cv)
        (dbSave cv)
        (dbClose cv)
        (printf "[CDL Gen]: refreshed %s in %s/%s\n" fparam lib cell)
        t
    )
)

; cdlgenTermPts(inst) : list of an instance's terminal points, sorted top->bottom (y desc).
(defun cdlgenTermPts (inst)
    (let (pts)
        (foreach it inst~>instTerms
            (let ((fig (car it~>term~>pins~>fig)))
                (when fig
                    (setq pts (cons (centerBox (dbTransformBBox fig~>bBox inst~>transform)) pts)))))
        (sort pts (lambda (a b) (greaterp (yCoord a) (yCoord b))))
    )
)

; cdlgenTermXY(inst termName) : point of a named terminal of an instance.
(defun cdlgenTermXY (inst termName)
    (let (res)
        (foreach it inst~>instTerms
            (when (equal it~>name termName)
                (let ((fig (car it~>term~>pins~>fig)))
                    (when fig
                        (setq res (centerBox (dbTransformBBox fig~>bBox inst~>transform)))))))
        res
    )
)

; cdlgenDiode(inst off w snap) : clean gate->drain short; stub leaves gate outward, clears past drain.
(defun cdlgenDiode (inst off w snap)
    (let (g d cx s ex vd ey)
        (setq g (cdlgenTermXY inst "G"))
        (setq d (cdlgenTermXY inst "D"))
        (setq cx (xCoord (centerBox inst~>bBox)))
        (setq s  (if (lessp (xCoord g) cx) (minus off) off))
        (setq ex (plus (xCoord g) s))
        (setq vd (if (lessp (yCoord d) (yCoord g)) (minus off) off))
        (setq ey (plus (yCoord d) vd))
        (schCreateWire cdlgenCV "draw" "full"
            (list g (list ex (yCoord g)) (list ex ey) (list (xCoord d) ey) d)
            w snap 0.0)
    )
)

; cdlgenPortStub(inst term net len dir w snap) : short stub off a terminal with a port pin at its end.
(defun cdlgenPortStub (inst term net len dir w snap)
    (let (p ex ey lo)
        (setq p (cdlgenTermXY inst term))
        (setq ex (xCoord p)) (setq ey (yCoord p))
        (cond
            ((equal dir "up")    (setq ey (plus ey len)))
            ((equal dir "down")  (setq ey (difference ey len)))
            ((equal dir "left")  (setq ex (difference ex len)))
            ((equal dir "right") (setq ex (plus ex len))))
        (schCreateWire cdlgenCV "draw" "full" (list p (list ex ey)) w snap 0.0)
        (setq lo (if (member dir (list "up" "down")) "R90" "R0"))
        (schCreatePin cdlgenCV ipin net "inputOutput" nil (list ex ey) lo)
    )
)

; cdlgenPlaceSch(lib cell scriptFile) : rebuild lib/cell schematic from a Python-generated script.
(defun cdlgenPlaceSch (lib cell scriptFile)
    (let (ok)
        (let ((old (ddGetObj lib cell "schematic")))
            (when old (ddDeleteObj old)))
        (setq cdlgenCV (dbOpenCellViewByType lib cell "schematic" "schematic" "w"))
        (unless cdlgenCV (error "[CDL Gen]: cannot open %s/%s schematic for write" lib cell))
        (setq ok (errset (load scriptFile) t))   ; never leave the cv locked on error
        (when ok (schCheck cdlgenCV) (dbSave cdlgenCV))
        (dbClose cdlgenCV)
        (unless ok (error "[CDL Gen]: place script failed (schematic closed)"))
        (printf "[CDL Gen]: placed %s/%s schematic\n" lib cell)
        t
    )
)

; cdlgenDrawSym(lib cell scriptFile) : run a Python-generated draw script into lib/cell symbol.
(defun cdlgenDrawSym (lib cell scriptFile)
    (let ((old (ddGetObj lib cell "symbol")))
        (when old (ddDeleteObj old)))
    (setq cdlgenCV (dbOpenCellViewByType lib cell "symbol" "schematicSymbol" "w"))
    (load scriptFile)
    (dbSave cdlgenCV)
    (dbClose cdlgenCV)
    (printf "[CDL Gen]: drew %s/%s symbol\n" lib cell)
    t
)
