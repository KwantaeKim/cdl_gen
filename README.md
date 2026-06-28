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

## Install

Git clone `cdl_gen` to your `virtuoso` directory (where you run `virtuoso`):

```
virtuoso/
├── cdl_gen/              # this repo
└── lib/                  # your library
    └── script.py         # copied from cdl_gen/templates/
```

## Step 1 — Set Up the Process (`techmap.json`)

`techmap.json` is the **single source of truth** for everything process-specific — PDK library, cell names, and parameter names. Set it once for your PDK and every generator, symbol, and CIW helper follows it; nothing process-specific is hardcoded anywhere else.

| Key | Meaning |
|---|---|
| `lib` | PDK library to import the primitives from |
| `cells` | general name → PDK cell, e.g. `{"nmos": "nmos1v", "pmos": "pmos1v"}` |
| `params` | general name → PDK parameter name, e.g. `{"l": "l", "w_f": "fw", "n_f": "fingers"}` |
| `defaults` | default sizes, e.g. `{"l": "1u", "w_f": "1u", "n_f": 1}` |

The general parameter names are:

| Name | Meaning |
|---|---|
| `l` | channel length |
| `w_f` | finger width (width of a single finger) |
| `n_f` | number of fingers (total width = `w_f` × `n_f`, computed by the PDK) |

To find your PDK's parameter names, instantiate the device in a schematic, select it, and press **`q`** (*Edit Object Properties*). Set the right-most **Display** column to **both** — each parameter then shows its name next to its value, so you can tell which names map to length, finger width, and number of fingers.

Edit `techmap.json` for your PDK, then build the primitive library (`cdlgenPrim`) and its symbols:

```bash
python3 cdl_gen/config.py     # create cdlgenPrim + generate prim.py
python3 cdlgenPrim/prim.py    # build the primitive schematics + symbols
```

Each primitive's symbol shape is drawn from `templates/<name>_sym.json` (e.g. `nmos_sym.json`, `pmos_sym.json`).

## Step 2 — Generate a Circuit

**Prepare a library** (e.g., `lib`). Either make it by hand in *Library Manager*, or generate it automatically — set `newlib` in `cdl_gen/newlib.py` and run:

```bash
python3 cdl_gen/newlib.py
```

This calls `cdl_gen.createlib()`, which creates the library and registers it in `cds.lib` (idempotent).

**Copy a template** (e.g., `cdl_gen/templates/cap.py`) to your library directory and rename it as you wish (call it `script` below).

**Run it** from your `virtuoso` directory:

```bash
python3 lib/script.py
```

**Refresh** *Library Manager* (**View** → **Refresh**, or `cdlgenRefresh()` in the CIW — see [CIW Helpers](#ciw-helpers)). The generated schematic now appears under your `lib`.

## Quick Start

Each script is organized into numbered sections. You edit **Section 2** to define your netlist; *Initialize* and *Generate* are boilerplate — no modification needed. An optional **Tidy schematic placement** section (see below) rebuilds the imported schematic into a clean, readable form.

```python
"""
1. Initialize (do not edit)
"""
# boilerplate

"""
2. Write a Netlist (edit this section)
"""
ckt = cdl_gen.subckt(name="simple_cap", pins=["A", "B"])
ckt.add_device(cdl_gen.device(name="C0", model="cap", terminals=["A", "B"], C=1e-15))

"""
3. Generate (do not edit)
"""
# boilerplate
```

See `templates/cap.py` and `templates/cap_dac/` for the full scripts.

### Tidy Schematic Placement

`spiceIn` imports connectivity but not placement, so generated schematics come out tangled. For a clean schematic, describe a placement and pass it to `cdl_gen.placesch(cell, placement)`; it rebuilds the schematic accordingly. Pass `None` to skip. See `templates/cap_dac/` for the format.

The placement is one `<cell>.json` with two nested blocks: `place` (instances, rails, pins) and `wire` (wires, diodes, powerlines, ports). `extract.py` snapshots a hand-edited schematic into a separate `wire_ext` block, leaving `place` and `wire` untouched:

```bash
python3 cdl_gen/extract.py <lib> <cell>
```

When `wire_ext` is present it overrides the authored `wire` (so the schematic matches your hand edits); delete it to revert to the authored structure.

An instance master is given either as `{"device": "nmos"}` — a PDK primitive resolved through `techmap.json` — or as an explicit `{"lib": ..., "cell": ...}`. Using `device` keeps the process out of the placement file.

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
| `cdlgenDumpSym(lib cell)` | Print a symbol's shapes, labels, and pins |
| `cdlgenDumpCDF(lib cell)` | Print a cell's CDF parameters |
| `cdlgenSetFingers(lib cell)` | Toggle each device's finger count (from `techmap.json`) so PDK total width recomputes |

`cdlgenDrawSym` and `cdlgenPlaceSch` are invoked in batch by `cdl_gen.drawsym` / `cdl_gen.placesch`; you don't call them by hand.

## Core API

| Class / Function | Description |
|---|---|
| `cdl_gen.device(name, model, terminals, **params)` | A single SPICE device instance (e.g., cap, res, ind) |
| `cdl_gen.subckt(name, pins)` | A `.SUBCKT` block containing devices |
| `subckt.add_device(device)` | Add a device to a subcircuit |
| `cdl_gen.techmap()` | Load `techmap.json` (the process map) |
| `cdl_gen.createlib(lib_name, tech=None)` | Create a Virtuoso library and register it in `cds.lib` (idempotent) |
| `cdl_gen.pathsetup()` | Resolve module name and working directories from the calling script |
| `cdl_gen.write_cdl(filename)` | Serialize all subcircuits to a `.cdl` file |
| `cdl_gen.scratchstart(lib_dir)` | If `--scratch` is set, wipe existing cells in the library |
| `cdl_gen.spicein(cdl, work_dir, lib_dir)` | Run Cadence `spiceIn` to import the netlist |
| `cdl_gen.topsymgen(cell_name)` | If `--topsym` is set, generate a Virtuoso symbol view |
| `cdl_gen.drawsym(cell, spec)` | Draw a custom symbol from `templates/<spec>_sym.json` |
| `cdl_gen.placesch(cell, placement)` | Rebuild a schematic cleanly from a placement (dict, JSON path, or `None`) |

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
| `templates/cap_dac/` | 3-bit binary-weighted capacitor DAC with Gaussian mismatch and clean placement |
| `templates/ota_5t/` | 5-transistor OTA, two variants (see below) |

### OTA Example (`templates/ota_5t/`)

A 5-transistor OTA in two flavors, each a script plus its `<cell>.json` placement:

| Files | Devices | Needs |
|---|---|---|
| `ota_5t.py` + `ota_5t.json` | `cdlgenPrim` primitives | Step 1 done (`config.py` + `prim.py`) |
| `ota_5t_noPrim.py` + `ota_5t_noPrim.json` | PDK cells directly (via `techmap`) | only `techmap.json` set |

To use, copy the chosen script **and its `.json`** into your library directory, then run it from your `virtuoso` directory:

```bash
cp cdl_gen/templates/ota_5t/ota_5t_noPrim.py   lib/
cp cdl_gen/templates/ota_5t/ota_5t_noPrim.json lib/
python3 lib/ota_5t_noPrim.py --scratch
```

The script reads its `<cell>.json` (`place` + `wire` blocks) and builds a clean schematic. To hand-tune and recapture, edit it in Virtuoso then run `python3 cdl_gen/extract.py <lib> <cell>` (writes `wire_ext`).
