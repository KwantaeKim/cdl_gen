# -----------------------------------------------------------------------------
# File          : virtuoso.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 06.Apr.2025
# Updated       : 06.May.2026
# -----------------------------------------------------------------------------

import subprocess, os, shutil, glob, json, re

SNAP = 0.03125   # default snap grid (Virtuoso Grid Controls -> Snap Spacing)
STUB = 0.5       # default stub length for powerlines / ports (override per entry with "len")

# drop benign batch noise (license + CDF doneProc warnings); real errors pass through
_QUIET = ("grep -vaE 'UseNextLicense|it has not been registered"
          "|icLic-302|doneProc|libInit\\.il successfully' || true")

def _snap(v, snap):
    return round(round(v / snap) * snap, 6)

def techmap():
    """Process map (single source of truth for PDK lib/cells/params)."""
    with open(os.path.join(os.path.dirname(__file__), "techmap.json")) as f:
        return json.load(f)

def createlib(lib_name, tech=None):
    """Create a Virtuoso library in cds.lib (tech: optional tech lib to bind)."""
    work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bind = f'techBindTechFile(ddGetObj("{lib_name}") "{tech}")' if tech else ""
    print(f"[CDL Gen]: Creating library '{lib_name}' ...")
    subprocess.run(f'''virtuoso -nograph <<EOC | awk '/===== Virtuoso =====/{{flag=1}} flag'
(printf "===== Virtuoso =====\\n")
(if ddGetObj("{lib_name}")
    (printf "[CDL Gen]: Library '{lib_name}' already exists.\\n")
    (progn
        ddCreateLib("{lib_name}" "./{lib_name}")
        {bind}
        (printf "[CDL Gen]: Library '{lib_name}' created.\\n")
    )
)
exit()
EOC
''', shell=True, cwd=work_dir)

def scratchstart(lib_dir):
    """Wipe existing cells in the library when --scratch is set."""
    from . import args
    if args.scratch:
        print("[CDL Gen]: Generating from scratch ...")
        subprocess.run(
            f"find {lib_dir} \
            -mindepth 1 -maxdepth 1 \
            -type d ! -name '__pycache__' \
            -exec rm -rf {{}} +",
            shell=True)

def spicein(cdl_filename, work_dir, lib_dir):
    """Import the CDL netlist with spiceIn ('spiceIn man' for the manual)."""
    import cdl_gen
    reflib_str = " ".join(["analogLib", "basic"] + cdl_gen.reflib_list)
    print(f"[CDL Gen]: reflibList = {reflib_str}")
    subprocess.run(f"spiceIn -version", shell=True, cwd=work_dir)
    cmd = (f'spiceIn -language SPICE'
           f' -netlistFile {cdl_filename}'
           f' -outputLib {os.path.basename(lib_dir)}'
           f' -reflibList "{reflib_str}"'
           f' -devmapFile {os.path.dirname(__file__)}/devmap.txt')
    print(f"[CDL Gen]: {cmd}")
    subprocess.run(cmd, shell=True, cwd=work_dir)

    # Move spiceIn log into cdl_gen/logs/
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    for src in glob.glob(os.path.join(work_dir, "c2s_*.log")):
        shutil.move(src, os.path.join(logs_dir, os.path.basename(src)))
    print(f"[CDL Gen]: Moved logs -> {logs_dir}/")

def topsymgen(ckt_top):
    from . import args, lib_dir
    if args.topsym:
        lib_name = os.path.basename(lib_dir)
        print(f"[CDL Gen]: Generating top cell symbol ...")
        subprocess.run(f'''virtuoso -nograph <<EOC | awk '/===== Virtuoso =====/{{flag=1}} flag'
(printf "===== Virtuoso =====\\n")
schPinListToSymbol(
    "{lib_name}",
    "{ckt_top}",
    "symbol",
    schSchemToPinList(
        "{lib_name}",
        "{ckt_top}",
        "schematic"
    )
)
exit()
EOC
''', shell=True)

def placesch(cell, placement, dstlib=None, params=None, snap=SNAP, width=0.0625):
    """
    Rebuild a schematic from a nested <cell>.json {place, wire} (wire_ext overrides wire; flat dict legacy).
    """
    from . import lib_dir, work_dir
    if placement is None:
        return
    if isinstance(placement, str) and not os.path.exists(placement):
        print(f"[CDL Gen]: no placement at {placement} (skipping; run cdl_gen.extractsch first)")
        return
    if dstlib is None:
        dstlib = os.path.basename(lib_dir)
    if isinstance(placement, dict):
        place_path = os.path.join(lib_dir, f"{cell}.json")
        with open(place_path, "w") as f:
            json.dump(placement, f, indent=2)
        print(f"[CDL Gen]: Wrote {place_path}")
        s = placement
    else:
        with open(placement) as f:
            s = json.load(f)

    place = s.get("place", s)                 # nested {place, wire, wire_ext}; flat dict = legacy
    wire  = s.get("wire", s)
    ext   = s.get("wire_ext")                 # extracted flat snapshot; overrides structured wire
    dflt   = place.get("master")
    insts  = place["instances"]
    row_y  = place.get("row_y", 0.0)
    rails  = wire.get("rails", [])
    if ext:
        pins   = ext.get("pins", place.get("pins", []))
        wires  = ext.get("wires", [])
        diodes = power = ports = []
    else:
        pins   = place.get("pins", [])
        diodes = wire.get("diodes", [])
        power  = wire.get("powerlines", [])
        ports  = wire.get("ports", [])
        wires  = wire.get("wires", [])

    pt = lambda x, y: f"(list {_snap(x, snap)} {_snap(y, snap)})"

    tm = None
    def master_of(inst):
        nonlocal tm
        if "device" in inst:                        # PDK primitive, resolved via techmap
            if tm is None:
                tm = techmap()
            return (tm["lib"], tm["cells"][inst["device"]], inst.get("view", "symbol"))
        m = inst if ("lib" in inst and "cell" in inst) else dflt
        return (m["lib"], m["cell"], m.get("view", "symbol"))

    out = []
    masters = {}
    for inst in insts:
        k = master_of(inst)
        if k not in masters:
            masters[k] = f"m{len(masters)}"
            out.append(f'(setq {masters[k]} (dbOpenCellViewByType "{k[0]}" "{k[1]}" "{k[2]}"))')
    out.append('(setq ipin (dbOpenCellViewByType "basic" "iopin" "symbol"))')

    # place instances (sizing from the params arg, not the layout)
    params = params or {}
    for inst in insts:
        nm = inst["name"]
        out.append(f'(setq {nm} (schCreateInst cdlgenCV {masters[master_of(inst)]} "{nm}" {pt(inst["x"], inst.get("y", row_y))} "{inst.get("orient","R0")}"))')
        prm = params.get(nm, inst.get("params", {}))
        if prm:
            sets = " ".join(f'(cdf~>{k}~>value = "{v}")' for k, v in prm.items())
            out.append(f'(let ((cdf (cdfGetInstCDF {nm}))) (when cdf {sets}))')

    # rails: auto-wire a row by top/bottom terminal to a shared rail + pin
    if rails:
        for inst in insts:
            nm = inst["name"]
            out.append(f'(setq {nm}_p (cdlgenTermPts {nm}))')
            out.append(f'(setq {nm}_t (car {nm}_p)) (setq {nm}_b (cadr {nm}_p))')
        for rail in rails:
            net, edge = rail["net"], rail["edge"]
            clr, pin_x = rail.get("clearance", 1.0), rail["pin_x"]
            members = []                              # (skill_pt_var, x)
            for inst in insts:
                nm = inst["name"]
                if inst.get("top") == net: members.append((f"{nm}_t", inst["x"]))
                if inst.get("bot") == net: members.append((f"{nm}_b", inst["x"]))
            if not members:
                continue
            ys = " ".join(f"(yCoord {w})" for w, _ in members)
            rv = f"rail_{net}"
            if edge == "top":
                out.append(f'(setq {rv} (plus {clr} (apply (quote max) (list {ys}))))')
            else:
                out.append(f'(setq {rv} (difference (apply (quote min) (list {ys})) {clr}))')
            for w, _ in members:
                out.append(f'(schCreateWire cdlgenCV "draw" "full" (list {w} (list (xCoord {w}) {rv})) {width} {snap} 0.0)')
            xs = [x for _, x in members] + [pin_x]
            out.append(f'(schCreateWire cdlgenCV "draw" "full" (list (list {min(xs)} {rv}) (list {max(xs)} {rv})) {width} {snap} 0.0)')
            out.append(f'(schCreatePin cdlgenCV ipin "{net}" "inputOutput" nil (list {pin_x} {rv}) "R0")')

    # diode-connected devices: clean gate->drain short
    for d in diodes:
        nm  = d if isinstance(d, str) else d["inst"]
        off = 0.125 if isinstance(d, str) else d.get("off", 0.125)
        out.append(f'(cdlgenDiode {nm} {_snap(off, snap)} {width} {snap})')

    # powerlines: short stub + label, one port pin per net (connect by name)
    for p in power:
        net, dr, ln = p["net"], p.get("dir", "up"), _snap(p.get("len", STUB), snap)
        for j, term in enumerate(p["terms"]):
            i, t = term.split(".")
            out.append(f'(cdlgenPowerline {i} "{t}" "{net}" {ln} "{dr}" {"t" if j == 0 else "nil"} {width} {snap})')

    # ports: terminal-anchored signal pin (straight stub off a terminal + the pin)
    for p in ports:
        i, t = p["term"].split(".")
        dr, ln = p.get("dir", "left"), _snap(p.get("len", STUB), snap)
        out.append(f'(cdlgenPowerline {i} "{t}" "{p["net"]}" {ln} "{dr}" t {width} {snap})')

    # explicit wires (Inst.term anchors to the real terminal)
    def node(n):
        if isinstance(n, str):
            i, t = n.split(".")
            return f'(cdlgenTermXY {i} "{t}")'
        return f'(list {_snap(n[0], snap)} {_snap(n[1], snap)})'
    for w in wires:
        out.append(f'(schCreateWire cdlgenCV "draw" "full" (list {" ".join(node(n) for n in w)}) {width} {snap} 0.0)')

    # standalone pins
    for p in pins:
        out.append(f'(schCreatePin cdlgenCV ipin "{p["name"]}" "{p.get("dir","inputOutput")}" nil {pt(p["x"], p.get("y",0.0))} "{p.get("orient","R0")}")')

    here   = os.path.dirname(__file__)
    il     = os.path.join(here, "cdl_gen.il")
    script = os.path.join(work_dir, "_cdlgen_place.il")
    with open(script, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"[CDL Gen]: Placing {dstlib}/{cell} ...")
    subprocess.run(f'''virtuoso -nograph <<EOC 2>&1 | {_QUIET}
(load "{il}")
(cdlgenPlaceSch "{dstlib}" "{cell}" "{script}")
exit()
EOC
''', shell=True, cwd=work_dir)

_NUM = r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'

def _parse_dumpsch(text):
    """Parse cdlgenDumpSch output into a placesch placement dict."""
    insts, pins, wires = [], [], []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("inst "):
            m = re.match(rf'inst "([^"]+)" (\S+)/(\S+) xy=\(({_NUM}) ({_NUM})\) orient="([^"]+)"', ln)
            if not m:
                continue
            name, lib, cell, x, y, orient = m.groups()
            insts.append({"name": name, "lib": lib, "cell": cell,
                          "x": float(x), "y": float(y), "orient": orient})
        elif ln.startswith("pin "):
            m = re.match(rf'pin "([^"]+)" xy=\(({_NUM}) ({_NUM})\) orient="([^"]+)"', ln)
            if m:
                n, x, y, o = m.groups()
                pins.append({"name": n, "x": float(x), "y": float(y), "orient": o})
        elif ln.startswith("wire points="):
            pts = re.findall(rf'\(({_NUM}) ({_NUM})\)', ln)
            wires.append([[float(x), float(y)] for x, y in pts])
    return {"instances": insts, "wires": wires, "pins": pins}

def extractsch(cell, dstlib=None):
    """Extract a hand-routed schematic into <cell>.json "wire_ext"; "place"/"wire" untouched."""
    from . import lib_dir, work_dir
    if dstlib is None:
        dstlib = os.path.basename(lib_dir)
    il = os.path.join(os.path.dirname(__file__), "cdl_gen.il")
    print(f"[CDL Gen]: Extracting {dstlib}/{cell} wires ...")
    r = subprocess.run(f'''virtuoso -nograph <<EOC
(load "{il}")
(cdlgenDumpSch "{dstlib}" "{cell}")
exit()
EOC
''', shell=True, cwd=work_dir, capture_output=True, text=True)
    p = _parse_dumpsch(r.stdout)
    path = os.path.join(lib_dir, f"{cell}.json")
    data = json.load(open(path)) if os.path.exists(path) else {"place": {}}
    data["wire_ext"] = {"wires": p["wires"], "pins": p["pins"]}   # snapshot; place/wire kept
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[CDL Gen]: Extracted {len(p['wires'])} wires -> {path} (wire_ext)")
    return path

def drawsym(cell, spec="nmos", dstlib=None):
    """
    Draw a primitive symbol from templates/<spec>_sym.json via cdlgenDrawSym.
    """
    from . import lib_dir, work_dir
    if dstlib is None:
        dstlib = os.path.basename(lib_dir)
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "templates", f"{spec}_sym.json")) as f:
        g = json.load(f)

    pt  = lambda p: f"(list {p[0]} {p[1]})"
    pts = lambda ps: "(list " + " ".join(pt(p) for p in ps) + ")"
    out = []
    for ln in g["lines"]:
        out.append(f'(dbCreateLine cdlgenCV (list "device" "drawing") {pts(ln)})')
    for e in g.get("ellipses", []):
        out.append(f'(dbCreateEllipse cdlgenCV (list "device" "drawing") {pts(e)})')
    for p in g["pins"]:
        out.append(
            f'(let ((fig (dbCreateRect cdlgenCV (list "pin" "drawing") {pts(p["bBox"])})) '
            f'(net (dbCreateNet cdlgenCV "{p["name"]}"))) '
            f'(dbCreateTerm net "{p["name"]}" "{p["dir"]}") '
            f'(dbCreatePin net fig "{p["name"]}"))')
    out.append(f'(dbCreateRect cdlgenCV (list "instance" "drawing") {pts(g["selbox"])})')
    for lb in g["labels"]:
        esc = lb["text"].replace('"', '\\"')
        lyr = f'(list "{lb["layer"][0]}" "{lb["layer"][1]}")'
        s = (f'(dbCreateLabel cdlgenCV {lyr} {pt(lb["orig"])} "{esc}" '
             f'"{lb["justify"]}" "{lb["orient"]}" "{lb["font"]}" {lb["height"]})')
        if lb.get("type", "normalLabel") != "normalLabel":
            s = f'(let ((l {s})) (l~>labelType = "{lb["type"]}"))'
        out.append(s)

    il     = os.path.join(here, "cdl_gen.il")
    script = os.path.join(work_dir, "_cdlgen_sym.il")
    with open(script, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"[CDL Gen]: Drawing {dstlib}/{cell} symbol from {spec}_sym.json ...")
    subprocess.run(f'''virtuoso -nograph <<EOC 2>&1 | {_QUIET}
(load "{il}")
(cdlgenDrawSym "{dstlib}" "{cell}" "{script}")
exit()
EOC
''', shell=True, cwd=work_dir)

