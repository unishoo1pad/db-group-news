'use strict';

// ── 상태 ──────────────────────────────────────────────
let currentFilter = 'all';
let currentSearch = '';

// ── DOM ───────────────────────────────────────────────
const newsGrid    = document.getElementById('news-grid');
const emptyState  = document.getElementById('empty-state');
const resultBar   = document.getElementById('result-bar');
const filterTabs  = document.getElementById('filter-tabs');
const searchInput = document.getElementById('search');
const statTotal   = document.getElementById('stat-total');
const statToday   = document.getElementById('stat-today');

// ── 유틸 ──────────────────────────────────────────────
const TODAY = new Date().toISOString().slice(0, 10); // "2026-06-19"

function formatDate(isoStr) {
  const d = new Date(isoStr);
  const m = d.getMonth() + 1;
  const day = d.getDate();
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${m}월 ${day}일 ${h}:${min}`;
}

function isToday(isoStr) {
  return isoStr.startsWith(TODAY);
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── 필터링 ────────────────────────────────────────────
function getFiltered() {
  return NEWS_DATA.articles
    .filter(a => {
      const matchFilter = currentFilter === 'all' || a.subsidiary === currentFilter;
      const q = currentSearch.toLowerCase();
      const matchSearch = !q ||
        a.title.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q) ||
        a.source.toLowerCase().includes(q);
      return matchFilter && matchSearch;
    })
    .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
}

// ── 카드 생성 ─────────────────────────────────────────
function createCard(article) {
  const today     = isToday(article.publishedAt);
  const safeTitle = escapeHtml(article.title);
  const safeDesc  = escapeHtml(article.description);
  const safeSource = escapeHtml(article.source);
  const linkUrl   = article.url;

  const el = document.createElement('article');
  el.className = 'news-card';
  el.setAttribute('role', 'article');
  el.innerHTML = `
    <div class="card-top">
      <span class="badge badge-${article.subsidiary}">${article.subsidiary}</span>
      ${today ? '<span class="badge-new">NEW</span>' : ''}
    </div>
    <p class="card-title">${safeTitle}</p>
    <p class="card-desc">${safeDesc}</p>
    <div class="card-footer">
      <div class="card-meta">
        <span class="card-source">${safeSource}</span>
        <span class="card-dot">·</span>
        <span>${formatDate(article.publishedAt)}</span>
      </div>
      <a class="card-link" href="${linkUrl}" target="_blank" rel="noopener noreferrer"
         onclick="event.stopPropagation()">
        기사 보기
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 6h8M6 2l4 4-4 4" stroke="currentColor" stroke-width="1.5"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </a>
    </div>
  `;

  el.addEventListener('click', () => {
    window.open(linkUrl, '_blank', 'noopener,noreferrer');
  });

  return el;
}

// ── 날짜별 그룹 ───────────────────────────────────────
function groupByDate(articles) {
  const groups = {};
  articles.forEach(a => {
    const date = a.publishedAt.slice(0, 10);
    if (!groups[date]) groups[date] = [];
    groups[date].push(a);
  });
  return Object.entries(groups).sort((a, b) => b[0].localeCompare(a[0]));
}

function formatDateHeader(dateStr) {
  const d = new Date(dateStr);
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`;
}

// ── 렌더링 ────────────────────────────────────────────
function render() {
  const list = getFiltered();
  newsGrid.innerHTML = '';

  if (list.length === 0) {
    emptyState.style.display = 'block';
    resultBar.textContent = '';
    return;
  }

  emptyState.style.display = 'none';
  const label = currentFilter === 'all' ? '전체' : currentFilter;
  const searchLabel = currentSearch ? ` · "${escapeHtml(currentSearch)}" 검색` : '';
  resultBar.textContent = `${label}${searchLabel} · ${list.length}건`;

  const groups = groupByDate(list);
  groups.forEach(([date, articles], idx) => {
    const section = document.createElement('div');
    section.className = 'date-section';

    const header = document.createElement('button');
    header.className = 'date-header';
    header.innerHTML = `
      <span class="date-label">${formatDateHeader(date)}</span>
      <span class="date-count">${articles.length}건</span>
      <svg class="date-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;

    const grid = document.createElement('div');
    grid.className = 'date-grid';
    articles.forEach(a => grid.appendChild(createCard(a)));

    header.addEventListener('click', () => {
      section.classList.toggle('collapsed');
    });

    section.appendChild(header);
    section.appendChild(grid);
    newsGrid.appendChild(section);
  });
}

// ── 통계 ──────────────────────────────────────────────
function updateStats() {
  const total = NEWS_DATA.articles.length;
  const today = NEWS_DATA.articles.filter(a => isToday(a.publishedAt)).length;
  statTotal.textContent = total;
  statToday.textContent = today;
}

// ── 날짜 표시 ─────────────────────────────────────────
function setDates() {
  const d = new Date();
  const dateStr = `${d.getFullYear()}. ${d.getMonth() + 1}. ${d.getDate()}. 기준`;
  document.getElementById('header-date').textContent = dateStr;
  document.getElementById('footer-updated').textContent =
    `마지막 수집: ${NEWS_DATA.lastUpdated}`;
}

// ── 이벤트 ────────────────────────────────────────────
filterTabs.addEventListener('click', e => {
  const tab = e.target.closest('.tab');
  if (!tab) return;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  tab.classList.add('active');
  currentFilter = tab.dataset.filter;
  render();
});

let searchTimer;
searchInput.addEventListener('input', e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    currentSearch = e.target.value.trim();
    render();
  }, 200);
});

// 필터 바 스크롤 shadow
const filterWrap = document.getElementById('filter-wrap');
window.addEventListener('scroll', () => {
  const scrolled = window.scrollY > 56 + 200;
  filterWrap.style.boxShadow = scrolled ? '0 2px 12px rgba(0,0,0,0.08)' : '';
}, { passive: true });

// ── 초기화 ────────────────────────────────────────────
setDates();
updateStats();
render();
