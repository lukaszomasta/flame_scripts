# Sammie Roto Flame Integration Script

This script integrates Autodesk Flame with Sammie Roto, enabling the one-click export of selected clips into a temporary workflow file for processing in Sammie Roto.
Sammie Roto is an amazing tool built by Zarxrax, you can find it here https://github.com/Zarxrax/Sammie-Roto-2


It adds a custom Flame Media Panel action: **Scripts → Sammie Roto it**.

---

## Overview

The tool performs the following pipeline:

1. Adds a custom Flame UI action in the Media Panel.
2. Validates the clip selection.
3. Ensures Sammie Roto is installed (or extracts it from a tarball).
4. Generates a temporary export preset XML based on the clip's color space.
5. Exports the selected clip(s) from Flame to `/tmp`.
6. Launches Sammie Roto in a separate process with the exported file.

---

## Features

* Flame Media Panel integration.
* Automatic Sammie Roto deployment from a portable tarball.
* ACES / Rec. 709 aware export preset handling.
* Background subprocess launch (non-blocking).

---

## Requirements

* Built for Autodesk Flame 2025 (requires rewrites for 2026).
* Sammie Roto portable package (`.tar.gz`) for a centrally managed deployment.

---

## Installation

1. Place this script inside Flame’s Python directory (e.g., `/opt/Autodesk/shared/python/` or your user scripts directory).
2. Edit the configuration paths in the script:

    ```python
    BASE_XML = "/opt/Autodesk/shared/export/presets/movie_file/base.xml"
    ACES_XML = "/opt/Autodesk/shared/export/presets/movie_file/base_acescg_to_rec709.xml"

    SAMMIE_PATH = "/path/to/SammieDir/"
    SAMMIE_TARBALL = "/path/to/source/tarball/Portable_Sammie_Roto_2.3.3.tar.gz"

    CTF_PATHS = {
     "acescg": "/path/to/ctf/luts/acescg_to_rec709.ctf",
     "acescct": "/path/to/ctf/luts/acescct_to_rec709.ctf"
    }
    ```

3. Restart Flame or rescan Python hooks from the Flame menu.

---

## Usage

1. Open the Flame Media Panel.
2. Select a clip.
3. Right-click → **Scripts** → **Sammie Roto it**.

The script will automatically export the selected clip(s) and launch Sammie Roto.

---

## Behavior Notes

### Sammie Deployment
* If Sammie is missing from `SAMMIE_PATH`, it automatically extracts from `SAMMIE_TARBALL`.
* A progress dialog displays during extraction.

### Export Format
* The script generates temporary export files in `/tmp`.
* Files are named based on clip names: `/tmp/<clip_name>.mov`.

### Color Management
The export preset XML dynamically adjusts based on the Flame clip color space:
* **acescg:** ACES CTF LUT to Rec. 709 applied.
* **acescct:** ACES CTF LUT to Rec. 709 applied.
* **Other / Rec. 709:** Base preset used without modification.

---

## Internal Flow

Flame Selection → Validate Clips → Ensure Sammie Exists (extract if needed) → Generate XML Export Preset → Flame Export to `/tmp` → Launch Sammie Roto subprocess.

---

## Known Limitations

* Only processes clip selections.
* Requires correct Flame export presets to exist on the system.
* Uses `/tmp` (files are expected to be cleared by the OS).
* No multi-clip batching in the Sammie launch (the last clip wins; Sammie expects one file).

---

## Security & Execution

* This tool executes a local subprocess.
* No network access or remote execution.
* Runs only the local Sammie Roto instance.

---

## Author Notes & License

* Designed for internal production workflows.
* **License:** Do whatever you need with it.
