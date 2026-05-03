# Statistical best-practices roadmap

Bestandsaufnahme: an welchen Stellen weichen die Verfahren in diesem Repo von etablierten statistischen Best Practices ab, und was kostet es das nachzuziehen. Ergänzt [`GRANULARITY_ANALYSIS.md`](GRANULARITY_ANALYSIS.md), das den item-level-Granularitäts-Teil derselben Frage abdeckt.

Reihenfolge der Umsetzung: **Apriori → Block 1 → Block 2**, mit kurzer Evaluation zwischen den Blöcken (Render + Sichtprüfung der Real-Data-Outputs).

## Übersicht — Lücken pro Verfahren

| Kap | Aktuell | Best Practice (state of the art) | Impact für Real-Data | Aufwand |
|---|---|---|---|---|
| **01 Apriori** | Confidence-only Triage mit Synth-zugeschnittenem Bundle-/Symmetry-Filter | Drei klar getrennte Sichten (Bundle / Cross-Sell / Top-Insight) auf einer Apriori-Run; `arules::is.redundant()`; multiple Metrics (Lift, Conviction, Leverage); erweitertes BUNDLE_PATTERNS für Real-Vokabular; Substring-Annotation | **HOCH** — Triage greift sonst nicht auf Real | ~2 h |
| **02 BCG** | K-means auf `StandardScaler`-skalierten *raw* share/growth | Cluster auf **log/cbrt-transformierten** features (cbrt nur für Plot, nicht fürs Clustering aktuell). Plus **Silhouette / Gap statistic** für k statt nur Elbow | **HOCH** — Real-Tails sonst Outlier-dominiert | ~30 min |
| **03 RFM** | StandardScaler + K-means | **Log-transform** für value (klassisch seit den 80ern), RobustScaler. Plus klassische **percentile-basierte R/F/M-Scores** (R1–R5 etc.) als Alternative | **HOCH** — value-Tail sprengt sonst die Cluster | ~45 min |
| **04 CLV** | BG/NBD + Gamma-Gamma standard, holdout-validiert | **Outlier-Trimming** monetary vor Gamma-Gamma. **Calibration plot** P(alive) vs. tatsächliche Repurchases | MEDIUM | ~30 min |
| **06 Survival** | KM + Cox PH auf department + basket-features | **Schoenfeld-Residual-Test** für PH-Assumption (`cph.check_assumptions()`). Stratifikation / time-varying covariate bei Verletzung | MEDIUM | ~20 min |
| **07 Forecasting** | Fest SARIMA(1,1,1)(1,1,1,12), single 3-Monats-Holdout | **Auto-ARIMA** (`pmdarima`) statt fester Order. **Rolling-origin CV** statt single holdout. **Box-Cox/log-transform**. **Prediction intervals** | **HOCH** — fester Order auf 25 Monaten oft schlecht | ~60 min |
| **08 Embeddings** | PPMI × SVD k=24 | **Shifted PPMI** (Levy & Goldberg 2014, log(k)-shift). Plus **min-count cutoff** für rare items. Dimensionalität-Validation | MEDIUM | ~30 min |
| **09 Uplift** | T-/S-Learner direkt | Auf Real ist discount nicht random → **Propensity-Score-Weighting**, **DR-Learner** (`econml.dr.LinearDRLearner`), **Causal Forest**. T/S allein ohne propensity ist auf observationalen Daten biased | **HOCH** — Schätzung sonst unzuverlässig | ~60 min |

**Übergreifende Themen** (nicht kapitel-spezifisch):
- **Outlier-Detection**: nirgendwo systematisch. IQR-Flags pro Feature
- **Missing-Value-Imputation**: nur Filter, keine Imputation. ~5 % Real-Daten gehen verloren
- **Feature-Scaling**: StandardScaler überall, RobustScaler oder log-transform für skewed Daten besser

## Vorgehen

### Apriori (jetzt)

Detail-Plan in der Implementierung — drei Sichten + arules-Werkzeuge, siehe Tabelle oben Zeile 01.

→ Render + Sicht-Prüfung der Real-Data-Outputs. Wenn die Cross-Sell-Liste nicht mehr von definitionalen Plumbing-Regeln dominiert ist und Bundle-Komposition + Top-Insight separat lesbar sind: weiter zu Block 1.

### Block 1 — High-impact Methoden-Fixes

In dieser Reihenfolge:
1. **02 BCG** — cluster auf transformierten features
2. **03 RFM** — log-transform value
3. **07 Forecasting** — Auto-ARIMA + Rolling-origin CV + Prediction intervals
4. **09 Uplift** — Propensity-Score / DR-Learner für observational case

→ Render + Sicht-Prüfung. Wenn die Cluster auf Real-Data nicht mehr von Tail-Outliers dominiert sind, Forecasting-MAE per category sich verbessert hat, und der Uplift-CATE einen propensity-bereinigten Wert zeigt: weiter zu Block 2.

### Block 2 — Verfeinerungen + übergreifend

In dieser Reihenfolge:
1. **06 Survival** — Schoenfeld-Residual-Check
2. **04 CLV** — Outlier-Trimming + Calibration-Plot
3. **08 Embeddings** — Shifted PPMI + min-count cutoff
4. Übergreifende Outlier-/Imputation-Strategie für Preprocess

→ Final-Render. Stand der Technik in jedem Verfahren, Real-Data-Pipeline durchgängig sauber.

## Aufwand gesamt

| Block | Aufwand |
|---|---|
| Apriori | ~2 h |
| Block 1 | ~3¼ h |
| Block 2 | ~2 h |
| Render-/Eval-Pausen | ~30 min |
| **Total** | **~7¾ h** |
