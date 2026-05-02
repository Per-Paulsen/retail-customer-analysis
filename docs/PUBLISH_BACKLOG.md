# Publish & Polish Backlog

Things to do *after* the analytical work is complete (which it is — see [`ROADMAP.md`](ROADMAP.md), all four method extensions implemented). This list is operational, not analytical: how to actually use the repo as a portfolio piece, plus optional polish items.

Ordered roughly by impact-to-effort.

---

## A. Use it (do these first — the actual point of the project)

These are the moves that make the work *visible*. Without them the repo is a tree falling in an empty forest.

### A1. Pin the repo on the GitHub profile
- **Where:** [github.com/Per-Paulsen](https://github.com/Per-Paulsen) → "Customize your pins"
- **Effort:** 30 seconds
- **Why:** profile visitors see a curated max-6 list; this should be one of them
- **Status:** ☐

### A2. LinkedIn post
- **Headline:** *"End-to-end retail analytics with R + Python: from market basket to causal uplift"* (or similar)
- **Body:** ~3 sentences. What it is, what's in it methodologically (one short list), the live link
- **Link to:** the **site**, not the repo (https://per-paulsen.github.io/retail-customer-analysis/) — recruiters click on the visual, not the GitHub
- **Effort:** 15 minutes
- **Status:** ☐

### A3. CV / portfolio entry
- **Format:** 4-bullet block in a "Projects" section
  - Bullet 1: what it is (one line)
  - Bullet 2: methods list (Apriori, BCG, RFM, BG/NBD, Cox PH, SARIMA, PPMI×SVD, meta-learners)
  - Bullet 3: tech stack (R, Python, Quarto, GitHub Pages, GitHub Actions)
  - Bullet 4: live link
- **Effort:** 10 minutes
- **Status:** ☐

### A4. Reading-order hint when you point someone at it
When sharing the link directly with someone, suggest the path:

1. **Dashboard first** ([dashboard.html](https://per-paulsen.github.io/retail-customer-analysis/dashboard.html)) — visual wow, KPIs in 30 seconds
2. **Insights** ([05-insights.html](https://per-paulsen.github.io/retail-customer-analysis/05-insights.html)) — shows the synthesis thinking, recommendations
3. **Specific chapters** based on what they care about

This avoids "I went to the repo and didn't know where to start" feedback.

---

## B. Repo-level polish (optional, all small)

### B1. Update GitHub repo description + topics
- The description is fine but topics haven't been refreshed since chapter 06. Add: `survival-analysis`, `causal-inference`, `bgnbd-model`, `embeddings`, `forecasting`
- Use `gh repo edit Per-Paulsen/retail-customer-analysis --add-topic survival-analysis --add-topic causal-inference ...`
- **Effort:** 2 minutes
- **Status:** ☐

### B2. Social-preview image (Open Graph)
- A 1280×640 PNG that shows when someone shares the repo / site link on Slack / LinkedIn / Twitter
- Either upload via GitHub repo settings (for the repo's link card), or include in `_quarto.yml` under `format: html: image:` (for the site)
- **Effort:** 15 minutes in Figma / Canva / Excalidraw
- **Status:** ☐

### B3. `docs/METHODOLOGY.md`
- Pull the triage framework (🟢 actionable / 🟡 sanity check / 🔴 data quality, plus the symmetry+accessory filtering for rules) into a standalone doc
- Generic enough to be a reference for future projects, not just this one
- Currently lives only inside chapter 05 and chapter 01 — extracting makes it linkable
- **Effort:** 30 minutes
- **Status:** ☐

### B4. `docs/CASE_STUDY.md`
- The story arc behind the repo: Innatura internship 2017 → why the original methods, what they couldn't see, how the modernized version fixes it
- Useful for a recruiter who wants the *narrative*, not just the methods
- **Effort:** 45 minutes
- **Status:** ☐

### B5. `CHANGELOG.md` with semantic-version tags
- Tag the current state as `v1.0.0`. Subsequent updates get tagged.
- Signals to a recruiter that the project is *maintained*, not abandoned
- `gh release create v1.0.0 --title "Initial release" --notes-from-tag` once the tag is pushed
- **Effort:** 20 minutes
- **Status:** ☐

---

## C. Future analytical work (deferred — see `ROADMAP.md`)

`ROADMAP.md` listed four method extensions. All are now ✅ implemented as chapters 04, 06, 07, 08, 09. New analytical extensions, if appetite returns:

- **Hierarchical / panel-data customer segmentation** — Mixed-effects models or hierarchical Bayesian RFM. Probably overkill for 2,400 customers; would shine with 100k+
- **Causal forest for heterogeneous treatment effects** — Replace meta-learners with `econml`'s `CausalForestDML` for richer per-customer uplift estimates. Currently blocked by Python 3.14 wheel issues; might work with a different Python env
- **Recommender system (matrix factorization or two-tower)** — Customer × product matrix → embeddings on both sides. Needs more customers/products to be meaningful
- **Real-time event stream simulation** — Generate streaming purchase events, demonstrate Kafka + processing pipeline. Big engineering lift, modest analytical novelty

None of these is necessary. The repo as it stands covers the methodological breadth a portfolio needs.

---

## D. Maintenance discipline (low priority)

Things to do *every few months* if the repo stays alive:

- **Re-render check** — push a no-op commit, verify CI still builds. Catches Quarto / package version drift.
- **Dependency updates** — `pip list --outdated`, `Rscript R/install_packages.R` (which idempotently updates), commit the lockfile changes if any
- **README freshness** — anything you've talked about with recruiters that didn't make it into the README? Add it.

---

## How to use this list

Pick **one item from category A** at a time. Don't bundle. Doing A1+A2+A3 in one sitting is realistic; doing A through D in one sitting is procrastination disguised as productivity.

Mark items as `☑` when done. The status checkboxes are your honest log of what's actually shipped vs. what's still aspiration.
