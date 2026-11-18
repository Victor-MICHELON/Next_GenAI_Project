#!/usr/bin/env python3
"""TD 2, étape 2 (binôme B) : le consensus erroné.

1. Cherche dans traces-td1.csv (5 modèles, dernière tentative par cellule) les
   valeurs fausses identiques renvoyées par au moins deux modèles.
2. Pour chaque cas trouvé : vote 2-sur-3 (panel fixe) et 3-sur-5 avec le
   `vote_k_sur_n` du binôme A ; la référence n'est lue qu'après la décision.
3. Ré-exécute les requêtes fautives des traces sur data/boutique.sqlite
   (lecture seule) et calcule le delta ligne par ligne avec la requête de
   référence : lignes comptées par la référence et manquées par la requête
   fautive, et lignes ajoutées à tort. Le delta doit couvrir tout l'écart.
4. Rejoue DEMO-VOTE (table jouet d'une ligne, en mémoire : exemple construit).

Aucun appel réseau.
    python td2/B-consensus/consensus_errone.py
"""
import csv
import importlib.util
import sqlite3
import sys
from types import SimpleNamespace
from collections import defaultdict
from pathlib import Path

TD1 = Path(__file__).resolve().parents[2] / "td1"
DB = TD1 / "data" / "boutique.sqlite"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, TD1 / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


atelier = load("atelier_vote", "atelier-vote.py")
vote = atelier.load_vote()
PANEL_3 = list(atelier.PANEL)
QUORUM_5 = PANEL_3 + [("groq", "openai/gpt-oss-20b"),
                      ("openrouter", "dots-studio/dots-3-note-preview:free")]


def proposals(rows, case, members):
    saved = atelier.PANEL
    atelier.PANEL = members
    try:
        return atelier.proposals_for(rows, case, "real")
    finally:
        atelier.PANEL = saved


def latest_cells(rows):
    last = {}
    for r in rows:
        if r["nature"] == "real":
            last[(r["case_id"], r["provider"], r["model_requested"])] = r
    return last


def shared_wrong_values(last):
    groups = defaultdict(list)
    for (case, _, _), r in sorted(last.items()):
        if r["verdict"] == "incorrect":
            groups[(case, r["value"])].append(r)
    return {k: v for k, v in groups.items() if len(v) >= 2}


def fmt(d):
    if d["consensus"]:
        return f"consensus {d['value']} ({d['votes']} voix: {', '.join(d['models'])})"
    return f"abstention (max {d['votes']} voix)"


def row_set(con, sql):
    """Lignes de commande (order_id, product_id) -> montant, retenues par le WHERE
    d'une requête SUM(...). On remplace la projection SUM par les lignes."""
    body = sql.strip().rstrip(";")
    start = body.upper().index("FROM")
    rows_sql = ("SELECT o.order_id, o.product_id, c.customer_id, c.birth_date, o.date, "
                "o.quantity_product * p.price " + body[start:])
    return {(r[0], r[1]): r[2:] for r in con.execute(rows_sql)}


def delta(con, ref_sql, bad_sql):
    ref, bad = row_set(con, ref_sql), row_set(con, bad_sql)
    missed = {k: ref[k] for k in ref.keys() - bad.keys()}
    added = {k: bad[k] for k in bad.keys() - ref.keys()}
    return missed, added


def by_customer(lines):
    agg = defaultdict(lambda: [0, 0])
    for (_, _), (cust, birth, _, amount) in lines.items():
        agg[(cust, birth)][0] += 1
        agg[(cust, birth)][1] += amount
    return sorted(agg.items(), key=lambda kv: kv[0][1])


def demo_vote():
    print("\n=== DEMO-VOTE (exemple construit, table jouet en mémoire) ===")
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE sales (sale_date TEXT, amount_cents INTEGER)")
    con.execute("INSERT INTO sales VALUES ('2026-01-01', 100)")
    strict = ("SELECT COALESCE(SUM(amount_cents), 0) FROM sales "
              "WHERE sale_date > '2026-01-01' AND sale_date < '2026-01-02'")
    large = ("SELECT COALESCE(SUM(amount_cents), 0) FROM sales "
             "WHERE sale_date >= '2026-01-01' AND sale_date < '2026-01-02'")
    v_strict = con.execute(strict).fetchone()[0]
    v_large = con.execute(large).fetchone()[0]
    print(f"  sale_date >  '2026-01-01' -> {v_strict}  (borne de début exclue : la vente du 1er janvier disparaît)")
    print(f"  sale_date >= '2026-01-01' -> {v_large}  (borne incluse, = référence 100)")
    props = [
        SimpleNamespace(provider="p1", model_requested="m1", value=v_strict, verdict="executed"),
        SimpleNamespace(provider="p2", model_requested="m2", value=v_strict, verdict="executed"),
        SimpleNamespace(provider="p3", model_requested="m3", value=v_large, verdict="executed"),
    ]
    d = vote(props, 2)
    print(f"  vote 2-sur-3 sur [0, 0, 100] -> {fmt(d)} ; référence 100 -> "
          f"{'OK' if d['value'] == 100 else 'consensus erroné'}")


def main():
    with open(TD1 / "traces-td1.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    last = latest_cells(rows)
    refs = {}
    with open(TD1 / "reference-td1.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            refs[r["case_id"]] = (r["sql"], int(r["revenue_cents"]))

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    cases = shared_wrong_values(last)
    print(f"{len(last)} cellules (dernière tentative), {len(cases)} valeur(s) fausse(s) partagée(s)")

    for (case, value), cells in sorted(cases.items()):
        ref_sql, ref_value = refs[case]
        models = [r["model_requested"] for r in cells]
        print(f"\n=== {case} : valeur fausse partagée {value} par {', '.join(models)} ===")
        d3 = vote(proposals(rows, case, PANEL_3), 2)
        d5 = vote(proposals(rows, case, QUORUM_5), 3)
        # la référence n'intervient qu'ici, après les deux décisions
        print(f"  panel fixe 2-sur-3 : {fmt(d3)}")
        print(f"  quorum 3-sur-5     : {fmt(d5)}")
        print(f"  référence {ref_value} (reference-td1.csv, recalculée : "
              f"{con.execute(ref_sql).fetchone()[0]})")
        for r in cells:
            executed = con.execute(r["sql"]).fetchone()[0]
            missed, added = delta(con, ref_sql, r["sql"])
            m, a = sum(x[3] for x in missed.values()), sum(x[3] for x in added.values())
            print(f"  - {r['model_requested']} : ré-exécutée -> {executed} ; "
                  f"manquées {len(missed)} lignes = {m}, ajoutées {len(added)} lignes = {a} ; "
                  f"{executed} + {m} - {a} = {executed + m - a} "
                  f"({'= référence' if executed + m - a == ref_value else 'ÉCART NON EXPLIQUÉ'})")
            for (cust, birth), (n, amount) in by_customer(missed):
                print(f"      manqué  {cust} né le {birth} : {n} lignes, {amount} cts")
            for (cust, birth), (n, amount) in by_customer(added):
                print(f"      ajouté  {cust} né le {birth} : {n} lignes, {amount} cts")

    demo_vote()


if __name__ == "__main__":
    main()
