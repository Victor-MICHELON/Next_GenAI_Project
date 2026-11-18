#!/usr/bin/env python3
"""
TD 1 - Analyse des cellules en échec (traces-*.csv / state-*.jsonl).

Pour chaque cell_id, on ne garde que la DERNIÈRE tentative, comme
`TableTraces.taux_par_modele` dans skeleton-multi-llm-en.py (clé (nature, cell_id),
la dernière ligne lue l'emporte). Pour chaque cellule dont le verdict n'est pas
"correct", le script affiche la trace et propose UNE cause, justifiée par un
élément précis du SQL ou de l'erreur. Les autres anomalies détectées sont listées
à part. Quand aucun indice du SQL ne permet de conclure, la cause est "à vérifier".

Le résultat est écrit en français dans notes/echecs-td1.md (une section par
cellule en échec), puis un récapitulatif est affiché : nombre de correct par
modèle et échecs par famille de questions (types de questions-td1.json).

Usage (à la racine du kit) :
    python3 analyze_failures.py                       # traces-A.csv ... traces-E.csv
    python3 analyze_failures.py traces-B.csv state-C.jsonl
    python3 analyze_failures.py --out notes/autre.md

Bibliothèque standard uniquement. Aucune requête n'est exécutée : l'analyse est statique.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
QUESTIONS = HERE / "questions-td1.json"
REFERENCES = HERE / "reference-td1.csv"
DEFAULT_TRACES = sorted(HERE.glob("traces-[A-Z].csv"))
OUT = HERE / "notes" / "echecs-td1.md"

MAX_OUTPUT_TOKENS = 1024          # plafond de sortie du squelette, raisonnement compris
ACCESS_STATUSES = {400, 401, 402, 403, 404, 429}

FAMILIES = {
    "period": "période",
    "age on a reference date": "âge à une date de référence",
    "age at the time of the order": "âge au moment de la commande",
    "product list": "liste de produits",
}
COMBINED = "combinées"
FAMILY_ORDER = list(FAMILIES.values()) + [COMBINED]

# Libellés des causes (une seule est retenue par cellule).
PERIODE = "convention de période (bornes)"
AGE_DIFF = "convention d'âge (différence d'années au lieu de l'âge révolu)"
AGE_CONFUSION = "convention d'âge (date de référence confondue avec la date de commande)"
AGE = "convention d'âge"
PRODUITS = "liste de produits"
MONTANT_QTE = "montant (prix sans quantité)"
MONTANT_NULL = "montant (NULL au lieu de 0)"
SQL_INVALIDE = "SQL invalide"
SQL_REJETE = "SQL rejeté"
TRONQUEE = "sortie tronquée (tokens au plafond)"
ACCES = "accès refusé (400-404/429)"
NON_EXECUTE = "non exécuté"
A_VERIFIER = "à vérifier"


# ==========================================================================
# 1. Chargement : questions, références, dernière tentative par cellule
# ==========================================================================

def load_questions(path: Path) -> dict:
    return {q["id"]: q for q in json.loads(path.read_text(encoding="utf-8"))["questions"]}


def load_references(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as stream:
        return {row["case_id"]: row["revenue_cents"] for row in csv.DictReader(stream)}


def read_traces(path: Path) -> list:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    with open(path, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def latest_by_cell(paths: list) -> dict:
    """Même règle que TableTraces.latest_by_cell : la dernière ligne d'une cellule l'emporte."""
    latest = {}
    for path in paths:
        for record in read_traces(path):
            record = {k: "" if v is None else str(v) for k, v in record.items()}
            latest[(record.get("nature", "real"), record["cell_id"])] = record
    return latest


def family(question_type: str) -> str:
    return COMBINED if "+" in question_type else FAMILIES.get(question_type, question_type)


# ==========================================================================
# 2. Lecture de la question : période, produits, âge
# ==========================================================================

def parse_question(text: str) -> dict:
    out = {"period": None, "products": None, "ref_date": None, "age_at_order": False, "age": None}
    m = re.search(r"from (\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2})?) to (\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2})?)", text)
    if m:
        out["period"] = (m.group(1), m.group(2))
    m = re.search(r"products? ([a-z](?:, [a-z])*(?: and [a-z])?) only", text)
    if m:
        out["products"] = set(re.findall(r"\b[a-z]\b", m.group(1)))
    m = re.search(r"exactly (\d+) years old", text)
    if m:
        out["age"] = int(m.group(1))
    m = re.search(r"reference date (\d{4}-\d{2}-\d{2})", text)
    if m:
        out["ref_date"] = date.fromisoformat(m.group(1))
    out["age_at_order"] = "at the time of the order" in text
    return out


# ==========================================================================
# 3. Outils d'analyse du SQL
# ==========================================================================

ORDER_DATE = r"\b(?:\w+\.)?date\b(?!\s*\()"          # orders.date, pas birth_date ni date(...)
PERIOD_CMP = re.compile(ORDER_DATE + r"\s*(>=|<=|<|>|=)\s*'([^']*)'", re.I)
PERIOD_BETWEEN = re.compile(ORDER_DATE + r"\s+BETWEEN\s+'([^']*)'\s+AND\s+'([^']*)'", re.I)
PRODUCT_IN = re.compile(r"product_id\s+IN\s*\(([^)]*)\)", re.I)
PRODUCT_EQ = re.compile(r"product_id\s*=\s*'(\w+)'", re.I)
YEAR = (r"(?:CAST\(\s*(?:SUBSTR|strftime)\([^()]*\)\s*AS\s+INTEGER\s*\)"
        r"|strftime\(\s*'%Y'\s*,\s*[^()]*?\)"
        r"|SUBSTR\([^()]*?,\s*1\s*,\s*4\s*\))")
YEAR_DIFF = re.compile(r"(" + YEAR + r")\s*-\s*(" + YEAR + r")", re.I)
YEAR_ARITH = re.compile(r"(" + YEAR + r")\s*\+\s*(\d+)\s*(<=|>=|<|>|=)\s*(\d{4})", re.I)


def snippet(text: str) -> str:
    return "`" + " ".join(text.split()) + "`"


def md_inline(text: str) -> str:
    """Texte sur une ligne en code Markdown, même s'il contient des accents graves."""
    text = " ".join(text.split())
    if not text:
        return "-"
    fence = "`" * (max((len(r) for r in re.findall(r"`+", text)), default=0) + 1)
    return f"{fence} {text} {fence}"


def block_from(sql: str, pattern: str, limit: int = 220) -> str:
    """Le SQL à partir de la première ligne qui contient le motif, sur une ligne, tronqué."""
    lines = sql.splitlines()
    for i, line in enumerate(lines):
        if re.search(pattern, line, re.I):
            text = " ".join(" ".join(lines[i:]).split()).rstrip(";").removeprefix("WHERE ").removeprefix("AND ")
            return text if len(text) <= limit else text[:limit] + " …"
    return ""


def line_of(sql: str, pattern: str) -> Optional[str]:
    for line in sql.splitlines():
        if re.search(pattern, line, re.I):
            return line.strip()
    return None


def strip_filters(sql: str) -> str:
    """Le SQL sans commentaires ni filtres de période ou de produit : il ne reste que la partie 'âge'."""
    out = re.sub(r"--[^\n]*", " ", sql)
    out = PERIOD_BETWEEN.sub(" ", out)
    out = PERIOD_CMP.sub(" ", out)
    out = PRODUCT_IN.sub(" ", out)
    return PRODUCT_EQ.sub(" ", out)


def strip_strings(sql: str) -> str:
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def minus_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:                   # 29 février
        return d.replace(year=d.year - years, day=28)


def completed_age(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def birth_bounds(sql: str) -> list:
    """Contraintes sur birth_date ramenées à (texte, 'upper' birth <= X | 'lower' birth > X, X).

    Formes reconnues : birth_date OP 'D' ; birth_date OP date('D', '-N years') ;
    'D' OP birth_date ; 'D' OP date(birth_date, '+N years') (et l'inverse).
    """
    norm = re.sub(r"strftime\(\s*'%Y-%m-%d'\s*,\s*('[^']*'|[\w.]+)\s*\)", r"\1", sql)
    norm = re.sub(r"\bdate\(\s*('[^']*'|[\w.]+)\s*\)", r"\1", norm)
    birth = r"(?:\w+\.)?birth_date\b(?!\s*,)"
    lit = r"(?:'(?P<{0}>\d{{4}}-\d{{2}}-\d{{2}})'|date\(\s*'(?P<{0}m>\d{{4}}-\d{{2}}-\d{{2}})'\s*,\s*'-(?P<{0}n>\d+) years?'\s*\))"
    plus = r"date\(\s*(?:\w+\.)?birth_date\s*,\s*'\+(?P<plus>\d+) years?'\s*\)"
    op = r"\s*(?P<op><=|>=|<|>)\s*"
    flip = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
    patterns = [(birth + op + lit.format("v"), False), (lit.format("v") + op + birth, True),
                (lit.format("v") + op + plus, True), (plus + op + lit.format("v"), False)]
    found = []
    for pattern, flipped in patterns:
        for m in re.finditer(pattern, norm, re.I):
            g = m.groupdict()
            value = date.fromisoformat(g["v"]) if g["v"] else minus_years(date.fromisoformat(g["vm"]), int(g["vn"]))
            value = minus_years(value, int(g.get("plus") or 0))
            o = flip[g["op"]] if flipped else g["op"]
            if o == "<":
                found.append((m.group(0), "upper", value - timedelta(days=1)))
            elif o == "<=":
                found.append((m.group(0), "upper", value))
            elif o == ">":
                found.append((m.group(0), "lower", value))
            else:
                found.append((m.group(0), "lower", value - timedelta(days=1)))
    return found


# ==========================================================================
# 4. Détecteurs : chacun renvoie (cause, justification) ou None
# ==========================================================================

def detect_amount(sql: str, trace: dict) -> list:
    out = []
    if trace["verdict_detail"].startswith("NULL instead of") or (trace["value"] == "" and trace["verdict"] == "incorrect"):
        if not re.search(r"\b(COALESCE|IFNULL)\s*\(", sql, re.I):
            out.append((MONTANT_NULL, f"la requête renvoie NULL (« {trace['verdict_detail']} ») et ne contient ni COALESCE ni IFNULL."))
        else:
            out.append((MONTANT_NULL, f"la requête renvoie NULL (« {trace['verdict_detail']} ») malgré un COALESCE : à relire."))
    for m in re.finditer(r"SUM\s*\(((?:[^()]|\([^()]*\))*)\)", sql, re.I):
        if "price" in m.group(1).lower() and "quantity_product" not in m.group(1).lower():
            out.append((MONTANT_QTE, f"l'agrégat {snippet(m.group(0))} somme le prix unitaire sans le multiplier par quantity_product."))
    return out


def detect_period(sql: str, q: dict) -> list:
    comparisons = [(m.group(0), m.group(1), m.group(2)) for m in PERIOD_CMP.finditer(sql)]
    between = list(PERIOD_BETWEEN.finditer(sql))
    if q["period"] is None:
        if comparisons or between:
            text = between[0].group(0) if between else comparisons[0][0]
            return [(PERIODE, f"filtre de période non demandé par la question : {snippet(text)}.")]
        return []
    start, end = (s.replace(" 00:00:00", "") for s in q["period"])
    out = []
    for m in between:
        out.append((PERIODE, f"{snippet(m.group(0))} : BETWEEN inclut la borne droite, la période doit être [S, E[ (date >= S AND date < E)."))
    lowers = [(t, o, v.replace(" 00:00:00", "")) for t, o, v in comparisons if o in (">=", ">")]
    uppers = [(t, o, v.replace(" 00:00:00", "")) for t, o, v in comparisons if o in ("<", "<=")]
    for t, o, v in lowers:
        if v != start:
            out.append((PERIODE, f"borne gauche {snippet(t)} au lieu de >= '{q['period'][0]}'."))
        elif o == ">":
            out.append((PERIODE, f"{snippet(t)} exclut la borne gauche, qui doit être incluse (>=)."))
    for t, o, v in uppers:
        if v != end:
            out.append((PERIODE, f"borne droite {snippet(t)} au lieu de < '{q['period'][1]}'."))
        elif o == "<=":
            out.append((PERIODE, f"{snippet(t)} inclut la borne droite, qui doit être exclue (<)."))
    if not between and not lowers:
        out.append((PERIODE, f"aucune borne gauche sur la date de commande (attendu date >= '{q['period'][0]}')."))
    if not between and not uppers:
        out.append((PERIODE, f"aucune borne droite sur la date de commande (attendu date < '{q['period'][1]}')."))
    for t, o, v in comparisons:
        if o == "=":
            out.append((PERIODE, f"égalité sur la date de commande {snippet(t)} au lieu d'un intervalle."))
    return out


def detect_products(sql: str, q: dict) -> list:
    found = set()
    texts = []
    for m in PRODUCT_IN.finditer(sql):
        found |= set(re.findall(r"'(\w+)'", m.group(1)))
        texts.append(m.group(0))
    for m in PRODUCT_EQ.finditer(sql):
        found.add(m.group(1))
        texts.append(m.group(0))
    expected = q["products"]
    if expected is None:
        return [(PRODUITS, f"filtre produit non demandé : {snippet(texts[0])}.")] if texts else []
    if not texts:
        return [(PRODUITS, f"aucun filtre sur product_id alors que la question limite aux produits {', '.join(sorted(expected))}.")]
    if found != expected:
        return [(PRODUITS, f"{snippet(' ; '.join(texts))} retient {{{', '.join(sorted(found))}}} au lieu de {{{', '.join(sorted(expected))}}}.")]
    return []


def detect_age(sql: str, q: dict) -> list:
    """Détecteurs d'âge, du plus spécifique au plus général. Plusieurs peuvent se déclencher."""
    part = strip_filters(sql)
    if q["age"] is None:
        if re.search(r"birth_date", part, re.I):
            return [(AGE, f"condition sur birth_date alors que la question ne porte pas sur l'âge : {snippet(line_of(part, 'birth_date'))}.")]
        return []
    if not re.search(r"birth_date", part, re.I):
        return [(AGE, "aucune condition sur birth_date : le filtre d'âge est absent.")]
    out = []
    ref = q["ref_date"]
    age = q["age"]

    # a. Date de référence confondue avec la date de commande.
    if ref is not None:
        used = next((m.group(0) for m in YEAR_DIFF.finditer(part) if re.search(ORDER_DATE, m.group(0))), None)
        used = used or line_of(part, ORDER_DATE)
        if used:
            out.append((AGE_CONFUSION, f"l'âge est calculé à partir de la date de commande ({snippet(used)}) "
                                       f"alors que la question fixe la date de référence {ref.isoformat()}."))

    # c. Année comparée à une date complète.
    m = re.search(r"strftime\(\s*'%Y'\s*,\s*(?:[^()]|\([^()]*\))*\)\s*(<=|>=|<|>|=)\s*'\d{4}-\d{2}-\d{2}'", part, re.I)
    if m:
        out.append((AGE, f"{snippet(m.group(0))} compare une année ('YYYY') à une date complète : en texte, la condition est vraie "
                         f"pour presque toutes les naissances, l'âge n'est plus contraint."))

    # d. Égalité stricte : seuls les clients dont c'est l'anniversaire ce jour-là.
    if not re.search(r"[<>]", strip_strings(part)) and re.search(r"birth_date[^;]*=|=[^;]*birth_date", part, re.I):
        out.append((AGE, f"la condition d'âge est une égalité ({snippet(block_from(part, r'birth_date'))}) : elle ne retient que les clients nés exactement "
                         f"{age} ans avant le jour J, pas tous ceux qui ont {age} ans révolus."))

    # e. Année de naissance codée en dur + comparaison mois-jour : le jour anniversaire mal placé.
    if ref is not None:
        mmdd = f"{ref.month:02d}-?{ref.day:02d}"
        pairs = [(m.group(0), m.group("op"), int(m.group("y"))) for m in re.finditer(
            r"(?P<op><=|>=|<|>)\s*'" + mmdd + r"'\s*\)?\s*AND\s*strftime\(\s*'%Y'\s*,\s*(?:\w+\.)?birth_date\s*\)\s*=\s*'(?P<y>\d{4})'",
            part, re.I)]
        for text, op, year in pairs:
            ok = (year == ref.year - age and op == "<=") or (year == ref.year - age - 1 and op == ">")
            if not ok:
                attendu = "<=" if year == ref.year - age else ">"
                born = f"{year}-{ref.month:02d}-{ref.day:02d}"
                out.append((AGE, f"{snippet(text)} : pour l'année de naissance {year} il faut mois-jour {attendu} "
                                 f"'{ref.month:02d}-{ref.day:02d}' ; le jour anniversaire est rangé du mauvais côté "
                                 f"(un client né le {born} a {ref.year - year} ans révolus le {ref.isoformat()})."))

    # f. Différence d'années ou année de naissance + N.
    for m in YEAR_DIFF.finditer(part):
        first, second = m.group(1), m.group(2)
        detail = f"l'âge est calculé par différence d'années {snippet(m.group(0))}"
        if "birth_date" in first.lower() and "birth_date" not in second.lower():
            detail += " ; la soustraction est inversée (naissance − référence), le résultat est négatif et ne vaut jamais " + str(age)
        else:
            branches = {int(found[-1]) for found in re.findall(YEAR_DIFF.pattern + r"\s*\)*\s*=\s*(\d+)", part, re.I)}
            if branches and age + 1 not in branches:
                detail += (f" ; aucune branche ne traite la différence {age + 1} avant l'anniversaire "
                           f"(clients de {age} ans révolus nés l'année précédente)")
            for b in sorted(branches - {age, age + 1}):
                detail += (f" ; la branche « = {b} » retient des clients de {b - 1} ou {b} ans : "
                           f"il fallait « = {age + 1} » avant l'anniversaire")
        out.append((AGE_DIFF, detail + "."))
        break
    for m in YEAR_ARITH.finditer(part):
        detail = f"{snippet(m.group(0))} : seule l'année de naissance compte (différence d'années)"
        if m.group(3) in ("<", "<="):
            detail += f" ; l'inégalité accepte aussi tous les clients plus âgés que {age} ans"
        out.append((AGE_DIFF, detail + "."))
        break
    if not any(c == AGE_DIFF for c, _ in out):
        m = re.search(r"strftime\(\s*'%Y'\s*,\s*(?:\w+\.)?birth_date\s*\)\s*=\s*'\d{4}'", part, re.I)
        if m and not out:
            out.append((AGE_DIFF, f"{snippet(m.group(0))} : l'âge est déduit de l'année de naissance seule."))

    # g. Bornes sur birth_date (date de référence) différentes de ]D-(N+1) ans, D-N ans].
    if ref is not None:
        upper_ok, lower_ok = minus_years(ref, age), minus_years(ref, age + 1)
        wrong = []
        for text, kind, value in birth_bounds(part):
            if kind == "upper" and value != upper_ok:
                wrong.append(f"{snippet(text)} ⇒ âge minimal accepté {completed_age(value, ref)}")
            if kind == "lower" and value != lower_ok:
                wrong.append(f"{snippet(text)} ⇒ âge maximal accepté {completed_age(value + timedelta(days=1), ref)}")
        if wrong:
            out.append((AGE, "bornes de naissance incorrectes : " + " ; ".join(wrong)
                             + f" (attendu birth_date ∈ ]{lower_ok.isoformat()}, {upper_ok.isoformat()}], soit {age} ans révolus le {ref.isoformat()})."))

    # b. Repli : date de référence absente du calcul d'âge (des bornes précalculées comme '2001-09-25' sont
    #    légitimes, d'où ce test en dernier).
    if not out and ref is not None and ref.isoformat() not in part and str(ref.year) not in part and "'now'" not in part.lower():
        out.append((AGE, f"ni la date de référence {ref.isoformat()} ni l'année {ref.year} n'apparaissent dans le calcul d'âge "
                         f"({snippet(block_from(re.sub(r'--[^\n]*', ' ', sql), 'birth_date'))}) : la condition ne dépend que de la date de naissance."))

    # h. Seuls le mois et le jour de naissance sont contraints.
    uses_year = re.search(r"'%Y|SUBSTR\([^()]*birth_date[^()]*,\s*1\s*,|years?'|birth_date\s*(<=|>=|<|>)|(<=|>=|<|>)\s*(?:\w+\.)?birth_date", part, re.I)
    if not out and not uses_year:
        expr = line_of(part, r"%m|%d|SUBSTR") or line_of(part, "birth_date")
        out.append((AGE, f"la condition ne porte que sur le mois et le jour de naissance ({snippet(expr)}) : aucune contrainte d'année, "
                         f"l'âge n'est pas calculé."))

    # Indices secondaires de format.
    for m in re.finditer(r"SUBSTR\(\s*(?:\w+\.)?birth_date\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", part, re.I):
        if (int(m.group(1)), int(m.group(2))) not in {(1, 4), (6, 2), (9, 2), (6, 5), (1, 10)}:
            out.append((AGE, f"{snippet(m.group(0))} : positions incohérentes avec le format 'YYYY-MM-DD' (mois en 6, jour en 9)."))
            break
    m = re.search(r"SUBSTR\([^()]*,\s*6\s*,\s*2\s*\)\s*\|\|\s*SUBSTR\([^()]*,\s*9\s*,\s*2\s*\)\s*(<=|>=|<|>|=)\s*'\d\d-\d\d'", part, re.I)
    if m:
        out.append((AGE, f"{snippet(m.group(0))} compare 'MMJJ' (sans tiret) à 'MM-JJ' : comparaison de textes de formats différents."))
    return out


def unbalanced(sql: str) -> Optional[str]:
    bare = strip_strings(sql)
    opened, closed = bare.count("("), bare.count(")")
    if opened != closed:
        return f"{opened} parenthèses ouvrantes pour {closed} fermantes"
    return None


# ==========================================================================
# 5. Une cause par cellule
# ==========================================================================

def tokens(trace: dict) -> Optional[int]:
    try:
        return int(float(trace.get("tokens_completion") or ""))
    except ValueError:
        return None


def diagnose(trace: dict, q: dict, current_reference: Optional[str]) -> tuple:
    """Renvoie (cause, justification, autres anomalies)."""
    sql, verdict = trace["sql"], trace["verdict"]
    detail, error = trace["verdict_detail"], trace["error"]
    status = int(trace["http_status"]) if trace["http_status"].isdigit() else None
    n_tokens = tokens(trace)
    semantic = (detect_amount(sql, trace) + detect_age(sql, q) + detect_period(sql, q) + detect_products(sql, q)) if sql else []
    others = [f"{c} — {j}" for c, j in semantic]

    if verdict == "access_error" or status in ACCESS_STATUSES:
        return ACCES, f"statut HTTP {trace['http_status'] or '?'} ; erreur : « {error or detail} ».", others
    if n_tokens is not None and n_tokens >= MAX_OUTPUT_TOKENS:
        return TRONQUEE, (f"tokens_completion = {n_tokens} ≥ plafond {MAX_OUTPUT_TOKENS} (raisonnement compris, "
                          f"tokens_reasoning = {trace.get('tokens_reasoning') or '?'}) : la réponse a été coupée."), others
    if verdict == "not_executed":
        return NON_EXECUTE, f"aucune requête exécutée ; statut HTTP {trace['http_status'] or '-'} ; erreur : « {error or detail or 'vide'} ».", others
    if verdict == "sql_rejected":
        reason = detail.split(" ", 1)[0]
        if reason == "not_select" and sql.lstrip().startswith("```"):
            why = ("le texte soumis commence par une clôture ```sql jamais refermée : l'extracteur ne la retire que si "
                   "elle est fermée, donc l'instruction ne commence pas par SELECT")
            if n_tokens is not None:
                why += f" (tokens_completion = {n_tokens}, loin du plafond {MAX_OUTPUT_TOKENS} : pas une troncature)"
            return SQL_REJETE, why + " (raison du bac à sable : `not_select`).", others
        statements = [s for s in strip_strings(sql).split(";") if s.strip()]
        if len(statements) > 1:
            return SQL_REJETE, f"{len(statements)} instructions séparées par « ; » ; le bac à sable n'en accepte qu'une (« {detail} »).", others
        return SQL_REJETE, f"refus du bac à sable : « {detail} ».", others
    if verdict == "sql_invalid":
        why = f"erreur SQLite : « {detail} »"
        paren = unbalanced(sql)
        if paren:
            why += f" ; le SQL compte {paren}"
            line = next((line.strip() for line in sql.splitlines() if unbalanced(line)), None)
            if line:
                why += f", déséquilibre sur la ligne {snippet(line)}"
        return SQL_INVALIDE, why + ".", others
    if verdict == "":
        return A_VERIFIER, f"cellule non notée (« {detail} ») : pas de référence pour comparer.", others

    # Verdict "incorrect".
    if current_reference is not None and trace["reference"] != current_reference:
        why = (f"la référence enregistrée dans la trace ({trace['reference']}) diffère de reference-td1.csv "
               f"({current_reference})")
        if trace["value"] == current_reference:
            why += " ; la valeur du modèle est égale à la référence actuelle : le verdict de la trace est probablement obsolète"
        return A_VERIFIER, why + ".", others
    if semantic:
        cause, why = semantic[0]
        return cause, why, others[1:]
    return A_VERIFIER, "aucun élément du SQL ne permet d'identifier l'écart à la référence.", others


# ==========================================================================
# 6. Sorties : notes/echecs-td1.md et récapitulatif
# ==========================================================================

def model_name(trace: dict) -> str:
    return f"{trace['provider']}:{trace['model_requested']}"


def section(trace: dict, q: dict, cause: str, why: str, others: list, current_reference: Optional[str]) -> str:
    title = f"## {model_name(trace)} – {trace['case_id']}"
    if trace.get("nature", "real") != "real":
        title += f" ({trace['nature']})"
    lines = [title, "",
             f"- Question ({family(q['type'])}) : {q['question']}",
             f"- Modèle : `{model_name(trace)}` (renvoyé : `{trace.get('model_returned') or '-'}`)",
             f"- Verdict : `{trace['verdict'] or 'non noté'}` — {md_inline(trace['verdict_detail'])}",
             f"- HTTP : {trace['http_status'] or '-'} ; erreur : {md_inline(trace['error'])}",
             f"- Valeur : {trace['value'] or '-'} ; référence : {trace['reference'] or '-'}"
             + (f" (reference-td1.csv : {current_reference})" if current_reference not in (None, trace["reference"]) else ""),
             f"- Tokens (sortie / raisonnement) : {trace.get('tokens_completion') or '-'} / {trace.get('tokens_reasoning') or '-'}",
             "", "````sql", trace["sql"].strip() or "-- aucun SQL", "````", "",
             f"**Cause proposée : {cause}.**", "", f"Justification : {why}"]
    if others:
        lines += ["", "Autres anomalies relevées :"] + [f"- {o}" for o in others]
    return "\n".join(lines) + "\n"


def recap(latest: dict, questions: dict, failures: list) -> str:
    per_model = defaultdict(lambda: [0, 0])
    for trace in latest.values():
        row = per_model[(trace.get("nature", "real"), model_name(trace))]
        row[0] += trace["verdict"] == "correct"
        row[1] += 1
    by_family = Counter(family(questions[t["case_id"]]["type"]) for t, _ in failures)
    totals = Counter(family(q["type"]) for q in questions.values())
    by_cause = Counter(cause for _, cause in failures)
    width = max(len(m) for _, m in per_model) + 2
    lines = ["Correct par modèle (dernière tentative de chaque cellule) :"]
    for (nature, model), (ok, n) in sorted(per_model.items(), key=lambda kv: (-kv[1][0], kv[0])):
        lines.append(f"  {model:{width}} {ok:>2}/{n}" + (f"  [{nature}]" if nature != "real" else ""))
    n_models = len(per_model)
    lines += ["", f"Échecs par famille de questions ({len(failures)} au total, {n_models} modèles) :"]
    for fam in FAMILY_ORDER:
        lines.append(f"  {fam:32} {by_family.get(fam, 0):>3} / {totals.get(fam, 0) * n_models} cellules")
    lines += ["", "Échecs par cause proposée :"]
    for cause, n in by_cause.most_common():
        lines.append(f"  {cause:72} {n:>3}")
    return "\n".join(lines)


def main() -> int:
    # La console Windows est en cp1252 : on force l'UTF-8 pour les accents et les flèches
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("traces", nargs="*", type=Path, help="fichiers de traces (.csv ou .jsonl), dans l'ordre chronologique")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    paths = args.traces or DEFAULT_TRACES
    if not paths:
        print("Aucun fichier de traces.", file=sys.stderr)
        return 1

    questions = load_questions(QUESTIONS)
    references = load_references(REFERENCES)
    latest = latest_by_cell(paths)
    failing = sorted((t for t in latest.values() if t["verdict"] != "correct"),
                     key=lambda t: (model_name(t), t["case_id"]))

    sections, failures = [], []
    for trace in failing:
        q = questions[trace["case_id"]]
        q_info = {**parse_question(q["question"]), **q}
        current = references.get(trace["case_id"])
        cause, why, others = diagnose(trace, q_info, current)
        failures.append((trace, cause))
        sections.append(section(trace, q, cause, why, others, current))
        print(f"\n=== {model_name(trace)} – {trace['case_id']}  [{trace['verdict'] or 'non noté'}] {' '.join(trace['verdict_detail'].split())}")
        print(f"    http={trace['http_status'] or '-'} erreur={trace['error'] or '-'} valeur={trace['value'] or '-'} référence={trace['reference'] or '-'}")
        print("    " + (trace["sql"].strip() or "-- aucun SQL").replace("\n", "\n    "))
        print(f"  → cause : {cause}\n    {why}")

    summary = recap(latest, questions, failures)
    header = ["# Échecs du TD 1 — analyse cellule par cellule", "",
              "Généré par `analyze_failures.py` à partir de : " + ", ".join(f"`{p.name}`" for p in paths) + ".",
              "Pour chaque cellule, seule la dernière tentative est retenue (même règle que `taux_par_modele`).",
              "Une seule cause est proposée par cellule ; elle s'appuie sur un élément précis du SQL ou de l'erreur.",
              "« à vérifier » signifie que le SQL ne permet pas de conclure.", "",
              "```text", summary, "```", ""]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(header) + "\n" + "\n".join(sections), encoding="utf-8")

    print(f"\n{len(failing)} cellule(s) en échec écrites dans {args.out.relative_to(HERE) if args.out.is_relative_to(HERE) else args.out}\n")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
