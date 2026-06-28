# -----------------------------------------------------------------------------
# File          : extract.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 28.Jun.2026
# -----------------------------------------------------------------------------
# README        : Extract a hand-tuned schematic's wires into <cell>_wire.json
# Usage         : python3 cdl_gen/extract.py <lib> <cell>
# -----------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cdl_gen

if len(sys.argv) < 3:
    sys.exit("usage: python3 cdl_gen/extract.py <lib> <cell>")
lib, cell = sys.argv[1], sys.argv[2]

cdl_gen.work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # virtuoso dir
cdl_gen.lib_dir  = os.path.join(cdl_gen.work_dir, lib)                          # target library
cdl_gen.extractsch(cell, dstlib=lib)
