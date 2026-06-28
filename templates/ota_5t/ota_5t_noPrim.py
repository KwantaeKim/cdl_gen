# -----------------------------------------------------------------------------
# File          : ota_5t_noPrim.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 28.Jun.2026
# -----------------------------------------------------------------------------
# README        : 5-transistor OTA built directly from PDK primitives (techmap)
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
cdl_filename = "ota_5t_noPrim.cdl"
cell = "ota_5t_noPrim"

tm    = cdl_gen.techmap()                         # process map (single source of truth)
nmos  = tm["cells"]["nmos"]                       # PDK cell for nmos
pmos  = tm["cells"]["pmos"]                       # PDK cell for pmos
pname = tm["params"]                              # general name -> PDK param name
pdk   = lambda p: {pname[k]: v for k, v in p.items()}
cdl_gen.reflib_list = [tm["lib"]]                 # import the PDK cells from the PDK lib

# device sizes (l, w_f, n_f)
nin = dict(l="1u", w_f="2u", n_f=2)               # input pair  (M1, M2)
pld = dict(l="1u", w_f="4u", n_f=2)               # mirror load (M3, M4)
ntl = dict(l="1u", w_f="4u", n_f=4)               # tail source (M5)
sizes = {k: pdk(v) for k, v in
         {"M1": nin, "M2": nin, "M3": pld, "M4": pld, "M5": ntl}.items()}

# 5T OTA: NMOS pair (M1,M2) -> PMOS mirror load (M3,M4), NMOS tail (M5).
# bulk tied to source; terminals are [D, G, S, B].
ckt = cdl_gen.subckt(name=cell, pins=["VDD", "VSS", "VINP", "VINN", "VBIAS", "VOUT"])
ckt.add_device(cdl_gen.device(name="M1", model=nmos, terminals=["DIODE", "VINP",  "TAIL", "TAIL"], **pdk(nin)))
ckt.add_device(cdl_gen.device(name="M2", model=nmos, terminals=["VOUT",  "VINN",  "TAIL", "TAIL"], **pdk(nin)))
ckt.add_device(cdl_gen.device(name="M3", model=pmos, terminals=["DIODE", "DIODE", "VDD",  "VDD"],  **pdk(pld)))
ckt.add_device(cdl_gen.device(name="M4", model=pmos, terminals=["VOUT",  "DIODE", "VDD",  "VDD"],  **pdk(pld)))
ckt.add_device(cdl_gen.device(name="M5", model=nmos, terminals=["TAIL",  "VBIAS", "VSS",  "VSS"],  **pdk(ntl)))

"""
3. Tidy schematic placement
"""
# set tidy = False to skip Section 3
tidy = True

placement = None
if tidy:
    print("[CDL Gen]: === 3. Tidy schematic placement ===")
    placement = os.path.join(cdl_gen.lib_dir, f"{cell}.json")

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
