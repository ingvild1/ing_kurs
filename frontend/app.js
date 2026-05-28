// React app — uses vendored React UMD + htm (no JSX build step).
// No service worker — tab-open is the contract for notifications.
const { useState, useEffect, useMemo, useRef } = React;
const html = htm.bind(React.createElement);

const AREAS = [
  ["NO1", "Oslo / Øst-Norge"],
  ["NO2", "Kristiansand / Sør-Norge"],
  ["NO3", "Trondheim / Midt-Norge"],
  ["NO4", "Tromsø / Nord-Norge"],
  ["NO5", "Bergen / Vest-Norge"],
];

const LEAD_MINUTES = 10;

function formatHour(iso) {
  return new Date(iso).toLocaleTimeString("nb-NO", { hour: "2-digit", minute: "2-digit" });
}

function formatPrice(nok) {
  return (nok * 100).toFixed(1) + " øre";
}

// REQ-004/009/012: returns the fire-time for the notification, or null to skip.
// delay=0 with fireAt=now means "fire immediately" (target already passed but window still active).
function computeFireTime(window, now) {
  const start = new Date(window.start);
  const end = new Date(window.end);
  const target = new Date(start.getTime() - LEAD_MINUTES * 60_000);
  if (now >= end) return null;
  if (now >= target) return { delay: 0, fireAt: now };
  return { delay: target.getTime() - now.getTime(), fireAt: target };
}

function PriceBar({ price, maxNok, isCheapest, isCurrent }) {
  const heightPct = Math.max(4, (price.NOK_per_kWh / maxNok) * 100);
  const base = isCheapest ? "bg-emerald-500" : "bg-slate-300";
  const ring = isCurrent ? "ring-2 ring-amber-500 ring-offset-1" : "";
  return html`
    <div class="flex flex-col items-center flex-1 min-w-0">
      <div class="text-[10px] text-slate-500 mb-1 truncate w-full text-center">${formatPrice(price.NOK_per_kWh)}</div>
      <div class="w-full flex items-end" style=${{ height: "160px" }}>
        <div class=${`w-full rounded-t ${base} ${ring}`} style=${{ height: `${heightPct}%` }}></div>
      </div>
      <div class="text-[10px] text-slate-600 mt-1">${formatHour(price.time_start)}</div>
    </div>
  `;
}

function ChargeAlert({ window: w }) {
  if (!w) return null;
  const now = new Date();
  const start = new Date(w.start);
  const end = new Date(w.end);
  const chargingNow = now >= start && now < end;
  const upcoming = now < start;

  let cls, title, body;
  if (chargingNow) {
    cls = "border-emerald-400 bg-emerald-50 text-emerald-900";
    title = "⚡ Lad nå!";
    body = `Vi er midt i det billigste vinduet (${formatHour(w.start)}–${formatHour(w.end)}). Snittpris: ${formatPrice(w.avg_nok_per_kwh)}/kWh.`;
  } else if (upcoming) {
    const minsTo = Math.max(1, Math.round((start - now) / 60000));
    const h = Math.floor(minsTo / 60);
    const m = minsTo % 60;
    cls = "border-amber-400 bg-amber-50 text-amber-900";
    title = `🕒 Vent ${h}t ${m}min med å lade`;
    body = `Billigste ${w.hours}-timers vindu starter ${formatHour(w.start)} og varer til ${formatHour(w.end)}. Snittpris: ${formatPrice(w.avg_nok_per_kwh)}/kWh.`;
  } else {
    cls = "border-slate-300 bg-slate-50 text-slate-800";
    title = "Dagens billigste vindu er over";
    body = `Det var ${formatHour(w.start)}–${formatHour(w.end)} (snitt ${formatPrice(w.avg_nok_per_kwh)}/kWh). Nye priser publiseres ca. kl 13.`;
  }
  return html`
    <div class=${`rounded-xl border-2 p-5 ${cls}`}>
      <div class="text-xl font-bold">${title}</div>
      <p class="mt-1 text-sm">${body}</p>
    </div>
  `;
}

function NotifyControls({ permission, scheduledFor, onRequest }) {
  // REQ-011/011b: API missing → message, no button.
  if (permission === "unsupported") {
    return html`<div role="alert" class="rounded-lg border border-amber-300 bg-amber-50 text-amber-900 p-3 text-sm">
      Nettleseren støtter ikke varsler.
    </div>`;
  }
  // REQ-010: denied → message, no button (also covers pre-blocked origin at load).
  if (permission === "denied") {
    return html`<div role="alert" class="rounded-lg border border-amber-300 bg-amber-50 text-amber-900 p-3 text-sm">
      Varsler må tillates i nettleseren for at funksjonen skal virke.
    </div>`;
  }
  // REQ-005: scheduled → non-interactive label replaces the button.
  if (scheduledFor) {
    const hhmm = new Date(scheduledFor).toLocaleTimeString("nb-NO", { hour: "2-digit", minute: "2-digit" });
    return html`<div class="rounded-lg border border-emerald-300 bg-emerald-50 text-emerald-900 p-3 text-sm font-medium">
      🔔 Varsel planlagt kl ${hhmm}
    </div>`;
  }
  // REQ-002/003: default permission → request button.
  if (permission === "default") {
    return html`<button type="button" onClick=${onRequest}
      class="rounded bg-emerald-600 text-white px-4 py-2 hover:bg-emerald-700 font-medium">
      🔔 Aktiver ladevarsel
    </button>`;
  }
  // permission === "granted" but no schedule today (window already passed). Quiet status.
  return html`<div class="text-xs text-slate-500">Varsler aktivert (intet vindu å planlegge i dag).</div>`;
}

function App() {
  const [area, setArea] = useState("NO1");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [permission, setPermission] = useState(
    typeof Notification === "undefined" ? "unsupported" : Notification.permission,
  );
  const [scheduledFor, setScheduledFor] = useState(null);
  // REQ-009: background tab throttling can drift setTimeout; bump on visibility to reschedule.
  const [visibilityTick, setVisibilityTick] = useState(0);

  // Refs: mutated without re-render; survive area changes within one session.
  const timeoutRef = useRef(null);
  const deliveredRef = useRef(new Set()); // REQ-008/015: in-memory dedupe per session.
  const deniedRef = useRef(false); // REQ-010b: short-circuit re-prompt.

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null); // clears stale label via the scheduling effect.
    fetch(`/api/prices?area=${area}`)
      .then(async (r) => {
        if (!r.ok) throw new Error((await r.json()).detail || "Kunne ikke hente priser");
        return r.json();
      })
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [area]);

  // REQ-004/005/007/007b/012/013: schedule (or cancel) the notification whenever
  // data or permission changes. Cleanup cancels any pending timeout from the prior run.
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setScheduledFor(null);

    if (permission !== "granted" || !data?.cheapest_window) return;

    const result = computeFireTime(data.cheapest_window, new Date());
    if (!result) return; // REQ-012: whole window is in the past.

    const { delay, fireAt } = result;
    const w = data.cheapest_window;
    const key = `${data.date}|${data.area}|${w.start}`;

    const fire = () => {
      // REQ-008: dedupe — never deliver the same (date, area, window-start) twice per session.
      if (deliveredRef.current.has(key)) return;
      deliveredRef.current.add(key);
      // REQ-006: title + body containing start, end, average price.
      new Notification(`⚡ Lad elbilen om ${LEAD_MINUTES} minutter`, {
        body: `Billigste vindu ${formatHour(w.start)}–${formatHour(w.end)}. Snittpris ${(w.avg_nok_per_kwh * 100).toFixed(1)} øre/kWh.`,
      });
    };

    // Same-day window — delay always < 24h, well within setTimeout's 32-bit range.
    timeoutRef.current = setTimeout(fire, delay);
    setScheduledFor(fireAt.toISOString());

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [data, permission, visibilityTick]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") setVisibilityTick((t) => t + 1);
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, []);

  const requestNotificationPermission = async () => {
    if (deniedRef.current) return; // REQ-010b
    const result = await Notification.requestPermission();
    setPermission(result);
    if (result === "denied") deniedRef.current = true;
  };

  const maxNok = useMemo(() => {
    if (!data?.prices?.length) return 1;
    return Math.max(...data.prices.map((p) => p.NOK_per_kWh));
  }, [data]);

  const cheapestRange = useMemo(() => {
    const out = new Set();
    if (!data?.cheapest_window) return out;
    const startMs = new Date(data.cheapest_window.start).getTime();
    const endMs = new Date(data.cheapest_window.end).getTime();
    for (let i = 0; i < data.prices.length; i++) {
      const p = data.prices[i];
      if (new Date(p.time_start).getTime() >= startMs && new Date(p.time_end).getTime() <= endMs) out.add(i);
    }
    return out;
  }, [data]);

  return html`
    <main class="max-w-5xl mx-auto p-6 space-y-6">
      <header class="space-y-1">
        <h1 class="text-3xl font-bold">⚡ Strømpriser i dag</h1>
        <p class="text-slate-600">Få vite når det er billigst å lade elbilen.</p>
      </header>

      <div class="flex flex-wrap items-center gap-3">
        <label for="area" class="text-sm font-medium text-slate-700">Prisområde:</label>
        <select id="area" value=${area} onChange=${(e) => setArea(e.target.value)}
                class="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">
          ${AREAS.map(([code, label]) => html`<option key=${code} value=${code}>${code} – ${label}</option>`)}
        </select>
        <div class="ml-auto">
          <${NotifyControls} permission=${permission} scheduledFor=${scheduledFor}
                             onRequest=${requestNotificationPermission} />
        </div>
      </div>

      ${loading && html`<div class="text-slate-500">Henter priser…</div>`}
      ${error && html`<div role="alert" class="rounded-lg border border-red-300 bg-red-50 text-red-800 p-4">${error}</div>`}

      ${data && html`
        <${ChargeAlert} window=${data.cheapest_window} />

        <section class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="flex items-baseline justify-between mb-3">
            <h2 class="text-lg font-semibold">Timepris (${data.date})</h2>
            <div class="text-xs text-slate-500 flex gap-3">
              <span class="flex items-center gap-1"><span class="inline-block w-3 h-3 bg-emerald-500 rounded"></span>Billigste vindu</span>
              <span class="flex items-center gap-1"><span class="inline-block w-3 h-3 bg-slate-300 ring-2 ring-amber-500 rounded"></span>Akkurat nå</span>
            </div>
          </div>
          <div class="flex gap-0.5 items-end">
            ${data.prices.map((p, i) => html`
              <${PriceBar} key=${p.time_start} price=${p} maxNok=${maxNok}
                           isCheapest=${cheapestRange.has(i)}
                           isCurrent=${i === data.current_hour_index} />
            `)}
          </div>
        </section>

        <p class="text-xs text-slate-500">
          Datakilde: <a href="https://www.hvakosterstrommen.no" class="underline">hvakosterstrommen.no</a>.
          Prisene er spotpris uten nettleie, avgifter og mva.
        </p>
      `}
    </main>
  `;
}

ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
