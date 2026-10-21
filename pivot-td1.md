# TD 1 — résultats modèles × questions

Source : `model-question-comparison-en.csv` (dernière tentative de chaque cellule).

| Modèle | C01 | C02 | C03 | C04 | C05 | C06 | C07 | C08 | C09 | C10 | C11 | C12 | C13 | C14 | C15 | C16 | C17 | C18 | C19 | C20 | Correct | incorrect | SQL inv./rejeté | accès refusé | non exécuté |
|:---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|--:|--:|--:|--:|--:|
| `groq:openai/gpt-oss-120b` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **20/20** | 0 | 0 | 0 | 0 |
| `groq:openai/gpt-oss-20b` | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **18/20** | 2 | 0 | 0 | 0 |
| `openrouter:cohere/north-mini-code:free` | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ! | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗* | ✗ | ✓ | **11/20** | 8 | 1 | 0 | 0 |
| `groq:qwen/qwen3.8-27b` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ! | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | **13/20** | 6 | 1 | 0 | 0 |
| `openrouter:dots-studio/dots-3-note-preview:free` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | **14/20** | 6 | 0 | 0 | 0 |

## Légende

- **✓** correct : la valeur exécutée est égale à la référence
- **✗** incorrect : le SQL s'exécute mais la valeur diffère de la référence (mauvaise réponse)
- **!** SQL invalide (erreur SQLite) ou rejeté par le bac à sable : pas de valeur
- **A** accès refusé (HTTP 400-404 ou 429) : ce n'est pas une mauvaise réponse, le modèle n'a pas été évalué
- **–** non exécuté (délai, erreur temporaire, cellule inachevée) : pas évalué non plus
- **\*** verdict à vérifier (voir la colonne explanation du CSV)

« Correct » compte les ✓ sur toutes les questions ; quand des cellules n'ont pas été évaluées (A ou –), le score sur les seules cellules évaluées est donné entre parenthèses.
