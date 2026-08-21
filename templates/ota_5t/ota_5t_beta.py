# -----------------------------------------------------------------------------
# File          : ota_5t_beta.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 27.Jun.2026
# -----------------------------------------------------------------------------
# README        : 5-transistor OTA from cdlgenPrim wrappers (BETA - unverified)
# -----------------------------------------------------------------------------

"""
1. Initialize
"""
print("[CDL Gen]: === 1. Initialize ===")
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cdl_gen
cdl_gen.pathsetup()

"""
2. Write a Netlist
"""
print("[CDL Gen]: === 2. Write a Netlist ===")
cell = "ota_5t_beta"
cdl_filename = f"{cell}.cdl"
cdl_gen.reflib_list = ["cdlgenPrim"]      # import nmos/pmos primitives from here

# device sizes (l, w_f, n_f)
nin = dict(l="1u", w_f="2u", n_f=2)       # input pair  (M1, M2)
pld = dict(l="1u", w_f="4u", n_f=2)       # mirror load (M3, M4)
ntl = dict(l="1u", w_f="4u", n_f=4)       # tail source (M5)
sizes = {"M1": nin, "M2": nin, "M3": pld, "M4": pld, "M5": ntl}   # per-instance sizing

# 5T OTA: NMOS pair (M1,M2) -> PMOS mirror load (M3,M4), NMOS tail (M5).
# bulk tied to source; terminals are [D, G, S, B].
ckt = cdl_gen.subckt(name=cell, pins=["VDD", "VSS", "VINP", "VINN", "VBIAS", "VOUT"])
ckt.add_device(cdl_gen.device(name="XM1", model="nmos", terminals=["DIODE", "VINP",  "TAIL", "TAIL"], **nin))
ckt.add_device(cdl_gen.device(name="XM2", model="nmos", terminals=["VOUT",  "VINN",  "TAIL", "TAIL"], **nin))
ckt.add_device(cdl_gen.device(name="XM3", model="pmos", terminals=["DIODE", "DIODE", "VDD",  "VDD"],  **pld))
ckt.add_device(cdl_gen.device(name="XM4", model="pmos", terminals=["VOUT",  "DIODE", "VDD",  "VDD"],  **pld))
ckt.add_device(cdl_gen.device(name="XM5", model="nmos", terminals=["TAIL",  "VBIAS", "VSS",  "VSS"],  **ntl))

"""
3. Tidy schematic placement
"""
print("[CDL Gen]: === 3. Tidy schematic placement ===")
tidy = True                                       # False to skip placement
placement = os.path.join(cdl_gen.lib_dir, f"{cell}.json") if tidy else None

"""
4. Generate
"""
print("[CDL Gen]: === 4. Generate ===")
cdl_filename = cdl_gen.write_cdl(cdl_filename)
cdl_gen.scratchstart(cdl_gen.lib_dir)
cdl_gen.spicein(cdl_filename, cdl_gen.work_dir, cdl_gen.lib_dir)
cdl_gen.topsymgen(cdl_gen.subckt.all_subckts[-1].name)
cdl_gen.del_pycache(cdl_gen.script_dir)
cdl_gen.placesch(cell, placement, params=sizes)
