"""Consistency check across numerical results, report, guide and slides.
Run from the project root:  python code/consistency_check.py
1. Every results CSV equals the snapshot in results_prev/ (except CPU-time columns).
2. Key numbers from numbers.tex appear in the report PDF text, guide PDF text.
3. Key numbers appear in the deck text (via the pptx XML).
Prints PASS/FAIL per check; exit status 1 if anything fails."""
import glob, os, re, shutil, subprocess, sys, zipfile
import numpy as np, pandas as pd

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))      # always work from the project root
for tool in ("pdftotext", "pdfinfo"):
    if not shutil.which(tool):
        sys.exit(f"{tool} not found (install poppler-utils)")

fails = 0
def report(ok, msg):
    global fails
    print(("PASS  " if ok else "FAIL  ") + msg)
    fails += (not ok)

# 1. results vs previous snapshot (timing columns are allowed to differ)
TIMING = ("time", "cpu", "cost", "tr_", "ratio_time", "cost_adj")
report(os.path.isdir("results_prev"), "results_prev/ snapshot exists (create it with: cp -r results results_prev, after a trusted run)")
for f in sorted(glob.glob("results/*.csv")):
    g = f.replace("results/", "results_prev/")
    if not os.path.exists(g):
        continue
    a, b = pd.read_csv(f), pd.read_csv(g)
    cols = [c for c in a.columns if c in b.columns and not any(t in c.lower() for t in TIMING)]
    same = a.shape[0] == b.shape[0]
    for c in cols:
        if pd.api.types.is_numeric_dtype(a[c]):
            same &= bool(np.allclose(a[c], b[c], rtol=1e-9, atol=1e-12, equal_nan=True))
        else:
            same &= bool((a[c] == b[c]).all())
    report(same, f"{os.path.basename(f)} identical to previous run (non-timing columns)")

def has_number(v, text):
    """True if v occurs as a whole number in text (so that '3.6' does not match inside '13.60')."""
    return re.search(rf"(?<![\d.]){re.escape(v)}(?!\d)", text) is not None

def pdftext(p):
    return subprocess.run(["pdftotext", p, "-"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.replace("\u2212", "-")

mac = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", open("report/numbers.tex").read()))
KEYS = ["vrCvA", "vrCvB", "vrCvC", "vrAntA", "vrAntB", "vrAntC", "caCvA", "caCvB", "caCvC", "caAntA", "caAntB", "caAntC",
        "slopeHiB", "thSlopeHiB", "aThB", "sdFiftyTwoB", "sdFiveOhFourB", "rhoCtlA", "peakK", "fwd"]
rep_t, gui_t = pdftext("report/report.pdf"), pdftext("docs/guide.pdf")
deck = ""
DECK = next(p for p in ("slides/slides.pptx", "slides/MAC_F244_Project_Presentation.pptx") if os.path.exists(p))
with zipfile.ZipFile(DECK) as z:
    for n in z.namelist():
        if n.startswith("ppt/slides/slide") or n.startswith("ppt/notesSlides/notesSlide"):
            deck += re.sub(r"<[^>]+>", " ", z.read(n).decode("utf8")) + " "
deck = deck.replace("\u2212", "-")

for k in KEYS:
    v = mac[k]
    report(has_number(v, rep_t), f"report contains {k} = {v}")
    report(has_number(v, gui_t), f"guide  contains {k} = {v}")
# deck holds figures as typed text; check the ones typed there (K-wise numbers are written as lists)
for v in ["17.2", "6.9", "3.6", "11.6", "4.8", "2.9", "-0.491", "44.4", "44.6", "105.1", "-0.487"]:
    report(has_number(v, deck), f"deck   contains {v}")
report("formula (9)" not in deck, "deck no longer uses old 'formula (9)' numbering")
npages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", "report/report.pdf"], capture_output=True, text=True,
                                                          encoding="utf-8", errors="replace").stdout).group(1))
report(npages <= 4, f"report has {npages} pages (limit 4)")
sys.exit(1 if fails else 0)
