# TD 2 — Routage (étape 3)

- [regle-routage.md](regle-routage.md) : la règle d'une page. Elle donne le premier modèle, le contrôle selon l'usage et la conduite à tenir en cas d'indisponibilité, famille par famille, avec les cellules TD 1 qui la justifient.
- [simulateur-avant.jsonl](simulateur-avant.jsonl) : la sortie de `python3 td1/atelier-routage.py` telle que fournie (7 scénarios, ressources fictives).
- [simulateur-apres.jsonl](simulateur-apres.jsonl) : la sortie de `python3 td1/atelier-routage-regle.py`, notre règle (12 scénarios simulés, nos cinq modèles et les routes payantes Groq).
- [rejeu-panels-td1.jsonl](rejeu-panels-td1.jsonl) : la sortie de `python3 td1/atelier-routage-regle.py --replay`. On y voit ce que chaque panel 2 sur 3 retenu aurait rendu sur les traces réelles du TD 1.

- [priorite-abonnement.jsonl](priorite-abonnement.jsonl) : la sortie de `python3 td1/atelier-routage-priorite.py`. Avec le `choose` d'origine, l'abonnement disponible passe avant l'attente d'une route gratuite épuisée. L'analyse est dans [reports/td2.md](../../reports/td2.md).

Le simulateur adapté relit `td1/model-question-comparison-en.csv` à chaque lancement : l'éligibilité d'un modèle et les cellules citées dans la raison viennent des traces, pas d'une saisie à la main. Les disponibilités et les délais de recharge des scénarios sont simulés.

À refaire :

```bash
cd td1
python3 atelier-routage.py          > ../td2/C-routing/simulateur-avant.jsonl
python3 atelier-routage-regle.py    > ../td2/C-routing/simulateur-apres.jsonl
python3 atelier-routage-regle.py --replay > ../td2/C-routing/rejeu-panels-td1.jsonl
```
