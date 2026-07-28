"""Generate a standalone HTML drill-down page for IG handle verification."""
import json, html
from pathlib import Path

REPORT = Path("ig_triage_report.json")
OUTPUT = Path("ig_drill.html")

with open(REPORT, encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]

rows_json = json.dumps(results, ensure_ascii=False)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IG Handle Drill — WhatHappeningPV</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 20px; }
  h1 { font-size: 1.3rem; margin-bottom: 8px; color: #fff; }
  .meta { color: #999; font-size: 0.85rem; margin-bottom: 16px; }
  .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 16px; }
  .toolbar label { font-size: 0.85rem; color: #aaa; }
  .toolbar select, .toolbar input { background: #1e1e1e; color: #e0e0e0; border: 1px solid #333; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; }
  .toolbar .count { margin-left: auto; color: #888; font-size: 0.85rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  th { text-align: left; padding: 8px 6px; border-bottom: 1px solid #333; color: #888; font-weight: 500; cursor: pointer; user-select: none; position: sticky; top: 0; background: #0f0f0f; }
  th:hover { color: #fff; }
  th .arrow { color: #666; margin-left: 3px; }
  td { padding: 5px 6px; border-bottom: 1px solid #1e1e1e; vertical-align: middle; }
  tr:hover td { background: #1a1a1a; }
  tr.checked td { opacity: 0.5; }
  a { color: #5b9aff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .handle-cell { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.78rem; }
  .tier1 { border-left: 3px solid #ff6b6b; }
  .tier2 { border-left: 3px solid #ffd93d; }
  .tier3 { border-left: 3px solid #6bcbff; }
  .badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; font-weight: 600; }
  .badge-t1 { background: #ff6b6b22; color: #ff6b6b; }
  .badge-t2 { background: #ffd93d22; color: #ffd93d; }
  .badge-t3 { background: #6bcbff22; color: #6bcbff; }
  .checkbox-cell { text-align: center; }
  .checkbox-cell input { width: 18px; height: 18px; cursor: pointer; accent-color: #5b9aff; }
  .progress-bar { height: 3px; background: #1e1e1e; border-radius: 2px; margin-bottom: 12px; overflow: hidden; }
  .progress-fill { height: 100%; background: #5b9aff; border-radius: 2px; transition: width 0.3s; }
  .key-hint { color: #555; font-size: 0.75rem; margin-left: 16px; }
  kbd { background: #1e1e1e; border: 1px solid #333; padding: 1px 5px; border-radius: 3px; font-size: 0.7rem; }
  .empty { color: #555; text-align: center; padding: 40px; }
  .bio-preview { color: #888; font-size: 0.75rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .tier-filter { display: flex; gap: 6px; }
  .tier-filter button { background: #1e1e1e; color: #aaa; border: 1px solid #333; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
  .tier-filter button.active { border-color: #5b9aff; color: #fff; }
  .tier-filter button:hover { color: #fff; }
  #search { width: 200px; }
</style>
</head>
<body>

<h1>Instagram Handle Drill-Down</h1>
<div class="meta">
  <span id="total-label"></span>
  <span class="key-hint"><kbd>↑</kbd><kbd>↓</kbd> navigate &nbsp; <kbd>Space</kbd> toggle &nbsp; <kbd>Enter</kbd> open profile</span>
</div>
<div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>

<div class="toolbar">
  <div class="tier-filter">
    <button data-tier="all" class="active">All</button>
    <button data-tier="1">T1 High</button>
    <button data-tier="2">T2 Med</button>
    <button data-tier="3">T3 Low</button>
  </div>
  <select id="status-filter">
    <option value="all">All status</option>
    <option value="unchecked">Unchecked only</option>
    <option value="checked">Checked only</option>
  </select>
  <input id="search" type="text" placeholder="Search name or handle...">
  <span class="count" id="count-label">0 / 0</span>
</div>

<table id="ig-table">
  <thead>
    <tr>
      <th style="width:32px"></th>
      <th data-col="business_name">Name <span class="arrow">↕</span></th>
      <th data-col="handle" style="width:220px">Handle <span class="arrow">↕</span></th>
      <th data-col="category" style="width:120px">Category <span class="arrow">↕</span></th>
      <th data-col="area" style="width:100px">Area <span class="arrow">↕</span></th>
      <th data-col="signal_tier" style="width:60px">Tier <span class="arrow">↕</span></th>
      <th data-col="status" style="width:80px">Status <span class="arrow">↕</span></th>
    </tr>
  </thead>
  <tbody id="tbody"></tbody>
</table>

<script>
const DATA = """ + rows_json + r""";

const STORAGE_KEY = 'ig_drill_checked';
let checked = new Set();
try {
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  saved.forEach(h => checked.add(h));
} catch(e) {}

let sortCol = null;
let sortDir = 1;
let filterTier = 'all';
let filterStatus = 'all';
let searchQuery = '';
let selectedIndex = 0;

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...checked]));
}

function toggleRow(handle) {
  if (checked.has(handle)) checked.delete(handle);
  else checked.add(handle);
  save();
  render();
}

function openProfile(handle) {
  window.open('https://www.instagram.com/' + handle + '/', '_blank');
}

function getVal(r, col) {
  if (col === 'handle') return r['handle'] || '';
  if (col === 'business_name') return r['business_name'] || '';
  if (col === 'category') return r['category'] || '';
  if (col === 'area') return r['area'] || '';
  if (col === 'signal_tier') return r['signal_tier'] || 99;
  if (col === 'status') return r['status'] || '';
  return '';
}

function filtered() {
  let list = DATA.slice();
  if (filterTier !== 'all') list = list.filter(r => r['signal_tier'] === parseInt(filterTier));
  if (filterStatus === 'unchecked') list = list.filter(r => !checked.has(r['handle']));
  if (filterStatus === 'checked') list = list.filter(r => checked.has(r['handle']));
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    list = list.filter(r => (r['business_name'] || '').toLowerCase().includes(q) || (r['handle'] || '').toLowerCase().includes(q));
  }
  if (sortCol) {
    list.sort((a, b) => {
      let va = getVal(a, sortCol), vb = getVal(b, sortCol);
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      if (va < vb) return -sortDir;
      if (va > vb) return sortDir;
      return 0;
    });
  }
  return list;
}

function render() {
  const list = filtered();
  const totalChecked = [...checked].filter(h => DATA.some(r => r['handle'] === h)).length;
  document.getElementById('progress-fill').style.width = (totalChecked / DATA.length * 100) + '%';
  document.getElementById('total-label').textContent = DATA.length + ' handles · ' + totalChecked + ' verified';
  document.getElementById('count-label').textContent = list.length + ' shown';

  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';

  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty">No matches</td></tr>';
    return;
  }

  if (selectedIndex >= list.length) selectedIndex = 0;
  if (selectedIndex < 0) selectedIndex = 0;

  list.forEach((r, i) => {
    const h = r['handle'];
    const isChecked = checked.has(h);
    const tier = r['signal_tier'] || 3;
    const tierClass = 'tier' + tier;
    const isSelected = (i === selectedIndex);
    const tr = document.createElement('tr');
    tr.className = (isChecked ? 'checked ' : '') + tierClass + (isSelected ? ' selected' : '');
    if (isSelected) tr.style.outline = '2px solid #5b9aff';

    // Checkbox
    const td0 = document.createElement('td');
    td0.className = 'checkbox-cell';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = isChecked;
    cb.addEventListener('change', () => toggleRow(h));
    td0.appendChild(cb);
    tr.appendChild(td0);

    // Name
    const td1 = document.createElement('td');
    td1.textContent = r['business_name'] || '';
    tr.appendChild(td1);

    // Handle
    const td2 = document.createElement('td');
    td2.className = 'handle-cell';
    const a = document.createElement('a');
    a.href = 'https://www.instagram.com/' + h + '/';
    a.target = '_blank';
    a.textContent = '@' + h;
    a.addEventListener('click', (e) => e.stopPropagation());
    td2.appendChild(a);
    tr.appendChild(td2);

    // Category
    const td3 = document.createElement('td');
    td3.textContent = r['category'] || '';
    tr.appendChild(td3);

    // Area
    const td4 = document.createElement('td');
    td4.textContent = r['area'] || '';
    tr.appendChild(td4);

    // Tier
    const td5 = document.createElement('td');
    const badge = document.createElement('span');
    badge.className = 'badge badge-t' + tier;
    badge.textContent = 'T' + tier;
    td5.appendChild(badge);
    tr.appendChild(td5);

    // Status
    const td6 = document.createElement('td');
    td6.textContent = r['status'] || '';
    tr.appendChild(td6);

    // Click on row = toggle
    tr.addEventListener('click', (e) => {
      if (e.target.tagName !== 'A' && e.target.tagName !== 'INPUT') {
        toggleRow(h);
      }
    });

    tbody.appendChild(tr);
  });

  // Scroll selected into view
  const sel = tbody.querySelector('.selected');
  if (sel) sel.scrollIntoView({ block: 'nearest' });
}

// Keyboard nav
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  const list = filtered();
  if (!list.length) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    selectedIndex = Math.min(selectedIndex + 1, list.length - 1);
    render();
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    selectedIndex = Math.max(selectedIndex - 1, 0);
    render();
  } else if (e.key === ' ') {
    e.preventDefault();
    const r = list[selectedIndex];
    if (r) toggleRow(r['handle']);
  } else if (e.key === 'Enter') {
    e.preventDefault();
    const r = list[selectedIndex];
    if (r) openProfile(r['handle']);
  }
});

// Sort on header click
document.querySelectorAll('th[data-col]').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.col;
    if (sortCol === col) sortDir *= -1;
    else { sortCol = col; sortDir = 1; }
    // update arrows
    document.querySelectorAll('th .arrow').forEach(a => a.textContent = '↕');
    th.querySelector('.arrow').textContent = sortDir === 1 ? '↑' : '↓';
    render();
  });
});

// Tier filter buttons
document.querySelectorAll('.tier-filter button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tier-filter button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterTier = btn.dataset.tier;
    selectedIndex = 0;
    render();
  });
});

// Status filter
document.getElementById('status-filter').addEventListener('change', (e) => {
  filterStatus = e.target.value;
  selectedIndex = 0;
  render();
});

// Search
document.getElementById('search').addEventListener('input', (e) => {
  searchQuery = e.target.value;
  selectedIndex = 0;
  render();
});

render();
</script>
</body>
</html>"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(HTML_TEMPLATE)

print(f"Generated: {OUTPUT.resolve()}")
