# -----------------------------------------------------------------------------
# File          : virtuoso.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 06.Apr.2025
# Updated       : 06.May.2026
# -----------------------------------------------------------------------------

import subprocess, os, shutil, glob

def createlib(lib_name, tech=None):
    """
    Create a Virtuoso library and register it in cds.lib.
    tech: optional tech library to bind (e.g. "gpdk045").
    """
    work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bind = f'techBindTechLibToDesignLib("{tech}" "{lib_name}")' if tech else ""
    print(f"[CDL Gen]: Creating library '{lib_name}' ...")
    subprocess.run(f'''virtuoso -nograph <<EOC | awk '/===== Virtuoso =====/{{flag=1}} flag'
(printf "===== Virtuoso =====\\n")
(if ddGetObj("{lib_name}")
    (printf "[CDL Gen]: Library '{lib_name}' already exists.\\n")
    (progn
        ddCreateLib("{lib_name}" "./{lib_name}")
        {bind}
        (printf "[CDL Gen]: Library '{lib_name}' created.\\n")
    )
)
exit()
EOC
''', shell=True, cwd=work_dir)

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

    # Move spiceIn log into cdl_gen/logs/
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    for src in glob.glob(os.path.join(work_dir, "c2s_*.log")):
        shutil.move(src, os.path.join(logs_dir, os.path.basename(src)))
    print(f"[CDL Gen]: Moved logs -> {logs_dir}/")

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

