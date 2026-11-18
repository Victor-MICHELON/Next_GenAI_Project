# TD 2 — Quorum (binôme A)

Vote k-sur-n implémenté dans `Orchestrateur.vote_k_sur_n` ([../../td1/skeleton-multi-llm-en.py](../../td1/skeleton-multi-llm-en.py)), puis comparaison du panel fixe 2-sur-3 avec un quorum 3-sur-5 sur les 20 questions du TD 1.

```
cd td1
python3 atelier-vote.py                                    # 4 exemples synthétiques
python3 atelier-vote.py --traces traces-td1.csv --case C02 # vraies traces, une question
cd ..
python3 td2/A-quorum/compare_quorum.py --csv td2/A-quorum/comparaison-2sur3-3sur5.csv
```

- [compare_quorum.py](compare_quorum.py) : tableau des 20 questions (réutilise `proposals_for` d'`atelier-vote.py`, aucun appel réseau).
- [comparaison-2sur3-3sur5.csv](comparaison-2sur3-3sur5.csv) : export du tableau.

Résultat : 16 consensus dans les deux cas, 1 faux (C09) en 2-sur-3 contre 0 en 3-sur-5. Les décisions changent sur C09 et C19. Analyse complète dans [../../reports/td2.md](../../reports/td2.md#1-étape-1---le-vote-k-sur-n-binôme-a).
