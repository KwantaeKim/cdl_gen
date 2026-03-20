# -----------------------------------------------------------------------------
# File          : virtuoso.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 06.Apr.2025
# -----------------------------------------------------------------------------

import subprocess, os

def scratchstart(lib_dir):
    """
    Delete the existing cells in the module library, if args.scratch = True
    """
    from . import args
    if args.scratch:
        print("[CDL Gen]: Generating from scratch ...")
        subprocess.run(
            f"find {lib_dir} \
            -mindepth 1 -maxdepth 1 \
            -type d ! -name '__pycache__' \
            -exec rm -rf {{}} +",
            shell=True)

def spicein(cdl_filename, work_dir, lib_dir):
    """
    Run spiceIn ('spiceIn man' to check the manual)
    """
    import cdl_gen
    reflib_str = " ".join(["analogLib", "basic"] + cdl_gen.reflib_list)
    print(f"[CDL Gen]: reflibList = {reflib_str}")
    subprocess.run(f"spiceIn -version", shell=True, cwd=work_dir)
    cmd = (f'spiceIn -language SPICE'
           f' -netlistFile {cdl_filename}'
           f' -outputLib {os.path.basename(lib_dir)}'
           f' -reflibList "{reflib_str}"'
           f' -devmapFile {os.path.dirname(__file__)}/devmap.txt')
    print(f"[CDL Gen]: {cmd}")
    subprocess.run(cmd, shell=True, cwd=work_dir)

def topsymgen(ckt_top):
    from . import args, lib_dir
    if args.topsym:
        lib_name = os.path.basename(lib_dir)
        print(f"[CDL Gen]: Generating top cell symbol ...")
        subprocess.run(f'''virtuoso -nograph <<EOC | awk '/===== Virtuoso =====/{{flag=1}} flag'
(printf "===== Virtuoso =====\\n")
schPinListToSymbol(
    "{lib_name}",
    "{ckt_top}",
    "symbol",
    schSchemToPinList(
        "{lib_name}",
        "{ckt_top}",
        "schematic"
    )
)
exit()
EOC
''', shell=True)

