import sys

with open('jayson index.html', 'r', encoding='utf-8') as f:
    jayson_html = f.read()

# Extract CSS
start_css = jayson_html.find('<style>')
end_css = jayson_html.find('</style>') + len('</style>')
css = jayson_html[start_css:end_css]

# Add custom CSS for newsletter formatting
custom_css = """
    .newsletter-summary {
      display: grid;
      gap: 8px;
    }
    .summary-topic {
      font-weight: 700;
      color: var(--text);
      font-size: 15px;
      line-height: 1.5;
    }
    .summary-support {
      color: var(--muted);
      font-size: 14.5px;
      line-height: 1.5;
    }
    .sentiment-positive { color: var(--good); border-color: var(--good); background: color-mix(in srgb, var(--good) 10%, transparent); }
    .sentiment-negative { color: var(--bad); border-color: var(--bad); background: color-mix(in srgb, var(--bad) 10%, transparent); }
    .sentiment-neutral { color: var(--warn); border-color: var(--warn); background: color-mix(in srgb, var(--warn) 10%, transparent); }
    .entity-row strong, .tag-row strong { font-size: 12px; color: var(--muted); text-transform: uppercase; }
"""
css = css.replace('</style>', custom_css + '\n  </style>')

html_body = """
<body>
  <div class="app-shell" data-theme="light">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <h1>Value Research</h1>
          <p id="generatedMeta">Loading data...</p>
        </div>
        <div class="top-actions">
          <a class="button" href="AGENTS.md">AGENTS.md</a>
          <a class="button" href="Processed/MASTER%20Report/">MASTER Report</a>
          <button class="button primary" type="button" id="themeToggle">Dark Mode</button>
        </div>
      </div>
    </header>

    <div class="layout">
      <aside class="sidebar" aria-label="Dashboard navigation">
        <section class="panel" aria-labelledby="timelineTitle">
          <div class="panel-header">
            <div>
              <h2 class="panel-title" id="timelineTitle">Timeline</h2>
              <p class="panel-subtitle" id="timelineSubtitle">0 processing days</p>
            </div>
          </div>
          <div class="timeline-list" id="timelineList"></div>
        </section>

        <section class="panel" aria-labelledby="metricsTitle">
          <div class="panel-header">
            <div>
              <h2 class="panel-title" id="metricsTitle">Coverage</h2>
              <p class="panel-subtitle">Processed intelligence</p>
            </div>
          </div>
          <div class="metric-grid" id="metricGrid"></div>
        </section>
      </aside>

      <main class="main">
        <section class="toolbar" aria-label="Filters">
          <div class="field">
            <label for="searchInput">Search</label>
            <input id="searchInput" type="search" placeholder="Search titles, companies, tags">
          </div>
          <div class="field">
            <label for="categoryFilter">Category</label>
            <select id="categoryFilter"></select>
          </div>
          <div class="field">
            <label for="industryFilter">Industry</label>
            <select id="industryFilter"></select>
          </div>
          <div class="field">
            <label for="sortSelect">Sort</label>
            <select id="sortSelect">
              <option value="category">Category</option>
              <option value="industry">Industry</option>
              <option value="title">Title</option>
            </select>
          </div>
          <button class="button" type="button" id="resetButton">Reset</button>
        </section>

        <section class="narrative" aria-labelledby="dailyHeadline">
          <div>
            <p class="narrative-kicker" id="selectedDateLabel">Current Day</p>
            <h2 id="dailyHeadline">No processed intelligence yet</h2>
            <p id="dailySummary">Add source files to the raw folders and run an agent processing cycle to populate this dashboard.</p>
          </div>
          <div class="narrative-meta">
            <span><strong id="dayItemCount">0</strong> items</span>
            <span><strong id="daySectorCount">0</strong> sectors</span>
          </div>
        </section>

        <section class="category-grid" id="categoryGrid" aria-label="News groups"></section>
      </main>
    </div>

    <footer class="footer">
      <span>Value Research dashboard data is generated from processed reports and wiki notes.</span>
      <span id="footerMeta">Vault: Value Research</span>
    </footer>
  </div>

  <script>
    const FALLBACK_DATA = {
      version: "2.0.0",
      updated: new Date().toISOString(),
      industries: [],
      days: []
    };

    let vaultData = FALLBACK_DATA;

    const CATEGORY_ORDER = [
      "Vietnam Enterprise",
      "Global Enterprise",
      "Vietnam Macro",
      "Global Macro"
    ];

    const state = {
      activeDate: null,
      query: "",
      category: "All",
      industry: "All",
      sort: "category"
    };

    const elements = {
      appShell: document.querySelector(".app-shell"),
      generatedMeta: document.getElementById("generatedMeta"),
      footerMeta: document.getElementById("footerMeta"),
      timelineList: document.getElementById("timelineList"),
      timelineSubtitle: document.getElementById("timelineSubtitle"),
      metricGrid: document.getElementById("metricGrid"),
      searchInput: document.getElementById("searchInput"),
      categoryFilter: document.getElementById("categoryFilter"),
      industryFilter: document.getElementById("industryFilter"),
      sortSelect: document.getElementById("sortSelect"),
      resetButton: document.getElementById("resetButton"),
      themeToggle: document.getElementById("themeToggle"),
      selectedDateLabel: document.getElementById("selectedDateLabel"),
      dailyHeadline: document.getElementById("dailyHeadline"),
      dailySummary: document.getElementById("dailySummary"),
      dayItemCount: document.getElementById("dayItemCount"),
      daySectorCount: document.getElementById("daySectorCount"),
      categoryGrid: document.getElementById("categoryGrid")
    };

    const emptyDay = {
      date: new Date().toISOString().slice(0, 10),
      headline: {
        title: "No processed intelligence yet",
        summary: "Add source files to the raw folders and run an agent processing cycle."
      },
      items: []
    };

    function getDays() {
      const days = Array.isArray(vaultData.days) ? vaultData.days : [];
      return days.length > 0 ? days : [emptyDay];
    }

    function escapeHtml(value) {
      if (value == null) return "";
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function formatDate(value) {
      if (!value) return "Unknown date";
      const date = new Date(value + "T00:00:00");
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "2-digit" });
    }

    function formatDateTime(value) {
      if (!value) return "Not generated";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString(undefined, { year: "numeric", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
    }

    function flattenItems(days = getDays()) {
      return days.flatMap((day) => {
        const items = Array.isArray(day.items) ? day.items : [];
        return items.map(it => ({ ...it, date: day.date }));
      });
    }

    function unique(values) {
      return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
    }

    function getDay(date) {
      return getDays().find((day) => day.date === date) || getDays()[0];
    }

    function getItemSearchText(item) {
      return [
        item.title,
        item.summary,
        item.category,
        item.industry,
        ...(item.companies || []),
        ...(item.tags || [])
      ].join(" ").toLowerCase();
    }

    function itemMatchesFilters(item) {
      const query = state.query.trim().toLowerCase();
      const queryMatch = query.length === 0 || getItemSearchText(item).includes(query);
      const categoryMatch = state.category === "All" || item.category === state.category;
      const industryMatch = state.industry === "All" || item.industry === state.industry;
      return queryMatch && categoryMatch && industryMatch;
    }

    function sortItems(items) {
      const sorted = [...items];
      const comparators = {
        category: (a, b) => {
          const categoryDelta = CATEGORY_ORDER.indexOf(a.category || "Other") - CATEGORY_ORDER.indexOf(b.category || "Other");
          return categoryDelta || (a.industry||"").localeCompare(b.industry||"") || (a.title||"").localeCompare(b.title||"");
        },
        industry: (a, b) => (a.industry||"").localeCompare(b.industry||"") || (a.title||"").localeCompare(b.title||""),
        title: (a, b) => (a.title||"").localeCompare(b.title||"")
      };
      return sorted.sort(comparators[state.sort] || comparators.category);
    }

    function groupBy(items, getter) {
      return items.reduce((groups, item) => {
        const key = getter(item) || "Other";
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(item);
        return groups;
      }, new Map());
    }

    function renderOptions(select, values, current) {
      const options = ["All", ...values];
      select.innerHTML = options
        .map((value) => `<option value="${escapeHtml(value)}"${value === current ? " selected" : ""}>${escapeHtml(value)}</option>`)
        .join("");
    }

    function renderFilters() {
      const items = flattenItems();
      renderOptions(elements.categoryFilter, CATEGORY_ORDER, state.category);
      renderOptions(elements.industryFilter, unique(items.map((item) => item.industry)), state.industry);
      elements.searchInput.value = state.query;
      elements.sortSelect.value = state.sort;
    }

    function renderMetrics() {
      const items = flattenItems();
      const sectors = new Set(items.map((item) => item.industry).filter(Boolean));
      const metrics = [
        ["News Items", items.length],
        ["Sectors", sectors.size],
        ["Days Tracked", getDays().length]
      ];

      elements.metricGrid.innerHTML = metrics
        .map(([label, value]) => `
          <div class="metric">
            <strong>${escapeHtml(value)}</strong>
            <span>${escapeHtml(label)}</span>
          </div>
        `)
        .join("");
    }

    function renderTimeline() {
      const days = getDays().slice().sort((a, b) => String(b.date).localeCompare(String(a.date)));
      if (!state.activeDate) state.activeDate = days[0]?.date || emptyDay.date;

      elements.timelineSubtitle.textContent = `${days.length} processing ${days.length === 1 ? "day" : "days"}`;
      elements.timelineList.innerHTML = days
        .map((day) => {
          const itemCount = Array.isArray(day.items) ? day.items.length : 0;
          const isActive = day.date === state.activeDate;
          return `
            <button class="day-button${isActive ? " active" : ""}" type="button" data-date="${escapeHtml(day.date)}">
              <strong>${escapeHtml(formatDate(day.date))}</strong>
              <span>${escapeHtml(itemCount)} items</span>
            </button>
          `;
        })
        .join("");

      elements.timelineList.querySelectorAll("[data-date]").forEach((button) => {
        button.addEventListener("click", () => {
          state.activeDate = button.dataset.date;
          render();
        });
      });
    }

    function renderNarrative(dayItems) {
      const day = getDay(state.activeDate);
      const sectors = new Set(dayItems.map((item) => item.industry).filter(Boolean));
      elements.selectedDateLabel.textContent = formatDate(day.date);
      
      let headlineTitle = "No processed intelligence yet";
      let headlineSummary = "Add source files to the raw folders and run an agent processing cycle to populate this dashboard.";
      
      if (day.headline) {
        headlineTitle = day.headline.title || headlineTitle;
        headlineSummary = day.headline.summary || headlineSummary;
      } else if (dayItems.length > 0) {
        headlineTitle = dayItems[0].title;
        headlineSummary = dayItems[0].summary;
      }

      elements.dailyHeadline.textContent = headlineTitle;
      elements.dailySummary.textContent = headlineSummary;
      elements.dayItemCount.textContent = dayItems.length;
      elements.daySectorCount.textContent = sectors.size;
    }

    function renderItem(item) {
      const companies = item.companies || [];
      const tags = item.tags || [];
      
      const actions = [];
      if (item.source_url) actions.push(`<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">↗ Open source</a>`);
      if (item.wiki_path) actions.push(`<a href="${encodeURI(item.wiki_path)}">📓 Open wiki note</a>`);
      if (item.report_path) actions.push(`<a href="${encodeURI(item.report_path)}">📊 Open report section</a>`);
      if (item.raw_path) actions.push(`<a href="${encodeURI(item.raw_path)}">📄 Open raw file</a>`);

      let topicSentence = "";
      let supportingIdeas = "";
      const summary = item.summary || "";
      const match = summary.match(/^([^.!?]+[.!?])(?:\s+|$)(.*)$/s);
      if (match) {
        topicSentence = match[1];
        supportingIdeas = match[2];
      } else {
        topicSentence = summary;
      }

      return `
        <details class="news-item">
          <summary>
            <div class="item-title">
              <strong>${escapeHtml(item.title || "Untitled item")}</strong>
            </div>
            ${item.sentiment ? `<span class="count-pill sentiment-${item.sentiment}">${escapeHtml(item.sentiment)}</span>` : ""}
          </summary>
          <div class="item-body">
            <div class="newsletter-summary">
              <p class="summary-topic">${escapeHtml(topicSentence)}</p>
              ${supportingIdeas ? `<p class="summary-support">${escapeHtml(supportingIdeas)}</p>` : ""}
            </div>
            ${companies.length ? `<div class="entity-row"><strong>Entities:</strong> ${companies.map(c => `<span class="entity">${escapeHtml(c)}</span>`).join("")}</div>` : ""}
            ${tags.length ? `<div class="tag-row"><strong>Tags:</strong> ${tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>` : ""}
            ${actions.length ? `<div class="action-row">${actions.join("")}</div>` : ""}
          </div>
        </details>
      `;
    }

    function renderCategory(name, items, index) {
      const grouped = groupBy(sortItems(items), (item) => item.industry || "Other");
      const industryMarkup = Array.from(grouped.entries())
        .sort((a,b) => a[0].localeCompare(b[0]))
        .map(([industry, industryItems]) => `
          <div class="industry-group">
            <div class="industry-heading">
              <span>${escapeHtml(industry)}</span>
              <span>${escapeHtml(industryItems.length)} ${industryItems.length === 1 ? "item" : "items"}</span>
            </div>
            <div class="item-list">
              ${industryItems.map(renderItem).join("")}
            </div>
          </div>
        `)
        .join("");

      return `
        <details class="category-section" ${index === 0 ? "open" : ""}>
          <summary>
            <div class="summary-main">
              <span class="chevron">></span>
              <div>
                <h3>${escapeHtml(name)}</h3>
                <span>${escapeHtml(grouped.size)} ${grouped.size === 1 ? "industry" : "industries"}</span>
              </div>
            </div>
            <span class="count-pill">${escapeHtml(items.length)}</span>
          </summary>
          ${items.length ? industryMarkup : `
            <div class="industry-group">
              <div class="empty-state">
                <strong>No matching items</strong>
                <span>This group will populate after processed sources are written to reports and dashboard data.</span>
              </div>
            </div>
          `}
        </details>
      `;
    }

    function renderCategories(dayItems) {
      const filtered = sortItems(dayItems.filter(itemMatchesFilters));
      const grouped = groupBy(filtered, (item) => item.category || "Unclassified");
      const categories = state.category === "All" ? CATEGORY_ORDER : [state.category];

      elements.categoryGrid.innerHTML = categories
        .map((category, index) => renderCategory(category, grouped.get(category) || [], index))
        .join("");
    }

    function renderMeta() {
      const itemCount = flattenItems().length;
      const generated = formatDateTime(vaultData.updated);
      elements.generatedMeta.textContent = `${itemCount} items | Last updated ${generated}`;
    }

    function render() {
      renderMeta();
      renderFilters();
      renderMetrics();
      renderTimeline();
      const dayItems = flattenItems([getDay(state.activeDate)]);
      renderNarrative(dayItems);
      renderCategories(dayItems);
    }

    function setTheme(theme) {
      elements.appShell.dataset.theme = theme;
      elements.themeToggle.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
      localStorage.setItem("jayvault-theme", theme);
    }

    // Event listeners
    elements.searchInput.addEventListener("input", (event) => {
      state.query = event.target.value;
      renderCategories(flattenItems([getDay(state.activeDate)]));
    });

    elements.categoryFilter.addEventListener("change", (event) => {
      state.category = event.target.value;
      render();
    });

    elements.industryFilter.addEventListener("change", (event) => {
      state.industry = event.target.value;
      render();
    });

    elements.sortSelect.addEventListener("change", (event) => {
      state.sort = event.target.value;
      render();
    });

    elements.resetButton.addEventListener("click", () => {
      state.query = "";
      state.category = "All";
      state.industry = "All";
      state.sort = "category";
      render();
    });

    elements.themeToggle.addEventListener("click", () => {
      const nextTheme = elements.appShell.dataset.theme === "dark" ? "light" : "dark";
      setTheme(nextTheme);
    });

    setTheme(localStorage.getItem("jayvault-theme") || "light");

    // Load actual data
    async function init() {
      try {
        const res = await fetch("news_database.json", { cache: "no-cache" });
        if (res.ok) {
          vaultData = await res.json();
        }
      } catch(e) {
        console.error("Could not load news_database.json", e);
      }
      render();
    }
    
    init();
  </script>
</body>
</html>
"""

full_html = f"<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>Value Research Dashboard</title>\n{css}\n</head>\n{html_body}"

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
