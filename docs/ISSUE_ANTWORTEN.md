# Antworten auf die offenen GitHub-Issues (Entwurf, Stand 2026-10-27)

Geprüft gegen den Code und die Releases bis 2.27.0. **Nichts davon ist gepostet.**

| # | Thema | Stand | Vorschlag |
| --- | --- | --- | --- |
| 13 | Handfahrt „ganz hoch" fährt beim nächsten Lux-Update wieder zu | erledigt in 2.23.1 und 2.26.1 | antworten, **schließen** |
| 17 | Reihenfolge der Rollläden | erledigt in 2.27.0 | antworten, **schließen** |
| 18 | „Verzögerung zwischen Rollläden" ohne Funktion | erledigt in 2.27.0 | antworten, **schließen** |
| 19 | Resident/Gästemodus | geht heute mit „Bedingung nicht hochfahren" | antworten, **schließen** |
| 14 | Hochfahren nachholen, wenn die Sperre wegfällt | nicht umgesetzt (Zeit-/Sonnenmodus) | antworten, offen lassen |
| 15 | Panel fehlt in der Seitenleiste | ungeklärt, keine Rückmeldung seit 5 Wochen | Rückfragen stellen, offen lassen |
| 16 | Regenschutz für Rollläden bei offenem Fenster | nicht umgesetzt | antworten, offen lassen |
| 11 | Beschattung für Jarolift | My-Position vorhanden, Fahrzeit-Simulation offen | Zwischenstand, offen lassen |
| 20 | Fenster schließen fährt auf veraltete Rückfahrhöhe (Dienste) | **echter Fehler**, nicht behoben | bestätigen, Fix folgt |
| 21 | My-Position wird nicht benutzt | **Ursache gefunden**, nicht behoben | bestätigen, Fix folgt |

Zu #20: `services.py` verwirft die Fensterzyklus-Merker (`trigger_actions`, `trigger_heights`) und die Nachholfahrt nirgends. Handfahrt (seit 2.23.0) und interne Hochfahrt tun es.
Zu #21: `_send_position()` drückt die My-Position nur, wenn der Antrieb `SET_POSITION` **nicht** kann. Ein Jarolift-Controller mit Positionssteuerung fällt durch.

---

## #13 (schließen)

Danke für die ausführliche Analyse, die Ursache stimmte genau.

Das ist behoben. Seit **2.23.1** (Linos hatte denselben Ablauf gemeldet) fährt der Helligkeitsmodus einen Rollladen **je Dunkelphase nur einmal** zu. Eine Dunkelphase beginnt, wenn die Schwelle unterschritten wird, und endet, wenn sie wieder überschritten wird oder das Runter-Fenster schließt. Dein Ablauf (Handfahrt auf etwa 96 %, Sensor meldet weiter 0,02 lx) bleibt damit oben.

Dein zweiter Fall (Zwischenposition 67 %) ist seit **2.26.1** ebenfalls abgedeckt: Eine Handfahrt auf eine Zwischenposition hebt den „gilt als unten"-Vermerk auf, und eine Handfahrt in der laufenden Dunkelphase gilt für diese Phase. Erst die **nächste** Dunkelphase fährt wieder zu.

Deinen Workaround mit der Automation kannst du dir damit sparen. Bitte wieder öffnen, falls es bei dir anders läuft.

---

## #17 (schließen)

Das gibt es jetzt, seit **2.27.0**.

Im **Dashboard** hat jede Bereichskarte (für Administratoren, ab zwei Rollläden) einen Knopf mit **Sortier-Symbol**. Anklicken, dann hat jeder Rollladen einen Pfeil nach oben und unten. Die Rollläden fahren in dieser Reihenfolge nacheinander, mit der **Verzögerung zwischen Rollläden** des Bereichs dazwischen. Gespeichert wird ein paar Sekunden nach dem letzten Klick.

- Die Liste im Tab *Rollläden* bleibt alphabetisch, das Dashboard zeigt die echte Fahrreihenfolge.
- Bereiche untereinander laufen weiter gleichzeitig; der **Mindestabstand zwischen Fahrbefehlen** unter *Einstellungen* staffelt sie.

Bitte wieder öffnen, falls es bei dir nicht funktioniert.

---

## #18 (schließen)

Du hattest recht, das war ein Fehler. Die Verzögerung wirkte nur bei der **Automatik**. Die Knöpfe im Dashboard rufen die `cover`-Dienste direkt auf und kannten nur den globalen Mindestabstand, deshalb gingen alle Befehle gleichzeitig raus.

Behoben in **2.27.0**: Hoch, Runter, Sonnenschutz und Lüften (für einen Bereich und fürs ganze Haus) nehmen jetzt das **Größere aus der Verzögerung des Bereichs und dem Mindestabstand**. *Stop* wartet nie.

Eine Einschränkung: Die Abfolge läuft im Browser-Tab. Das Panel muss offen bleiben, bis der letzte Rollladen gefahren ist.

Die Reihenfolge der Rollläden lässt sich seit derselben Version im Dashboard ändern (siehe #17). Bitte wieder öffnen, falls es bei dir weiter gleichzeitig fährt.

---

## #19 (schließen, Englisch)

Most of this is possible today, without a new setting.

In the **area form** there is the condition **"Do not open"**. Pick a `binary_sensor` or `input_boolean` there, for example `input_boolean.guest_mode`. While it is `on`:

- the area is **not opened automatically** in the morning,
- **closing and sun protection keep running** (otherwise the house would stand open all evening),
- when it is `off` again, the area behaves as before.

It is set **per area**, so one guest mode can hold the guest room while the others keep running. If your helper has the opposite meaning, tick **"Reverse the meaning"** under the sensor. A weekend or holiday sleep-in works the same way ("Never open on a weekend").

What is *not* there: opening automatically **when the switch goes off** again. That is tracked in #14. Closing this one as the guest-mode case already works; please reopen if something specific is still missing.

---

## #14 (offen lassen)

Danke, das ist ein stimmiger Wunsch, und ich habe nachgesehen, wie es sich heute verhält:

- **Helligkeitsmodus:** Fällt die Sperre weg, fährt der Rollladen **bei der nächsten Lux-Meldung** im erlaubten Hochfahr-Fenster von selbst hoch.
- **Zeit- und Sonnenmodus:** Die Hochfahrt ist ein Ereignis, das einmal am Tag feuert. Ist sie durch die Sperre ausgefallen, wird sie **nicht nachgeholt**, wenn der Schalter später ausgeht. Das ist die Lücke, die du beschreibst.

Bis das eingebaut ist, hilft eine kleine Automation: Trigger „Bedtime-Schalter geht aus", Aktion `shutter_pilot.open_group` mit dem `area_id` des Bereichs. Die Dienste fahren von Hand und fragen die Sperre nicht ab.

Der Wunsch bleibt offen. Mein Gedanke zur Umsetzung: Fällt die Sperre innerhalb der Zeit zwischen Hochfahren und Runterfahren weg, wird die ausgefallene Hochfahrt einmal nachgeholt, unter Beachtung der übrigen Bedingungen.

---

## #15 (offen lassen, Rückfragen)

Entschuldige die späte Antwort. Die Meldung im Protokoll („custom integration … has not been tested") erscheint bei **jeder** benutzerdefinierten Integration und ist harmlos, daran liegt es nicht.

Das Panel wird für alle Benutzer registriert, nicht nur für Administratoren. Wenn der Eintrag in der Seitenleiste fehlt, bitte der Reihe nach prüfen:

1. **Einstellungen → Geräte & Dienste:** Steht dort **Shutter Pilot** als eingerichtete Integration? Nur über HACS herunterzuladen reicht nicht, die Integration muss über *Integration hinzufügen* angelegt werden. Zeigt der Eintrag „Einrichtung fehlgeschlagen" oder „Neu laden"?
2. **Profil → Seitenleiste:** Dort kann man Einträge ausblenden. Ist *Shutter Pilot* dort abgehakt/ausgeblendet?
3. **Protokoll:** Bitte nach dem Neustart unter *Einstellungen → System → Protokolle* nach `shutter_pilot` suchen und Zeilen mit `ERROR` oder `WARNING` hier einfügen.

Wenn du mir die Bildschirmfotos der Integration unter *Geräte & Dienste* und die Protokollzeilen schickst, kann ich genauer sagen, woran es liegt. Bitte auch kurz die aktuelle Version von Shutter Pilot nennen, inzwischen gibt es 2.27.

---

## #16 (offen lassen)

Danke für den Vorschlag. Das gibt es für Rollläden bisher nicht, und ich kann den Wunsch gut nachvollziehen.

Naheliegend wäre, den **Regensensor aus den Markisen-Einstellungen** (*Einstellungen → Wind-, Regen- und Frostschutz*) mitzunutzen: Regnet es und steht der Fensterkontakt eines Rollladens auf offen oder gekippt, fährt er in eine einstellbare Position und danach wieder auf die vorherige. Für **Dachfenster** gibt es den Regenschutz schon (Fenster schließen bei Regen, mit Sperrzeit).

Bis das da ist, bleibt deine eigene Automation der richtige Weg. Der Wunsch bleibt offen.

---

## #11 (offen lassen, Zwischenstand)

Kurzer Zwischenstand:

- Für Jarolift-Controller gibt es inzwischen die **„My"-Position** (*Rollladen-Formular → Antrieb meldet keine Position*): Eine Button-Entität (bei Jarolift der „Shade"-Knopf) wird angegeben, dazu der Prozentwert, dem sie entspricht. Jede Fahrt, die höchstens 15 % daneben liegt, drückt dann diesen Knopf. Damit lässt sich die Beschattung mit der angelernten Position fahren.
- Die **Fahrzeit-Simulation** (Zwischenposition über die Fahrzeit annähern) ist weiter nicht umgesetzt, dieses Issue bleibt dafür offen.

Hinweis zu den Jarolift-Controllern mit Positionssteuerung: Dort wurde die My-Position bisher nicht benutzt, siehe #21. Das wird gerade angepasst.

---

## #20 (offen lassen, bestätigen)

Danke für die genaue Analyse, ich habe es im Code nachvollzogen: Du hast recht.

Der Fenstertrigger merkt sich beim Öffnen die Rückfahrhöhe (bei dir 0 % um 22:48) und fährt beim Schließen darauf zurück. Die Handfahrt (seit 2.23.0) und die interne Hochfahrt verwerfen diese Merker, die **Dienste** `open_group`, `close_group`, `sun_protect_group`, `ventilate_group` und `resume_automation` tun das nicht. Im Modus „Kein Zeitplan" mit externem Scheduler ist das der einzige Weg, auf dem der Bereich fährt, deshalb trifft es dich voll.

Das ist ein Fehler, kein Wunsch. Ich ändere es so, wie du vorgeschlagen hast: Eine Fahrt über diese Dienste ist eine neuere Entscheidung als die gemerkte Rückfahrhöhe und verwirft sie samt einer wartenden Nachholfahrt. Kommt mit der nächsten Version.

---

## #21 (offen lassen, bestätigen)

Danke für die genaue Beschreibung, damit war die Ursache klar.

Die My-Position wird bisher **nur bei Antrieben benutzt, die gar keine Positionsfahrt kennen**. Wo `set_cover_position` geht, gilt die Zahl als die genauere Anweisung. Dein Jarolift-Controller bietet die Positionssteuerung zusätzlich an, deshalb wurde der „Shade"-Knopf nie gedrückt, auch mit „Antrieb meldet keine Position" und passender My-Position.

Für einen Antrieb **ohne Rückmeldung** stimmt die Annahme nicht, denn die Position ist dort nur eine zeitbasierte Schätzung des Controllers. Ich ändere es so: Ist **„Antrieb meldet keine Position"** gesetzt und eine My-Position eingetragen, wird bei einer Fahrt innerhalb der Toleranz (15 %) der **Button** gedrückt, auch wenn der Controller die Positionssteuerung kann. Ohne den Haken bleibt alles wie bisher. Kommt mit der nächsten Version.
