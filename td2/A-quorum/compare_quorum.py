#!/usr/bin/env python3
"""TD 2, étape 1 : comparaison panel 2-sur-3 / quorum 3-sur-5 sur les traces du TD 1.

On réutilise tel quel `proposals_for` d'atelier-vote.py (dernière tentative par
membre, une erreur reste dans n sans voter) et notre `vote_k_sur_n` du squelette.
La référence n'est lue qu'APRÈS la décision, pour la colonne de comparaison.
Aucun appel réseau.

    python3 td2/A-quorum/compare_quorum.py            # tableau markdown sur stdout
    python3 td2/A-quorum/compare_quorum.py --csv out.csv
"""
import argparse
import csv
import importlib.util
import sys
from pathlib import Path

TD1 = Path(__file__).resolve().parents[2] / "td1"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, TD1 / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


atelier = load("atelier_vote", "atelier-vote.py")
vote = atelier.load_vote()

PANEL_3 = list(atelier.PANEL)  # gpt-oss-120b, north-mini-code, qwen3.8-27b
QUORUM_5 = PANEL_3 + [
    ("groq", "openai/gpt-oss-20b"),
    ("openrouter", "dots-studio/dots-3-note-preview:free"),
]
SHORT = {
    "openai/gpt-oss-120b": "120b", "cohere/north-mini-code:free": "cohere",
    "qwen/qwen3.8-27b": "qwen", "openai/gpt-oss-20b": "20b",
    "dots-studio/dots-3-note-preview:free": "dots",
}


def proposals(rows, case, members):
    """Même logique que atelier-vote.proposals_for, mais pour une liste de membres
    quelconque (on change temporairement le panel du module)."""
    saved = atelier.PANEL
    atelier.PANEL = members
    try:
        return atelier.proposals_for(rows, case, "real")
    finally:
        atelier.PANEL = saved


def fmt(decision):
    if decision["consensus"]:
        return f"{decision['value']} ({decision['votes']} voix)"
    return f"abstention (max {decision['votes']})"


def check(decision, ref):
    if not decision["consensus"]:
        return "-"
    return "oui" if decision["value"] == ref else "**NON**"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", type=Path, default=TD1 / "traces-td1.csv")
    parser.add_argument("--references", type=Path, default=TD1 / "reference-td1.csv")
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.traces.open(encoding="utf-8", newline="")))
    refs = {r["case_id"]: int(r["revenue_cents"])
            for r in csv.DictReader(args.references.open(encoding="utf-8", newline=""))}
    raw = {(r["model_requested"], r["case_id"]): r for r in rows if r["nature"] == "real"}

    out = []
    for case in sorted(refs):
        d3 = vote(proposals(rows, case, PANEL_3), 2)   # décision d'abord...
        d5 = vote(proposals(rows, case, QUORUM_5), 3)
        ref = refs[case]                               # ...référence ensuite
        values = []
        for _, model in QUORUM_5:
            r = raw.get((model, case), {})
            shown = r.get("value") or "-"
            if r.get("verdict") not in {"correct", "incorrect"}:
                shown = r.get("verdict", "absent")
            values.append(f"{SHORT[model]}={shown}")
        changed = (d3["consensus"], d3["value"]) != (d5["consensus"], d5["value"])
        out.append({"case": case, "ref": ref, "d3": fmt(d3), "ok3": check(d3, ref),
                    "d5": fmt(d5), "ok5": check(d5, ref),
                    "changed": "oui" if changed else "", "values": ", ".join(values)})

    print("| Question | Référence | 2-sur-3 | = réf. | 3-sur-5 | = réf. | Décision change | Valeurs des 5 modèles |")
    print("|---|---:|---|:-:|---|:-:|:-:|---|")
    for o in out:
        print(f"| {o['case']} | {o['ref']} | {o['d3']} | {o['ok3']} | {o['d5']} | {o['ok5']} "
              f"| {o['changed']} | {o['values']} |")

    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(out[0]))
            writer.writeheader()
            writer.writerows(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
