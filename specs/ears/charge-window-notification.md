# Charge-window browser notification

> Brukeren får et nettleservarsel 10 minutter før det billigste ladevinduet starter, slik at elbilen kan settes på lading uten å sjekke siden manuelt.

**Type:** New feature
**System:** Strømpris-appen (frontend React-app + backend `/api/prices`)
**Date:** 2026-05-28

## Context

Appen viser i dag dagens timepriser fra hvakosterstrommen.no og fremhever et billigste 3-timers vindu. Brukeren må selv sjekke siden for å vite når lading bør starte. Denne specen legger til et nettleservarsel som fyrer 10 minutter før det billigste vinduet starter, og utvider vinduet til 4 timer slik at en typisk lading rekkes innenfor det. Frontenden bruker den vendrete React-stakken; ingen Service Worker innføres, så varslene krever at fanen er åpen (i bakgrunnen eller forgrunnen).

## Pending changes

Implementering ferdig i `backend/app/routers/prices.py` og `frontend/app.js`. Awaiting UAT — manuell verifisering i nettleser per `## Verification notes` nedenfor. Sett til `None.` etter UAT.

## Requirements

### Functional requirements

REQ-001 [✅ Implemented]: While computing the cheapest charging window, the backend shall return the 4 consecutive hours of the day with the lowest average NOK_per_kWh.
  - `backend/app/routers/prices.py:14` `CHARGE_WINDOW_HOURS = 4`; `cheapest_window` scans consecutive windows of that length.

REQ-002 [✅ Implemented]: While `Notification.permission` is `"default"` and the Notification API is available, the frontend shall display a button labelled "Aktiver ladevarsel".
  - `frontend/app.js:104-108`.

REQ-003 [✅ Implemented]: When the user clicks the "Aktiver ladevarsel" button, the frontend shall call `Notification.requestPermission()`.
  - `frontend/app.js:206-211` (button `onClick` → `requestNotificationPermission`).

REQ-004 [✅ Implemented]: When `Notification.requestPermission()` resolves to `"granted"`, the frontend shall schedule a single browser notification to fire exactly 10 minutes before the `cheapest_window.start` returned by `/api/prices` for the currently selected price area.
  - `frontend/app.js:14` `LEAD_MINUTES = 10`; `computeFireTime` + scheduling effect at `app.js:160-187`.

REQ-005 [✅ Implemented]: While a notification for the current selection is scheduled and pending, the frontend shall replace the "Aktiver ladevarsel" button with a non-interactive label of the form `"Varsel planlagt kl HH:MM"`, where `HH:MM` is the scheduled fire time formatted in Norwegian locale (`nb-NO`, 24-hour).
  - `frontend/app.js:97-102` (`toLocaleTimeString("nb-NO", {hour: "2-digit", minute: "2-digit"})`).

REQ-006 [✅ Implemented]: When the scheduled fire time is reached, the frontend shall display a browser notification whose title is `"⚡ Lad elbilen om 10 minutter"` and whose body contains the cheapest window's start time, end time (each formatted `HH:MM`), and average price formatted as `"<X.X> øre/kWh"`.
  - `frontend/app.js:181-183` (title uses `LEAD_MINUTES`; body has start, end, øre/kWh).

REQ-007 [✅ Implemented]: When the user changes the selected price area, the frontend shall cancel any pending scheduled notification for the previously selected area.
  - `frontend/app.js:161-164` (effect clears `timeoutRef` on re-run; `setData(null)` on area change at `:135` triggers the effect).

REQ-007b [✅ Implemented]: When the user changes the selected price area and `Notification.permission` is `"granted"`, the frontend shall schedule a new notification based on the cheapest window of the newly selected area.
  - Same effect at `frontend/app.js:160-187`; new `data` from the area-change fetch reschedules.

REQ-008 [✅ Implemented]: While a notification has already been delivered for a given `(date, area, cheapest_window.start)` tuple, the frontend shall not deliver another notification for the same tuple within the same browser session.
  - `frontend/app.js:128, 174, 178-179` (`deliveredRef` Set keyed by `date|area|window.start`).

REQ-009 [✅ Implemented]: If `Notification.permission` becomes `"granted"` after the computed fire time (10 minutes before `cheapest_window.start`) has already passed but before `cheapest_window.end`, then the frontend shall display the notification immediately.
  - `frontend/app.js:30-32` (returns `delay: 0` when `now >= target` but `now < end`).

### Unwanted behavior / error handling

REQ-010 [✅ Implemented]: If `Notification.requestPermission()` resolves to `"denied"`, then the frontend shall display an inline message stating that varsler må tillates i nettleseren for at funksjonen skal virke.
  - `frontend/app.js:91-95`.

REQ-010b [✅ Implemented]: If `Notification.requestPermission()` resolved to `"denied"` earlier in the session, then the frontend shall not call `Notification.requestPermission()` again during the same session.
  - `frontend/app.js:129, 207, 210` (`deniedRef` short-circuit).

REQ-011 [✅ Implemented]: If the browser does not expose `window.Notification`, then the frontend shall display an inline message stating that nettleseren ikke støtter varsler.
  - `frontend/app.js:85-89` (`permission === "unsupported"` branch; set at `:119-121`).

REQ-011b [✅ Implemented]: If the browser does not expose `window.Notification`, then the frontend shall not render the "Aktiver ladevarsel" button.
  - Same branch returns before the button branch.

REQ-012 [✅ Implemented]: If the computed fire time (10 minutes before `cheapest_window.start`) is already in the past at page load and `cheapest_window.end` is also in the past, then the frontend shall not schedule a notification.
  - `frontend/app.js:30` (`if (now >= end) return null;`) → effect bails at `:170`.

REQ-012b [✅ Implemented]: While no notification is scheduled and no notification has been delivered, the frontend shall not display the "Varsel planlagt"-label.
  - `frontend/app.js:165` (`setScheduledFor(null)` on every effect run); label only renders when `scheduledFor` is truthy (`:97`).

### Constraints

REQ-013 [✅ Implemented]: The frontend shall implement notification scheduling using `setTimeout` against the current selection's `cheapest_window.start`.
  - `frontend/app.js:187` (`setTimeout(fire, delay)`).

REQ-013b [✅ Implemented]: The frontend shall not register a Service Worker for this feature.
  - No `navigator.serviceWorker` references in `frontend/`.

REQ-014 [✅ Implemented, awaiting UAT]: The frontend shall fire the notification within ±30 seconds of the target time (10 minutes before `cheapest_window.start`).
  - `frontend/app.js:198-204` (`visibilitychange` listener bumps `visibilityTick`, reschedule effect re-runs to defend against background-tab `setTimeout` throttling). Best-effort — needs manual browser verification per `## Verification notes`.

REQ-015 [✅ Implemented]: The frontend shall persist deduplication state for REQ-008 only for the duration of the current page session (in-memory; reload clears it).
  - `frontend/app.js:128` (`useRef(new Set())`; no `localStorage`/`sessionStorage` writes).

## Verification notes

- **REQ-001:** Update backend unit test `test_cheapest_window_picks_lowest_average` so the asserted window length is 4; add a test that constructs 24 prices and confirms the returned window has `hours == 4`.
- **REQ-002, 003, 005, 011:** Manual browser check with the Notification API available — confirm button visible in default state, permission prompt on click, label swap after grant, and inline error when `Notification` is undefined (simulate by deleting `window.Notification`).
- **REQ-004, 006, 014:** Adjust the upstream price data via DevTools network override so the cheapest window starts 12 minutes ahead; verify the notification fires within the 30-second window and contains the formatted body.
- **REQ-007:** Change the area dropdown after a notification is scheduled and verify the label updates to the new fire time.
- **REQ-008:** Reload-free area toggle back-and-forth must not produce duplicate notifications for the same tuple within the session.
- **REQ-009:** Use DevTools to set system clock or use a stubbed price response with `cheapest_window.start` 5 minutes in the past; grant permission and verify immediate fire.
- **REQ-010:** Block notifications in browser settings and click the button — confirm the inline denial message appears and the button does not re-prompt.
- **REQ-012:** Stub `/api/prices` so `cheapest_window.start` is before "now"; verify no schedule, no label.

## Open questions

- Should the notification include a click action (e.g., focusing the tab or showing a deep-link to the chart)? Spec currently leaves the notification non-interactive — flag if behaviour beyond display is desired.
- Should the dedupe state survive reloads (e.g., via `localStorage`)? Current spec scopes it to the session (REQ-015); revisit if users complain about duplicate notifications across reloads.
