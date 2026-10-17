"""
Read the repository's own result files (results_*.txt) into plain data for the Method page.

The page never holds typed-in numbers: it shows what the evaluation scripts printed, so the page and the code
cannot drift apart. If a file is missing, that part is simply absent and the page says so.

    results_model.txt, results_model_h1.txt, results_model_h5.txt   calibration of the 80% range (model.py --evaluate)
    results_robust.txt                                              does Dambulla add skill? (robust_check.py)
    results_decision.txt                                            rupee backtest (decision_backtest.py)
"""
import re
from pathlib import Path

CAL_FILES = {1: "results_model_h1.txt", 3: "results_model.txt", 5: "results_model_h5.txt"}
SERIES_RE = r"(wholesale|retail)\s+(Pettah|Narahenpita)"


def _read(root, name):
    p = Path(root) / name
    return p.read_text(encoding="utf-8") if p.exists() else None


def calibration(root):
    out = []
    for h, name in CAL_FILES.items():
        text = _read(root, name)
        if not text:
            continue
        for line in text.splitlines():
            m = re.match(rf"^{SERIES_RE}\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%\s+(.*)$", line)
            if m:
                out.append(dict(series=f"{m.group(1)} {m.group(2)}", h=h, tests=int(m.group(3)),
                                inside=float(m.group(4)), half_width=float(m.group(5)),
                                by_year={y: int(v) for y, v in re.findall(r"(\d{4}):(\d+)%", m.group(6))}))
    return out


def gain(root):
    text = _read(root, "results_robust.txt")
    out = []
    pat = re.compile(rf"^{SERIES_RE}\s+(\d)\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+([+-][\d.]+)\s+"
                     r"\[([+-][\d.]+),([+-][\d.]+)\]\s+([+-][\d.]+)\s+(.*?)\s+(\d+)/(\d+)\s+(.*?)\s+\(gap coef ([+-][\d.]+)\)")
    for line in (text or "").splitlines():
        m = pat.match(line)
        if m:
            g = m.groups()
            out.append(dict(series=f"{g[0]} {g[1]}", h=int(g[2]), tests=int(g[3]), skill_c=float(g[5]), skill_d=float(g[6]),
                            gain=float(g[7]), lo=float(g[8]), hi=float(g[9]), placebo=float(g[10]),
                            by_year={y: float(v) for y, v in re.findall(r"(\d{4}):([+-][\d.]+)", g[11])},
                            items_positive=int(g[12]), items=int(g[13]), verdict=g[14].strip(), gap_coef=float(g[15])))
    return out


def decision(root):
    text = _read(root, "results_decision.txt")
    out = []
    if not text:
        return out
    blocks = re.split(r"(?m)^=== ", text)[1:]
    pct = lambda s: float(s.rstrip("%"))
    for b in blocks:
        head = re.match(rf"{SERIES_RE}\s+horizon (\d) report days\s+(\d+) decisions", b)
        if not head:
            continue
        r = dict(series=f"{head.group(1)} {head.group(2)}", h=int(head.group(3)), decisions=int(head.group(4)))
        d_rows, c_rows = [], []
        for line in b.splitlines():
            m = re.match(r"always wait\s+-\s+([+-]?[\d.]+%)", line)
            if m:
                r["wait_pct"] = pct(m.group(1))
            m = re.match(r"hindsight best\s+-\s+([+-]?[\d.]+%)\s+([+-]?[\d.]+)", line)
            if m:
                r["hindsight_pct"], r["hindsight_rs"] = pct(m.group(1)), float(m.group(2))
            m = re.match(r"follow model ([CD]) \([^)]*\)\s+(?:\d+% acted|all calls)\s+([+-]?[\d.]+%)\s+([+-]?[\d.]+)\s+(\d+)%", line)
            if m:
                row = dict(pct=pct(m.group(2)), rs=float(m.group(3)), hit=int(m.group(4)))
                (d_rows if m.group(1) == "D" else c_rows).append(row)
            m = re.match(r"\s*Dambulla vs own-history model, all calls\s*:\s*([+-]?[\d.]+) pts of purchase value \[([+-]?[\d.]+), ([+-]?[\d.]+)\]", line)
            if m:
                r["d_vs_c_pts"], r["d_vs_c_lo"], r["d_vs_c_hi"] = (float(x) for x in m.groups())
        if len(d_rows) == 3 and len(c_rows) == 3:      # strongest 25%, strongest 50%, all calls
            r["d_top25"], r["d_all"], r["c_all"] = d_rows[0], d_rows[2], c_rows[2]
            out.append(r)
    return out


def build(root):
    files = [n for n in list(CAL_FILES.values()) + ["results_robust.txt", "results_decision.txt"] if (Path(root) / n).exists()]
    return dict(calibration=calibration(root), gain=gain(root), decision=decision(root), sources=files)
