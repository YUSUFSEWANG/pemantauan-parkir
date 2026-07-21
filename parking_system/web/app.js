const API_BASE = "";
let selectedLotId = null;
let lotsCache = {};
let searchQuery = "";
let sortMode = "name";

// Info tambahan (non-parkir) untuk lahan tertentu, contoh: profil institusi
const INSTITUTION_INFO = {
  "PP-ABNAUL-AMIR": {
    type: "Sekolah Agama",
    title: "Pondok Pesantren Abnaul Amir",
    address: "H9QV+5C8, Moncobalang, Desa Bontosunggu, Kec. Bontonompo Selatan, Kabupaten Gowa, Sulawesi Selatan 92153",
    fields: [
      ["Nama Satuan", "MAS Abnaul Amir"],
      ["NPSN", "40320446"],
      ["Jenjang", "MA (Madrasah Aliyah) — Dikmen"],
      ["Status", "Swasta"],
      ["Kecamatan", "Bontonompo Selatan"],
      ["Kabupaten", "Gowa"],
      ["Provinsi", "Sulawesi Selatan"],
      ["Telepon", "0813-4263-6860"],
    ],
  },
};

const barrierSVG = `
<svg viewBox="0 0 34 34" width="34" height="34">
  <circle cx="4" cy="17" r="3" fill="var(--lane-yellow)"/>
  <rect class="arm" x="4" y="15" width="26" height="4" rx="2" fill="var(--full)"/>
</svg>`;

function fmt(n) { return n.toLocaleString('id-ID'); }

function gaugeColor(rate) {
  if (rate >= 90) return 'var(--full)';
  if (rate >= 70) return 'var(--warn)';
  return 'var(--available)';
}

function renderSummary(lots) {
  const total = lots.reduce((a, l) => a + l.total_slots, 0);
  const occupied = lots.reduce((a, l) => a + l.occupied_slots, 0);
  const available = total - occupied;
  const online = lots.filter(l => l.status === 'online').length;
  document.getElementById('sum-lots').textContent = lots.length;
  document.getElementById('sum-available').textContent = fmt(available);
  document.getElementById('sum-occupied').textContent = fmt(occupied);
  document.getElementById('sum-rate').textContent = total ? (Math.round(occupied/total*1000)/10) + '%' : '–';
  document.getElementById('sum-online').textContent = online + '/' + lots.length;
}

function lotCardHTML(lot) {
  const rate = lot.occupancy_rate;
  const isOpen = lot.available_slots > 0;
  return `
  <div class="lot-card ${lot.id === selectedLotId ? 'selected' : ''}" data-id="${lot.id}">
    <div class="lot-card-top">
      <div>
        <div class="lot-id">${lot.id} · ${lot.node_id || '—'}</div>
        <div class="lot-name">${lot.name}</div>
        <div class="lot-location">${lot.location || ''}</div>
      </div>
      <div class="barrier ${isOpen ? 'open' : ''}">${barrierSVG}</div>
    </div>
    <div class="lot-numbers">
      <span class="lot-available" style="color:${gaugeColor(rate)}">${lot.available_slots}</span>
      <span class="lot-total">/ ${lot.total_slots} slot tersedia</span>
    </div>
    <div class="lot-caption">Okupansi ${rate}%</div>
    <div class="gauge"><div class="gauge-fill" style="width:${rate}%; background:${gaugeColor(rate)}"></div></div>
    <div class="lot-footer">
      <span>${lot.status === 'online' ? '● ONLINE' : '○ OFFLINE'}</span>
      <span>${new Date(lot.last_update).toLocaleTimeString('id-ID')}</span>
    </div>
  </div>`;
}

function applyFilterSort(lots) {
  let out = lots;
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    out = out.filter(l =>
      l.name.toLowerCase().includes(q) ||
      l.id.toLowerCase().includes(q) ||
      (l.location || "").toLowerCase().includes(q)
    );
  }
  out = [...out];
  if (sortMode === "name") out.sort((a, b) => a.name.localeCompare(b.name));
  if (sortMode === "available") out.sort((a, b) => b.available_slots - a.available_slots);
  if (sortMode === "rate") out.sort((a, b) => b.occupancy_rate - a.occupancy_rate);
  return out;
}

function renderLots(lots) {
  lots.forEach(l => lotsCache[l.id] = l);
  const grid = document.getElementById('lots-grid');
  const view = applyFilterSort(lots);
  grid.innerHTML = view.length
    ? view.map(lotCardHTML).join('')
    : `<p style="color:var(--text-dim); grid-column:1/-1;">Tidak ada lahan yang cocok dengan pencarian.</p>`;
  grid.querySelectorAll('.lot-card').forEach(card => {
    card.addEventListener('click', () => selectLot(card.dataset.id));
  });
  renderSummary(lots);
}

function renderInfoPanel(lotId) {
  const panel = document.getElementById('info-panel');
  const info = INSTITUTION_INFO[lotId];
  if (!info) { panel.hidden = true; return; }
  panel.hidden = false;
  document.getElementById('info-type').textContent = info.type;
  document.getElementById('info-title').textContent = info.title;
  document.getElementById('info-address').textContent = info.address;
  document.getElementById('info-photo').textContent = info.title;
  document.getElementById('info-grid').innerHTML = info.fields
    .map(([k, v]) => `<div class="info-item"><span class="k">${k}</span><span class="v">${v}</span></div>`)
    .join('');
}

async function selectLot(lotId) {
  selectedLotId = lotId;
  document.querySelectorAll('.lot-card').forEach(c => {
    c.classList.toggle('selected', c.dataset.id === lotId);
  });
  const lot = lotsCache[lotId];
  document.getElementById('history-lot-name').textContent = lot ? lot.name : lotId;
  renderInfoPanel(lotId);
  await loadHistory(lotId);
}

async function loadHistory(lotId) {
  const res = await fetch(`${API_BASE}/api/lots/${lotId}/history?limit=60`);
  const rows = await res.json();
  drawHistoryChart(rows);
}

function drawHistoryChart(rows) {
  const canvas = document.getElementById('history-canvas');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 1000;
  const cssH = 260;
  canvas.width = cssW * dpr;
  canvas.height = cssH * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  if (!rows.length) {
    ctx.fillStyle = '#9A9CA6';
    ctx.font = '13px Inter, sans-serif';
    ctx.fillText('Belum ada data riwayat untuk lahan ini.', 16, 30);
    return;
  }

  const padL = 42, padR = 16, padT = 16, padB = 28;
  const w = cssW - padL - padR;
  const h = cssH - padT - padB;
  const maxTotal = Math.max(...rows.map(r => r.total_slots), 1);

  // grid + y labels
  ctx.strokeStyle = '#3A3D45';
  ctx.fillStyle = '#9A9CA6';
  ctx.font = '10px monospace';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padT + h - (h * i / 4);
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(padL + w, y);
    ctx.stroke();
    ctx.fillText(Math.round(maxTotal * i / 4), 6, y + 3);
  }

  // occupied line
  const pts = rows.map((r, i) => {
    const x = padL + (w * i / Math.max(rows.length - 1, 1));
    const y = padT + h - (h * r.occupied_slots / maxTotal);
    return [x, y];
  });

  // fill area
  ctx.beginPath();
  ctx.moveTo(pts[0][0], padT + h);
  pts.forEach(p => ctx.lineTo(p[0], p[1]));
  ctx.lineTo(pts[pts.length - 1][0], padT + h);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, padT, 0, padT + h);
  grad.addColorStop(0, 'rgba(242,194,48,0.35)');
  grad.addColorStop(1, 'rgba(242,194,48,0.02)');
  ctx.fillStyle = grad;
  ctx.fill();

  // line
  ctx.beginPath();
  pts.forEach((p, i) => i === 0 ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1]));
  ctx.strokeStyle = '#F2C230';
  ctx.lineWidth = 2;
  ctx.stroke();

  // x labels (first, mid, last timestamps)
  ctx.fillStyle = '#9A9CA6';
  [0, Math.floor(rows.length/2), rows.length-1].forEach(i => {
    const t = new Date(rows[i].timestamp).toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'});
    ctx.fillText(t, pts[i][0] - 14, cssH - 8);
  });
}

async function loadLots() {
  const res = await fetch(`${API_BASE}/api/lots`);
  const lots = await res.json();
  renderLots(lots);
  if (!selectedLotId && lots.length) selectLot(lots[0].id);
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  const dot = document.getElementById('conn-dot');
  const txt = document.getElementById('conn-text');

  ws.onopen = () => { dot.classList.add('on'); txt.textContent = 'terhubung — real-time'; };
  ws.onclose = () => {
    dot.classList.remove('on');
    txt.textContent = 'terputus — mencoba lagi…';
    setTimeout(connectWS, 2000);
  };
  ws.onerror = () => ws.close();
  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.type === 'update') {
      loadLots();
      if (msg.lot.id === selectedLotId) loadHistory(selectedLotId);
    }
  };
  // keep-alive ping
  setInterval(() => { if (ws.readyState === 1) ws.send('ping'); }, 15000);
}

loadLots();
connectWS();
setInterval(loadLots, 10000); // fallback polling jika WS gagal

document.getElementById('search-input').addEventListener('input', (e) => {
  searchQuery = e.target.value;
  renderLots(Object.values(lotsCache));
});

document.querySelectorAll('.sort-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    sortMode = btn.dataset.sort;
    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderLots(Object.values(lotsCache));
  });
});
