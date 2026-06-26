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
