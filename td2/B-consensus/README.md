# TD 2 — Le faux consensus (binôme B)

Recherche dans `td1/traces-td1.csv` des valeurs fausses identiques renvoyées par au moins deux modèles, vote 2-sur-3 et 3-sur-5 avec le `vote_k_sur_n` du binôme A, diagnostic des clauses SQL fautives, puis requête delta sur `td1/data/boutique.sqlite`, ouverte en lecture seule.

```
python td2/B-consensus/consensus_errone.py
sqlite3 -readonly td1/data/boutique.sqlite < td2/B-consensus/delta_queries.sql
```

- [consensus_errone.py](consensus_errone.py) : recherche des valeurs fausses partagées, votes, ré-exécution des requêtes fautives, delta ligne par ligne et DEMO-VOTE (table jouet en mémoire). Aucun appel réseau.
- [delta_queries.sql](delta_queries.sql) : les requêtes delta de C09 et de C10.

Résultats :

- **C09** : qwen et cohere répondent tous les deux 0 alors que la référence vaut 487980. Le panel 2-sur-3 livre ce 0 : c'est un faux consensus. Le quorum 3-sur-5 s'abstient. Les deux requêtes donnent 0 pour des raisons différentes :
  - qwen écrit une condition mois-jour contradictoire ;
  - cohere compare l'année de naissance à 25 et ajoute une fenêtre de dates vide.
  
  Le `COALESCE(SUM, 0)` transforme ensuite l'ensemble vide en 0. Le delta trouve 6 clients et 68 lignes, soit 487980 centimes : il explique tout l'écart.
- **C10** : qwen et dots répondent tous les deux 119410 alors que la référence vaut 558980. Les deux quorums s'abstiennent. Le delta trouve 59 lignes, soit 439570 centimes : ce sont les commandes de clients de 25 ans passées avant leur anniversaire, dans l'année civile qui suit leurs 25 ans.

L'analyse complète est dans [../../reports/td2.md](../../reports/td2.md#2-étape-2---le-faux-consensus-binôme-b).
