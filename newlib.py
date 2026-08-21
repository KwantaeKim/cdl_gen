# -----------------------------------------------------------------------------
# File          : newlib.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 26.Jun.2026
# -----------------------------------------------------------------------------
# README        : Create a new Virtuoso library
# Usage         : python3 cdl_gen/newlib.py <libname>
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
2. Create a Library
"""
print("[CDL Gen]: === 2. Create a Library ===")
names = [a for a in sys.argv[1:] if not a.startswith("-")]
if not names:
    sys.exit("usage: python3 cdl_gen/newlib.py <libname>")
cdl_gen.createlib(names[0], tech=cdl_gen.techmap()["lib"])   # bind the PDK techfile
