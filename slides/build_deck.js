const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");

const THEME = {
  name: "StochasticFinance", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "0B1B3A", lt1: "FFFFFF", dk2: "3A4A6B", lt2: "EEF2F8",
            accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "EDA100", accent5: "6250D6", accent6: "E34948",
            hlink: "2A78D6", folHlink: "6250D6" }
};
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";               // 10 x 5.625 in
pres.title = "Monte Carlo Pricing and Delta Hedging under GBM";
pres.author = "MAC F244 Group";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---- layouts
pres.defineSlideMaster({ title: "DARK", background: { color: "0B1B3A" },
  objects: [], slideNumber: { x: 9.2, y: 5.2, color: "AFC0DD", fontSize: 10 },
  // placeholders
});
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" },
  slideNumber: { x: 9.2, y: 5.22, color: "6B7A99", fontSize: 10 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontFace: "Cambria", fontSize: 30, bold: true, color: "0B1B3A", align: "left", valign: "middle", margin: 0 }, text: "" } }] });

const W = 10, H = 5.625;
const NAVY = "0B1B3A", SLATE = "3A4A6B", PALE = "EEF2F8", BLUE = "2A78D6", ORANGE = "EB6834", AQUA = "1BAF7A", MUTED = "5B6A88";

function content(title, section, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
function card(s, x, y, w, h, head, body, accent, name) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: PALE }, line: { color: PALE }, rectRadius: 0.08, objectName: name + " card" });
  s.addText(head, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontFace: "Cambria", fontSize: 18, bold: true, color: accent, margin: 0, isTextBox: true, objectName: name + " head" });
  s.addText(body, { x: x + 0.2, y: y + 0.58, w: w - 0.4, h: h - 0.7, fontFace: "Calibri", fontSize: 14, color: NAVY, valign: "top", margin: 0, paraSpaceAfter: 5, isTextBox: true, objectName: name + " body" });
}
function bul(items) { return items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })); }

// ================= 1 title
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
s.addText("Monte Carlo Pricing and Delta Hedging of European Options under GBM", { x: 0.6, y: 1.0, w: 8.8, h: 1.7, fontFace: "Cambria", fontSize: 34, bold: true, color: "FFFFFF", margin: 0, valign: "top", isTextBox: true, objectName: "Title" });
s.addText("A numerical study of hedging errors and convergence", { x: 0.6, y: 2.8, w: 8.8, h: 0.5, fontFace: "Calibri", fontSize: 20, italic: true, color: "9CC3F5", margin: 0, isTextBox: true, objectName: "Subtitle" });
s.addText("MAC F244 – Stochastic Calculus and Applications to Finance\nSucheta Sarangi · Ayush Manocha · Kamal Kumar Manchenella · Anikait Rao · Arnav Paliwal", { x: 0.6, y: 4.2, w: 8.8, h: 0.8, fontFace: "Calibri", fontSize: 14, color: "CBD6EA", margin: 0, isTextBox: true, objectName: "Group" });
s.addNotes("Introduce the group and the project in one sentence: we study two different numerical errors for a European call under GBM – the statistical error of Monte Carlo pricing and the discretisation error of delta hedging – and we compare both with Black–Scholes theory.");

// ================= 2 two errors
pres.addSection({ title: "Problem and model" });
s = content("Two different numerical errors", "Problem and model",
 "Key message: pricing error is a property of the ESTIMATOR (N simulations); hedging error is a property of the STRATEGY (M rebalancing dates). More paths N does not reduce hedging error; it only measures it better. Mention the three research questions briefly.");
card(s, 0.5, 1.2, 4.35, 2.6, "Pricing error", bul(["Source: Monte Carlo uses N random samples","Shrinks as N → ∞, rate N^(-1/2)","Remedy: variance reduction (antithetic, control variate)","Measured by RMSE and 95% CI coverage"]), BLUE, "pricing");
card(s, 5.15, 1.2, 4.35, 2.6, "Hedging error", bul(["Source: hedge adjusted only at M dates","Shrinks as M → ∞, rate M^(-1/2)","Remedy: rebalance more often (costly in practice)","Measured by mean, sd, RMSE of HE"]), ORANGE, "hedging");
s.addText([{ text: "RQ1 ", options: { bold: true, color: BLUE } }, { text: "variance reduction vs strike; N^(-1/2) rate and CI coverage.   ", options: {} },
           { text: "RQ2 ", options: { bold: true, color: BLUE } }, { text: "does sd(HE) decay like M^(-1/2) and match the asymptotic formula?   ", options: {} },
           { text: "RQ3 ", options: { bold: true, color: BLUE } }, { text: "effect of moneyness, volatility and real-world drift.", options: {} }],
  { x: 0.5, y: 4.05, w: 9.0, h: 1.0, fontFace: "Calibri", fontSize: 14, color: NAVY, margin: 0, valign: "top", isTextBox: true, objectName: "Research questions" });

// ================= 3 model
s = content("Model: GBM, risk-neutral world, Black–Scholes", "Problem and model",
 "GBM: exact solution from Ito's formula on ln S; the -sigma^2/2 is the Ito correction. Because the solution is exact we simulate with NO Euler error. Girsanov: replacing mu by r gives the risk-neutral measure Q; the replicating portfolio never uses mu so the price cannot depend on it. Black-Scholes price is the benchmark; delta is the hedge ratio; gamma measures how fast delta changes and is the source of discrete hedging error.");
const eq = [
  ["Real world (P)", "dS = μS dt + σS dW      S_t = S₀ exp{(μ − ½σ²)t + σW_t}"],
  ["Risk-neutral (Q)", "S_T = S₀ exp{(r − ½σ²)T + σ√T Z},   Z ~ N(0,1)"],
  ["Price", "C₀ = e^(−rT) E_Q[(S_T − K)⁺] = S₀Φ(d₁) − Ke^(−rT)Φ(d₂)"],
  ["Greeks", "Δ = Φ(d₁)        Γ = φ(d₁) / (S σ √(T−t))"]];
eq.forEach((r, i) => {
  const y = 1.2 + i * 0.82;
  s.addShape(pres.ShapeType.roundRect, { x: 0.5, y, w: 5.9, h: 0.7, fill: { color: PALE }, line: { color: PALE }, rectRadius: 0.06, objectName: "eq card " + i });
  s.addText(r[0], { x: 0.65, y: y + 0.04, w: 5.6, h: 0.25, fontFace: "Calibri", fontSize: 11, bold: true, color: BLUE, margin: 0, isTextBox: true, objectName: "eq label " + i });
  s.addText(r[1], { x: 0.65, y: y + 0.28, w: 5.6, h: 0.35, fontFace: "Cambria", fontSize: 14, color: NAVY, margin: 0, isTextBox: true, objectName: "eq " + i });
});
card(s, 6.7, 1.2, 2.8, 3.2, "Why this way?", bul(["GBM: positive prices, exact solution","Q: option price cannot depend on μ","BS: exact benchmark for every number we simulate","Γ large near strike → hedging error"]), AQUA, "why");

// ================= 4 MC estimators
pres.addSection({ title: "Part A: pricing" });
s = content("Monte Carlo pricing and variance reduction", "Part A: pricing",
 "Plain MC: average of discounted payoffs; SE = s/sqrt(N); CLT gives the 95% interval. Antithetic: use Z and -Z; payoff is monotone so the pair is negatively correlated; compare at the same number N of payoff evaluations (N/2 pairs) and compute SE from pair averages. Control variate: X = e^{-rT} S_T has known mean S0; subtract beta*(X - S0); beta from an independent pilot of 1e5 so the estimator stays unbiased; variance multiplied by 1 - rho^2.");
card(s, 0.5, 1.2, 2.85, 2.9, "Plain MC", [{ text: "Ĉ = mean of Yᵢ", options: { breakLine: true, fontFace: "Cambria" } }, { text: "SE = s_Y / √N", options: { breakLine: true, fontFace: "Cambria" } }, { text: "95% CI: Ĉ ± 1.96·SE", options: { breakLine: true, fontFace: "Cambria" } }, { text: "Unbiased; RMSE ∝ N^(−1/2)", options: {} }], BLUE, "plain");
card(s, 3.575, 1.2, 2.85, 2.9, "Antithetic", [{ text: "Pair Y(Z) with Y(−Z)", options: { breakLine: true, fontFace: "Cambria" } }, { text: "Payoff increasing in Z → negative correlation ρ", options: { breakLine: true } }, { text: "Var = (1+ρ)Var(Y)/N, never worse", options: { breakLine: true } }, { text: "N/2 pairs = N payoffs", options: {} }], ORANGE, "anti");
card(s, 6.65, 1.2, 2.85, 2.9, "Control variate", [{ text: "X = e^(−rT)S_T, E[X] = S₀", options: { breakLine: true, fontFace: "Cambria" } }, { text: "Ĉ − β(X̄ − S₀)", options: { breakLine: true, fontFace: "Cambria" } }, { text: "β from independent pilot (10⁵)", options: { breakLine: true } }, { text: "Var × (1 − ρ²)", options: {} }], AQUA, "cv");

s.addText("Fair comparison: every method uses the same number N of payoff evaluations. Variance reduction lowers the constant, not the N^(−1/2) rate.", { x: 0.5, y: 4.3, w: 9.0, h: 0.7, fontFace: "Calibri", fontSize: 15, italic: true, color: SLATE, margin: 0, valign: "top", isTextBox: true, objectName: "Fair comparison note" });

// ================= 5 E1 convergence
s = content("E1: all three estimators converge at N^(−1/2)", "Part A: pricing",
 "Log-log RMSE vs N, R=400 replications per N. Slope about -0.5 for all nine curves. Antithetic and control curves are parallel but lower: variance reduction changes the constant, not the rate. One OLS CI (control, K=90, seed 1) just missed -0.5; with a second seed all slopes lie in [-0.501,-0.491] so we attribute it to sampling noise. Coverage pooled: plain 95.2%, antithetic 94.4%, control 94.8%.");
s.addImage({ path: "../figures/fig1_rmse_vs_N.png", x: 1.0, y: 1.1, w: 8.0, h: 8.0 * 488 / 1275, altText: "Log-log plot of RMSE against N for plain, antithetic and control-variate Monte Carlo at K=90,100,110; all have slope about minus one half", objectName: "Fig RMSE vs N" });
const st = [["−0.50 ± 0.01", "OLS slope, all 9 curves × 2 seeds"], ["94.4 – 95.2 %", "pooled 95% CI coverage"], ["Constant, not rate", "what variance reduction changes"]];
st.forEach((t, i) => {
  const x = 0.5 + i * 3.05;
  s.addText(t[0], { x, y: 4.35, w: 2.9, h: 0.5, fontFace: "Cambria", fontSize: 22, bold: true, color: BLUE, margin: 0, isTextBox: true, objectName: "stat " + i });
  s.addText(t[1], { x, y: 4.85, w: 2.9, h: 0.4, fontFace: "Calibri", fontSize: 12, color: MUTED, margin: 0, isTextBox: true, objectName: "stat label " + i });
});

// ================= 6 variance reduction chart
s = content("Variance reduction depends on the strike", "Part A: pricing",
 "Variance ratio = plain variance / method variance for the same number of payoff evaluations, from 5 million samples. Control variate: 17.2, 6.9, 3.6; antithetic 4.0, 2.0, 1.4 for K=90,100,110. In the money the payoff is almost linear in S_T so the stock is an excellent control and the mirror payoffs are strongly negatively correlated; out of the money most payoffs are zero. CPU time relative to plain: antithetic 0.57/0.48/0.53, control 1.48/1.42/1.23 (timings are noisy, about +-20%). Cost-adjusted: antithetic 6.9/4.2/2.6, control 11.6/4.8/2.9. NOTE: an earlier version had a timing bug in the antithetic code and claimed control wins at all strikes; after the fix control wins clearly at K=90, narrowly at 100 and ties at 110.");
s.addChart(pres.charts.BAR, [
  { name: "Antithetic", labels: ["K = 90 (ITM)", "K = 100 (ATM)", "K = 110 (OTM)"], values: [3.95, 2.00, 1.37] },
  { name: "Control variate", labels: ["K = 90 (ITM)", "K = 100 (ATM)", "K = 110 (OTM)"], values: [17.25, 6.88, 3.61] }],
  { x: 0.5, y: 1.15, w: 5.6, h: 3.9, barDir: "col", barGrouping: "clustered", chartColors: [ORANGE, AQUA], showTitle: true, title: "Variance reduction ratio vs plain MC", titleFontSize: 14, titleColor: NAVY, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 11, dataLabelColor: NAVY, dataLabelFontFace: "+mn-lt",
    showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: NAVY, legendFontFace: "+mn-lt",
    catAxisLabelColor: NAVY, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt", valAxisLabelColor: MUTED, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: "D9DFEA", size: 0.5 }, catGridLine: { style: "none" }, valAxisMinVal: 0, barGapWidthPct: 60 });
card(s, 6.4, 1.2, 3.1, 3.85, "Reading the chart", bul(["In the money: payoff ≈ S_T − K, so the stock is a near-perfect control","Out of the money: most payoffs are 0, little to exploit","After CPU cost (control vs antithetic): 11.6 / 4.8 / 2.9 vs 6.9 / 4.2 / 2.6 – control wins at K=90, narrowly at 100, tie at 110"]), BLUE, "reading");

// ================= 6b why control beats antithetic
s = content("Why control beats antithetic", "Part A: pricing",
 "Top row: payoff against the stock price. Bottom row: Y(Z) against Y(-Z). Antithetic gain is 1/(1+rho_a) with rho_a = -0.75, -0.50, -0.27; control gain is 1/(1-rho^2) with rho = 0.97, 0.92, 0.85. The call payoff is flat at zero for low stock prices, so the mirror of a high payoff is zero, not a large negative value. The fraction of zero payoffs is 25, 44 and 63 percent for K=90, 100, 110, so both tricks help less as K rises.");
s.addImage({ path: "../figures/fig8_payoff_scatter.png", x: 0.5, y: 1.15, w: 5.9, h: 5.9 / 1.864, altText: "Payoff against stock price and Y(Z) against Y(-Z) for three strikes", objectName: "Payoff scatter" });
card(s, 6.6, 1.2, 2.9, 3.85, "What the numbers say", bul(["Antithetic: 1/(1+ρ) with ρ = −0.75, −0.50, −0.27","Control: 1/(1−ρ²) with ρ = 0.97, 0.92, 0.85","Zero payoffs: 25 / 44 / 63 %","Mirror of a high payoff is just 0, not very negative"]), BLUE, "why1");

// ================= 7 hedging
pres.addSection({ title: "Part B: hedging" });
s = content("Delta hedging and where the error comes from", "Part B: hedging",
 "Self-financing recursion; HE is discounted so that it is in time-0 money. NOTE: the proposal's definition mixed discounted and undiscounted amounts; we corrected it. Pathwise identity: HE = sum of integrals of (delta_k - Delta(t,S_t)) against d(S tilde). If we rebalanced continuously the bracket would vanish. Under Q the integral has mean exactly zero. Between dates delta changes by Gamma times the stock move; each step gives error -1/2 e^{-r t_k} Gamma S^2 sigma^2 dt (Z^2 - 1), mean zero, size proportional to dt, uncorrelated, so variance is a*dt and sd is proportional to M^{-1/2}. The histogram shows the distribution: centred, mildly left-skewed, narrowing with M.");
s.addText([{ text: "V₍ₖ₊₁₎ = δₖ S₍ₖ₊₁₎ + (Vₖ − δₖ Sₖ) e^(rΔt),   δₖ = Φ(d₁(tₖ, Sₖ))", options: { breakLine: true } },
           { text: "HE_M = e^(−rT) (V_M − (S_T − K)⁺) = Σ ∫ (δₖ − Δ(t,S_t)) dS̃_t", options: { breakLine: true } },
           { text: "Var(HE_M) ≈ a·Δt,   a = (σ⁴/2) ∫₀ᵀ e^(−2rt) E[(S²Γ)²] dt", options: {} }],
  { x: 0.5, y: 1.15, w: 9.0, h: 1.05, fontFace: "Cambria", fontSize: 14, color: NAVY, margin: 0.1, paraSpaceAfter: 6, valign: "middle", fill: { color: PALE }, isTextBox: true, objectName: "Hedging equations" });
s.addImage({ path: "../figures/fig3_histograms.png", x: 0.5, y: 2.4, w: 6.3, h: 6.3 / 2.644, altText: "Histograms of hedging error for M=12, 52 and 252 rebalancing dates, narrowing as M grows", objectName: "Fig histograms" });
s.addText(bul(["Hedge wrong by Γ × stock move between dates", "Per-step error: mean 0, size ∝ Δt, uncorrelated", "M steps ⇒ sd ∝ √M · (1/M) = M^(−1/2)", "Continuous trading ⇒ HE = 0"]),
  { x: 7.0, y: 2.4, w: 2.5, h: 2.6, fontFace: "Calibri", fontSize: 14, color: NAVY, margin: 0, valign: "top", paraSpaceAfter: 6, isTextBox: true, objectName: "Hedging bullets" });
s.addText("Histograms: K = 100, μ = r, 10⁵ paths", { x: 0.5, y: 4.85, w: 6.3, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true, objectName: "Hist caption" });

// ================= 8 E2/E4
s = content("E2/E4: sd ∝ M^(−1/2), theory fits", "Part B: hedging",
 "(a) simulated sd versus formula (12) evaluated as an exact sum over the rebalancing dates, and the leading term sqrt(a dt). (b) simulated sd divided by the leading term approaches 1 from below. (c) Var/dt against sqrt(dt) is a straight line a + b sqrt(dt); intercept = a. HONEST RESULT: the pre-specified criterion (bootstrap CI of the slope on M>=52 contains -1/2) is NOT met: slope -0.491, CI [-0.495,-0.488] for K=100, because of the dt^{3/2} correction (b about -14). Fitted a = 44.4 [44.0,44.7] versus theory 44.6 for K=100; matches for K=90, for K=110 theory is 1.3% above the fit. The exact discrete sum is within 0.1-2.5% for M>=126.");
s.addImage({ path: "../figures/fig6_theory_vs_sim.png", x: 1.0, y: 1.1, w: 8.0, h: 8.0 * 493 / 1300, altText: "Three panels: simulated hedging-error sd against theory, ratio to leading term, and variance over dt against sqrt dt", objectName: "Fig theory vs simulation" });
const st2 = [["−0.49", "slope of sd vs M (M ≥ 52); CI [−0.495, −0.488]"], ["44.4 vs 44.6", "fitted vs theoretical a (K = 100)"], ["1–2 %", "formula (12) accuracy for M ≥ 126"]];
st2.forEach((t, i) => {
  const x = 0.5 + i * 3.05;
  s.addText(t[0], { x, y: 4.35, w: 2.9, h: 0.5, fontFace: "Cambria", fontSize: 22, bold: true, color: ORANGE, margin: 0, isTextBox: true, objectName: "stat2 " + i });
  s.addText(t[1], { x, y: 4.85, w: 2.9, h: 0.45, fontFace: "Calibri", fontSize: 12, color: MUTED, margin: 0, isTextBox: true, objectName: "stat2 label " + i });
});

// ================= 9 E3 sensitivity
s = content("E3: strike, volatility and drift", "Part B: hedging",
 "(a) Relative to the premium, error is largest out of the money: RMSE/C0 at M=52 is 4.2%, 8.6%, 15.9% for K=90,100,110. In absolute terms sd is largest for K=110, not at-the-money as the proposal expected: formula (12) peaks near K=110 because the stock is most likely to be near the strike late in the option's life, which for r>0 is above S0. (b) sd is almost proportional to sigma because S^2 Gamma is proportional to 1/sigma. (c) Under mu=0.15 the stock drifts toward/away from the strike; sd changes by x0.85 (K=90), x0.95 (K=100), x1.03 (K=110); formula (12) with E_P predicts these within 1-6%.");
s.addImage({ path: "../figures/fig4_sensitivity.png", x: 1.1, y: 1.1, w: 7.8, h: 7.8 * 488 / 1272, altText: "Three panels: relative hedging error by strike, hedging sd by volatility, and sd ratio under real-world drift", objectName: "Fig sensitivity" });
s.addText(bul(["Relative error largest out of the money; absolute sd largest near K ≈ 110 (not at S₀) – differs from the proposal's expectation", "sd ∝ σ (S²Γ ∝ 1/σ)", "Drift 0.15 changes sd by ×0.85 / ×0.95 / ×1.03; formula (12) under P predicts it within 1–6%"]),
  { x: 0.5, y: 4.2, w: 9.0, h: 1.0, fontFace: "Calibri", fontSize: 14, color: NAVY, margin: 0, valign: "top", paraSpaceAfter: 3, isTextBox: true, objectName: "E3 bullets" });

// ================= 10 drift mean
s = content("Real-world drift: mean error is O(Δt)", "Part B: hedging",
 "Under Q the mean of HE is zero for every M: tested in 63 configurations, largest |z| = 2.62, below the Bonferroni limit 3.35. Under mu=0.15 the mean is negative and shrinks with M; M times mean is roughly constant (about -1.2 for sigma=0.1) so the mean is O(dt), vanishing faster than the sd which is O(sqrt dt). At M=252 the mean is about 1% of the sd. We only tested the order, not an exact constant.");
s.addImage({ path: "../figures/fig5_drift_mean.png", x: 0.5, y: 1.15, w: 6.0, h: 6.0 * 488 / 1055, altText: "Mean hedging error versus M under mu=r and mu=0.15, and M times mean being roughly constant", objectName: "Fig drift mean" });
card(s, 6.75, 1.2, 2.75, 3.4, "Findings", bul(["Under Q: mean ≈ 0 in all 63 configs (max |z| = 2.62 < 3.35)", "Under μ = 0.15: mean < 0, M × mean ≈ constant", "Mean ≈ 1% of sd at M = 252"]), AQUA, "drift");

// ================= 11 why peak and slope
s = content("Two puzzles: the K = 110 peak, the slope", "Part B: hedging",
 "Left: sqrt(a) rises with K to a peak near K = 110; dividing by K moves the peak to about 104, near the forward price 105.1, because dollar gamma S^2*Gamma carries an S^2 factor. Right: local slopes between neighbouring M. Theory is Var = a dt + b dt^1.5 with b < 0 (fitted -10.6, -14.2, -14.6), so the local slope starts near -0.45 and approaches -0.49 at the largest M: the rate -1/2 holds asymptotically but our strict criterion (bootstrap interval containing -0.5) was not met over M >= 52. We report this honestly. Theory slope over M >= 52 is -0.487 for K = 100.");
s.addImage({ path: "../figures/fig7_strike_and_local_slopes.png", x: 1.3, y: 1.1, w: 7.4, h: 7.4 / 2.488, altText: "sqrt(a) against strike, sqrt(a)/K, and local slopes against M", objectName: "Strike and local slopes" });
s.addText(bul(["Peak of √a at K = 110; per unit of strike it is at K ≈ 104, near the forward price 105.1 (dollar gamma has an S² factor)","Variance ≈ aΔt + bΔt^1.5, b < 0: local slope runs from −0.449 to −0.491, approaching −0.5 from above","Strict slope criterion not met (−0.491, CI [−0.495, −0.488]); theory on the same range gives −0.487"]), { x: 0.6, y: 4.2, w: 8.8, h: 1.3, fontFace: "Calibri", fontSize: 14, color: NAVY, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true, objectName: "Puzzle bullets" });

// ================= 11b E5/E6: wrong volatility and real data
pres.addSection({ title: "Part B: extensions" });
s = content("E5/E6: wrong volatility, and real S&P 500 data", "Part B: hedging",
 "Two experiments added after the first version, extending Part B beyond GBM with the correct sigma. E5: hedge with sigma-hat != true sigma = 0.2; the mean error no longer vanishes as M grows, it equals the premium mispricing C_BS(sigma-hat) - C_BS(sigma), while the sd still falls like M^(-1/2). Simulation matches theory to within 0.1% at M=252. E6: sell and delta-hedge a one-year at-the-money call on every one of 2002 overlapping windows of S&P 500 daily closes since Nov 2016. Using the volatility realised in the window, daily hedging sd is 9.0% of the premium (GBM simulation at the same vol: 4.5%) -- real markets have extra sd from volatility changes and jumps that discretisation theory does not capture. Using only the trailing one-year volatility (the honest, no-hindsight case) sd jumps to 53.6% and the mean hedging error is -25.5% of the premium: this is E5's wrong-volatility bias showing up live, because realised vol departs from last year's trailing estimate (vol ranged 7-35% over the sample).");
s.addImage({ path: "../figures/fig9_wrong_vol_and_real_data.png", x: 0.5, y: 1.1, w: 9.0, h: 9.0 * 300 / 1150, altText: "Panel a: mean hedging error against hedging volatility with theory overlaid. Panel b: histograms of hedging error over S&P 500 windows, daily vs weekly. Panel c: daily-hedge error by start date, trailing vs realised volatility", objectName: "Fig wrong vol and real data" });
s.addText(bul(["E5: hedging with the wrong vol adds a bias that does NOT shrink with M -- it equals the premium mispricing (sim 3.78 vs theory 3.78 for sigma-hat=0.3; sim -3.65 vs theory -3.65 for sigma-hat=0.1)", "E6 (2002 S&P 500 windows since Nov 2016): with realised vol, daily sd = 9.0% of C0 (GBM: 4.5%) -- real markets add extra risk beyond discretisation", "E6 with only trailing (honest) vol: sd = 53.6%, mean = -25.5% of C0 -- E5's bias at work when the hedger does not know the vol in advance"]),
  { x: 0.5, y: 4.15, w: 9.0, h: 1.3, fontFace: "Calibri", fontSize: 13.5, color: NAVY, valign: "top", margin: 0, paraSpaceAfter: 3, isTextBox: true, objectName: "E5E6 bullets" });

pres.addSection({ title: "Wrap-up" });
s = content("Pricing error vs hedging error", "Wrap-up",
 "This is the central distinction. Use the table to answer 'why doesn't increasing N reduce the hedging error?'. Pricing error belongs to the estimator; hedging error belongs to the strategy. If you hedge starting from the MC price instead of the exact price, you simply add the constant offset (C-hat minus C0) to every HE.");
const hdr = { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontFace: "Calibri", fontSize: 13 };
const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontFace: "Calibri", fontSize: 13, color: NAVY, fill: { color: o.first ? "EEF2F8" : "FFFFFF" } }, o) });
s.addTable([
  [{ text: "", options: hdr }, { text: "Monte Carlo pricing error", options: hdr }, { text: "Discrete hedging error", options: hdr }],
  [cell("Source", { bold: true, first: true }), cell("Finite sample of N paths"), cell("Hedge adjusted at only M dates")],
  [cell("Property of", { bold: true, first: true }), cell("the estimator"), cell("the strategy")],
  [cell("Shrinks when", { bold: true, first: true }), cell("N → ∞"), cell("M → ∞ (not with N)")],
  [cell("Rate (observed)", { bold: true, first: true }), cell("N^(−1/2); slope −0.50 ± 0.01"), cell("M^(−1/2) asymptotically (slope −0.49)")],
  [cell("Reduced by", { bold: true, first: true }), cell("Antithetic / control variates (3.6–17×)"), cell("More rebalancing (4× trades halves sd)")],
  [cell("Mean", { bold: true, first: true }), cell("0 (unbiased)"), cell("0 under Q; O(Δt) under μ ≠ r")]],
  { x: 0.5, y: 1.2, w: 9.0, colW: [1.9, 3.5, 3.6], rowH: 0.52, border: { type: "solid", pt: 0.75, color: "C9D3E6" }, valign: "middle", margin: [0, 0.1, 0, 0.1], objectName: "Comparison table" });

// ================= 12 deviations
s = content("What did not match, and what we simplified", "Wrap-up",
 "Be upfront about these in the viva: they show we understand the results. 1) Strict slope criterion not met because of the dt^{3/2} correction. 2) a for K=110 slightly outside CI. 3) Maximum absolute sd near K=110 rather than at-the-money. 4) The proposal's HE definition mixed discounting; corrected. Simplifications: R=400 instead of 1000; bootstrap resamples paths only. E5 (wrong volatility) and E6 (real S&P 500 data) were added later and are now both in the report and this deck (previous slide).");
card(s, 0.5, 1.2, 4.35, 3.7, "Differences from the proposal", bul(["Slope criterion (M ≥ 52) strictly not met: −0.49, not −0.50", "K = 110: fitted a vs theory off by about 1.3%", "Largest absolute sd near K ≈ 110, not at-the-money", "HE definition corrected: discount the payoff too"]), ORANGE, "differences");
card(s, 5.15, 1.2, 4.35, 3.7, "Simplifications", bul(["R = 400 replications (not 1000); second seed as noise check", "Bootstrap resamples paths only, not individual time steps", "Analytic premium and Δ in the hedge to isolate rebalancing error", "E5/E6 added after the first version (added, not skipped) -- see previous slide"]), BLUE, "simplify");

// ================= 13 conclusion
pres.addSection({ title: "Close" });
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Close" });
s.addText("Conclusions", { x: 0.6, y: 0.5, w: 8.8, h: 0.8, fontFace: "Cambria", fontSize: 34, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, objectName: "Conclusion title" });
s.addText(bul(["Monte Carlo pricing error ∝ N^(−1/2); the control variate cut variance 3.6–17×, most in the money", "Hedging error ∝ M^(−1/2) asymptotically and is untouched by N; formula (12) is accurate to 1–2% for M ≥ 126", "Strike, volatility and drift change the error in ways formula (12) explains (also under real-world drift)", "A wrong hedging volatility adds a bias that more trading cannot remove; on real S&P 500 data this effect dominates", "Limitations: constant σ and r, no transaction costs, single call, heuristic asymptotics"]),
  { x: 0.6, y: 1.5, w: 8.8, h: 3.2, fontFace: "Calibri", fontSize: 17, color: "E4ECF8", margin: 0, valign: "top", paraSpaceAfter: 9, isTextBox: true, objectName: "Conclusion bullets" });
s.addText("Next: transaction costs · stochastic volatility · other payoffs (put, digital)", { x: 0.6, y: 4.6, w: 8.8, h: 0.4, fontFace: "Calibri", fontSize: 14, italic: true, color: "9CC3F5", margin: 0, isTextBox: true, objectName: "Next steps" });
s.addNotes("Close with the one-sentence takeaway: two different errors, two different convergence rates, and the theory predicts the hedging error well once finite-M corrections are included. Then take questions.");

(async () => {
  await pres.writeFile({ fileName: "MAC_F244_Project_Presentation.pptx" });
  await applyTheme("MAC_F244_Project_Presentation.pptx", THEME);
  console.log("deck written");
})();
