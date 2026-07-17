// OSM Highway Topology Error Reports — plain HTML/CSS/JS front end.
// No build step required: open index.html directly, or serve the folder statically.

const appEl = document.getElementById("app");

const state = {
  results: null,
  loading: true,
  error: null,
  searchQuery: "",
  sortBy: "name",
  filterStatus: "all",
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function parseStateHash(hash) {
  const match = hash.match(/^#\/state\/([^/]+)$/);
  return match ? match[1] : null;
}

function spinner(label) {
  return `
    <div class="flex flex-col items-center justify-center h-screen gap-4">
      <div class="spinner"></div>
      <p class="text-slate-300">${escapeHtml(label)}</p>
    </div>
  `;
}

function errorBox(message) {
  return `
    <div class="max-w-2xl mx-auto rounded-lg border border-red-500/30 bg-red-500/10 p-5">
      <p class="font-semibold text-red-400">Failed to load data</p>
      <p class="text-sm text-red-300/90 mt-1">${escapeHtml(message)}</p>
    </div>
  `;
}

function renderHeader(results) {
  const totalStates = results.total_states || 0;
  const totalIssues = results.total_issues || 0;
  const successfulAnalyses = results.successful_analyses || 0;
  const lastUpdated = results.timestamp
    ? new Date(results.timestamp).toLocaleString()
    : "Unknown";

  const stats = [
    { label: "Total States", value: totalStates, className: "text-white" },
    {
      label: "Total Issues Found",
      value: totalIssues,
      className: "text-orange-400",
    },
    {
      label: "Successful Analyses",
      value: successfulAnalyses,
      className: "text-green-400",
    },
    {
      label: "Last Updated",
      value: lastUpdated,
      className: "text-white text-sm",
    },
  ];

  return `
    <div class="border-b border-slate-700 pb-10">
      <div class="mb-8">
        <h1 class="text-4xl font-bold text-white mb-3">🗺️ OSM Highway Topology Errors</h1>
        <p class="text-slate-300 leading-relaxed">
          Automated analysis of OpenStreetMap highway topology across US states
        </p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        ${stats
          .map(
            (stat) => `
          <div class="rounded-lg border border-slate-700 bg-slate-800/60 p-5 transition-colors hover:border-slate-600">
            <p class="text-sm text-slate-400 mb-2">${escapeHtml(stat.label)}</p>
            <p class="text-3xl font-bold truncate ${stat.className}">${escapeHtml(String(stat.value))}</p>
          </div>
        `,
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderSearchAndFilter() {
  return `
    <div class="rounded-lg border border-slate-700 bg-slate-800/60 p-5">
      <div class="flex flex-col gap-5 md:flex-row md:items-end">
        <div class="flex-1">
          <label for="search" class="mb-1 block text-xs font-medium text-slate-400">Search</label>
          <div class="relative">
            <svg class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              id="search"
              type="text"
              value="${escapeHtml(state.searchQuery)}"
              placeholder="Search states…"
              class="w-full rounded-md border border-slate-600 bg-slate-900 py-2 pl-9 pr-9 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            ${
              state.searchQuery
                ? `<button type="button" id="clear-search" aria-label="Clear search" class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>`
                : ""
            }
          </div>
        </div>
        <div class="md:w-48">
          <label for="sort" class="mb-1 block text-xs font-medium text-slate-400">Sort</label>
          <select id="sort" class="w-full rounded-md border border-slate-600 bg-slate-900 py-2 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="name" ${state.sortBy === "name" ? "selected" : ""}>Name (A–Z)</option>
            <option value="issues-asc" ${state.sortBy === "issues-asc" ? "selected" : ""}>Issues (Low to High)</option>
            <option value="issues-desc" ${state.sortBy === "issues-desc" ? "selected" : ""}>Issues (High to Low)</option>
          </select>
        </div>
        <div class="md:w-48">
          <label for="filter" class="mb-1 block text-xs font-medium text-slate-400">Filter</label>
          <select id="filter" class="w-full rounded-md border border-slate-600 bg-slate-900 py-2 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="all" ${state.filterStatus === "all" ? "selected" : ""}>All Results</option>
            <option value="success" ${state.filterStatus === "success" ? "selected" : ""}>Successful Only</option>
            <option value="failed" ${state.filterStatus === "failed" ? "selected" : ""}>Failed Only</option>
          </select>
        </div>
      </div>
    </div>
  `;
}

function getFilteredAndSortedResults() {
  if (!state.results || !state.results.results) return [];

  let filtered = state.results.results.filter((s) => {
    const matchesSearch = s.name
      .toLowerCase()
      .includes(state.searchQuery.toLowerCase());

    if (state.filterStatus === "success") return matchesSearch && s.success;
    if (state.filterStatus === "failed") return matchesSearch && !s.success;
    return matchesSearch;
  });

  filtered.sort((a, b) => {
    switch (state.sortBy) {
      case "name":
        return a.name.localeCompare(b.name);
      case "issues-asc":
        return (a.issues || 0) - (b.issues || 0);
      case "issues-desc":
        return (b.issues || 0) - (a.issues || 0);
      default:
        return 0;
    }
  });

  return filtered;
}

function renderResultsList(results) {
  if (!results || results.length === 0) {
    return `
      <div class="text-center py-12">
        <p class="text-slate-400 text-lg">No results found</p>
      </div>
    `;
  }

  return `
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      ${results
        .map(
          (s) => `
        <div class="flex flex-col rounded-lg border border-slate-700 bg-slate-800/60 overflow-hidden transition-colors hover:border-slate-600">
          <div class="p-5 border-b border-slate-700 flex items-start justify-between gap-3">
            <h2 class="text-lg font-semibold text-white">${escapeHtml(s.name)}</h2>
            ${
              s.success
                ? `<span class="shrink-0 rounded-full bg-green-500/15 px-2.5 py-1 text-xs font-medium text-green-400">✓ Success</span>`
                : `<span class="shrink-0 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-400">✗ Failed</span>`
            }
          </div>
          <div class="p-5 flex-1">
            <p class="text-sm text-slate-400 mb-2">Issues Found</p>
            <p class="text-3xl font-bold text-orange-400">${escapeHtml(String(s.issues || 0))}</p>
          </div>
          <div class="p-5 border-t border-slate-700">
            <a href="#/state/${encodeURIComponent(s.state)}" class="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500 transition-colors">
              View Report
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
          </div>
        </div>
      `,
        )
        .join("")}
    </div>
  `;
}

function renderDashboard() {
  document.title = "OSM Highway Topology Error Reports";

  appEl.innerHTML = `
    <div class="space-y-10">
      ${renderHeader(state.results)}
      <div id="search-filter">${renderSearchAndFilter()}</div>
      <div id="results-list">${renderResultsList(getFilteredAndSortedResults())}</div>
    </div>
  `;

  attachDashboardListeners();
}

function attachDashboardListeners() {
  const searchInput = document.getElementById("search");
  const sortSelect = document.getElementById("sort");
  const filterSelect = document.getElementById("filter");
  const clearBtn = document.getElementById("clear-search");

  searchInput?.addEventListener("input", (e) => {
    state.searchQuery = e.target.value;
    // Preserve focus/caret position across re-render.
    const caret = e.target.selectionStart;
    document.getElementById("results-list").innerHTML = renderResultsList(
      getFilteredAndSortedResults(),
    );
    const searchFilterEl = document.getElementById("search-filter");
    searchFilterEl.innerHTML = renderSearchAndFilter();
    attachDashboardListeners();
    const newInput = document.getElementById("search");
    if (newInput) {
      newInput.focus();
      newInput.setSelectionRange(caret, caret);
    }
  });

  clearBtn?.addEventListener("click", () => {
    state.searchQuery = "";
    renderDashboard();
  });

  sortSelect?.addEventListener("change", (e) => {
    state.sortBy = e.target.value;
    document.getElementById("results-list").innerHTML = renderResultsList(
      getFilteredAndSortedResults(),
    );
  });

  filterSelect?.addEventListener("change", (e) => {
    state.filterStatus = e.target.value;
    document.getElementById("results-list").innerHTML = renderResultsList(
      getFilteredAndSortedResults(),
    );
  });
}

function formatTimestamp(timestamp) {
  try {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleDateString(undefined, {
      year: "2-digit",
      month: "short",
      day: "numeric",
    });
  } catch {
    return timestamp;
  }
}

function renderStateReportTable(report) {
  if (!report.flagged || report.flagged.length === 0) {
    return `
      <div class="rounded-lg border border-slate-700 bg-slate-800/60 text-center py-16">
        <p class="text-slate-300 text-lg">No topology errors found for ${escapeHtml(report.state_name || "")} ✨</p>
      </div>
    `;
  }

  return `
    <div class="overflow-x-auto rounded-lg border border-slate-700 shadow-lg">
      <table class="w-full bg-slate-800 text-sm">
        <thead>
          <tr class="bg-slate-900 text-left text-slate-300 uppercase text-xs tracking-wide">
            <th class="px-4 py-3.5">Way ID</th>
            <th class="px-4 py-3.5">Name</th>
            <th class="px-4 py-3.5">Highway</th>
            <th class="px-4 py-3.5">Version</th>
            <th class="px-4 py-3.5">Last Edited</th>
            <th class="px-4 py-3.5">Issue</th>
            <th class="px-4 py-3.5">Edit</th>
          </tr>
        </thead>
        <tbody>
          ${report.flagged
            .map(
              (fw) => `
            <tr class="border-t border-slate-700 hover:bg-slate-700/50">
              <td class="px-4 py-3.5 font-mono">
                <a href="${escapeHtml(fw.osm_url)}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:underline">${escapeHtml(String(fw.way_id))}</a>
              </td>
              <td class="px-4 py-3.5 text-slate-200">${escapeHtml(fw.name || "")}</td>
              <td class="px-4 py-3.5">
                <span class="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-200">${escapeHtml(fw.highway)}</span>
              </td>
              <td class="px-4 py-3.5 text-slate-300">${escapeHtml(String(fw.version))}</td>
              <td class="px-4 py-3.5 text-slate-400">${escapeHtml(formatTimestamp(fw.timestamp))}</td>
              <td class="px-4 py-3.5 text-orange-300">Start: ${escapeHtml(fw.start_connecting_highways || "none")}; End: ${escapeHtml(fw.end_connecting_highways || "none")}</td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="flex gap-2">
                  <a href="${escapeHtml(fw.id_url)}" target="_blank" rel="noopener noreferrer" class="editor-link text-xs font-bold px-2 py-1 rounded bg-blue-700 text-white hover:opacity-90">iD</a>
                  <a href="${escapeHtml(fw.josm_url)}" target="_blank" rel="noopener noreferrer" class="editor-link text-xs font-bold px-2 py-1 rounded bg-slate-600 text-white hover:opacity-90">JOSM</a>
                  <a href="${escapeHtml(fw.level0_url)}" target="_blank" rel="noopener noreferrer" class="editor-link text-xs font-bold px-2 py-1 rounded bg-green-700 text-white hover:opacity-90">L0</a>
                </div>
              </td>
            </tr>
          `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderBackButton() {
  return `
    <button type="button" id="back-button" class="-ml-3 inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
      Back to all states
    </button>
  `;
}

async function renderStateReport(stateSlug, stateName) {
  document.title = stateName
    ? `${stateName} — OSM Highway Topology Errors`
    : "OSM Highway Topology Error Reports";

  appEl.innerHTML = `
    <div class="space-y-8">
      ${renderBackButton()}
      ${spinner("Loading report…")}
    </div>
  `;
  attachBackButton();

  try {
    const url = `reports/${stateSlug}.json`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch report from ${url}`);
    }
    const report = await response.json();
    const displayName = report.state_name || stateName || stateSlug;

    document.title = `${displayName} — OSM Highway Topology Errors`;

    appEl.innerHTML = `
      <div class="space-y-8">
        ${renderBackButton()}
        <div class="space-y-8">
          <div>
            <h1 class="text-3xl font-bold text-white mb-3">🚗 OSM Highway Topology Errors — ${escapeHtml(displayName)}</h1>
            <p class="text-slate-300 leading-relaxed">
              Generated ${escapeHtml(new Date(report.generated).toLocaleString())} ·
              ${escapeHtml(report.total_issues.toLocaleString())} issue${report.total_issues === 1 ? "" : "s"} found
            </p>
          </div>
          ${renderStateReportTable(report)}
        </div>
      </div>
    `;
    attachBackButton();
  } catch (err) {
    appEl.innerHTML = `
      <div class="space-y-8">
        ${renderBackButton()}
        ${errorBox(err.message)}
      </div>
    `;
    attachBackButton();
  }
}

function attachBackButton() {
  document.getElementById("back-button")?.addEventListener("click", () => {
    window.location.hash = "";
  });
}

async function route() {
  const activeState = parseStateHash(window.location.hash);

  if (activeState) {
    const activeStateInfo = state.results?.results?.find(
      (s) => s.state === activeState,
    );
    await renderStateReport(activeState, activeStateInfo?.name);
    return;
  }

  if (state.loading) {
    appEl.innerHTML = spinner("Loading results…");
    return;
  }

  if (state.error) {
    appEl.innerHTML = errorBox(state.error);
    return;
  }

  renderDashboard();
}

async function init() {
  window.addEventListener("hashchange", route);

  try {
    const url = "results.json";
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch results from ${url}`);
    }
    state.results = await response.json();
  } catch (err) {
    state.error = err.message;
  } finally {
    state.loading = false;
  }

  route();
}

init();
