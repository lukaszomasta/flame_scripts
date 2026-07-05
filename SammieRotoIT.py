import flame
import os
import subprocess
import shutil
import tarfile


from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import Qt


BASE_XML = "/opt/Autodesk/shared/export/presets/movie_file/base.xml" #edit to a base export xml preset, for me it is rec709 source with no LUT
ACES_XML = "/opt/Autodesk/shared/export/presets/movie_file/base_acescg_to_rec709.xml" #edit to a LUT export xml preset, for me it is a preset with acescg to rec LUT

#edit paths to CTF luts for 2025 or change to OCIO management for >2025
CTF_PATHS = {
    "acescg" : "path/to/ctf/luts/acescg_to_rec709.ctf",
    "acescct" : "path/to/ctf/luts/acescct_to_rec709.ctf"
}

TMP_PATH = "/tmp"
SAMMIE_PATH = "/path/to/SammieDir/" #path to Sammie Roto 
SAMMIE_TARBALL = "/path/to/source/tarball/Portable_Sammie_Roto_2.3.3.tar.gz" #centrally managed master tarball

def get_media_panel_custom_ui_actions():
    """Return action for media panel which triggers extraction of metadata."""
    return [{
        'name': 'Scripts',
        'actions': [{
            'name': 'SammieRoto it',
            'isVisible': _selection_contains_clip,
            'execute': _main
        }]
    }]

def _extract_with_progress(tarball_path, dest_path, title):
    with tarfile.open(tarball_path, "r:*") as tar:
        members = tar.getmembers()
        progress = QProgressDialog(title, "Cancel", 0, len(members))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        for i, member in enumerate(members):
            if progress.wasCanceled():
                raise RuntimeError("Extraction cancelled by user.")
            tar.extract(member, path=dest_path)
            progress.setValue(i + 1)

        progress.close()

def sammie_version_ensure():
    path_to_sammie = Path(SAMMIE_PATH)
    tarball_name = Path(SAMMIE_TARBALL).name.split(".tar")[0]
    extracted_folder = path_to_sammie / tarball_name
    path_to_sammie.mkdir(parents=True, exist_ok=True)

    if not extracted_folder.exists():
        msg = f"{extracted_folder} not found, extracting from {SAMMIE_TARBALL}..."
        QMessageBox.warning(None, "Missing Sammie Folder", msg)
        _extract_with_progress(SAMMIE_TARBALL, path_to_sammie, "Extracting Sammie Roto...")

    sammie_starter = extracted_folder / "start_sammie_portable.sh"

    if not sammie_starter.exists():
        msg = (
            f"Sammie starter script missing at {sammie_starter}.\n"
            f"Portable package may be corrupt or incomplete.\n"
            f"Extracting from {SAMMIE_TARBALL}"
        )
        QMessageBox.warning(None, "Missing or corrupted starter script", msg)
        _extract_with_progress(SAMMIE_TARBALL, path_to_sammie, "Re-extracting Sammie Roto...")

        if not sammie_starter.exists():
            QMessageBox.critical(
                None,
                "Sammie repair failed",
                f"Starter script still missing after re-extraction.\n"
                f"Urgently report to Lukasz!"
            )
            raise FileNotFoundError(f"Could not recover {sammie_starter}")

    return sammie_starter

def xml_editor(cspace) -> str:
    cspace = cspace.lower()

    if cspace not in CTF_PATHS:
        if cspace not in ("rec.709 video", "unknown"):
            print("Unexpected colourspace tag, passing unchanged, deal with it...")
        dst = os.path.join(TMP_PATH, "base.xml")
        shutil.copyfile(BASE_XML, dst)
        return dst

    xml_content = Path(ACES_XML).read_text(encoding="utf-8")

    open_tag, close_tag = "<ColorTransformFileName>", "</ColorTransformFileName>"
    start = xml_content.index(open_tag) + len(open_tag)
    end = xml_content.index(close_tag)

    new_content = xml_content[:start] + CTF_PATHS[cspace] + xml_content[end:]

    dst = os.path.join(TMP_PATH, "base_acescg_to_rec709.xml")

    Path(dst).write_text(new_content, encoding="utf-8")
    xml_path = os.path.join (TMP_PATH, "base_acescg_to_rec709.xml")

    return xml_path

def _selection_contains_clip(selection):
    for item in selection:
        if isinstance(item, flame.PySequence):
            return False
            
    for item in selection:
        if isinstance(item, flame.PyClip):
            return True

            
    return False

def run_sammie(temp_file, sammie_starter):
    sammie_starter = Path(sammie_starter)
    sammie_dir = sammie_starter.parent
    python_bin = sammie_dir / "python_env" / "bin" / "python"
    launcher = sammie_dir / "launcher.py"

    subprocess.Popen(
        [
            str(python_bin), str(launcher),
            "--rpath", str(sammie_dir),
            "--file", str(temp_file),
        ],
        cwd=str(sammie_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

def _main(selection):
    print("*" * 20)
    print("Starting SammieRoto IT")
    print("*" * 20)

    print("Ensuring SammieRoto present")
    sammie_starter = sammie_version_ensure()
    print(f"SammieRoto present: {sammie_starter}")

    for clip in selection:
        clip_cspace = str(clip.get_colour_space()).strip("'")
        clip_name = str(clip.name).strip("'")
        print(f"Creating preset for {clip_name} in {clip_cspace}")
        xml_path = xml_editor(clip_cspace)
        print(f"Preset ready in {xml_path}")

        exporter = flame.PyExporter()
        exporter.foreground = True
        exporter.export(clip, xml_path, TMP_PATH)

        temp_file = Path(TMP_PATH, f"{clip_name}.mov")
        print(f"Temp file in {temp_file}")

        if not temp_file.is_file():
            msg = f"Missing temp file: {temp_file}"
            print(msg)
            QMessageBox.warning(
                None,
                "Error, Failed to find temp file!", 
                msg
            )
            raise FileNotFoundError(msg)
        
    run_sammie(temp_file, sammie_starter)

    

