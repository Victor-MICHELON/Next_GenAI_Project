#!/usr/bin/env python3
"""Fusion des traces des opérateurs A à E en un seul traces-td1.csv.

On lit les traces-*.csv (sauf traces-td1.csv et les fichiers demo), on garde
toutes les lignes dans l'ordre d'origine, retries compris, sous un seul en-tête
(les colonnes de la dataclass Trace du squelette). Les fichiers sources ne sont
jamais modifiés. Aucun appel réseau.

Usage : python merge_traces.py
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from collections import Counter, defaultdict
from dataclasses import fields
from pathlib import Path

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "traces-td1.csv"
REFERENCES = ICI / "reference-td1.csv"


def colonnes_trace() -> list[str]:
    """Récupère les colonnes depuis la dataclass Trace du squelette, pour ne pas les recopier à la main.
    L'import ne lance rien : le main du squelette est protégé par if __name__ == "__main__"."""
    sys.path.insert(0, str(ICI))  # le squelette importe sandbox_sqlite, placé à côté
    spec = importlib.util.spec_from_file_location("skeleton", ICI / "skeleton-multi-llm-en.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["skeleton"] = module  # nécessaire pour que @dataclass retrouve le module
    spec.loader.exec_module(module)
    return [f.name for f in fields(module.Trace)]


def fichiers_sources() -> list[Path]:
    """traces-*.csv des opérateurs, sans le fichier fusionné ni les démos."""
    return [p for p in sorted(ICI.glob("traces-*.csv"))
            if p.name != SORTIE.name and "demo" not in p.name.lower()]


def main() -> int:
    # La console Windows est en cp1252 : on force l'UTF-8 pour les accents et les flèches
    sys.stdout.reconfigure(encoding="utf-8")
    colonnes = colonnes_trace()
    sources = fichiers_sources()
    if not sources:
        print("Aucun fichier traces-*.csv trouvé.")
        return 1

    # 1. Lecture et fusion, dans l'ordre des fichiers puis des lignes
    lignes: list[dict] = []
    print("Lignes par fichier source :")
    for chemin in sources:
        with open(chemin, encoding="utf-8", newline="") as flux:
            lecteur = csv.DictReader(flux)
            if lecteur.fieldnames != colonnes:
                manque = set(colonnes) - set(lecteur.fieldnames or [])
                en_trop = set(lecteur.fieldnames or []) - set(colonnes)
                print(f"  ATTENTION {chemin.name} : en-tête différent (manque {sorted(manque)}, en trop {sorted(en_trop)})")
            contenu = list(lecteur)
        print(f"  {chemin.name:20} {len(contenu):>4}")
        lignes.extend(contenu)
    print(f"  {'total':20} {len(lignes):>4}")

    # Les valeurs absentes restent vides : restval="" et rien n'est recalculé
    with open(SORTIE, "w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.DictWriter(flux, fieldnames=colonnes, restval="", extrasaction="ignore", lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    print(f"\nÉcrit : {SORTIE.name} ({len(lignes)} lignes + en-tête)")

    # 2. Cellules distinctes par modèle (et par nature, qu'on ne mélange pas)
    cellules = defaultdict(set)
    for l in lignes:
        cellules[(l["nature"], f"{l['provider']}:{l['model_requested']}")].add(l["cell_id"])
    print("\nCellules distinctes par modèle (attendu : 20) :")
    total = 0
    for (nature, modele), ids in sorted(cellules.items()):
        alerte = "" if len(ids) == 20 else "   <- différent de 20"
        print(f"  {modele:50} {nature:10} {len(ids):>3}{alerte}")
        total += len(ids)
    alerte = "" if total == 100 else "   <- différent de 100"
    print(f"  {'total':61} {total:>3}{alerte}")

    # 3. Tentatives par cellule : nombre de lignes et valeur max de la colonne attempts
    nb_lignes = Counter((l["nature"], l["cell_id"]) for l in lignes)
    max_attempts = defaultdict(int)
    for l in lignes:
        cle = (l["nature"], l["cell_id"])
        try:
            max_attempts[cle] = max(max_attempts[cle], int(l["attempts"] or 0))
        except ValueError:
            print(f"  ATTENTION attempts non numérique pour {l['cell_id']} : {l['attempts']!r}")
    print("\nTentatives par cellule :")
    repartition = Counter(max(nb_lignes[c], max_attempts[c]) for c in nb_lignes)
    for n, compte in sorted(repartition.items()):
        print(f"  {n} tentative(s) : {compte} cellule(s)")
    trop = [c for c in nb_lignes if max(nb_lignes[c], max_attempts[c]) > 2]
    if trop:
        print("  ATTENTION plus de 2 tentatives : " + ", ".join(f"{c[1]} ({c[0]})" for c in trop))
    retries = [c for c in nb_lignes if nb_lignes[c] > 1 or max_attempts[c] > 1]
    if retries:
        print("  Cellules avec retry :")
        for nature, cell_id in retries:
            print(f"    {cell_id} ({nature}) : {nb_lignes[(nature, cell_id)]} ligne(s), attempts max {max_attempts[(nature, cell_id)]}")
    else:
        print("  Cellules avec retry : aucune")

    # 4. Une seule empreinte de prompt par question, tous modèles confondus
    empreintes = defaultdict(set)
    for l in lignes:
        empreintes[l["case_id"]].add(l["prompt_sha256"])
    exceptions = {c: e for c, e in empreintes.items() if len(e) != 1}
    print(f"\nEmpreinte prompt_sha256 : {len(empreintes)} case_id")
    if exceptions:
        for case_id, valeurs in sorted(exceptions.items()):
            print(f"  ATTENTION {case_id} a {len(valeurs)} empreintes :")
            for v in sorted(valeurs):
                modeles = sorted({l["model_requested"] for l in lignes if l["case_id"] == case_id and l["prompt_sha256"] == v})
                print(f"    {v or '(vide)'} <- {', '.join(modeles)}")
    else:
        print("  une seule empreinte par case_id pour tous les modèles : OK")

    # 5. Colonne reference comparée à reference-td1.csv
    with open(REFERENCES, encoding="utf-8", newline="") as flux:
        refs = {r["case_id"]: r["revenue_cents"].strip() for r in csv.DictReader(flux)}
    ecarts = [l for l in lignes if l["reference"].strip() != refs.get(l["case_id"], "<absent>")]
    print(f"\nColonne reference vs {REFERENCES.name} ({len(refs)} références) :")
    if ecarts:
        for l in ecarts:
            print(f"  ATTENTION {l['cell_id']} : trace {l['reference']!r}, référence {refs.get(l['case_id'], 'absente')!r}")
    else:
        print("  toutes les lignes correspondent : OK")

    # Rappel des natures présentes, pour ne pas les mélanger plus tard
    print("\nNatures présentes : " + ", ".join(f"{n} = {c}" for n, c in sorted(Counter(l["nature"] for l in lignes).items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
