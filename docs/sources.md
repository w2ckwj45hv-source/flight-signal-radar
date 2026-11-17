# Daten- und Betriebsprüfung

Stand: 17.11.2026. Die Prüfung betrifft dieses nichtkommerzielle Lernprojekt. Kein SLA und keine Gewähr für dauerhafte Verfügbarkeit.

## adsb.lol – ausgewählte Quelle

- Offizielle Dokumentation: https://www.adsb.lol/docs/open-data/api
- Schema: https://api.adsb.lol/api/openapi.json
- Lizenzhinweis für API-Daten: ODbL 1.0, direkt auf der API-Dokumentationsseite. Die gesonderte Privacy-Seite behandelt zusätzlich die CC0-Abgabe durch einspeisende Empfänger. Für den hier bezogenen API-Bestand wird konservativ ODbL verwendet.
- Lizenz: https://opendatacommons.org/licenses/odbl/1-0/
- Erlaubter Datengebrauch: Die ODbL erlaubt Nutzung, Bearbeitung und Weitergabe mit ihren Pflichten. Quelle und Lizenz werden auf der Webseite sichtbar genannt; der normalisierte Datenbestand einschließlich Zeitreihe bleibt unter ODbL und ist direkt herunterladbar. Der Anwendungscode ist getrennt MIT-lizenziert.
- Zugang: ohne Konto oder Schlüssel.
- Dokumentiertes Kontingent: ohne Schlüssel 500 Anfragen/Tag/IP; dynamische Beschränkungen und 429 möglich. Täglich 48 geplante Abrufe, maximal 288/Tag bei lokalen manuellen Wiederholungen im Fünfminutentakt. Andere Nutzer derselben öffentlichen IP können deren Kontingent mitnutzen. Keine bezahlte Ersatzquelle.
- Gebiet: 50.03 N, 8.57 O, Radius 100 NM, öffentlicher Bezugspunkt Flughafen Frankfurt.
- Endpoint: `GET https://api.adsb.lol/v2/lat/50.03/lon/8.57/dist/100`.
- Erster technischer Test: HTTP 200, 68 Datensätze in einer Antwort. Weiterer geprüfter Test: 58 gültige Positionen, keine verworfen. Das sind flüchtige Momentaufnahmen, keine Langzeitstatistik.
- Datenlücken: fehlende Position, zu alte Position, unbekannte Höhe/Geschwindigkeit. Fehlende Werte bleiben unbekannt. Kennung ist keine bestätigte Airline. Bodenposition zählt mit; der Listenfilter trennt sie sichtbar.
- Messzeit: `now` in Unix-Millisekunden, Positionszeit `now/1000 - seen_pos`. Quellenzeit maximal 300 Sekunden alt und maximal 120 Sekunden in der Zukunft. Position maximal 120 Sekunden alt.
- Netzwerktest Windows: Python/OpenSSL meldete ein abgelaufenes Zertifikat. Windows PowerShell und System-curl mit Schannel konnten dieselbe Quelle mit aktiver Zertifikatsprüfung abrufen. Deshalb nutzt Windows `System32/curl.exe`; andere Systeme nutzen Python/urllib. Keine deaktivierte Zertifikatsprüfung.

## Alternativen

- OpenSky: https://opensky-network.org/about/terms-of-use – im Briefing wegen erforderlicher gesonderter Vereinbarung für operative Nutzung ausgeschlossen; kein automatischer Ersatz.
- adsb.fi: https://github.com/adsbfi/opendata – persönliche, nichtkommerzielle Nutzung, Namensnennung, 1 Anfrage/Sekunde. Wegen engerem Nutzungsrahmen nicht als öffentlicher Standard dieses Projekts gewählt.
- Aktien: ausdrücklich zurückgestellt. Keine Kursquelle, keine Schlüssel und keine implizite Veröffentlichungserlaubnis angenommen.

## Kostenloser Betrieb

- Standardrunner `ubuntu-latest` nur in einem öffentlichen Repository. Ein expliziter Workflow-Guard verhindert versehentlichen Betrieb in einem privaten Fork.
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- GitHub Pages für öffentliche GitHub-Free-Repositories, ausschließlich nichtkommerzielles Beobachtungsprojekt: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- Keine Actions-Artefakte oder Caches im Sammler. Die feste Oberfläche liegt im Pages-Zweig gh-pages; aktuelle Daten liest sie aus der öffentlichen JSON-Datei im main-Zweig über raw.githubusercontent.com. Deshalb ist für Messwert-Updates kein neues Pages-Deployment nötig. Keine kostenpflichtigen Runner oder Upgrades.
- Repositorygröße wird über die GitHub-API geprüft; bei 50.000 KB wird angehalten. Der aktuelle normalisierte Snapshot und 100 Tage verdichtete Zählungen werden versioniert. Git enthält ältere Versionen: Wachstum ist begrenzt überwacht, nicht durch Dateilöschung rückwirkend beseitigt.
- Cron `17,47 * * * *`: nominell 48 Läufe/Tag, verspätete oder ausfallende Läufe möglich. https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- Nach 60 Tagen ohne relevante Repositoryaktivität kann GitHub Zeitpläne abschalten. Kein künstlicher Keepalive; über Actions erneut aktivieren. Datenalter steht sichtbar auf der Seite.
- Telegram-Grundablauf: https://core.telegram.org/bots/faq – Bot vom Nutzer bei BotFather anlegen und privaten Chat starten. Kein Bot wurde vom Projekt erfunden oder ohne eingerichteten Empfänger verwendet.

## Noch offene Nachweise

Ein echter 24–72-Stunden-Test, langfristige Abdeckung und echte Ereignisse benötigen fortlaufende Sammlung. Acht frühere Wochen für denselben Wochentag und dieselbe UTC-Stunde lassen sich nicht durch erfundene Trainingsdaten ersetzen. Ein erfolgreicher erster Abruf ist keine Zuverlässigkeitsmessung.

