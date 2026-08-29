# Forum-Antworten zu 2.18.0

Vier Beiträge. Drei davon beschreiben – ohne es zu wissen – **dieselbe Zeile
Code**: der Fensterkontakt erreichte nur den (nahezu) geschlossenen Rollladen.
Dazu ein CSS-Fehler, der wie eine Geschmacksfrage aussah, ein Schutzsensor, der
eine Markise dauerhaft sperren konnte, und die Antwort auf die My-Position, die
seit 2.16.0 offen war.

---

## @pcsv17 – die Balkontür, die nur aus dem Geschlossenen reagiert

Hallo pcsv17,

**das war ein Fehler bei mir**, und du hast ihn genau beschrieben: „Das Rollo
fährt aber nur in diese Position, wenn es vorher ganz geschlossen war. Wurde
das Rollo manuell auf z. B. 45 % gefahren und ich öffne dann die Tür, passiert
nichts."

Dahinter steckt eine Prüfung, die es gut meinte: der Fensterkontakt soll
mittags **nicht** einen offenen Rollladen herunterziehen, nur weil jemand ein
Fenster kippt. Deshalb reagierte er nur aus dem geschlossenen Zustand heraus.
Die Prüfung war aber **richtungsblind** – und der Aussperrschutz ist auf diesem
Weg das Einzige, was überhaupt nach *oben* fährt. Genau der Haken also, wegen
dem man ihn setzt, war damit ausgesperrt.

Ab 2.18.0 wird zusätzlich gefragt, in welche Richtung die Fahrt ginge: **würde
sie den Rollladen öffnen, wird gefahren – egal, wo er steht.** Dein Fall: 45 %,
Tür auf, Kipp-Position 30 %, vom Aussperrschutz auf 95 % geklemmt → 95 liegt
über 45, also fährt er hoch. Beim Schließen der Tür geht er auf die 45 %
zurück, auf denen du ihn geparkt hattest.

Der ursprüngliche Zweck bleibt: steht der Rollladen ohne Aussperrschutz offen,
zieht ihn ein Fenster weiterhin nicht herunter.

### Der zweite Teil deiner Meldung ist eine Einstellungssache

„Unabhängig von dem Aussperrschutz fährt er beim Öffnen auch nicht die Position
‚bei Fenster offen' an."

Das stimmt, und es liegt an deinem Kontakt: In deinem Screenshot steht nur
**ein** Schieber, „Position bei Fenster gekippt". Das heißt, dein Kontakt ist
zweiwertig – er meldet nur „zu" und „nicht zu", nicht „gekippt" gegen „offen".
Die Information, dass die Tür ganz aufsteht, gibt es dann schlicht nicht, und
Shutter Pilot fährt in beiden Fällen die Kipp-Position. „Position bei Fenster
offen" wird bei dir nie benutzt (das steht seit 2.8.2 auch so im
Einstellungs-Export).

Für „Tür auf → Rollladen ganz hoch" also einfach:

* **Position bei Fenster gekippt** von 30 % auf **100 %**, oder
* **Mindest-Position wenn Tür offen** von 95 % auf **100 %**

Beides führt zum selben Ergebnis. Wenn du „gekippt" und „offen" wirklich
unterscheiden willst, bräuchte es einen Kontakt mit drei Zuständen oder eine
zweite Entität für „gekippt" – dafür gibt es im Formular das Feld
„Zusätzlicher Sensor für gekippt".

