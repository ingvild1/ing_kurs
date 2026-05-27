async function loadHealth() {
  try {
    const r = await fetch('/api/health');
    if (!r.ok) throw new Error('health request failed');
    const data = await r.json();
    document.getElementById('status').textContent = data.status;
  } catch (e) {
    showError('Backend unreachable — could not load /api/health.');
  }
}

async function loadPings() {
  try {
    const r = await fetch('/api/pings');
    if (!r.ok) throw new Error('pings request failed');
    const data = await r.json();
    document.getElementById('ping-count').textContent = `Pings: ${data.length}`;
  } catch (e) {
    showError('Backend unreachable — could not load /api/pings.');
  }
}

async function sendPing() {
  try {
    const r = await fetch('/api/pings', { method: 'POST' });
    if (!r.ok) throw new Error('post request failed');
    await loadPings();
  } catch (e) {
    showError('Backend unreachable — could not POST /api/pings.');
  }
}

function showError(msg) {
  const el = document.getElementById('error');
  el.textContent = msg;
  el.hidden = false;
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('send-ping').addEventListener('click', sendPing);
  loadHealth();
  loadPings();
});
