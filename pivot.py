#!/usr/bin/env python3
"""
TD 1 - Tableau croisé modèles × questions pour la plénière.

Lit UNIQUEMENT model-question-comparison-en.csv (une ligne finale par couple
modèle × question) et écrit la même vue en Markdown (pivot-td1.md) et en HTML
simple (pivot-td1.html) : un symbole par cellule, le total par modèle, une légende.

Usage (à la racine du kit) :
    python3 pivot.py
    python3 pivot.py --csv autre.csv --md autre.md --html autre.html

Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import csv
import html
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SYMBOLS = {
    "correct": "✓",
    "incorrect": "✗",
    "sql_invalid": "!",
    "sql_rejected": "!",
    "access_error": "A",
    "not_executed": "–",
}
UNKNOWN = "?"
TO_CHECK = "*"           # explanation commençant par « À vérifier »

LEGEND = [
    ("✓", "correct : la valeur exécutée est égale à la référence"),
    ("✗", "incorrect : le SQL s'exécute mais la valeur diffère de la référence (mauvaise réponse)"),
    ("!", "SQL invalide (erreur SQLite) ou rejeté par le bac à sable : pas de valeur"),
    ("A", "accès refusé (HTTP 400-404 ou 429) : ce n'est pas une mauvaise réponse, le modèle n'a pas été évalué"),
    ("–", "non exécuté (délai, erreur temporaire, cellule inachevée) : pas évalué non plus"),
    (TO_CHECK, "verdict à vérifier (voir la colonne explanation du CSV)"),
]
COUNTS = [("✓", "correct"), ("✗", "incorrect"), ("!", "SQL inv./rejeté"), ("A", "accès refusé"), ("–", "non exécuté")]


def load(path: Path) -> tuple[list, list, dict]:
    """Renvoie (modèles, questions, {(modèle, question): ligne}) dans l'ordre d'apparition."""
    models, cases, cells = [], [], {}
    with open(path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["model_id"] not in models:
                models.append(row["model_id"])
            if row["case_id"] not in cases:
                cases.append(row["case_id"])
            cells[(row["model_id"], row["case_id"])] = row
    return models, sorted(cases), cells


def symbol(row: dict | None) -> str:
    if row is None:
        return ""
    mark = SYMBOLS.get(row["status"], UNKNOWN)
    if row["explanation"].lower().startswith("à vérifier"):
        mark += TO_CHECK
    return mark


def totals(model: str, cases: list, cells: dict) -> dict:
    marks = [symbol(cells.get((model, case))).rstrip(TO_CHECK) for case in cases]
    out = {s: marks.count(s) for s, _ in COUNTS}
    out["evaluated"] = out["✓"] + out["✗"] + out["!"]         # accès refusé et non exécuté exclus
    return out


def score(t: dict, n_cases: int) -> str:
    text = f"{t['✓']}/{n_cases}"
    if t["evaluated"] != n_cases:
        text += f" ({t['✓']}/{t['evaluated']} évalués)"
    return text


def to_markdown(models: list, cases: list, cells: dict, source: str) -> str:
    head = ["Modèle"] + cases + ["Correct"] + [label for _, label in COUNTS[1:]]
    lines = ["# TD 1 — résultats modèles × questions", "",
             f"Source : `{source}` (dernière tentative de chaque cellule).", "",
             "| " + " | ".join(head) + " |",
             "|" + "|".join([":---"] + [":-:"] * len(cases) + ["--:"] * len(COUNTS)) + "|"]
    for model in models:
        t = totals(model, cases, cells)
        row = [f"`{model}`"] + [symbol(cells.get((model, c))) for c in cases]
        row += [f"**{score(t, len(cases))}**"] + [str(t[s]) for s, _ in COUNTS[1:]]
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "## Légende", ""] + ["- **" + s.replace("*", "\\*") + f"** {text}" for s, text in LEGEND]
    lines += ["", "« Correct » compte les ✓ sur toutes les questions ; quand des cellules n'ont pas été évaluées "
                  "(A ou –), le score sur les seules cellules évaluées est donné entre parenthèses."]
    return "\n".join(lines) + "\n"


CSS = """
body { font-family: system-ui, sans-serif; margin: 2rem; background: #fff; color: #1d1d1f; }
h1 { font-size: 1.4rem; }
table { border-collapse: collapse; font-size: 1rem; }
th, td { border: 1px solid #d0d0d5; padding: .35rem .5rem; text-align: center; }
th { background: #f2f2f5; }
td.model { text-align: left; font-family: ui-monospace, monospace; white-space: nowrap; }
td.total { font-weight: 600; text-align: right; }
td.num { text-align: right; color: #555; }
.ok { background: #e3f4e5; color: #136f2a; }
.ko { background: #fbe3e1; color: #a1170c; font-weight: 700; }
.sql { background: #fff1d6; color: #8a5300; font-weight: 700; }
.acc { background: #e2ecfb; color: #1b4f9c; font-weight: 700; }
.nx { background: #eeeeef; color: #666; }
ul { line-height: 1.6; }
"""
CLASSES = {"✓": "ok", "✗": "ko", "!": "sql", "A": "acc", "–": "nx"}


def to_html(models: list, cases: list, cells: dict, source: str) -> str:
    esc = html.escape
    head = "".join(f"<th>{esc(c)}</th>" for c in cases)
    head += "<th>Correct</th>" + "".join(f"<th>{esc(label)}</th>" for _, label in COUNTS[1:])
    body = []
    for model in models:
        t = totals(model, cases, cells)
        tds = [f'<td class="model">{esc(model)}</td>']
        for case in cases:
            row = cells.get((model, case))
            mark = symbol(row)
            title = f' title="{esc(row["status"] + " — " + row["explanation"])}"' if row else ""
            tds.append(f'<td class="{CLASSES.get(mark.rstrip(TO_CHECK), "")}"{title}>{esc(mark)}</td>')
        tds.append(f'<td class="total">{esc(score(t, len(cases)))}</td>')
        tds += [f'<td class="num">{t[s]}</td>' for s, _ in COUNTS[1:]]
        body.append("<tr>" + "".join(tds) + "</tr>")
    legend = "".join(f'<li><span class="{CLASSES.get(s, "")}">&nbsp;{esc(s)}&nbsp;</span> {esc(text)}</li>' for s, text in LEGEND)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TD 1 modèles × questions</title>
<style>{CSS}</style>
</head>
<body>
<h1>TD 1 — résultats modèles × questions</h1>
<p>Source : <code>{esc(source)}</code> (dernière tentative de chaque cellule). Survoler une cellule affiche l'explication.</p>
<table>
<thead><tr><th>Modèle</th>{head}</tr></thead>
<tbody>
{chr(10).join(body)}
</tbody>
</table>
<h2>Légende</h2>
<ul>{legend}</ul>
<p>« Correct » compte les ✓ sur toutes les questions ; quand des cellules n'ont pas été évaluées (A ou –),
le score sur les seules cellules évaluées est donné entre parenthèses.</p>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--csv", type=Path, default=HERE / "model-question-comparison-en.csv")
    parser.add_argument("--md", type=Path, default=HERE / "pivot-td1.md")
    parser.add_argument("--html", type=Path, default=HERE / "pivot-td1.html")
    args = parser.parse_args()

    models, cases, cells = load(args.csv)
    if not cells:
        print(f"Aucune ligne dans {args.csv}.", file=sys.stderr)
        return 1
    unknown = sorted({row["status"] for row in cells.values()} - set(SYMBOLS))
    if unknown:
        print(f"Statuts inconnus, affichés « {UNKNOWN} » : {', '.join(unknown)}", file=sys.stderr)

    args.md.write_text(to_markdown(models, cases, cells, args.csv.name), encoding="utf-8")
    args.html.write_text(to_html(models, cases, cells, args.csv.name), encoding="utf-8")
    print(args.md.read_text(encoding="utf-8"))
    print(f"Écrit : {args.md.name}, {args.html.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
