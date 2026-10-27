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

import re
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


def _specificity(selector: str) -> tuple[int, int, int]:
    """(ids, classes/attributes/pseudo-classes, elements) nach CSS-Regeln.

    `:not(...)` zaehlt wie sein Argument - genau der Punkt, an dem der erste
    Anlauf (2.21.x) danebenlag: zwei `:not([type=...])` sind zwei Klassen.
    """
    ids = classes = elements = 0
    rest = selector
    while ":not(" in rest:
        start = rest.index(":not(")
        end = rest.index(")", start)
        inner = rest[start + 5:end]
        i, c, e = _specificity(inner)
        ids, classes, elements = ids + i, classes + c, elements + e
        rest = rest[:start] + rest[end + 1:]
    for token in re.findall(r"#[\w-]+|\.[\w-]+|\[[^\]]*\]|:[\w-]+|[a-z][\w-]*", rest):
        if token.startswith("#"):
            ids += 1
        elif token[0] in ".[:":
            classes += 1
        else:
            elements += 1
    return ids, classes, elements


def test_the_slider_row_keeps_its_own_input_styling() -> None:
    """bjoerg (Forum): am Lux-Feld war der Schieber winzig, das Zahlenfeld
    riesig. Ursache: die Sammelregel `.field input:not([type=checkbox])`
    (aus 2.18.0, fuer die Checkbox gebaut) traf auch `type=range` mit, und
    `.slider-row .slider-num` verlor gegen deren `width:100%`.

    Wolf (2.22.5): der erste Fix `.field .slider-row .slider-num` (0,3,0)
    verlor immer noch - `:not([type=...])` zaehlt wie eine Klasse, die
    Sammelregel steht bei (0,3,1). Das Zahlenfeld nahm weiterhin die ganze
    Zeile ein und schob die Einheit auf dem Telefon aus dem Rahmen. Deshalb
    wird hier nicht mehr der Selektor-Text geprueft, sondern die
    Spezifitaet beider Regeln gegeneinander gerechnet."""
    panel = (
        Path(__file__).parent.parent
        / "custom_components/shutter_pilot/frontend/shutter-pilot-panel.js"
    )
    text = panel.read_text(encoding="utf-8")
    general = re.search(r"(\.field input:not\(\[type=checkbox\]\):not\(\[type=range\]\))", text)
    assert general, "die Sammelregel fuer Eingabefelder fehlt"
    num = re.search(r"\n\s*([^\n{]*\.slider-num)\{width:88px", text)
    assert num, "die feste Breite des Zahlenfelds neben dem Schieber fehlt"
    assert _specificity(num.group(1)) > _specificity(general.group(1)), (
        f"{num.group(1)!r} muss {general.group(1)!r} schlagen, sonst wirkt "
        "width:88px nie"
    )
    # Gegenprobe des Rechners selbst: der alte Selektor haette verloren.
    assert _specificity(".field .slider-row .slider-num") < _specificity(general.group(1))


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


def test_sun_bound_zero_is_explained_in_the_panel() -> None:
    """Eine 0 bei den Sonnengrenzen ist eine Grenze, nur leer ist keine (Linos).

    Ohne sichtbaren Hinweis oeffnete ein Haus erst ab Sonnenaufgang, obwohl
    der Nutzer "keine Grenze" meinte. Der Hinweis muss immer da sein, die
    Warnung nur bei einer ausdruecklichen 0."""
    text = (
        Path(__file__).parent.parent
        / "custom_components/shutter_pilot/frontend/shutter-pilot-panel.js"
    ).read_text(encoding="utf-8")
    assert text.count("f_sunbound_empty:") == 11
    assert text.count("f_sunbound_zero:") == 11
    assert 'T("f_sunbound_empty")' in text
    warn = re.search(r"\.some\(([^\n]*)\)\?html`[^`]*f_sunbound_zero", text)
    assert warn, "die Warnung bei einer ausdruecklichen 0 fehlt"
    # leer darf nicht warnen: "" und null muessen vorher ausgeschlossen sein
    assert '!==""' in warn.group(1) and "!=null" in warn.group(1)


def test_storm_and_lock_fields_are_in_the_panel() -> None:
    """Windschutz fuer Raffstores und Sperr-Entitaet (2.25.0)."""
    root = Path(__file__).parent.parent / "custom_components/shutter_pilot"
    text = (root / "frontend/shutter-pilot-panel.js").read_text(encoding="utf-8")
    for key in ("sec_storm", "sec_storm_sub", "f_storm_guard", "f_storm_guard_hint",
                "f_storm_position", "f_storm_tilt", "f_guard_rwind",
                "f_guard_lockout_hint_rwind", "sec_rwind", "sec_rwind_sub",
                "f_rwind_intro", "f_lock_entity", "f_lock_entity_hint"):
        assert text.count(f"{key}:") == 11, key
    # Der Haken traegt die Vorgabe selbst ein: der Schieber zeigt sonst 0 %,
    # waehrend das Backend mit 100 % faehrt.
    assert "s.storm_position=100" in text and "s.storm_tilt=100" in text
    for name in ("AWNING_UNUSED_KEYS", "WINDOW_UNUSED_KEYS"):
        block = re.search(rf"const {name} = \[(.*?)\];", text, re.S)
        assert block, name
        for key in ("storm_guard", "storm_position", "storm_tilt",
                    "automation_lock_entity"):
            assert f'"{key}"' in block.group(1), (name, key)


def test_door_lock_hooks_are_in_the_form_and_the_unused_key_lists() -> None:
    """`window_react` und `drive_after_close_up` (Raffstore, Florian/Claus).

    Das Formular bietet beide an, Markise und Dachfenster loeschen sie beim
    Umwandeln (sonst bleiben sie gespeichert, sichtbar und wirkungslos), und
    das Panel spiegelt die Listen in const.py."""
    root = Path(__file__).parent.parent / "custom_components/shutter_pilot"
    text = (root / "frontend/shutter-pilot-panel.js").read_text(encoding="utf-8")
    for key in ("f_window_react", "f_window_react_hint", "f_drive_after_up",
                "f_drive_after_up_hint"):
        assert text.count(f"{key}:") == 11, key
    assert "s.window_react!==false" in text  # Vorgabe an, wie bisher
    assert "s.drive_after_close_up" in text
    for name in ("AWNING_UNUSED_KEYS", "WINDOW_UNUSED_KEYS"):
        block = re.search(rf"const {name} = \[(.*?)\];", text, re.S)
        assert block, name
        assert '"drive_after_close_up"' in block.group(1), name
        assert '"window_react"' in block.group(1), name


def test_keep_and_tilt_order_fields_are_in_the_panel() -> None:
    """Hoehe/Lamellen "unveraendert" und der Winkel nach der Hoehe (2.26.0)."""
    root = Path(__file__).parent.parent / "custom_components/shutter_pilot"
    text = (root / "frontend/shutter-pilot-panel.js").read_text(encoding="utf-8")
    for key in ("f_keep_position", "f_keep_position_on", "f_keep_tilt",
                "f_keep_tilt_on", "f_tilt_after_position",
                "f_tilt_after_position_hint"):
        assert text.count(f"{key}:") == 11, key
    for name in ("AWNING_UNUSED_KEYS", "WINDOW_UNUSED_KEYS"):
        block = re.search(rf"const {name} = \[(.*?)\];", text, re.S)
        assert block, name
        for key in ("keep_position_open", "keep_position_closed",
                    "keep_position_sun_protect", "keep_tilt_open",
                    "keep_tilt_closed", "keep_tilt_sun_protect",
                    "tilt_after_position"):
            assert f'"{key}"' in block.group(1), (name, key)


def test_drive_delay_applies_to_the_dashboard_buttons() -> None:
    """Die Verzoegerung des Bereichs gilt auch fuer die Knoepfe (GitHub #18)."""
    result = _run("drive_delay.mjs")
    assert result.returncode == 0, "drive_delay:\n" + result.stdout + result.stderr
    assert "FAIL" not in result.stdout, result.stdout


def test_shutters_can_be_reordered_on_the_dashboard() -> None:
    """Reihenfolge verschieben (GitHub #17)."""
    result = _run("reorder.mjs")
    assert result.returncode == 0, "reorder:\n" + result.stdout + result.stderr
    assert "FAIL" not in result.stdout, result.stdout


def test_the_guard_form_warns_about_missing_and_reversed_thresholds() -> None:
    """Frankchief (simon42 #212): Schwelle nicht eingetragen, Werte verkehrt."""
    result = _run("guard_slot.mjs")
    assert result.returncode == 0, "guard_slot:\n" + result.stdout + result.stderr
    assert "FAIL" not in result.stdout, result.stdout


def test_order_and_guard_form_keys_are_in_all_languages() -> None:
    root = Path(__file__).parent.parent / "custom_components/shutter_pilot"
    text = (root / "frontend/shutter-pilot-panel.js").read_text(encoding="utf-8")
    for key in ("btn_reorder", "btn_reorder_done", "reorder_hint", "btn_move_up",
                "btn_move_down", "f_guard_no_threshold", "f_guard_wrong_way"):
        assert text.count(f"{key}:") == 11, key
