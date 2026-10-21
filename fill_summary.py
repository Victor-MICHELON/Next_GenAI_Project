#!/usr/bin/env python3
"""Remplit five-model-summary-en.csv à partir des traces fusionnées et du portefeuille.

Sources utilisées, et rien d'autre :
- modeles-autorises.json : les cinq modèles requis, leurs paramètres et l'opérateur ;
- portefeuille-modeles-2026-09-28.csv (+ portefeuille-modeles-en.md pour les dates) :
  index public et prix d'une route payante du même identifiant exact ;
- traces-td1.csv (sortie de merge_traces.py) et reference-td1.csv : résultats ;
- questions-td1.json : famille de chaque question.

Aucun appel réseau. Une valeur absente des sources reste N/A avec sa raison.
L'en-tête du template est conservé tel quel.

Usage : python fill_summary.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RESUME = ICI / "five-model-summary-en.csv"
PORTEFEUILLE = ICI / "portefeuille-modeles-2026-09-28.csv"
TRACES = ICI / "traces-td1.csv"

# Dates tirées de la section Sources de portefeuille-modeles-en.md
DATE_INDEX = "2026-09-28"   # index publics relevés le 28/09/2026
DATE_PRIX = "2026-09-29"    # prix des routes payantes relus le 29/09/2026

# Familles simples (type exact de questions-td1.json) ; un type avec "+" est une combinée
FAMILLES = {"period": "période", "age on a reference date": "âge (date de référence)",
            "age at the time of the order": "âge (au moment de la commande)", "product list": "produits"}
COMPOSANTES = {"period": "période", "age on a reference date": "âge date réf.",
               "age at the time of the order": "âge à la commande", "product list": "produits"}


def lire_csv(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8", newline="") as flux:
        return list(csv.DictReader(flux))


def bilan(cases: list[str], lignes: dict) -> str:
    """'x/n correct' avec les cas, puis les échecs avec leur verdict, puis accès/non exécutés à part."""
    evalues = [c for c in cases if c in lignes]
    corrects = [c for c in evalues if lignes[c]["verdict"] == "correct"]
    texte = f"{len(corrects)}/{len(evalues)} correct ({' '.join(cases)})"
    echecs = [f"{c} {lignes[c]['verdict']}" for c in evalues if lignes[c]["verdict"] != "correct"]
    if echecs:
        texte += " ; échecs : " + ", ".join(echecs)
    manquants = [c for c in cases if c not in lignes]
    if manquants:
        texte += " ; sans trace : " + " ".join(manquants)
    return texte


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    autorises = json.loads((ICI / "modeles-autorises.json").read_text(encoding="utf-8"))
    operateur = {r["modele"]: r["membre"] for r in autorises["budget_td1"]["repartition"]}
    types = {q["id"]: q["type"] for q in json.loads((ICI / "questions-td1.json").read_text(encoding="utf-8"))["questions"]}
    refs = {r["case_id"]: r["revenue_cents"] for r in lire_csv(ICI / "reference-td1.csv")}
    portefeuille = lire_csv(PORTEFEUILLE)
    traces = lire_csv(TRACES)

    # Garde-fou : la colonne reference des traces doit être la référence validée,
    # sinon les verdicts ne sont pas exploitables tels quels
    ecarts = [t["cell_id"] for t in traces if t["reference"] != refs.get(t["case_id"])]
    if ecarts:
        print("Arrêt : reference différente de reference-td1.csv pour " + ", ".join(ecarts))
        return 1

    with open(RESUME, encoding="utf-8", newline="") as flux:
        entete = next(csv.reader(flux))

    # Questions par famille simple, et combinées à part
    par_famille = defaultdict(list)
    combinees = []
    for case_id in sorted(types):
        if "+" in types[case_id]:
            combinees.append(case_id)
        else:
            par_famille[types[case_id]].append(case_id)

    sorties = []
    for m in autorises["modeles"]:
        fournisseur, modele = m["gate"], m["identifiant_exact"]
        lettre = operateur[modele]
        # Dernière tentative par cellule, nature real uniquement
        lignes_modele = [t for t in traces if t["provider"] == fournisseur and t["model_requested"] == modele]
        derniere = {}
        for t in lignes_modele:
            if t["nature"] == "real":
                derniere[t["case_id"]] = t
        autres_natures = sorted({t["nature"] for t in lignes_modele} - {"real"})

        # --- Portefeuille : même identifiant exact uniquement ---
        rangs = [p for p in portefeuille if p["identifiant_gate"] == modele]
        index = next((p for p in rangs if p["score_public"].strip()), None)
        payante = next((p for p in rangs if p["acces"] == "payant"), None)
        if index:
            public_index, index_date = index["score_public"], DATE_INDEX
            index_source = f"{PORTEFEUILLE.name}, ligne {index['cle']}"
        elif rangs:
            public_index, index_date = "N/A", "N/A"
            index_source = f"N/A : ligne {rangs[0]['cle']} présente dans {PORTEFEUILLE.name} mais sans index public relevé"
        else:
            public_index, index_date = "N/A", "N/A"
            index_source = (f"N/A : modèle absent de {PORTEFEUILLE.name} (sélection du 14/10/2026 postérieure "
                            "à l'instantané du 28/09/2026) ; pas d'autre source autorisée")
        if payante:
            route = f"{payante['gate']} {payante['identifiant_gate']} (paiement au token)"
            prix_in, prix_out, prix_date = payante["prix_entree_usd_m"], payante["prix_sortie_usd_m"], DATE_PRIX
            prix_source = (f"{PORTEFEUILLE.name}, ligne {payante['cle']} ; portefeuille-modeles-en.md, "
                           "catalogue de l'agrégateur relu le 29/09/2026")
        else:
            if rangs:
                raison = (f"N/A : le portefeuille ne documente que la route gratuite "
                          f"{', '.join(p['cle'] for p in rangs)}, aucune route payante du même identifiant")
            else:
                raison = "N/A : modèle absent du portefeuille, aucune route payante documentée"
            if modele.startswith("qwen/qwen3.8"):
                raison += " (qwen3.8-flash et qwen3.8-max-0902 sont d'autres modèles)"
            route, prix_in, prix_out, prix_date, prix_source = raison, "N/A", "N/A", "N/A", "N/A : voir paid_route_same_model"

        params = ", ".join(f"{k}={json.dumps(v) if isinstance(v, dict) else v}" for k, v in m["parametres"].items())
        acces = f"{fournisseur}, {modele}, gratuit ({'plan Free' if fournisseur == 'groq' else 'route :free, prix plafonné à 0'}) ; compte du membre {lettre} ; {params}, temperature=0"

        # --- Résultats par famille ---
        periode = bilan(par_famille["period"], derniere)
        age = ("date de référence " + bilan(par_famille["age on a reference date"], derniere)
               + " | au moment de la commande " + bilan(par_famille["age at the time of the order"], derniere))
        produits = bilan(par_famille["product list"], derniere)
        detail_comb = []
        for c in combinees:
            comps = " + ".join(COMPOSANTES[p.strip()] for p in types[c].split("+"))
            v = derniere[c]["verdict"] if c in derniere else "sans trace"
            detail_comb.append(f"{c} ({comps}) {v}")
        comb = (bilan(combinees, derniere) + " ; détail : " + ", ".join(detail_comb)
                + " ; les combinées ne sont pas recomptées dans les autres colonnes")

        # --- Limites ---
        nb_lignes = len([t for t in lignes_modele if t["nature"] == "real"])
        retries = sum(1 for t in derniere.values() if int(t["attempts"] or 1) > 1) + (nb_lignes - len(derniere))
        acces_err = sum(1 for t in derniere.values() if t["verdict"] == "access_error")
        non_exec = sum(1 for t in derniere.values() if t["verdict"] == "not_executed")
        manquantes = 20 - len(derniere)
        couts = [t["cost_native"] for t in derniere.values()]
        renseignes = [float(c) for c in couts if c != ""]
        if not renseignes:
            cout = f"cost_native vide sur {len(couts)}/{len(couts)} lignes ({fournisseur} ne le renvoie pas) : aucun coût mesuré, pas de total"
        elif len(renseignes) < len(couts):
            cout = (f"cost_native renseigné sur {len(renseignes)}/{len(couts)} lignes, sous-total {sum(renseignes):g} : "
                    "ce n'est pas un total complet")
        else:
            cout = f"cost_native renseigné sur {len(couts)}/{len(couts)} lignes, somme {sum(renseignes):g} (route gratuite)"
        limites = [f"un seul passage de 20 questions sur une base : pas de taux d'erreur général ni de classement",
                   f"{nb_lignes} lignes real, {retries} retry, {acces_err} accès refusé, {non_exec} non exécutée, {manquantes} cellule manquante",
                   cout]
        if autres_natures:
            limites.append("lignes " + "/".join(autres_natures) + " présentes dans les traces mais exclues du décompte")
        if modele == "openai/gpt-oss-120b":
            limites.append("détail du run et preuves d'usage Groq dans reports/role-A-run.md")
        if modele == "cohere/north-mini-code:free":
            limites.append("C18 notée d'abord incorrect contre 286650 (référence erronée) ; traces-C.csv et state-C.jsonl "
                           "re-notés contre 62480 dans le commit 33a097d, la valeur d'origine reste dans l'historique git")

        valeurs = {
            "provider": fournisseur, "model_id": modele,
            "public_index": public_index, "index_date": index_date, "index_source": index_source,
            "paid_route_same_model": route, "input_usd_per_million": prix_in, "output_usd_per_million": prix_out,
            "price_date": prix_date, "price_source": prix_source, "access_used": acces,
            "period_results": periode, "age_results": age, "product_results": produits, "combined_results": comb,
            "trace_files": f"traces-{lettre}.csv ; state-{lettre}.jsonl ; fusion dans traces-td1.csv",
            "limits": " ; ".join(limites),
        }
        sorties.append({col: valeurs.get(col, "") for col in entete})

    with open(RESUME, "w", encoding="utf-8", newline="") as flux:
        ecrivain = csv.DictWriter(flux, fieldnames=entete, lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(sorties)
    print(f"Écrit : {RESUME.name} ({len(sorties)} lignes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
