# -----------------------------------------------------------------------------
# File          : cap.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 20.Mar.2026
# -----------------------------------------------------------------------------
# README        : Capacitor
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
cdl_filename = "cap.cdl"

#-----------------------------------------------------------
# simple capacitor
#-----------------------------------------------------------
ckt = cdl_gen.subckt(name="simple_cap", pins=["A","B"])
ckt.add_device(cdl_gen.device(
    name="C0", model="cap", terminals=["A", "B"], C=1e-15,
))

"""
3. Generate
"""
cdl_filename = cdl_gen.write_cdl(cdl_filename)
cdl_gen.scratchstart(cdl_gen.lib_dir)
cdl_gen.spicein(cdl_filename, cdl_gen.work_dir, cdl_gen.lib_dir)
cdl_gen.topsymgen(cdl_gen.subckt.all_subckts[-1].name)
cdl_gen.del_pycache(cdl_gen.script_dir)
