// Tourist Heartbeat Sender - Interactive Web

let map;
let marker;
let current = { lat: 26.1625, lng: 91.7794 };
let hbTimer = null;

const cfg = {
  get targetUrl() { return localStorage.getItem('hb_target') || 'http://localhost:2030/v1/app/ingest'; },
  set targetUrl(v) { localStorage.setItem('hb_target', v); },
  get deviceId() { return localStorage.getItem('hb_device') || 'tourist-sim-001'; },
  set deviceId(v) { localStorage.setItem('hb_device', v); },
  get interval() { return parseInt(localStorage.getItem('hb_interval') || '5', 10); },
  set interval(v) { localStorage.setItem('hb_interval', String(v)); },
};

function $(id) { return document.getElementById(id); }
function log(line) {
  const el = $('log');
  if (!el) return;
  const div = document.createElement('div');
  div.className = 'entry';
  div.textContent = `[${new Date().toLocaleTimeString()}] ${line}`;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

function initMap() {
  map = L.map('map').setView([20.5937, 78.9629], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors', maxZoom: 19, minZoom: 3
  }).addTo(map);
  map.on('click', (e) => {
    setLocation(e.latlng.lat, e.latlng.lng);
    sendOnce();
  });
  setLocation(current.lat, current.lng);
}

function setLocation(lat, lng) {
  current = { lat, lng };
  if (marker) marker.remove();
  marker = L.marker([lat, lng]).addTo(map);
  marker.bindPopup(`Lat: ${lat.toFixed(6)}<br/>Lng: ${lng.toFixed(6)}`).openPopup();
  $('coords').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
}

async function postHeartbeat(lat, lng) {
  const payload = {
    tourist_id: null,
    device_id: cfg.deviceId,
    position: { lat, lng, alt: null, speed_mps: null, ts: new Date().toISOString() },
    health: { heart_rate: null, fall_detected: null, battery: null },
    sos: null,
    app: { build: '1.0.0', platform: 'web-lite' }
  };
  try {
    const res = await fetch(cfg.targetUrl, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    const ok = res.ok;
    log(`POST ${cfg.targetUrl} -> ${res.status} ${ok ? 'OK' : await res.text()}`);
  } catch (e) {
    log(`ERROR: ${e.message}`);
  }
}

function startHeartbeat() {
  stopHeartbeat();
  const intervalMs = Math.max(1, cfg.interval) * 1000;
  hbTimer = setInterval(() => postHeartbeat(current.lat, current.lng), intervalMs);
  $('status').textContent = `Heartbeat running every ${cfg.interval}s → ${cfg.targetUrl}`;
  log(`Heartbeat started: ${cfg.interval}s → ${cfg.targetUrl}`);
}

function stopHeartbeat() {
  if (hbTimer) clearInterval(hbTimer);
  hbTimer = null;
  $('status').textContent = 'Idle';
  log('Heartbeat stopped');
}

function sendOnce() { postHeartbeat(current.lat, current.lng); }

function bindUI() {
  $('targetUrl').value = cfg.targetUrl;
  $('deviceId').value = cfg.deviceId;
  $('interval').value = cfg.interval;

  $('saveCfg').addEventListener('click', () => {
    cfg.targetUrl = $('targetUrl').value.trim();
    cfg.deviceId = $('deviceId').value.trim();
    cfg.interval = parseInt($('interval').value, 10) || 5;
    log('Configuration saved');
  });

  $('startHb').addEventListener('click', startHeartbeat);
  $('stopHb').addEventListener('click', stopHeartbeat);

  $('setLoc').addEventListener('click', () => {
    const lat = parseFloat($('lat').value);
    const lng = parseFloat($('lng').value);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      setLocation(lat, lng);
      sendOnce();
    } else {
      log('Invalid coordinates');
    }
  });

  $('viewIndia').addEventListener('click', () => {
    map.setView([20.5937, 78.9629], 5);
  });
  $('zoomLoc').addEventListener('click', () => {
    map.setView([current.lat, current.lng], 13);
  });

  document.querySelectorAll('.preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const lat = parseFloat(btn.dataset.lat);
      const lng = parseFloat(btn.dataset.lng);
      setLocation(lat, lng);
      sendOnce();
    });
  });
}

window.addEventListener('DOMContentLoaded', () => {
  bindUI();
  initMap();
  log('UI ready');
});
