# Flight Signal Radar – Bauplan

Auftrag: Projektbriefing vom 17.11.2026; anschließender ausdrücklicher Bauauftrag mit selbstständiger Ausführung.

## Entscheidung
Lokales, kostenloses Beobachtungswerkzeug mit Python-Standardbibliothek und statischem HTML/CSS/JavaScript. Region: 100 nautische Meilen um Frankfurt (50.03, 8.57), keine private Adresse. adsb.lol liefert öffentliche ODbL-Daten. 30-Minuten-Takt, keine Zugangsdaten erforderlich. Eine lokale Anwendung ist sofort nutzbar; GitHub-Betrieb wird als manuell aktivierbare Vorlage vorbereitet. Es wird kein privates Wissen veröffentlicht.

Gestaltung: Papier #F5F1E8, Petrol #123F46, Türkis #147D79, Text #183036. Georgia/Calibri, maßstäbliche Radarprojektion ohne externe Kartenkacheln. Flugzeuge bleiben an gemessenen Positionen. Rechte Seitenleiste mit Details, unten Zeitreihe und Logbuch. Handy: Zustand vor Karte, Details darunter. 200-ms-Übergänge, reduzierte Bewegung respektieren.

## Dateien und Arbeitsschritte
- [ ] `tests/test_radar.py`: Prüfungen zuerst für Validierung, doppelte Kennungen, Datenalter, leere Daten, Fehlererhalt und Statistik.
- [ ] `collector.py`: zeitgestempelte Positionen prüfen; Zustand atomar speichern; Abrufe begrenzen; letzte gute Daten bei Fehler behalten. Ein Zustand ist die atomare Veröffentlichungseinheit.
- [ ] `signals.py`: abgeschlossene UTC-Stunden aus 30-Minuten-Slots; Median; mindestens 80 % Abdeckung, acht frühere Stunden desselben Wochentags und derselben UTC-Stunde, |z| > 2 und absolute Differenz >= 5, Streuung null ohne z-Wert. Kennungen deterministisch. 100 Tage Historie.
- [ ] `server.py`: Loopback-Webserver und Hintergrundsammlung; manuelle Aktualisierung aus der lokalen Oberfläche, nur gleiche Herkunft zulassen. Keine Geheimnisse ausliefern.
- [ ] `web/`: Radar mit auswählbaren Flugzeugen, Suchfeld, Zeitreihe, Quellendetails, verständliche Fehler-, Leer- und Lernzustände. Letzte Messung und Abrufzeit getrennt zeigen.
- [ ] `notify.py`: optionaler Telegram-Versand mit Umgebungsschlüsseln, Versandprotokoll und Begrenzung; kein Versand ohne eingerichteten Empfänger.
- [ ] Start-/Stoppskripte, README, Datenquellenprotokoll, optionaler GitHub-Workflow mit öffentlichem Standard-Runner.
- [ ] Gesamttests, echter Abruf, Desktop-/Handyprüfung und unabhängige Schlussprüfung.

## Kritische Prüfpunkte
Ungültige Antworten dürfen gültigen Stand nicht ersetzen. Wiederholungen innerhalb desselben Messslots erhöhen nicht die Abdeckung. Der aktuelle unvollständige Stundenblock zählt nicht als Ereignis. Baselines stammen ausschließlich aus früheren Zeitfenstern. Positionen und Quellenzeit müssen frisch sein. Fehlende Daten sind kein Rückgangssignal. Geheimnisse stehen nie im Webordner oder Fehlerprotokoll.

## Noch nicht abnehmbar
24–72 Stunden Zuverlässigkeit und acht Wochen Baseline benötigen echte Laufzeit. Telegram benötigt einen vom Nutzer eingerichteten Bot und Chat. Öffentliche Bereitstellung und automatischer Cloudbetrieb sind ohne eingerichtetem Zielkonto nicht nachgewiesen. Keine Börsenprognosen.
