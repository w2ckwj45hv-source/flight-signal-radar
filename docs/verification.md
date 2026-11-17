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

Öffentlicher Workflow und Pages-Bereitstellung werden separat nachgewiesen. Ein 24–72-Stunden-Test ist noch nicht abgelaufen. Telegram-Empfang benötigt einen eingerichteten Bot und Empfänger; ohne diese Daten wurde keine Nachricht versandt. Acht passende frühere Wochen fehlen erwartungsgemäß.

## Betriebsentscheidung

Der Sammler erzeugt keine Actions-Artefakte oder Caches. Pages rendert eine feste statische Oberfläche, die den aktuellen JSON-Datenstand aus main nachlädt. Diese Vereinfachung vermeidet kontoweiten Artefaktspeicher im laufenden Sammler. Alle Daten in öffentlichen Projektdateien stammen aus der öffentlichen Quelle oder aus ausdrücklich künstlichen Test-Fixtures; keine persönlichen Vault-Inhalte.
