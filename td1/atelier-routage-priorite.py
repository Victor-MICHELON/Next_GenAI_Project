#!/usr/bin/env python3
"""TD 2, étape 3 : montrer la priorité de choose() dans atelier-routage.py (non modifié).

Deux scénarios simulés ajoutés, avec la fonction choose() d'origine :
1. small-free épuisé (recharge dans 30 min, avant l'échéance de 120 min),
   senior-subscription disponible : choose() prend l'abonnement tout de suite ;
2. small-free et senior-subscription épuisés : choose() diffère sur small-free.

Usage : python3 atelier-routage-priorite.py
"""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("routage", Path(__file__).resolve().parent / "atelier-routage.py")
routage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routage)

requete = {"difficulty": 1, "high_impact": False, "can_wait": True, "deadline_minutes": 120, "budget": 0.30}


def epuise(resources, ids, reset=30):
    return [dict(r, available=False, reset_minutes=reset) if r["id"] in ids else dict(r) for r in resources]


for nom, ressources in [
    ("free exhausted, subscription available", epuise(routage.RESOURCES, {"small-free"})),
    ("free and subscription exhausted", epuise(routage.RESOURCES, {"small-free", "senior-subscription"})),
]:
    print(json.dumps({"scenario": nom, "nature": "simulation", "request": requete,
                      "result": routage.choose(requete, ressources)}))
