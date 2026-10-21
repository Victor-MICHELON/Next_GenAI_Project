#!/usr/bin/env python3
"""
TD 1 - Calcul et vérification des 20 références (reference-td1.csv).

Méthode 1 : une requête SQLite par question, exécutée sur data/boutique.sqlite (lecture seule).
Méthode 2 (contrôle indépendant) : recalcul en Python pur à partir des 3 CSV, sans SQL.
Le fichier reference-td1.csv n'est écrit que si les deux méthodes donnent la même valeur partout.

Usage (à la racine du kit, à côté de skeleton-multi-llm-en.py) :
    python compute_references.py            # calcule, compare, écrit reference-td1.csv
    python compute_references.py --dry-run  # calcule et compare sans écrire

Assistance au code déclarée : script préparé avec un assistant IA, relu et vérifié par le groupe.
Aucune valeur ne vient d'un modèle : tout est calculé ici, sur la base.
"""

import argparse
import csv
import sqlite3
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "data" / "boutique.sqlite"
DATA = HERE / "data"
OUT = HERE / "reference-td1.csv"

ABC = ("a", "b", "c")

# --------------------------------------------------------------------------
# Paramètres de chaque question, relus dans questions-td1-en.
#   period    : (début inclus, fin exclue)
#   products  : liste de produits, None = tous
#   age_ref   : date de référence pour "exactement 25 ans", None = pas de filtre
#   age_order : True = "25 ans au moment de la commande"
# VÉRIFIEZ cette table ligne par ligne contre l'énoncé : une erreur ici fausse les deux méthodes.
# --------------------------------------------------------------------------
SPECS = {
    "C01": dict(period=("2026-03-01 00:00:00", "2026-06-01 00:00:00")),
    "C02": dict(age_ref="2026-09-25"),
    "C03": dict(products=ABC, period=("2026-01-01 00:00:00", "2026-07-01 00:00:00")),
    "C04": dict(period=("2026-01-01 00:00:00", "2026-10-01 00:00:00")),
    "C05": dict(period=("2026-06-01 00:00:00", "2026-06-02 00:00:00")),
    "C06": dict(period=("2025-01-01 00:00:00", "2026-01-01 00:00:00")),
    "C07": dict(period=("2026-05-31 00:00:00", "2026-06-01 00:00:00")),
    "C08": dict(age_ref="2026-09-24"),
    "C09": dict(age_ref="2026-09-26"),
    "C10": dict(age_order=True),
    "C11": dict(age_ref="2026-12-01"),
    "C12": dict(products=ABC),
    "C13": dict(products=("a", "c"), period=("2026-04-01 00:00:00", "2026-05-01 00:00:00")),
    "C14": dict(products=ABC, period=("2026-10-01 00:00:00", "2026-12-01 00:00:00")),
    "C15": dict(period=("2026-03-01 00:00:00", "2026-06-01 00:00:00"), age_ref="2026-09-25"),
    "C16": dict(products=ABC, age_ref="2026-09-25"),
    "C17": dict(products=ABC, period=("2026-01-01 00:00:00", "2026-07-01 00:00:00"), age_ref="2026-09-25"),
    "C18": dict(period=("2026-05-01 00:00:00", "2026-06-01 00:00:00"), age_order=True),
    "C19": dict(products=("d",), period=("2026-09-01 00:00:00", "2026-10-01 00:00:00"), age_ref="2026-09-25"),
    "C20": dict(period=("2026-06-01 00:00:00", "2026-09-01 00:00:00")),
}


# --------------------------------------------------------------------------
# Méthode 1 : SQL
# --------------------------------------------------------------------------
def build_sql(spec: dict) -> str:
    """Une seule requête SELECT, une ligne, une colonne revenue_cents (0 au lieu de NULL)."""
    needs_customers = bool(spec.get("age_ref") or spec.get("age_order"))
    sql = ("SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents "
           "FROM orders o JOIN product p ON p.product_id = o.product_id")
    if needs_customers:
        sql += " JOIN customers c ON c.customer_id = o.customer_id"
    where = []
    if spec.get("period"):
        start, end = spec["period"]
        # période fermée à gauche, ouverte à droite
        where.append(f"o.date >= '{start}' AND o.date < '{end}'")
    if spec.get("products"):
        where.append("o.product_id IN (" + ", ".join(f"'{x}'" for x in spec["products"]) + ")")
    if spec.get("age_ref"):
        d = spec["age_ref"]
        # âge révolu = 25 le jour D  <=>  25e anniversaire <= D  et  26e anniversaire > D
        where.append(f"c.birth_date <= date('{d}', '-25 years') AND c.birth_date > date('{d}', '-26 years')")
    if spec.get("age_order"):
        # même règle, avec le jour de chaque ligne de commande
        where.append("c.birth_date <= date(o.date, '-25 years') AND c.birth_date > date(o.date, '-26 years')")
    if where:
        sql += " WHERE " + " AND ".join(where)
    return sql + ";"


def run_sql(sql: str) -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only = 1")
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    finally:
        conn.close()
    assert cols == ["revenue_cents"], f"colonne attendue revenue_cents, obtenu {cols}"
    assert len(rows) == 1, f"une seule ligne attendue, obtenu {len(rows)}"
    return int(rows[0][0])


# --------------------------------------------------------------------------
# Méthode 2 : Python pur sur les CSV (aucun SQL, aucune fonction date de SQLite)
# --------------------------------------------------------------------------
def read_csv(name: str) -> list:
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_date(text: str) -> date:
    return date.fromisoformat(text[:10])


def completed_age(birth: date, day: date) -> int:
    """Années révolues : on retire 1 si l'anniversaire n'est pas encore passé (mois, jour)."""
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def python_value(spec: dict, orders: list, prices: dict, births: dict) -> int:
    total = 0
    for o in orders:
        if spec.get("period"):
            start, end = spec["period"]
            if not (start <= o["date"] < end):          # même format texte, comparaison lexicale sûre
                continue
        if spec.get("products") and o["product_id"] not in spec["products"]:
            continue
        birth = births[o["customer_id"]]
        if spec.get("age_ref") and completed_age(birth, date.fromisoformat(spec["age_ref"])) != 25:
            continue
        if spec.get("age_order") and completed_age(birth, to_date(o["date"])) != 25:
            continue
        total += int(o["quantity_product"]) * prices[o["product_id"]]
    return total


# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="ne pas écrire reference-td1.csv")
    args = parser.parse_args()

    if not DB.exists():
        sys.exit(f"Base introuvable : {DB}. Lance le script depuis la racine du kit.")

    orders = read_csv("orders.csv")
    prices = {r["product_id"]: int(r["price"]) for r in read_csv("product.csv")}
    births = {r["customer_id"]: to_date(r["birth_date"]) for r in read_csv("customers.csv")}

    rows, mismatches = [], []
    print(f"{'case':5} {'SQL':>10} {'Python':>10}  check")
    print("-" * 36)
    for case_id, spec in SPECS.items():
        sql = build_sql(spec)
        v_sql = run_sql(sql)
        v_py = python_value(spec, orders, prices, births)
        ok = v_sql == v_py
        print(f"{case_id:5} {v_sql:>10} {v_py:>10}  {'OK' if ok else 'DIFF'}")
        if not ok:
            mismatches.append(case_id)
        rows.append((case_id, sql, v_sql))

    if mismatches:
        print(f"\nÉcarts sur {mismatches} : rien n'est écrit. Cherche la cause avant de continuer.")
        return 1
    print("\nLes deux méthodes concordent sur les 20 questions.")

    if args.dry_run:
        print("--dry-run : reference-td1.csv non modifié.")
        return 0
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id", "sql", "revenue_cents"])
        w.writerows(rows)
    print(f"Écrit : {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
