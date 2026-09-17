"""Pure unit test per la logica di normalizzazione ISPRA."""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.mark.pure_unit
class TestNormalizeHelpers:
    """Test funzioni helper del normalizzatore (se importabili)."""

    def test_scripts_dir_exists(self):
        assert SCRIPTS_DIR.exists()

    def test_normalize_script_exists(self):
        script = SCRIPTS_DIR / "normalize_ispra_all.py"
        assert script.exists()

    def test_script_is_valid_python(self):
        import py_compile
        script = SCRIPTS_DIR / "normalize_ispra_all.py"
        result = py_compile.compile(str(script), doraise=True)
        assert result is not None
