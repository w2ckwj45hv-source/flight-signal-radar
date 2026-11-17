"use strict";
const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const hosted = location.hostname.endsWith(".github.io");
const repository = location.pathname.split("/").filter(Boolean)[0];
// Pages serves the interface; raw GitHub serves the collector's current public file.
const DATA_URL =
  hosted && repository
    ? `https://raw.githubusercontent.com/${location.hostname.split(".")[0]}/${encodeURIComponent(repository)}/main/web/data/state.json`
    : "data/state.json";
let state = null,
  selected = null,
  activeTab = "events",
  localServer = false;
const format = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 0 });
const timeFormat = new Intl.DateTimeFormat("de-DE", {
  timeZone: "Europe/Berlin",
  hour: "2-digit",
  minute: "2-digit",
});
const fullFormat = new Intl.DateTimeFormat("de-DE", {
  timeZone: "Europe/Berlin",
  dateStyle: "medium",
  timeStyle: "medium",
});
const text = (id, value) => {
  $(id).textContent = value;
};
const node = (tag, attrs = {}, content) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (content !== undefined) el.textContent = content;
  return el;
};
const html = (tag, className, value) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (value !== undefined) el.textContent = value;
  return el;
};
const dateText = (stamp) =>
  stamp ? fullFormat.format(new Date(stamp * 1000)) : "noch nicht vorhanden";
function age(stamp) {
  const minutes = Math.max(0, Math.floor((Date.now() / 1000 - stamp) / 60));
  return minutes < 1
    ? "vor weniger als einer Minute"
    : minutes < 60
      ? `vor ${minutes} Minuten`
      : `vor ${Math.floor(minutes / 60)} Std. ${minutes % 60} Min.`;
}
function notice(message) {
  text("notice", message);
  $("notice").hidden = !message;
}

function project(lat, lon) {
  const r = state.region;
  const a = (r.lat * Math.PI) / 180,
    b = (lat * Math.PI) / 180,
    delta = ((lon - r.lon) * Math.PI) / 180;
  const h =
    Math.sin((b - a) / 2) ** 2 +
    Math.cos(a) * Math.cos(b) * Math.sin(delta / 2) ** 2;
  const distance = 3440.065 * 2 * Math.asin(Math.min(1, Math.sqrt(h)));
  const bearing = Math.atan2(
    Math.sin(delta) * Math.cos(b),
    Math.cos(a) * Math.sin(b) - Math.sin(a) * Math.cos(b) * Math.cos(delta),
  );
  const radius = (distance / r.radius_nm) * 290;
  return [400 + Math.sin(bearing) * radius, 335 - Math.cos(bearing) * radius];
}

function updateStatus() {
  if (!state) return;
  const latest = state.latest,
    status = state.status;
  const old = !latest || Date.now() / 1000 - latest.measured_at > 2700;
  const error = status.state === "error";
  text(
    "quick-count",
    latest
      ? `${latest.valid} Flugzeuge im Gebiet · Quelle adsb.lol`
      : "Quelle adsb.lol",
  );
  text(
    "status-title",
    error
      ? "Quelle gerade nicht erreichbar"
      : !latest
        ? "Die erste Beobachtung fehlt noch"
        : old
          ? "Letzter Stand ist veraltet"
          : "Letzter Abruf erfolgreich",
  );
  text(
    "status-detail",
    latest
      ? `Gemessen ${age(latest.measured_at)}. Abruf alle 30 Minuten.`
      : "Starte den lokalen Sammler für echte Positionen.",
  );
  $("status-dot").className =
    `status-dot ${!old && !error ? "fresh" : "stale"}`;
  if (error) notice(status.message);
  else if (latest?.statistics_eligible === false)
    notice(
      "Ein großer Teil der Quellenpositionen fehlt oder ist ungültig. Die verwendbaren Positionen sind sichtbar; diese Momentaufnahme zählt nicht für die Statistik.",
    );
  else if (old && latest)
    notice(
      "Dieser Stand ist älter als 45 Minuten. Die Positionen werden nicht fortgeschrieben. Starte den Sammler oder aktualisiere die Daten.",
    );
  else notice("");
  text(
    "measurement-time",
    latest
      ? `Messung ${timeFormat.format(new Date(latest.measured_at * 1000))} Uhr`
      : "Noch keine Messung",
  );
  text(
    "source-times",
    `Quellenmessung: ${dateText(latest?.measured_at)}. Abgerufen: ${dateText(latest?.fetched_at)}. Alle angezeigten Uhrzeiten: Europe/Berlin; statistische Fenster: UTC.`,
  );
}

function renderRadar() {
  const planes = $("planes"),
    airports = $("airports");
  planes.replaceChildren();
  airports.replaceChildren();
  for (const [name, lat, lon] of [
    ["FRA", 50.0333, 8.5706],
    ["MHG", 49.4731, 8.5142],
    ["STR", 48.6899, 9.222],
    ["HHN", 49.9487, 7.2639],
  ]) {
    const [x, y] = project(lat, lon);
    const g = node("g");
    g.append(
      node("circle", { cx: x, cy: y, r: 3, class: "airport-dot" }),
      node("text", { x: x + 8, y: y + 4, class: "airport-label" }, name),
    );
    airports.append(g);
  }
  const rows = state.latest?.aircraft || [];
  rows.forEach((a, i) => {
    const [x, y] = project(a.lat, a.lon);
    const g = node("g", {
      class: `plane ${selected === a.id ? "selected" : ""}`,
      transform: `translate(${x.toFixed(2)},${y.toFixed(2)})`,
      role: "button",
      tabindex: "0",
      "data-aircraft": a.id,
      "data-kind": "plane",
      "aria-label": `${a.callsign || a.id}, ${a.ground ? "am Boden" : a.altitude_ft === null ? "Höhe unbekannt" : format.format(a.altitude_ft) + " Fuß"}`,
      "aria-pressed": String(selected === a.id),
    });
    g.append(
      node("title", {}, `${a.callsign || a.id} · ${a.registration || a.id}`),
      node("circle", { r: 14, class: "halo" }),
      node("path", {
        d: "M0-8 2-2 7 2 7 4 2 2 2 6 4 7 4 8 0 7 -4 8 -4 7 -2 6 -2 2 -7 4 -7 2 -2-2Z",
        transform: `rotate(${a.track ?? 0})`,
      }),
    );
    if (i % 7 === 0 || selected === a.id)
      g.append(
        node("text", { x: 12, y: 4, class: "plane-label" }, a.callsign || a.id),
      );
    const choose = () => selectAircraft(a.id);
    g.addEventListener("click", choose);
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        choose();
      }
    });
    planes.append(g);
  });
  $("radar-empty").hidden = rows.length > 0;
  if (!rows.length && state.latest) {
    $("radar-empty").querySelector("strong").textContent =
      "Keine gültige Position im Gebiet";
    $("radar-empty").querySelector("p").textContent =
      "Die Quelle hat einen leeren Datenstand geliefert. Das belegt keine vollständige Verkehrsfreiheit.";
  }
  text("radar-count", `${rows.length} geprüfte Positionen`);
}

function renderAnalysis() {
  const a = state.analysis;
  const descriptions = {
    learning: [
      "Sammle Vergleichsdaten",
      "Für eine Einordnung fehlen frühere Wochen mit derselben UTC-Stunde und demselben Wochentag.",
    ],
    coverage: [
      "Noch keine vollständige Stunde",
      "Pro abgeschlossener Stunde brauchen wir zwei Messungen. Datenlücken werden nicht als Verkehrsrückgang gewertet.",
    ],
    no_variance: [
      "Vergleich ohne Streuung",
      "Die bisherigen Vergleichswerte sind identisch. Daraus lässt sich kein sinnvoller z-Wert berechnen.",
    ],
    normal: [
      "Keine Auffälligkeit erkannt",
      "Die letzte vollständige Stunde liegt innerhalb der vorläufigen Prüfgrenzen.",
    ],
    signal: [
      "Eine Stunde fällt auf",
      "Die Sichtbarkeit weicht vom bisherigen Vergleich ab. Im Ereignis findest du Messwert, Vergleich und Abdeckung.",
    ],
  };
  const [title, detail] = descriptions[a.state] || descriptions.learning;
  text("analysis-title", title);
  text("analysis-detail", detail);
  text(
    "baseline-note",
    `${a.baseline_count} von ${a.required} vergleichbaren Stunden`,
  );
  $("learning-fill").style.width =
    `${Math.min(100, (a.baseline_count / a.required) * 100)}%`;
}

function renderDetails() {
  const container = $("details");
  const a = state.latest?.aircraft.find((a) => a.id === selected);
  if (!a) {
    container.replaceChildren(
      html("span", "small-heading", "Ein Flugzeug näher ansehen"),
      html("h2", "", "Jede Position erzählt mehr."),
      html(
        "p",
        "",
        "Wähle eine Maschine auf dem Radar oder in der Liste. Hier erscheinen ihre gemessenen Werte.",
      ),
    );
    return;
  }
  container.replaceChildren(
    html("span", "small-heading", "Ausgewählte Position"),
    html("h2", "", a.callsign || a.id),
    html(
      "p",
      "",
      `${a.registration || "Registrierung unbekannt"} / ${a.type || "Typ unbekannt"}`,
    ),
  );
  const close = html("button", "detail-close", "×");
  close.setAttribute("aria-label", "Auswahl schließen");
  close.addEventListener("click", () => selectAircraft(null));
  container.append(close);
  const dl = html("dl", "detail-values");
  for (const [label, value] of [
    [
      "Höhe",
      a.ground
        ? "Am Boden"
        : a.altitude_ft === null
          ? "Unbekannt"
          : `${format.format(a.altitude_ft)} ft`,
    ],
    [
      "Geschwindigkeit",
      a.speed_kt === null ? "Unbekannt" : `${format.format(a.speed_kt)} kn`,
    ],
    [
      "Flugrichtung",
      a.track === null ? "Unbekannt" : `${Math.round(a.track)}°`,
    ],
    ["Kennung", a.id],
  ]) {
    const pair = html("div");
    pair.append(html("dt", "", label), html("dd", "", value));
    dl.append(pair);
  }
  container.append(
    dl,
    html(
      "p",
      "quiet",
      `Position: ${a.lat.toFixed(4)}° N, ${a.lon.toFixed(4)}° O. Gemessen ${timeFormat.format(new Date(a.observed_at * 1000))} Uhr.`,
    ),
  );
}
function selectAircraft(id) {
  const focused = document.activeElement,
    focusId = focused?.getAttribute("data-aircraft"),
    kind = focused?.getAttribute("data-kind");
  selected = id;
  renderRadar();
  renderDetails();
  renderList();
  if (focusId && kind)
    document
      .querySelector(`[data-aircraft="${focusId}"][data-kind="${kind}"]`)
      ?.focus({ preventScroll: true });
}

function renderList() {
  const query = $("search").value.toLowerCase().trim(),
    filter = $("filter").value;
  const all = state.latest?.aircraft || [];
  const rows = all.filter(
    (a) =>
      [a.callsign, a.id, a.registration, a.type]
        .join(" ")
        .toLowerCase()
        .includes(query) &&
      (filter === "all" ||
        (filter === "ground" ? a.ground : !a.ground && a.altitude_ft !== null)),
  );
  const body = $("aircraft-list");
  body.replaceChildren();
  rows
    .sort((a, b) => (a.callsign || a.id).localeCompare(b.callsign || b.id))
    .forEach((a) => {
      const tr = html("tr", selected === a.id ? "selected" : "");
      const name = html("td", "", a.callsign || a.id);
      name.append(html("small", "", a.registration || a.id));
      tr.append(name);
      [
        a.type || "—",
        a.ground
          ? "Am Boden"
          : a.altitude_ft === null
            ? "Unbekannt"
            : `${format.format(a.altitude_ft)} ft`,
        a.speed_kt === null ? "Unbekannt" : `${format.format(a.speed_kt)} kn`,
        `${a.lat.toFixed(3)} / ${a.lon.toFixed(3)}`,
      ].forEach((v) => tr.append(html("td", "", v)));
      const action = html("td"),
        button = html("button", "row-button", "Ansehen");
      button.setAttribute("aria-label", `${a.callsign || a.id} ansehen`);
      button.dataset.aircraft = a.id;
      button.dataset.kind = "list";
      button.addEventListener("click", () => {
        selectAircraft(a.id);
        if (matchMedia("(max-width:760px)").matches)
          $("details").scrollIntoView({
            behavior: matchMedia("(prefers-reduced-motion:reduce)").matches
              ? "instant"
              : "smooth",
            block: "center",
          });
      });
      action.append(button);
      tr.append(action);
      body.append(tr);
    });
  if (!rows.length) {
    const td = html(
      "td",
      "",
      all.length
        ? "Keine Maschine passt zu deiner Suche."
        : "Nach dem ersten erfolgreichen Abruf erscheinen hier die Positionen.",
    );
    td.colSpan = 6;
    const tr = html("tr");
    tr.append(td);
    body.append(tr);
  }
  text(
    "list-summary",
    `${rows.length} von ${all.length} Positionen angezeigt. Höhen in Fuß, Geschwindigkeit über Grund in Knoten.`,
  );
}

function renderChart() {
  const chart = $("chart");
  chart.replaceChildren();
  const hours = Number($("period").value),
    now = Date.now() / 1000;
  const rows = state.analysis.hourly.filter((h) => h.time > now - hours * 3600);
  if (!rows.length) {
    const empty = html("div", "chart-empty");
    const illustration = node("svg", {
      viewBox: "0 0 60 60",
      "aria-hidden": "true",
    });
    illustration.append(
      node("path", {
        d: "M8 46h44M8 46V12M14 37l9-7 10 3 12-16",
        fill: "none",
        stroke: "#147D79",
        "stroke-width": 1.5,
        "stroke-dasharray": "3 4",
      }),
      node("circle", { cx: 45, cy: 17, r: 3, fill: "#147D79" }),
    );
    const copy = html("div");
    copy.append(
      html("strong", "", "Die Kurve wächst mit der Zeit."),
      html(
        "p",
        "",
        "Nach der ersten abgeschlossenen UTC-Stunde erscheinen echte Messwerte. Es wird nichts ergänzt.",
      ),
    );
    empty.append(illustration, copy);
    chart.append(empty);
    return;
  }
  const svg = node("svg", {
    viewBox: "0 0 650 180",
    role: "img",
    "aria-label": `${rows.length} beobachtete Stunden im gewählten Zeitraum; ${rows.filter((r) => r.coverage >= 0.8).length} vollständig erfasst.`,
    preserveAspectRatio: "none",
  });
  const end = Math.floor(now / 3600) * 3600,
    start = end - hours * 3600,
    max = Math.max(10, ...rows.map((r) => r.value)) * 1.15;
  for (let i = 0; i < 4; i++) {
    const y = 18 + i * 43;
    svg.append(
      node("path", {
        d: `M34 ${y}H640`,
        stroke: "#123F46",
        "stroke-opacity": 0.12,
      }),
      node(
        "text",
        { x: 2, y: y + 4, fill: "#183036", "font-size": 10 },
        String(Math.round(max * (1 - i / 3))),
      ),
    );
  }
  let prev = null;
  rows.forEach((row) => {
    const x = 34 + ((row.time - start) / (end - start)) * 606,
      y = 147 - (row.value / max) * 129;
    if (prev && row.time - prev.time === 3600)
      svg.append(
        node("path", {
          d: `M${prev.x} ${prev.y}L${x} ${y}`,
          stroke: "#147D79",
          "stroke-width": 2,
          fill: "none",
          "stroke-dasharray":
            row.coverage < 0.8 || prev.coverage < 0.8 ? "4 4" : "none",
        }),
      );
    const dot = node("circle", {
      cx: x,
      cy: y,
      r: 3.5,
      fill: row.coverage >= 0.8 ? "#147D79" : "#F5F1E8",
      stroke: "#147D79",
    });
    dot.append(
      node(
        "title",
        {},
        `${dateText(row.time)}: Median ${row.value}, ${row.samples}/${row.expected} Messungen`,
      ),
    );
    svg.append(dot);
    prev = { ...row, x, y };
  });
  for (const [t, x, anchor] of [
    [start, 34, "start"],
    [end, 640, "end"],
  ])
    svg.append(
      node(
        "text",
        { x, y: 174, "text-anchor": anchor, fill: "#183036", "font-size": 10 },
        hours > 24
          ? new Intl.DateTimeFormat("de-DE", {
              timeZone: "Europe/Berlin",
              day: "2-digit",
              month: "2-digit",
            }).format(new Date(t * 1000))
          : timeFormat.format(new Date(t * 1000)),
      ),
    );
  chart.append(svg);
}

function renderEvents() {
  const target = $("event-list");
  target.replaceChildren();
  const rows = activeTab === "log" ? state.log : [...state.events].reverse();
  if (!rows.length) {
    const empty = html("div", "event-empty");
    empty.append(
      html(
        "strong",
        "",
        activeTab === "log"
          ? "Noch kein Abruf protokolliert."
          : "Noch keine Auffälligkeit.",
      ),
      html(
        "p",
        "",
        activeTab === "log"
          ? "Jeder Abruf hinterlässt hier einen kurzen Eintrag."
          : "Die Vergleichsbasis wächst erst. Bis sie ausreicht, werden keine statistischen Ereignisse behauptet.",
      ),
    );
    target.append(empty);
    return;
  }
  rows.slice(0, 30).forEach((e) => {
    const item = html("div", "event-item"),
      t = html("time", "", timeFormat.format(new Date(e.time * 1000)) + " Uhr");
    t.dateTime = new Date(e.time * 1000).toISOString();
    t.title = dateText(e.time);
    const content = html("div");
    if (activeTab === "log")
      content.append(
        html(
          "strong",
          "",
          e.state === "ok"
            ? "Datenstand aktualisiert"
            : "Abruf nicht erfolgreich",
        ),
        html("p", "", e.message),
      );
    else
      content.append(
        html(
          "strong",
          "",
          e.kind === "increase"
            ? "Mehr Flugzeuge sichtbar"
            : "Weniger Flugzeuge sichtbar",
        ),
        html(
          "p",
          "",
          `Stundenmedian ${e.value}; Vergleich ${e.baseline.toFixed(1)}. z = ${e.z}; Abdeckung ${Math.round(e.coverage * 100)} %. ${dateText(e.time)}.`,
        ),
      );
    item.append(t, content);
    target.append(item);
  });
}
function render() {
  text("count", state.latest ? String(state.latest.valid) : "—");
  renderRadar();
  renderAnalysis();
  renderDetails();
  renderList();
  renderChart();
  renderEvents();
  updateStatus();
}
async function load() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw Error("unavailable");
    const next = await response.json();
    if (
      next.schema !== 1 ||
      !next.region ||
      !next.analysis ||
      !Array.isArray(next.observations)
    )
      throw Error("invalid");
    state = next;
    render();
  } catch {
    if (!state) {
      text("status-title", "Noch kein lesbarer Datenstand");
      text(
        "status-detail",
        "Starte „Radar starten“ im Projektordner. Der erste Abruf erstellt die Daten.",
      );
      $("radar-empty").hidden = false;
      notice(
        "Es wurde kein gültiger Datenstand gefunden. Die Anzeige erfindet keine Positionen.",
      );
    } else
      notice(
        "Die Ergebnisdatei ist gerade nicht lesbar. Der bisherige Stand bleibt sichtbar.",
      );
  }
}
$("refresh").addEventListener("click", async () => {
  const button = $("refresh");
  button.disabled = true;
  button.textContent = "Wird geprüft …";
  try {
    if (localServer) {
      const r = await fetch("api/refresh", {
        method: "POST",
        headers: { "X-Radar-Request": "refresh" },
      });
      if (!r.ok) throw Error("refresh");
      state = await r.json();
      render();
      const wait = Math.max(
        0,
        Math.ceil((state.status.attempted_at + 300 - Date.now() / 1000) / 60),
      );
      if (wait > 0)
        notice(
          `Datenstand geprüft. Zum Schutz des kostenlosen Kontingents liegen zwischen Quellenabrufen mindestens 5 Minuten. Nächster automatischer Abruf: ${timeFormat.format(new Date(state.status.next_at * 1000))} Uhr.`,
        );
    } else await load();
  } catch {
    notice(
      "Die Aktualisierung ist nicht gelungen. Prüfe, ob der lokale Sammler noch läuft.",
    );
  } finally {
    button.disabled = false;
    button.textContent = "Daten aktualisieren ↻";
  }
});
$("search").addEventListener("input", () => state && renderList());
$("filter").addEventListener("change", () => state && renderList());
$("period").addEventListener("change", () => state && renderChart());
for (const tab of ["events", "log"])
  $(tab + "-tab").addEventListener("click", () => {
    activeTab = tab;
    for (const name of ["events", "log"]) {
      $(name + "-tab").classList.toggle("active", name === tab);
      $(name + "-tab").setAttribute("aria-pressed", String(name === tab));
    }
    if (state) renderEvents();
  });
if (!hosted)
  fetch("api/status")
    .then((r) => (r.ok ? r.json() : null))
    .then((r) => {
      localServer = r?.local === true;
    })
    .catch(() => {});
const download = document.querySelector(
  'a[download="flight-signal-radar-daten.json"]',
);
download.href = DATA_URL;
load();
setInterval(load, 60000);
setInterval(updateStatus, 15000);
