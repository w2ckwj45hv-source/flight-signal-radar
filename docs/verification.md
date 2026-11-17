# Prüfprotokoll · 17.11.2026

## Erledigt

- 22 automatisierte Prüfungen: Validierung, ungültige/alte/zukünftige Zeitstempel, Kennungs-Deduplizierung, echte leere Antworten, Datenqualität, atomarer Fehlererhalt, Abrufpause, Statistik, Telegram und Windows-Transport.
- Neue Tests zunächst rot ausgeführt, anschließend grün. Regressionen aus der unabhängigen Prüfung separat nachgestellt.
- Unabhängige Codeprüfung: vier wichtige Befunde; alle behoben: teilweise defekte Antworten nicht statistisch zählen, Windows-Prozess-Timeout abfangen, optionalen Telegram-Ausfall vom Speichern entkoppeln, Retry-After über Neustarts durchsetzen.
- Echte Quellenabrufe mit aktivem TLS geprüft. Die lokale Sammlung hat nach einem protokollierten Netzwerktestfehler wieder erfolgreich echte Messungen gespeichert. Keine erfundene Historie.
- JavaScript-Syntax geprüft.
- Browser: 390, 768, 1024 und 1440 Pixel breit ohne Seitenüberlauf. Radar, Suche ohne Treffer, Maschinen-Auswahl per Tastatur einschließlich erhaltenem Fokus und Abruflogbuch geprüft. Keine gemeldeten JavaScript-Laufzeitfehler.
- Lokaler Start, Stoppen und erneuter Start mit den mitgelieferten Skripten geprüft.

## Noch laufend/offen

Erster öffentlicher Workflow erfolgreich: https://github.com/w2ckwj45hv-source/flight-signal-radar/actions/runs/44185360052. Er hat den kurz zuvor lokal gespeicherten Zustand innerhalb der Abrufpause korrekt weiterverwendet; dies allein belegt noch keinen neuen Quellenabruf in der Cloud. Pages-Bereitstellung erfolgreich: https://github.com/w2ckwj45hv-source/flight-signal-radar/actions/runs/44185373782. Öffentliche Seite und Datenabruf aus main auf Desktop und Handy geprüft: https://w2ckwj45hv-source.github.io/flight-signal-radar/.

Neuer echter Quellenabruf in GitHub Actions am 17.11.2026 um 23:02:32 Uhr Europe/Berlin: 39 geprüfte Positionen, neuer Quellen- und Abrufzeitpunkt, Status ok, Bot-Commit 0ef4f5a. Erfolgreicher Lauf: https://github.com/w2ckwj45hv-source/flight-signal-radar/actions/runs/44186015134. Damit ist nicht nur der Workflowstart, sondern auch ein neuer Cloudabruf nachgewiesen. Die Zahl ist eine Momentaufnahme, keine aktuelle Dauerzahl.

Ein 24–72-Stunden-Test ist noch nicht abgelaufen. Telegram-Empfang benötigt einen eingerichteten Bot und Empfänger; ohne diese Daten wurde keine Nachricht versandt. Acht passende frühere Wochen fehlen erwartungsgemäß.

## Betriebsentscheidung

Der Sammler erzeugt keine Actions-Artefakte oder Caches. Pages rendert eine feste statische Oberfläche, die den aktuellen JSON-Datenstand aus main nachlädt. Diese Vereinfachung vermeidet kontoweiten Artefaktspeicher im laufenden Sammler. Alle Daten in öffentlichen Projektdateien stammen aus der öffentlichen Quelle oder aus ausdrücklich künstlichen Test-Fixtures; keine persönlichen Vault-Inhalte.

Das einmalige Pages-Build-Paket (16.115 Bytes) wurde nach dem erfolgreichen Deployment entfernt; danach waren keine Artefakte in diesem Repository gespeichert. Private lokale Endpunkte geprüft: Aktualisierung ohne passende Herkunft wurde mit HTTP 403 abgewiesen; Zugriff auf collector.py mit HTTP 404. Der lokale Sammler wurde nach Einrichtung der Cloud beendet, damit nicht zwei Betriebswege parallel sammeln.
