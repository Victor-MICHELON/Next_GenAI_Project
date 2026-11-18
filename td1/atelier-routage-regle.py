#!/usr/bin/env python3
"""TD 2, étape 3 : le simulateur de routage adapté à la règle du sous-groupe.

Version adaptée de atelier-routage.py (laissé intact, sa sortie est la version
« avant »). Aucun appel réseau, aucune clé.

Ce qui change par rapport au simulateur fourni :
- RESOURCES contient nos cinq modèles du TD 1, plus les routes payantes Groq
  Developer documentées dans methode-cout-en.md (étape 2, prix du 05/10/2026) ;
- le « niveau » abstrait est remplacé par les familles de questions sur
  lesquelles le modèle a été correct dans le TD 1. Ces familles sont recalculées
  à chaque lancement depuis model-question-comparison-en.csv : la règle cite les
  cellules, elle ne les recopie pas à la main ;
- le contrôle dépend de la famille et de l'usage (tableau de bord interne,
  chiffre montré au client, montant versé) ;
- chaque décision porte une raison lisible avec les cellules TD 1 qui la
  justifient, et le rejeu sur les traces TD 1 du panel de quorum retenu.

Les disponibilités et les délais de recharge des scénarios sont simulés, pas
mesurés chez un fournisseur. Les prix sont des équivalents facturés pour une
enveloppe fixe (2 000 tokens en entrée, 1 024 en sortie, modeles-autorises.json) :
la dépense réelle du TD reste 0 (plans gratuits).

Usage :
    python3 atelier-routage-regle.py                      # tous les scénarios
    python3 atelier-routage-regle.py --scenario <nom>     # un scénario
    python3 atelier-routage-regle.py --replay             # rejeu des panels sur TD 1
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
COMPARAISON = ICI / "model-question-comparison-en.csv"
QUESTIONS = ICI / "questions-td1.json"

ENTREE_TOKENS, SORTIE_TOKENS = 2000, 1024

# Types exacts de questions-td1.json -> famille de la règle
FAMILLES = {
    "period": "période",
    "age on a reference date": "âge à une date",
    "age at the time of the order": "âge à la commande",
    "product list": "produits",
}
COMBINEES = "combinées"


def cout(entree_usd_m, sortie_usd_m):
    """Équivalent facturé d'une requête pour l'enveloppe fixe, en USD HT."""
    if entree_usd_m is None:
        return None
    return round((ENTREE_TOKENS * entree_usd_m + SORTIE_TOKENS * sortie_usd_m) / 1e6, 6)


# Modèles du TD 1. `vendor` sert à garder un panel de familles distinctes :
# gpt-oss-120b et gpt-oss-20b sont la même famille (openai), ils ne comptent
# jamais comme deux voix indépendantes.
MODELES = [
    # id, vendor, prix entrée/sortie de la route payante du même modèle (USD/M), dans le portefeuille ?
    ("groq:openai/gpt-oss-20b", "openai", 0.075, 0.30, True),
    ("groq:openai/gpt-oss-120b", "openai", 0.15, 0.60, True),
    ("groq:qwen/qwen3.8-27b", "qwen", 0.80, 4.00, True),
    ("openrouter:cohere/north-mini-code:free", "cohere", None, None, False),
    ("openrouter:dots-studio/dots-3-note-preview:free", "dots", None, None, False),
]


def resources():
    """Une ressource gratuite (plan Free / route :free) par modèle, plus la route
    payante Groq Developer du même modèle quand methode-cout-en.md la documente."""
    out = []
    for mid, vendor, pin, pout, portefeuille in MODELES:
        prix = cout(pin, pout)
        out.append({"id": mid, "model": mid, "vendor": vendor, "access": "free",
                    "in_portfolio": portefeuille, "available": True, "reset_minutes": None,
                    "cash": 0.0, "billed_equivalent": prix})
        if prix is not None:
            out.append({"id": mid.replace("groq:", "groq-developer:"), "model": mid,
                        "vendor": vendor, "access": "tokens", "in_portfolio": portefeuille,
                        "available": True, "reset_minutes": None,
                        "cash": prix, "billed_equivalent": prix})
    return out


RESOURCES = resources()

# Panels de quorum par famille (2 sur 3, trois familles distinctes). Choisis sur
# les cellules TD 1 ; le rejeu (--replay) montre ce qu'ils auraient rendu.
# 3 sur 5 n'est pas retenu : nos cinq modèles ne couvrent que quatre familles
# (les deux gpt-oss sont openai), un 3 sur 5 compterait openai deux fois.
PANELS = {
    "période": ["groq:openai/gpt-oss-20b", "groq:qwen/qwen3.8-27b",
                "openrouter:dots-studio/dots-3-note-preview:free"],
    "produits": ["groq:openai/gpt-oss-20b", "openrouter:cohere/north-mini-code:free",
                 "openrouter:dots-studio/dots-3-note-preview:free"],
    "âge à une date": ["groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
                       "openrouter:dots-studio/dots-3-note-preview:free"],
    COMBINEES: ["groq:openai/gpt-oss-20b", "groq:qwen/qwen3.8-27b",
                "openrouter:dots-studio/dots-3-note-preview:free"],
    # Âge à la commande : pas de panel fiable. {120b, qwen, dots} rend un
    # consensus faux sur C10 (qwen et dots : 119410 contre 558980).
    "âge à la commande": None,
}

# Contrôle selon le coût d'une erreur : tableau de bord interne (erreur visible
# en interne, corrigeable), chiffre montré au client (crédibilité, litige),
# montant versé (argent sorti, difficile à récupérer).
# "reference" = recalcul indépendant (requête SQL validée + recalcul Python sur
# les CSV, comme compute_references.py), sans LLM.
CONTROLES = {
    "période":           {"dashboard": "none", "customer": "quorum 2-of-3", "payout": "reference + review"},
    "produits":          {"dashboard": "none", "customer": "quorum 2-of-3", "payout": "reference + review"},
    "âge à une date":    {"dashboard": "quorum 2-of-3", "customer": "reference", "payout": "reference + review"},
    "âge à la commande": {"dashboard": "reference", "customer": "reference", "payout": "reference + review"},
    COMBINEES:           {"dashboard": "quorum 2-of-3", "customer": "reference", "payout": "reference + review"},
}


# --------------------------------------------------------------------------
# Lecture du TD 1
# --------------------------------------------------------------------------

def famille_de(type_question):
    return COMBINEES if "+" in type_question else FAMILLES[type_question]


def charger_td1():
    """{famille: {modèle: {case_id: ligne finale}}} depuis le CSV long du TD 1."""
    types = {q["id"]: q["type"] for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]}
    td1 = defaultdict(lambda: defaultdict(dict))
    with open(COMPARAISON, encoding="utf-8", newline="") as flux:
        for ligne in csv.DictReader(flux):
            td1[famille_de(types[ligne["case_id"]])][ligne["model_id"]][ligne["case_id"]] = ligne
    return td1


TD1 = charger_td1()


def bilan(famille, modele):
    cellules = TD1[famille][modele]
    ok = sorted(c for c, l in cellules.items() if l["status"] == "correct")
    ko = sorted(f"{c} {l['status']}" for c, l in cellules.items() if l["status"] != "correct")
    return ok, ko


def eligible(resource, famille):
    """Éligible si le modèle a été correct sur toutes les cellules TD 1 de la famille."""
    if famille not in TD1:
        return False
    ok, ko = bilan(famille, resource["model"])
    return bool(ok) and not ko


def justification(resource, famille):
    ok, _ = bilan(famille, resource["model"])
    return f"{resource['model']} {len(ok)}/{len(ok)} correct en TD 1 ({' '.join(ok)})"


# --------------------------------------------------------------------------
# Rejeu d'un panel sur les traces TD 1 (vote local, même contrat que TD 2)
# --------------------------------------------------------------------------

def vote(valeurs, k):
    """valeurs : liste de cents ou None (erreur : reste dans n, ne vote pas)."""
    n = len(valeurs)
    if not n // 2 < k <= n:
        raise ValueError("k doit être une majorité stricte")
    compte = Counter(v for v in valeurs if v is not None)
    if compte:
        v, nb = compte.most_common(1)[0]
        if nb >= k:
            return {"consensus": True, "value": v, "votes": nb}
    return {"consensus": False, "value": None, "votes": max(compte.values(), default=0)}


def rejeu_panel(famille):
    panel = PANELS.get(famille)
    if not panel:
        return None
    cas = sorted({c for m in TD1[famille].values() for c in m})
    out = []
    for c in cas:
        lignes = [TD1[famille][m][c] for m in panel]
        valeurs = [int(l["value_cents"]) if l["value_cents"] not in ("", None) else None for l in lignes]
        d = vote(valeurs, 2)
        ref = int(lignes[0]["reference_cents"])
        issue = "abstention" if not d["consensus"] else ("juste" if d["value"] == ref else "consensus FAUX")
        out.append(f"{c} {issue}")
    return out


# --------------------------------------------------------------------------
# La politique
# --------------------------------------------------------------------------

def choose(request, resources):
    """Règle du sous-groupe, déterministe, avec une raison lisible.

    1. modèles éligibles = corrects sur toute la famille en TD 1 ; on prend le
       moins cher (équivalent facturé du portefeuille), d'abord en capacité
       gratuite disponible ;
    2. premier modèle indisponible -> modèle éligible suivant ;
    3. aucun gratuit disponible et la requête peut attendre la recharge -> defer
       (la disponibilité est re-mesurée au réveil) ;
    4. sinon route payante du même modèle si le budget l'autorise ;
    5. sinon abstention : on ne fabrique pas de réponse.
    """
    famille, usage = request["family"], request["use"]
    if famille not in CONTROLES:
        return {"action": "abstain", "resource": None, "cash": 0, "checks": "n/a",
                "reason": f"famille inconnue « {famille} » : aucune cellule TD 1 ne justifie un modèle"}
    checks = CONTROLES[famille][usage]
    elig = [r for r in resources if r["in_portfolio"] and eligible(r, famille)]
    # Ordre : équivalent facturé croissant (le moins cher d'abord), puis id
    elig.sort(key=lambda r: (r["billed_equivalent"], r["id"]))
    base = {"checks": checks}
    if checks.startswith("quorum"):
        base["panel"] = PANELS[famille]
    if not elig:
        return {"action": "abstain", "resource": None, "cash": 0, **base,
                "reason": f"aucun modèle du portefeuille correct sur toute la famille {famille} en TD 1"}

    gratuits = [r for r in elig if r["cash"] == 0]
    premier = gratuits[0] if gratuits else None
    dispo = [r for r in gratuits if r["available"]]
    if dispo:
        r = dispo[0]
        if r is premier:
            raison = f"premier modèle de la famille {famille} : le moins cher éligible ; {justification(r, famille)}"
        else:
            raison = (f"{premier['id']} indisponible, modèle éligible suivant ; {justification(r, famille)}")
        return {"action": "run", "resource": r["id"], "cash": 0,
                "billed_equivalent_usd": r["billed_equivalent"], **base, "reason": raison}

    attente = [r for r in gratuits if r["reset_minutes"] is not None
               and 0 < r["reset_minutes"] <= request["deadline_minutes"]]
    if attente and request["can_wait"]:
        r = min(attente, key=lambda r: r["reset_minutes"])
        return {"action": "defer", "resource": r["id"], "cash": 0, **base,
                "wake_in_minutes": r["reset_minutes"],
                "reason": (f"aucun modèle éligible disponible pour {famille} ; la requête peut attendre : "
                           f"recharge de {r['id']} dans {r['reset_minutes']} min, disponibilité re-mesurée au réveil ; "
                           f"{justification(r, famille)}")}

    payants = [r for r in elig if r["cash"] > 0 and r["available"] and r["cash"] <= request["budget"]]
    if payants:
        r = payants[0]
        return {"action": "run", "resource": r["id"], "cash": r["cash"], **base,
                "reason": (f"capacité gratuite épuisée, requête non différable : route payante du même modèle "
                           f"dans le budget ({r['cash']} USD) ; {justification(r, famille)}")}

    hors_td1 = [r for r in resources if r["access"] == "free" and not eligible(r, famille)]
    hors_portefeuille = sorted(r["id"] for r in resources if r["access"] == "free"
                               and not r["in_portfolio"] and eligible(r, famille))
    raison = f"aucun modèle éligible disponible pour {famille} dans le délai et le budget"
    indispos = [r for r in elig if r["cash"] == 0]
    if indispos:
        raison += " ; éligibles mais indisponibles : " + ", ".join(justification(r, famille) for r in indispos)
    if hors_td1:
        details = []
        for r in sorted(hors_td1, key=lambda r: r["id"]):
            ok, ko = bilan(famille, r["model"])
            details.append(f"{r['id']} {len(ok)}/{len(ok) + len(ko)} ({', '.join(ko)})")
        raison += " ; en échec sur la famille en TD 1 : " + " ; ".join(details)
    if hors_portefeuille:
        raison += f" ; corrects mais absents du portefeuille (pas de prix ni de route payante) : {', '.join(hors_portefeuille)}"
    return {"action": "abstain", "resource": None, "cash": 0, **base, "reason": raison}


# --------------------------------------------------------------------------
# Scénarios (simulés)
# --------------------------------------------------------------------------

def indispo(resources, ids, reset=60):
    return [dict(r, available=False, reset_minutes=reset) if r["id"] in ids else dict(r) for r in resources]


GPT20, GPT120 = "groq:openai/gpt-oss-20b", "groq:openai/gpt-oss-120b"
DEV120 = "groq-developer:openai/gpt-oss-120b"


def scenarios():
    base = {"can_wait": True, "deadline_minutes": 120, "budget": 0.0}
    openai_vides = indispo(RESOURCES, {GPT20, GPT120})
    return [
        ("période tableau de bord", {**base, "family": "période", "use": "dashboard"}, RESOURCES),
        ("période versement", {**base, "family": "période", "use": "payout"}, RESOURCES),
        ("produits client", {**base, "family": "produits", "use": "customer"}, RESOURCES),
        ("âge à une date client", {**base, "family": "âge à une date", "use": "customer"}, RESOURCES),
        ("âge à la commande tableau de bord", {**base, "family": "âge à la commande", "use": "dashboard"}, RESOURCES),
        ("combinées tableau de bord", {**base, "family": COMBINEES, "use": "dashboard"}, RESOURCES),
        ("période, premier modèle épuisé", {**base, "family": "période", "use": "dashboard"},
         indispo(RESOURCES, {GPT20})),
        ("âge à une date, 120b épuisé, différable", {**base, "family": "âge à une date", "use": "dashboard"},
         indispo(RESOURCES, {GPT120})),
        ("âge à une date, 120b épuisé, urgent", {**base, "family": "âge à une date", "use": "dashboard",
                                                 "can_wait": False, "deadline_minutes": 5},
         indispo(RESOURCES, {GPT120})),
        ("combinées, openai épuisé, urgent avec budget", {**base, "family": COMBINEES, "use": "customer",
                                                          "can_wait": False, "deadline_minutes": 5, "budget": 0.01},
         openai_vides),
        ("combinées, openai et payant indisponibles, urgent", {**base, "family": COMBINEES, "use": "customer",
                                                              "can_wait": False, "deadline_minutes": 5, "budget": 0.01},
         indispo(openai_vides, {DEV120, "groq-developer:openai/gpt-oss-20b"})),
        ("famille inconnue", {**base, "family": "panier moyen", "use": "dashboard"}, RESOURCES),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", help="n'afficher que le scénario nommé")
    parser.add_argument("--replay", action="store_true", help="rejouer les panels de quorum sur les traces TD 1")
    args = parser.parse_args()
    if args.replay:
        for famille in CONTROLES:
            print(json.dumps({"family": famille, "panel": PANELS.get(famille),
                              "td1_replay_2_of_3": rejeu_panel(famille), "nature": "replay of real TD 1 traces"},
                             ensure_ascii=False))
        return
    trouve = False
    for nom, requete, res in scenarios():
        if args.scenario and nom != args.scenario:
            continue
        trouve = True
        resultat = choose(requete, res)
        if "panel" in resultat:
            resultat["panel_td1_replay"] = rejeu_panel(requete["family"])
        print(json.dumps({"scenario": nom, "nature": "simulation", "request": requete, "result": resultat},
                         ensure_ascii=False))
    if not trouve:
        parser.error("scénario inconnu")


if __name__ == "__main__":
    main()
