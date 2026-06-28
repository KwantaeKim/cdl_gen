# -----------------------------------------------------------------------------
# File          : cap_dac.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 20.Mar.2026
# Updated       : 28.Jun.2026
# -----------------------------------------------------------------------------
# README        : Capacitor DAC (+mismatch)
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
import random

cdl_filename = None
cell    = "cap_dac_3b"
mean    = 1e-15
std_dev = mean * 0.01
groups  = [("B0", 1), ("B1", 2), ("B2", 4)]   # bit -> # unit caps

def rand_cap():
    return float(f"{random.gauss(mean, std_dev):.4e}")

ckt_top = cdl_gen.subckt(name=cell, pins=["B0", "B1", "B2", "VOUT"])

sizes = {}                                    # per-instance cap value (kept out of placement)
n = 0
for bit, count in groups:
    for _ in range(count):
        cval = rand_cap()
        name = f"C{n}"
        ckt_top.add_device(cdl_gen.device(name=name, model="cap", terminals=["VOUT", bit], C=cval))
        sizes[name] = {"c": f"{cval:.5e}"}
        n += 1

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
