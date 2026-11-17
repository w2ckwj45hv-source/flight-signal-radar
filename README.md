# Flight Signal Radar

Ein kostenloses regionales Flugbeobachtungsprojekt. Echte Positionen im Umkreis von 100 nautischen Meilen um Frankfurt, ein Logbuch und vorsichtige Vergleiche derselben UTC-Stunde desselben Wochentags. Keine Börsenprognose und kein vollständiger Flugplan.

## Start auf diesem Windows-PC

**`Radar starten.cmd` doppelklicken.** Es öffnet `http://127.0.0.1:8765`. Der Sammler läuft im Hintergrund alle 30 Minuten, solange der PC läuft. **`Radar stoppen.cmd`** beendet den eigenen Prozess. Nach einem Neustart erneut starten. Es werden keine Autostarts oder Windows-Aufgaben heimlich installiert.

Alternativ in PowerShell: `./start.ps1` und `./stop.ps1`. Die Skripte verwenden vorhandenes Python ab 3.11 oder die verfügbare Codex-Laufzeit. Diese kann sich durch App-Updates verschieben; dann Python kostenlos installieren oder den Laufzeitpfad im Startskript aktualisieren. Kein pip, kein npm und keine kostenpflichtigen Dienste nötig.

Auf anderen Systemen: `python3 server.py` starten; Strg+C stoppt. Einzelner Abruf: `python3 collector.py`. Prüfungen: `python3 -m unittest discover -s tests -v`. Die Standardbibliothek reicht.

## Bedienung und Datenalter

- Eine Maschine auf dem Radar oder in der Liste auswählen. Suche nach Rufzeichen, Kennung, Typ oder Registrierung. Höhe in Fuß, Geschwindigkeit über Grund in Knoten. Unbekannte Werte bleiben unbekannt.
- „Daten aktualisieren“ ruft lokal frühestens alle fünf Minuten erneut die Quelle ab. Auf der öffentlichen statischen Webseite lädt der Knopf den zuletzt veröffentlichten Stand; er greift nicht direkt auf die Flug-API zu.
- Die Radarpositionen sind gemessen und werden nicht künstlich weiterbewegt. Das Radar ist eine regionale Projektion mit Entfernungsringen, keine Navigationskarte. Flughäfen sind öffentliche geografische Bezugspunkte.
- Messzeit und Abrufzeit werden getrennt angezeigt. Ab 45 Minuten ist der Stand veraltet. Ein gescheiterter Abruf zeigt den Fehler und behält die letzte gültige Messung.
- Zwei Beobachtungsplätze pro abgeschlossener UTC-Stunde; wiederholte Abrufe im selben Halb-Stunden-Fenster zählen nicht zusätzlich. Die Zeitreihe zeichnet Lücken nicht zu.
- Für eine Auffälligkeit braucht es acht vollständige frühere Vergleichsstunden desselben Wochentags und derselben UTC-Stunde. Acht Wochen echte Laufzeit können daher nötig sein. Mindestens 80 % Abdeckung, mehr als zwei Standardabweichungen und mindestens fünf Flugzeuge Unterschied. Streuung null erzeugt keinen z-Wert. Die Regeln sind vorläufige Prüfgrenzen.

## Öffentlicher automatischer Betrieb

Der Workflow `.github/workflows/radar.yml` ist für ein **öffentliches** GitHub-Repository vorbereitet. Er verwendet kostenlose Standardrunner und GitHub Pages, prüft die Tests, sammelt Daten und veröffentlicht alle 30 Minuten. Ein manueller Start ist unter Actions möglich. Gleichzeitige Läufe sind gesperrt. Er aktiviert keine kostenpflichtigen Ausweichdienste.

Pages verwendet den Zweig `gh-pages`, Ordner `/`. Die Oberfläche liest den aktuellen JSON-Datenstand aus dem öffentlichen `main`-Zweig über raw.githubusercontent.com; dessen Zwischenspeicher kann einige Minuten Verzögerung hinzufügen. Nach Änderungen an der Oberfläche: `git subtree split --prefix web -b pages-update`, dann `git push origin pages-update:gh-pages` und den lokalen Hilfszweig wieder entfernen. Zeitpläne können verspätet laufen oder nach 60 Tagen ohne Aktivität deaktiviert werden. Actions → Workflow → „Enable workflow“ bzw. „Run workflow“ reaktiviert den Betrieb. Workflow deaktivieren stoppt die Cloudsammlung; Pages kann den letzten Stand weiter anzeigen, deutlich als veraltet.

Die Sammlung erzeugt keine Actions-Artefakte und keine Caches. Die feste Oberfläche wird separat über den kostenlosen Pages-Zweig bereitgestellt. Ab 50 MB Repositorygröße hält der Sammler an. Vor einer großen Erweiterung das Budget neu prüfen. Quellenkontingent ohne Schlüssel: laut adsb.lol 500 Abrufe/Tag/IP, geplant 48. Laufende IP-Kontingente können von anderen Nutzern geteilt werden. Keine Garantie für kostenlos unbegrenzte Verfügbarkeit.

## Telegram optional einrichten

1. In Telegram bei `@BotFather` einen kostenlosen Bot erstellen und dessen privaten Chat starten.
2. Token und numerische Chat-ID als Umgebungsvariablen `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` setzen. Niemals in den Webordner, Code oder Chat kopieren. Für GitHub: Repository → Settings → Secrets and variables → Actions, dieselben zwei Namen als Secrets anlegen.
3. Lokal mit diesen Variablen `python notify.py --test` ausführen: Die Nachricht trägt ausdrücklich „TEST“. Der Startprozess erbt Umgebungsvariablen beim Start, daher danach neu starten. Für den öffentlichen Link optional `RADAR_PUBLIC_URL` mit einer HTTPS-Adresse setzen.

Das Versandprotokoll liegt lokal unter `.local/sent.json`, in Actions unter `runtime/sent.json` ohne Token oder Chat-ID. Maximal eine Nachricht pro Minute, bestätigte Ereignisse werden nicht erneut gesendet. Ereignisse über zwei Stunden alt werden nicht nachträglich versandt. Bei abgebrochener Verbindung nach erfolgreichem Telegram-Empfang ist eine doppelte Nachricht möglich. Ohne Bot und Chat wird nichts verschickt. Einrichtung nicht als erledigt betrachten, bevor eine echte Testnachricht angekommen ist.

## Dateien und Wiederherstellung

`collector.py`: Abruf, Validierung, atomare Speicherung. `signals.py`: Stundenvergleich. `server.py`: lokaler Webserver mit Sammlung. `transport.py`: HTTPS ohne ausgeschaltete Zertifikatsprüfung. `notify.py`: optionaler Versand. `web/`: vollständige statische Oberfläche. `web/data/state.json`: letzter Stand, Zählreihe, Ereignisse und die letzten 50 Abrufe.

Ein ungültiger Zustand wird nicht still überschrieben. Stoppe den Sammler, kopiere die defekte Datei zur Diagnose und stelle eine vorherige gültige Version aus Git wieder her. Falls noch keine Historie existiert, verschiebe die defekte Datei aus `web/data/` heraus und starte neu; dabei beginnt die Vergleichssammlung von vorn. Nicht einfach löschen, wenn wichtige Messreihen darin liegen.

Bei Startproblemen `.local/error.log` ansehen. Port 8765 kann bereits belegt sein. Die Stopproutine prüft den vollständigen Skriptpfad, bevor sie einen Prozess beendet. Der Server lauscht nur auf diesem PC; Zugriff vom Handy erfolgt über die öffentliche Seite, nicht durch Öffnen des lokalen Servers ins Netz.

## Herkunft und Grenzen

Flugdatensatz von [adsb.lol](https://www.adsb.lol), verfügbar unter [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Der normalisierte Bestand einschließlich abgeleiteter Zählreihen steht ebenfalls unter ODbL 1.0 und ist auf der Webseite herunterladbar. Anwendungscode: MIT. Details, aktuelle Quellenprüfung und Gratisbudget: [docs/sources.md](docs/sources.md).

Ein erster echter Abruf ist geprüft; Zuverlässigkeit über 24–72 Stunden, achtwöchige Vergleichsbasis und Telegram-Empfang sind gesonderte Abnahmekriterien. Es gibt keine erfundenen historischen Beobachtungen, Testtreffer oder versandten Nachrichten.

