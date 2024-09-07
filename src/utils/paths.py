import os
import sys


def resourcePath(relativePath):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relativePath).replace("\\", "/")


# Reserved file names on Windows
RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def isValidFilename(filename: str) -> bool:
    # Forbidden characters in Windows
    forbiddenChars = r'<>:"/\\|?*'

    # Check if the filename contains any forbidden characters
    if any(char in filename for char in forbiddenChars):
        return False

    # Extract the file name without the extension
    baseName = os.path.splitext(filename)[0]

    # Check if the base name is a reserved word (case insensitive)
    return False if baseName.upper() in RESERVED_NAMES else len(filename) <= 255
