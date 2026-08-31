"""Das Panel rendern, ohne Home Assistant zu starten.

Warum das hier steht und nicht als Wegwerf-Werkzeug im Scratchpad: in 2.20.0
blieb beim Umbenennen einer Variablen ein `awning` stehen, und das Panel warf
danach beim Bearbeiten *jedes* Rollladens einen ReferenceError. `node --check`
findet so etwas nicht – es ist gueltige Syntax –, und drei Nutzer haben es
gemeldet, bevor es auffiel.

Der Renderer deckt jeden Zweig ab, der eine eigene Variable hat: alle Tabs in
beiden Breiten, alle Formulare, alle vier Bereichsmodi, neu und bearbeitet.
Besonders wichtig sind **zwei Eintraege je Geraeteart**: der Kopierknopf wird
erst ab dem zweiten gerendert, und genau darin sass der Fehler.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PANEL_DIR = Path(__file__).parent / "panel"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node nicht installiert")


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, str(PANEL_DIR / script)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(PANEL_DIR),
    )


def test_the_panel_parses() -> None:
    panel = (
        Path(__file__).parent.parent
        / "custom_components/shutter_pilot/frontend/shutter-pilot-panel.js"
    )
    result = subprocess.run(
        [NODE, "--check", str(panel)], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr


def test_every_view_and_form_renders() -> None:
    result = _run("render_all.mjs")
    assert result.returncode == 0, (
        "Panel-Rendering fehlgeschlagen:\n" + result.stdout + result.stderr
    )
    assert "FAIL" not in result.stdout, result.stdout


def test_all_eleven_languages_carry_the_same_keys() -> None:
    result = _run("i18n_parity.mjs")
    assert result.returncode == 0, (
        "i18n unvollstaendig:\n" + result.stdout + result.stderr
    )
