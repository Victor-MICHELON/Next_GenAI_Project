# Aide d'IA - calcul des références (deuxième calcul)

Assistant : Codex. Date : 21 octobre 2026. Contexte : branche de Bertrand.

## Demande faite à l'assistant, mot pour mot

> Changement de plan. On fait les 20 quetsions ensuite on push
> Etnsuite on passera au role A

## Méthode et décisions

On a relu le schéma, le protocole et les vingt questions. L'assistant a aidé à écrire les requêtes SQLite `SELECT`, qu'on a exécutées en lecture seule. Chaque montant a été recalculé à part en Python, en parcourant les CSV fournis. On a gardé le format à trois colonnes que le squelette attend pour `reference-td1.csv`, ainsi que les scripts et la preuve de calcul (`reports/reference-verification.csv`).

Aucune API de modèle n'a été appelée, et aucune réponse d'un modèle évalué n'a été utilisée. Le groupe a relu le code et l'interprétation des questions, et reste responsable de leur explication. Les vingt valeurs ont ensuite été validées par le corrigé du prof.
