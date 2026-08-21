# -----------------------------------------------------------------------------
# File          : config.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 26.Jun.2026
# -----------------------------------------------------------------------------
# README        : Create a library and scaffold its primitive (NMOS) script
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
2. Create a Library and its Script
"""
print("[CDL Gen]: === 2. Create a Library and its Script ===")
newlib   = "cdlgenPrim"

tm       = cdl_gen.techmap()         # process map (single source of truth)
libname  = tm["lib"]                 # library to import the primitives from
cells    = tm["cells"]               # primitive -> PDK cell (model)
pname    = tm["params"]              # general name -> PDK-specific param name
sizing   = tm["defaults"]            # general param defaults (l, w_f, n_f)

cdl_gen.createlib(newlib, tech=libname)

prim_code = f'''\
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
cdl_filename = "prim.cdl"

libname = "{libname}"               # library to import the primitives from
cells   = {cells}   # primitive -> PDK cell (model)
pname   = {pname}   # general name -> PDK param name
sizing  = {sizing}  # general params (l, w_f, n_f) + defaults
cdl_gen.reflib_list = [libname]

for primname, cellname in cells.items():
    ckt = cdl_gen.subckt(name=primname, pins=["D", "G", "S", "B"], params=sizing)
    ckt.add_device(cdl_gen.device(
        name="M0", model=cellname, terminals=["D", "G", "S", "B"],
        **{{pname[g]: g for g in sizing}},   # only params the subckt declares
    ))

"""
3. Generate
"""
print("[CDL Gen]: === 3. Generate ===")
cdl_filename = cdl_gen.write_cdl(cdl_filename)
cdl_gen.scratchstart(cdl_gen.lib_dir)
cdl_gen.spicein(cdl_filename, cdl_gen.work_dir, cdl_gen.lib_dir)
cdl_gen.del_pycache(cdl_gen.script_dir)
for primname in cells:
    cdl_gen.topsymgen(primname)
    cdl_gen.drawsym(primname, spec=primname)
'''

run_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prim_path = os.path.join(run_dir, newlib, "prim.py")
os.makedirs(os.path.dirname(prim_path), exist_ok=True)
with open(prim_path, "w") as f:
    f.write(prim_code)
print(f"[CDL Gen]: Generated {prim_path}")
