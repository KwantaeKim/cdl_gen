# -----------------------------------------------------------------------------
# File          : __init__.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 31.May.2025
# Updated       : 20.Mar.2026
# -----------------------------------------------------------------------------

from .device import device
from .subckt import subckt
from .virtuoso import scratchstart, spicein, topsymgen
import argparse, subprocess, os, sys, shutil

if shutil.which("spiceIn") is None:
    print("[CDL Gen]: ERROR - 'spiceIn' not found. Source your Cadence environment first.")
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", action="store_true")
    parser.add_argument("--topsym", action="store_true")
    return parser.parse_args()

args = parse_args()
module = None
work_dir = None
lib_dir = None
script_dir = None
reflib_list = []

def pathsetup(bag=False):
    """
    Set up module name and paths.
    If bag=True, use BAG_WORK_DIR environment variable.
    Otherwise, use current script directory.
    """
    global module, work_dir, lib_dir, script_dir

    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    lib_dir = script_dir
    module = os.path.basename(script_dir)
    work_dir = os.path.dirname(script_dir)
    print(f"[CDL Gen]: Module name: '{module}'")

def write_cdl(cdl_filename=None, subckts=None):
    """
    Writes the given subcircuits to a .cdl file.
    
    Parameters
    ----------
    cdl_filename : str
        Name of the output CDL file.
    subckts : list[Subckt]
        A list of Subckt objects to be written.
    """
    if subckts is None:
        subckts = subckt.all_subckts
    if cdl_filename is None:
        cdl_filename = f"{script_dir}/{module}.cdl"
    else:
        cdl_filename = f"{script_dir}/{cdl_filename}"
    netlist_text = "\n".join(subckt.to_cdl() for subckt in subckts)
    with open(cdl_filename, "w") as f:
        f.write(netlist_text)
    print(f"[CDL Gen]: CDL netlist written to: {cdl_filename}")
    return cdl_filename

def del_pycache(script_dir):
    """
    Delete __pycache__
    """
    subprocess.run(
        f"find {script_dir} \
        -maxdepth 1 \
        -type d -name '__pycache__' \
        -exec rm -rf {{}} +",
        shell=True)
