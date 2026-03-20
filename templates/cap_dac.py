# -----------------------------------------------------------------------------
# File          : cap_dac.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 20.Mar.2026
# -----------------------------------------------------------------------------
# README        : Capacitor DAC (+mismatch)
# -----------------------------------------------------------------------------

"""
1. Initialize
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cdl_gen
cdl_gen.pathsetup()

"""
2. Write a Netlist
"""
#-----------------------------------------------------------
# user setup
#-----------------------------------------------------------
import random

cdl_filename = None
mean = 1e-15
std_dev = mean * 0.01

#-----------------------------------------------------------
# unit capacitor (unique per instance)
#-----------------------------------------------------------
def make_unit_cap(name):
    ckt = cdl_gen.subckt(
        name=name,
        pins=["TOP", "BOT"]
    )
    ckt.add_device(cdl_gen.device(
        name="C0",
        model="cap",
        terminals=["TOP", "BOT"],
        C=float(f"{random.gauss(mean, std_dev):.4e}"),
    ))
    return ckt

#-----------------------------------------------------------
# 3-bit cap DAC (binary-weighted)
#-----------------------------------------------------------
cap_b0 = make_unit_cap("cap_b0")
cap_b1 = [make_unit_cap(f"cap_b1_{i}") for i in range(2)]
cap_b2 = [make_unit_cap(f"cap_b2_{i}") for i in range(4)]

ckt_top = cdl_gen.subckt(
    name="cap_dac_3b",
    pins=["B0", "B1", "B2", "VOUT", "VSS"]
)
# B0: 1C
ckt_top.add_device(cdl_gen.device(
    name="xc0",
    model=cap_b0.name,
    terminals=["VOUT", "B0"],
))
# B1: 2C
for i in range(2):
    ckt_top.add_device(cdl_gen.device(
        name=f"xc1_{i}",
        model=cap_b1[i].name,
        terminals=["VOUT", "B1"],
    ))
# B2: 4C
for i in range(4):
    ckt_top.add_device(cdl_gen.device(
        name=f"xc2_{i}",
        model=cap_b2[i].name,
        terminals=["VOUT", "B2"],
    ))



"""
3. Generate
"""
cdl_filename = cdl_gen.write_cdl(cdl_filename)
cdl_gen.scratchstart(cdl_gen.lib_dir)
cdl_gen.spicein(cdl_filename, cdl_gen.work_dir, cdl_gen.lib_dir)
cdl_gen.topsymgen(cdl_gen.subckt.all_subckts[-1].name)
cdl_gen.del_pycache(cdl_gen.script_dir)
