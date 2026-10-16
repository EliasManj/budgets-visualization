/* app.js — Personal budget dashboard
   Direction: product-performs · Seed: 1917340263
   Palette: Plum-black and pink · Type: Work Sans */

'use strict'

// ── Constants ─────────────────────────────────────────────────────
const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
const ALL_CARDS = ['amex', 'bbva_debit', 'bbva_credit', 'banamex_debit', 'banamex_credit']
const BAR_MAX_PCT = 200   // matches original ylim(0, 200)
const PAGE_SZ = 20

// ── State ─────────────────────────────────────────────────────────
const S = {
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  dayStart: 1,
  dayEnd: 31,
  allTags: [],
  selTags: [],
  cards: [...ALL_CARDS],
  sortCol: 'date',
  sortDir: 'Ascending',
  tagSortCol: null,
  tagSortDir: 'Ascending',
  activeTab: 'tx',
  // data
  transactions: [],
  byTag: [],
  imports: [],
  summary: null,
  prevSummary: null,
  budgetUsage: [],
  cetes: [],
  // ui
  txPage: 1,
  loading: false,
}

// ── Formatting ────────────────────────────────────────────────────
const _fmtFull = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 0, maximumFractionDigits: 2 })
const _fmtShort = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 0, maximumFractionDigits: 0 })

const fmt = n => (n == null || isNaN(n)) ? '—' : _fmtFull.format(n)
const fmtShort = n => (n == null || isNaN(n)) ? '—' : _fmtShort.format(n)

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

// ── URL params ────────────────────────────────────────────────────
function buildParams() {
  const p = new URLSearchParams({
    month: S.month, year: S.year,
    day_start: S.dayStart, day_end: S.dayEnd,
    sort_column: S.sortCol, sort_order: S.sortDir,
  })
  S.selTags.forEach(t => p.append('tags', t))
  S.cards.forEach(c => p.append('cards', c))
  return p
}

// ── API ───────────────────────────────────────────────────────────
async function apiFetch(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

async function loadBudgets() {
  const budgets = await apiFetch('/api/budgets')
  S.allTags = budgets.map(b => b.tag)
  S.selTags = [...S.allTags]
}

async function fetchAll() {
  if (S.loading) return

  // Short-circuit: empty filter → clear data without hitting API
  if (S.selTags.length === 0 || S.cards.length === 0) {
    S.transactions = []; S.byTag = []; S.imports = []
    S.prevSummary = S.summary
    S.summary = {
      total: 0, total_expense: 0, budget_overspent: 0,
      total_income: 0, total_invested: 0, saved_cash: 0, remaining_in_bank: 0,
      projections: { '5yr_no_interest': 0, '5yr_10pct_compound': 0, '5yr_20pct_compound': 0 }
    }
    S.budgetUsage = []; S.txPage = 1
    renderAll(); return
  }

  S.loading = true
  setLoading(true)
  try {
    const p = buildParams()
    const cp = new URLSearchParams({ month: S.month, year: S.year })
    const [tx, byTag, imp, sum, usage, cetes] = await Promise.all([
      apiFetch(`/api/transactions?${p}`),
      apiFetch(`/api/transactions/by-tag?${p}`),
      apiFetch(`/api/imports?${p}`),
      apiFetch(`/api/summary?${p}`),
      apiFetch(`/api/budget-usage?${p}`),
      apiFetch(`/api/cetes?${cp}`),
    ])
    S.transactions = tx; S.byTag = byTag; S.imports = imp
    S.prevSummary = S.summary; S.summary = sum
    S.budgetUsage = usage; S.cetes = cetes
    S.txPage = 1
    renderAll()
  } catch (e) {
    console.error(e)
    showError('Error al conectar con la API. Verifica que el servidor esté corriendo en :8000.')
  } finally {
    S.loading = false; setLoading(false)
  }
}

// ── Render: transactions ──────────────────────────────────────────
function updateSortIndicators() {
  document.querySelectorAll('#tx-table th[data-sort]').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc')
    if (th.dataset.sort === S.sortCol) {
      th.classList.add(S.sortDir === 'Ascending' ? 'sort-asc' : 'sort-desc')
    }
  })
}

function renderTx() {
  const tbody = document.getElementById('tx-body')
  if (!S.transactions.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">Sin transacciones</td></tr>`
    document.getElementById('pagination').innerHTML = ''
    updateSortIndicators()
    return
  }
  const start = (S.txPage - 1) * PAGE_SZ
  const page = S.transactions.slice(start, start + PAGE_SZ)
  tbody.innerHTML = page.map(t => `
    <tr>
      <td>${esc(t.date)}</td>
      <td>${esc(t.description)}</td>
      <td class="r">${fmt(t.amount)}</td>
      <td><span class="tag-chip">${esc(t.tag ?? '')}</span></td>
      <td class="muted-cell">${esc(t.card ?? '')}</td>
      <td class="muted-cell">${esc(t.category ?? '')}</td>
    </tr>`).join('')
  renderPagination(S.transactions.length)
  updateSortIndicators()
}

function renderPagination(total) {
  const pages = Math.ceil(total / PAGE_SZ)
  const el = document.getElementById('pagination')
  if (pages <= 1) { el.innerHTML = ''; return }

  const from = (S.txPage - 1) * PAGE_SZ + 1
  const to = Math.min(S.txPage * PAGE_SZ, total)

  let btns = ''
  if (S.txPage > 1) btns += `<button class="btn-page" data-p="${S.txPage - 1}">←</button>`
  let prev = 0
  for (let i = 1; i <= pages; i++) {
    if (i !== 1 && i !== pages && Math.abs(i - S.txPage) > 2) {
      if (prev !== 0) { btns += `<span class="page-ellipsis">…</span>`; prev = 0 }
      continue
    }
    btns += `<button class="btn-page${i === S.txPage ? ' active' : ''}" data-p="${i}">${i}</button>`
    prev = i
  }
  if (S.txPage < pages) btns += `<button class="btn-page" data-p="${S.txPage + 1}">→</button>`

  el.innerHTML = `<span class="page-info">${from}–${to} de ${total}</span><div class="page-btns">${btns}</div>`
  el.querySelectorAll('.btn-page').forEach(b =>
    b.addEventListener('click', () => { S.txPage = parseInt(b.dataset.p); renderTx() })
  )
}

// ── Render: by-tag ────────────────────────────────────────────────
function updateTagSortIndicators() {
  document.querySelectorAll('#tag-table th[data-sort]').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc')
    if (th.dataset.sort === S.tagSortCol) {
      th.classList.add(S.tagSortDir === 'Ascending' ? 'sort-asc' : 'sort-desc')
    }
  })
}

function renderByTag() {
  const tbody = document.getElementById('tag-body')
  if (!S.byTag.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-cell">Sin datos</td></tr>`
    updateTagSortIndicators()
    return
  }

  let rows = [...S.byTag]
  if (S.tagSortCol) {
    const col = S.tagSortCol
    const asc = S.tagSortDir === 'Ascending'
    const totals = rows.filter(r => String(r.category ?? '').startsWith('Total'))
    const rest = rows.filter(r => !String(r.category ?? '').startsWith('Total'))
    rest.sort((a, b) => {
      const av = a[col] ?? '', bv = b[col] ?? ''
      return typeof av === 'number'
        ? asc ? av - bv : bv - av
        : asc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av))
    })
    rows = [...rest, ...totals]
  }

  tbody.innerHTML = rows.map(row => {
    const isTotal = String(row.category ?? '').startsWith('Total')
    const pct = row.budget > 0 ? (row.amount / row.budget) * 100 : 0
    const cls = isTotal ? 'row-total' : pct >= 130 ? 'row-over' : pct > 100 ? 'row-warn' : ''
    return `<tr class="${cls}">
      <td>${esc(row.tag || '—')}</td>
      <td class="muted-cell">${esc(row.category)}</td>
      <td class="r">${fmt(row.budget ?? 0)}</td>
      <td class="r">${fmt(row.amount ?? 0)}</td>
    </tr>`
  }).join('')
  updateTagSortIndicators()
}

// ── Render: imports ───────────────────────────────────────────────
function renderImports() {
  const tbody = document.getElementById('imp-body')
  if (!S.imports.length) {
    tbody.innerHTML = `<tr><td colspan="2" class="empty-cell">Sin ingresos</td></tr>`; return
  }
  tbody.innerHTML = S.imports.map(r =>
    `<tr><td>${esc(r.date)}</td><td class="r">${fmt(r.amount)}</td></tr>`
  ).join('')
}

// ── Render: budget bars ───────────────────────────────────────────
function renderBars() {
  const chart = document.getElementById('bars-chart')
  const totalEl = document.getElementById('bars-total')

  const total = S.summary?.total_expense ?? 0
  const prevTotal = S.prevSummary?.total_expense ?? total
  animateCounter(totalEl, prevTotal, total, 900, fmtShort)

  if (!S.budgetUsage.length) {
    chart.innerHTML = `<p class="empty-cell" style="margin:auto">Sin datos</p>`; return
  }

  // Top 3 by pct get visible labels
  const sorted = [...S.budgetUsage].sort((a, b) => b.percentage_used - a.percentage_used)
  const showLabel = new Set(sorted.slice(0, 3).map(u => u.tag))

  chart.innerHTML = S.budgetUsage.map((item, i) => {
    const pct = item.percentage_used
    const cls = pct >= 130 ? 'bar-over' : pct > 100 ? 'bar-warn' : 'bar-ok'
    return `
      <div class="bar-col" data-raw="${pct.toFixed(2)}">
        <div class="bar ${cls}" style="--bar-delay:${i * 35}ms">
          <span class="bar-pct">${pct.toFixed(0)}%</span>
        </div>
        <span class="bar-name">${esc(item.tag)}</span>
      </div>`
  }).join('')

  // Animate bars: set height 0 → target after one paint
  requestAnimationFrame(() => requestAnimationFrame(() => applyBarHeights()))
}

function applyBarHeights() {
  const chart = document.getElementById('bars-chart')
  if (!chart) return
  const available = Math.max(chart.clientHeight - 28 - 4, 80)  // minus bar-name + gap
  chart.querySelectorAll('.bar-col').forEach(col => {
    const pct = parseFloat(col.dataset.raw)
    const h = Math.min(Math.max((pct / BAR_MAX_PCT) * available, 2), available)
    const bar = col.querySelector('.bar')
    if (bar) bar.style.height = `${h}px`
  })
}

function replayBarAnimation() {
  const bars = document.querySelectorAll('#bars-chart .bar')
  bars.forEach(bar => {
    const savedH = bar.style.height
    bar.style.transition = 'none'
    bar.style.height = '0px'
    void bar.offsetWidth
    bar.style.transition = ''
    bar.style.height = savedH
  })
}

// ── Render: metrics ───────────────────────────────────────────────
function renderMetrics() {
  const panel = document.getElementById('metrics-panel')
  const s = S.summary
  if (!s) { panel.innerHTML = ''; return }
  const prev = S.prevSummary

  const cards = [
    { lbl: 'Total gastado', val: s.total_expense, prev: prev?.total_expense },
    {
      lbl: 'Exceso presupuesto', val: s.budget_overspent, prev: prev?.budget_overspent,
      warn: s.budget_overspent > 0
    },
    { lbl: 'Ingresos del mes', val: s.total_income, prev: prev?.total_income },
    { lbl: 'Invertido', val: s.total_invested, prev: prev?.total_invested },
    { lbl: 'Ahorro en banco', val: s.saved_cash, prev: prev?.saved_cash },
    {
      lbl: 'Delta bancario', val: s.remaining_in_bank, prev: prev?.remaining_in_bank,
      note: s.remaining_in_bank >= 0 ? 'superávit' : 'déficit',
      surplus: s.remaining_in_bank >= 0,
      deficit: s.remaining_in_bank < 0
    },
  ]

  const p = s.projections
  panel.innerHTML = `
    <div class="metrics-grid">
      ${cards.map(c => `
        <div class="metric-card${c.warn ? ' is-warn' : ''}${c.surplus ? ' is-surplus' : ''}${c.deficit ? ' is-deficit' : ''}">
          <span class="metric-val" data-from="${c.prev ?? c.val}" data-to="${c.val}">${fmt(c.val)}</span>
          <span class="metric-lbl">${c.lbl}</span>
          ${c.note ? `<span class="metric-note">${c.note}</span>` : ''}
        </div>`).join('')}
    </div>
    <div class="proj-section">
      <p class="proj-title">Proyecciones de inversión</p>
      <div class="proj-rows">
        <div class="proj-row">
          <span class="proj-lbl">${fmt(s.total_invested)}/mes · 5 años sin interés</span>
          <span class="proj-val">${fmt(p['5yr_no_interest'])}</span>
        </div>
        <div class="proj-row">
          <span class="proj-lbl">${fmt(s.total_invested)}/mes · 5 años al 10% compuesto</span>
          <span class="proj-val">${fmt(p['5yr_10pct_compound'])}</span>
        </div>
        <div class="proj-row">
          <span class="proj-lbl">${fmt(s.total_invested)}/mes · 5 años al 20% compuesto</span>
          <span class="proj-val">${fmt(p['5yr_20pct_compound'])}</span>
        </div>
      </div>
    </div>`

  panel.querySelectorAll('.metric-val').forEach(el => {
    const from = parseFloat(el.dataset.from) || 0
    const to = parseFloat(el.dataset.to) || 0
    if (from !== to) animateCounter(el, from, to, 700, fmt)
  })
}

// ── Render: cetes ─────────────────────────────────────────────────
function renderCetes() {
  const tbody = document.getElementById('cetes-body')
  if (!S.cetes.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">Sin datos CETES</td></tr>`; return
  }
  tbody.innerHTML = S.cetes.map(r => `
    <tr>
      <td>${esc(r.date)}</td>
      <td>${esc(r.instrumento)}</td>
      <td class="r">${fmt(r.invertido)}</td>
      <td class="r ${r.plusminus >= 0 ? 'pos' : 'neg'}">${fmt(r.plusminus)}</td>
      <td class="r">${fmt(r.disp)}</td>
      <td class="r">${fmt(r.valuado)}</td>
    </tr>`).join('')
}

// ── Render all ────────────────────────────────────────────────────
function renderAll() {
  renderTx(); renderByTag(); renderImports()
  renderBars(); renderMetrics(); renderCetes()
  document.getElementById('header-period').textContent = `${MONTHS[S.month - 1]} ${S.year}`
}

// ── Counter animation ─────────────────────────────────────────────
function animateCounter(el, from, to, ms, formatter) {
  const start = performance.now()
  const tick = now => {
    const t = Math.min((now - start) / ms, 1)
    const ease = 1 - Math.pow(1 - t, 3)
    el.textContent = formatter(from + (to - from) * ease)
    if (t < 1) requestAnimationFrame(tick)
    else el.textContent = formatter(to)
  }
  requestAnimationFrame(tick)
}

// ── Loading / error ───────────────────────────────────────────────
function setLoading(on) {
  document.getElementById('loading-dot')?.classList.toggle('is-active', on)
}

function showError(msg) {
  const t = document.getElementById('error-toast')
  if (!t) return
  t.textContent = msg; t.hidden = false
  setTimeout(() => { t.hidden = true }, 6000)
}

// ── Sidebar: month grid ───────────────────────────────────────────
function initMonthGrid() {
  const grid = document.getElementById('month-grid')
  grid.innerHTML = MONTHS.map((m, i) =>
    `<button class="month-btn${S.month === i + 1 ? ' is-active' : ''}"
             data-m="${i + 1}" type="button" aria-pressed="${S.month === i + 1}">${m}</button>`
  ).join('')

  grid.addEventListener('click', e => {
    const btn = e.target.closest('.month-btn')
    if (!btn) return
    S.month = parseInt(btn.dataset.m)
    grid.querySelectorAll('.month-btn').forEach(b => {
      const on = parseInt(b.dataset.m) === S.month
      b.classList.toggle('is-active', on)
      b.setAttribute('aria-pressed', on)
    })
    debounce()
  })
}

// ── Sidebar: year ─────────────────────────────────────────────────
function initYear() {
  const disp = document.getElementById('year-display')
  disp.textContent = S.year
  document.getElementById('year-prev').addEventListener('click', () => {
    S.year--; disp.textContent = S.year; debounce()
  })
  document.getElementById('year-next').addEventListener('click', () => {
    S.year++; disp.textContent = S.year; debounce()
  })
}

// ── Sidebar: day range ────────────────────────────────────────────
function initDayRange() {
  const sEl = document.getElementById('day-start')
  const eEl = document.getElementById('day-end')
  const lbl = document.getElementById('day-label')
  const update = () => {
    let s = parseInt(sEl.value), e = parseInt(eEl.value)
    if (s > e) { const tmp = s; s = e; e = tmp }
    S.dayStart = s; S.dayEnd = e
    lbl.textContent = `${s}–${e}`
    debounce()
  }
  sEl.addEventListener('input', update)
  eEl.addEventListener('input', update)
}

// ── Sidebar: tags ─────────────────────────────────────────────────
function initTags() {
  const list = document.getElementById('tags-list')
  list.innerHTML = S.allTags.map(t =>
    `<label class="check-item">
       <input type="checkbox" value="${esc(t)}" checked>
       <span>${esc(t)}</span>
     </label>`
  ).join('')
  list.addEventListener('change', () => {
    S.selTags = [...list.querySelectorAll('input:checked')].map(i => i.value)
    debounce()
  })
  document.getElementById('tags-all').addEventListener('click', () => {
    list.querySelectorAll('input').forEach(i => i.checked = true)
    S.selTags = [...S.allTags]; debounce()
  })
  document.getElementById('tags-none').addEventListener('click', () => {
    list.querySelectorAll('input').forEach(i => i.checked = false)
    S.selTags = []; debounce()
  })
}

// ── Sidebar: cards ────────────────────────────────────────────────
function initCards() {
  const list = document.getElementById('cards-list')
  list.innerHTML = ALL_CARDS.map(c =>
    `<label class="check-item">
       <input type="checkbox" value="${c}" checked>
       <span>${c}</span>
     </label>`
  ).join('')
  list.addEventListener('change', () => {
    S.cards = [...list.querySelectorAll('input:checked')].map(i => i.value)
    debounce()
  })
  document.getElementById('cards-all').addEventListener('click', () => {
    list.querySelectorAll('input').forEach(i => i.checked = true)
    S.cards = [...ALL_CARDS]; debounce()
  })
  document.getElementById('cards-none').addEventListener('click', () => {
    list.querySelectorAll('input').forEach(i => i.checked = false)
    S.cards = []; debounce()
  })
}

// ── Sidebar: sort ─────────────────────────────────────────────────
function initSort() {
  document.getElementById('sort-col').addEventListener('change', e => {
    S.sortCol = e.target.value; debounce()
  })
  document.querySelectorAll('input[name="sort-order"]').forEach(r =>
    r.addEventListener('change', e => { S.sortDir = e.target.value; debounce() })
  )
}

function initTableSort() {
  document.querySelectorAll('#tx-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      if (S.sortCol === th.dataset.sort) {
        S.sortDir = S.sortDir === 'Ascending' ? 'Descending' : 'Ascending'
      } else {
        S.sortCol = th.dataset.sort
        S.sortDir = 'Ascending'
      }
      const colSelect = document.getElementById('sort-col')
      if (colSelect) colSelect.value = S.sortCol
      document.querySelectorAll('input[name="sort-order"]').forEach(r => {
        r.checked = r.value === S.sortDir
      })
      debounce()
    })
  })
}

function initTagTableSort() {
  document.querySelectorAll('#tag-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      if (S.tagSortCol === th.dataset.sort) {
        S.tagSortDir = S.tagSortDir === 'Ascending' ? 'Descending' : 'Ascending'
      } else {
        S.tagSortCol = th.dataset.sort
        S.tagSortDir = 'Ascending'
      }
      renderByTag()
    })
  })
}
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab
      S.activeTab = tab
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b === btn)
        b.setAttribute('aria-selected', b === btn)
      })
      document.querySelectorAll('.tab-panel').forEach(p => {
        const on = p.id === `tab-${tab}`
        on ? p.removeAttribute('hidden') : p.setAttribute('hidden', '')
      })
      window.scrollTo({ top: 0, behavior: 'instant' })
      if (tab === 'sum') {
        // Re-trigger bar animation + ensure all enter-up elements are visible
        setTimeout(() => {
          replayBarAnimation()
          document.querySelectorAll('#tab-sum .enter-up:not(.in-view)').forEach(el =>
            el.classList.add('in-view')
          )
        }, 50)
      }
    })
  })
}

// ── Action buttons ────────────────────────────────────────────────
function initActions() {
  const refresh = document.getElementById('btn-refresh')
  const reset = document.getElementById('btn-reset')

  refresh.addEventListener('click', async () => {
    refresh.disabled = true; refresh.textContent = 'Actualizando…'
    try { await fetch('/api/refresh', { method: 'POST' }); await fetchAll() }
    catch { showError('Error al actualizar datos') }
    finally { refresh.disabled = false; refresh.textContent = 'Actualizar' }
  })

  reset.addEventListener('click', async () => {
    if (!confirm('¿Eliminar todos los datos de la base de datos?')) return
    reset.disabled = true; reset.textContent = 'Reseteando…'
    try { await fetch('/api/reset', { method: 'POST' }); await fetchAll() }
    catch { showError('Error al resetear datos') }
    finally { reset.disabled = false; reset.textContent = 'Resetear' }
  })
}

// ── Motion: masked headline reveal ────────────────────────────────
function initReveal() {
  requestAnimationFrame(() =>
    setTimeout(() => document.querySelector('.wordmark-line')?.classList.add('is-revealed'), 120)
  )
}

// ── Motion: scroll entrances ──────────────────────────────────────
function initEntrances() {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target) }
    })
  }, { threshold: 0.05 })
  document.querySelectorAll('.enter-up').forEach(el => obs.observe(el))
}

// ── Debounce ──────────────────────────────────────────────────────
let _dt
function debounce() { clearTimeout(_dt); _dt = setTimeout(fetchAll, 280) }

// ── Init ──────────────────────────────────────────────────────────
async function init() {
  try {
    await loadBudgets()
    initMonthGrid(); initYear(); initDayRange()
    initTags(); initCards(); initSort(); initTableSort(); initTagTableSort()
    initTabs(); initActions(); initReveal()
    await fetchAll()
    initEntrances()
  } catch (e) {
    console.error('Init error:', e)
    showError('Error al inicializar. Verifica que el servidor API esté corriendo.')
  }
}

init()
