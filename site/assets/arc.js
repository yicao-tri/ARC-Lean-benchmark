(function () {
  "use strict";
  const data = window.ARC_DATA;
  if (!data) return;

  const pretty = (value) => String(value || "—").replaceAll("_", " ");
  const percent = (value) => value === "" || value == null ? "—" : `${(Number(value) * 100).toFixed(Number(value) % 1 ? 1 : 0)}%`;

  function setupNavigation() {
    const links = [...document.querySelectorAll(".nav-link")];
    const sections = links.map((link) => document.querySelector(link.getAttribute("href"))).filter(Boolean);
    if (!("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver((entries) => {
      entries.filter((entry) => entry.isIntersecting).forEach((entry) => {
        links.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`));
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    sections.forEach((section) => observer.observe(section));
  }

  function setupDemo() {
    const root = document.querySelector("[data-audit-demo]");
    if (!root || !data.cases.length) return;
    let caseId = data.cases[0].id;
    let mode = "arc";
    const get = (name) => root.querySelector(`[data-field='${name}']`);
    const decisionCeiling = { supported: "source scoped support only", falsified: "bounded falsification only", inconclusive: "compatibility only" };

    function render() {
      const item = data.cases.find((candidate) => candidate.id === caseId);
      const ceiling = mode === "arc" ? pretty(item.ceiling) : decisionCeiling[item.decision];
      const isRisk = mode === "decision" && ceiling !== pretty(item.ceiling);
      get("claim").textContent = item.claim;
      get("scope").textContent = `Declared scope: ${item.scope}`;
      get("evidence").textContent = item.evidence_summary;
      get("world-a").textContent = item.mechanisms[0] || "The measured target is directly reproduced inside the declared scope.";
      get("world-b").textContent = item.mechanisms[1] || "No live alternative is required for this bounded descriptive target.";
      get("decision").textContent = pretty(item.decision);
      get("identifiability").textContent = pretty(item.identifiability);
      get("ceiling").textContent = ceiling;
      get("risk").textContent = isRisk ? "overclaim risk" : "within ceiling";
      get("risk").parentElement.className = `verdict ${isRisk ? "risk" : "safe"}`;
      get("closure").textContent = item.closure;
      get("formal").textContent = item.formal === "kernel_checked" ? "Lean receipt: kernel checked" : "Formal receipt: not required";
      root.querySelectorAll(".case-button").forEach((button) => button.classList.toggle("active", button.dataset.case === caseId));
      root.querySelectorAll(".mode-button").forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
    }

    root.querySelectorAll(".case-button").forEach((button) => button.addEventListener("click", () => { caseId = button.dataset.case; render(); }));
    root.querySelectorAll(".mode-button").forEach((button) => button.addEventListener("click", () => { mode = button.dataset.mode; render(); }));
    render();
  }

  function setupTable() {
    const tbody = document.querySelector("[data-results-body]");
    if (!tbody) return;
    let family = "all";
    function render() {
      const rows = data.table.filter((row) => family === "all" || row.family === family);
      tbody.innerHTML = rows.map((row) => {
        const values = ["seed_overclaim_rate", "seed_identifiability_exact_match", "seed_decision_exact_match", "seed_joint_exact_match", "public_overclaim_rate", "public_identifiability_exact_match", "public_decision_exact_match", "public_joint_exact_match"];
        return `<tr><td>${row.family}</td><td>${row.method}</td>${values.map((key) => `<td class="${row[key] === "" ? "dash" : ""}">${percent(row[key])}</td>`).join("")}</tr>`;
      }).join("");
    }
    document.querySelectorAll(".family-button").forEach((button) => button.addEventListener("click", () => {
      family = button.dataset.family;
      document.querySelectorAll(".family-button").forEach((candidate) => candidate.classList.toggle("active", candidate === button));
      render();
    }));
    render();
  }

  function setupCarousels() {
    document.querySelectorAll("[data-scroll-target]").forEach((button) => button.addEventListener("click", () => {
      const target = document.querySelector(button.dataset.scrollTarget);
      if (!target) return;
      target.scrollBy({ left: Number(button.dataset.direction || 1) * target.clientWidth * 0.82, behavior: "smooth" });
    }));
  }

  setupNavigation();
  setupDemo();
  setupTable();
  setupCarousels();
})();
