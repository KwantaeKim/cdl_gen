<p align="center">
  <img src="./logo--cdl_gen.png" width="100">
</p>

# cdl_gen

A Python-to-schematic generator that creates CDL (Circuit Description Language) netlists and imports them into Cadence Virtuoso.

Define your circuits in Python, and `cdl_gen` handles netlist generation, Virtuoso library import via `spiceIn`, and symbol creation.

## Prerequisites

- **Python 3.9+**
- **Cadence Virtuoso**

Verify your environment before running:

```bash
which python3    # should return a Python 3.9+ path
which spiceIn    # should return the Cadence spiceIn path
```

## Setup

**Step 1:** Verify your prerequisites (see above).

**Step 2:** Git clone `cdl_gen` to your `virtuoso` directory (where you run `virtuoso`):

```
virtuoso/
├── cdl_gen/              # this repo
└── lib/                  # your library
    └── script.py         # copied from cdl_gen/templates/
```

**Step 3:** Prepare a new library (e.g., `lib`). Either make it by hand in *Library Manager*, or generate it automatically — set `newlib` in `cdl_gen/newlib.py` and run:

```bash
python3 cdl_gen/newlib.py
```

This calls `cdl_gen.createlib()`, which creates the library and registers it in `cds.lib` (idempotent). Then refresh *Library Manager* (see [CIW Helpers](#ciw-helpers)).

**Step 4:** Copy a template (e.g., `cdl_gen/templates/cap.py`) to your library directory. Rename the file as you wish. Let's call it `script` in the following steps.

**Step 5:** In terminal, move to your `virtuoso` directory and run:

```bash
python3 lib/script.py
```

**Step 6:** Refresh *Library Manager* (**View** → **Refresh**, or run `cdlgenRefresh()` in the CIW — see [CIW Helpers](#ciw-helpers)). Now you can see the generated schematic under your `lib`.

## Quick Start

Each script has three sections. Users only need to edit **Section 2** to define their netlist. Sections 1 and 3 are boilerplate — no modification needed.

```python
"""
1. Initialize (do not edit)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cdl_gen
cdl_gen.pathsetup()

"""
2. Write a Netlist (edit this section)
"""
ckt = cdl_gen.subckt(name="simple_cap", pins=["A", "B"])
ckt.add_device(cdl_gen.device(
    name="C0", model="cap", terminals=["A", "B"], C=1e-15,
))

"""
3. Generate (do not edit)
"""
cdl_filename = cdl_gen.write_cdl()
cdl_gen.scratchstart(cdl_gen.lib_dir)
cdl_gen.spicein(cdl_filename, cdl_gen.work_dir, cdl_gen.lib_dir)
cdl_gen.topsymgen(cdl_gen.subckt.all_subckts[-1].name)
cdl_gen.del_pycache(cdl_gen.script_dir)
```

See `templates/cap.py` and `templates/cap_dac.py` for more examples.

### Options

| Flag | Description |
|---|---|
| `--scratch` | Delete existing cells in the library before importing |
| `--topsym` | Generate a Virtuoso symbol view for the top-level cell |

```bash
python3 lib/script.py                    # import into existing library
python3 lib/script.py --scratch          # wipe cells first, then import
python3 lib/script.py --topsym           # also generate top cell symbol
python3 lib/script.py --scratch --topsym # both
```

## CIW Helpers

`cdl_gen.il` adds SKILL helpers for the Virtuoso CIW. An already-open session only sees external `cdl_gen` changes (`newlib.py`, `spiceIn`) after a refresh. Load the helper in the CIW:

```scheme
load("./cdl_gen/cdl_gen.il")
```

To automate this, add that `load(...)` line at the end of `./.cdsinit` so the helper is available in every session without loading it by hand.

Then, after running a generator script:

```scheme
cdlgenRefresh()
```

| Function | Description |
|---|---|
| `cdlgenRefresh()` | Full *Library Manager* refresh from disk (same as **View** → **Refresh**) |

## Core API

| Class / Function | Description |
|---|---|
| `cdl_gen.device(name, model, terminals, **params)` | A single SPICE device instance (e.g., cap, res, ind) |
| `cdl_gen.subckt(name, pins)` | A `.SUBCKT` block containing devices |
| `subckt.add_device(device)` | Add a device to a subcircuit |
| `cdl_gen.createlib(lib_name, tech=None)` | Create a Virtuoso library and register it in `cds.lib` (idempotent) |
| `cdl_gen.pathsetup()` | Resolve module name and working directories from the calling script |
| `cdl_gen.write_cdl(filename)` | Serialize all subcircuits to a `.cdl` file |
| `cdl_gen.scratchstart(lib_dir)` | If `--scratch` is set, wipe existing cells in the library |
| `cdl_gen.spicein(cdl, work_dir, lib_dir)` | Run Cadence `spiceIn` to import the netlist |
| `cdl_gen.topsymgen(cell_name)` | If `--topsym` is set, generate a Virtuoso symbol view |

## Device Mapping

The file `devmap.txt` maps SPICE primitives to Cadence device types:

```
resistor  → res
capacitor → cap
inductor  → ind
```

## Templates

| File | Description |
|---|---|
| `templates/cap.py` | Simple single capacitor |
| `templates/cap_dac.py` | 3-bit binary-weighted capacitor DAC with Gaussian mismatch |

