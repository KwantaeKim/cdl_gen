# -----------------------------------------------------------------------------
# File          : newlib.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 26.Jun.2026
# -----------------------------------------------------------------------------
# README        : Create a new Virtuoso library
# -----------------------------------------------------------------------------

"""
1. Initialize
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cdl_gen
cdl_gen.pathsetup()

"""
2. Create a Library
"""
newlib = "cdlgenTemplates"       # Write your library name
cdl_gen.createlib(newlib)
