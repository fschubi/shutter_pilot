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


def test_no_invalid_mdi_icon_names() -> None:
    """bjoerg (Forum): eine leere Stelle statt eines Icons vor „Hochfahren
    unterbinden". Ursache war `mdi:weekend` – der Name existiert im
    Material-Design-Icons-Set nicht (gegen pictogrammers.com geprueft, 404).
    Ein Rendertest findet das nicht, weil `<ha-icon>` bei einem unbekannten
    Namen einfach nichts zeichnet statt einen Fehler zu werfen – von hier aus
    also nur als fehlende Zeichenkette pruefbar, nicht als Verhalten."""
    panel = (
        Path(__file__).parent.parent
        / "custom_components/shutter_pilot/frontend/shutter-pilot-panel.js"
    )
    text = panel.read_text(encoding="utf-8")
    assert "mdi:weekend" not in text
    assert '"mdi:calendar-weekend","sec_noup"' in text


def test_the_slider_row_keeps_its_own_input_styling() -> None:
    """bjoerg (Forum): am Lux-Feld war der Schieber winzig, das Zahlenfeld
    riesig. Ursache: die Sammelregel `.field input:not([type=checkbox])`
    (aus 2.18.0, fuer die Checkbox gebaut) traf auch `type=range` mit, und
    `.slider-row .slider-num` verlor gegen deren `width:100%`, weil beide
    dieselbe Spezifitaet hatten. Dieselbe Fehlerklasse wie 2.18.0, an einem
    zweiten Eingabetyp - ein CSS-Cascade-Fehler laesst sich von hier aus nur
    als Text pruefen, nicht als gerendertes Layout."""
    panel = (
        Path(__file__).parent.parent
        / "custom_components/shutter_pilot/frontend/shutter-pilot-panel.js"
    )
    text = panel.read_text(encoding="utf-8")
    assert ":not([type=checkbox]):not([type=range])" in text
    assert ".field .slider-row .slider-num{width:88px" in text


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


def test_the_copy_button_carries_the_right_keys() -> None:
    """Bereiche kommen mit, Identitaet und Fenstersensoren nicht."""
    result = _run("copy_from.mjs")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FAIL" not in result.stdout, result.stdout


def test_the_lists_are_sorted_without_losing_the_index() -> None:
    """Sortiert angezeigt, aber der Index zeigt auf die volle Liste –
    sonst loescht ein Klick den falschen Eintrag."""
    result = _run("sorting.mjs")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FAIL" not in result.stdout, result.stdout
