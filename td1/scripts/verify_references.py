"""Execute reference SQL read-only; cross-check independently on CSV rows.

Run from any directory. --write fills only blank reference rows, or accepts
already identical rows. No model calls, no external dependencies.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def csv_rows(name):
    with (ROOT / 'data' / name).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'data/manifest.json').read_text())
    db = ROOT / 'data/boutique.sqlite'
    for path, expected in [(db, manifest['sqlite_file_sha256'])] + [
        (ROOT / 'data' / name, expected) for name, expected in manifest['csv_sha256'].items()
    ]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f'Fingerprint mismatch: {path.name}')
    questions = json.loads((ROOT / 'questions-td1.json').read_text())['questions']
    sql_text = (ROOT / 'scripts/reference_queries.sql').read_text()
    queries = dict(re.findall(r'^-- (C\d{2})\n([^\n]+)', sql_text, re.M))
    wanted = {f'C{i:02}' for i in range(1, 21)}
    if set(queries) != wanted or {q['id'] for q in questions} != wanted:
        raise SystemExit('Expected exactly C01-C20 in SQL and questions')

    # Independent CSV implementation: completed age is calculated with Python
    # calendar arithmetic, not the SQL birth-date predicates.
    prices = {r['product_id']: int(r['price']) for r in csv_rows('product.csv')}
    births = {r['customer_id']: date.fromisoformat(r['birth_date']) for r in csv_rows('customers.csv')}
    orders = csv_rows('orders.csv')
    def age(birth, when):
        return when.year - birth.year - ((when.month, when.day) < (birth.month, birth.day))
    def period(when, start, end):
        return datetime.fromisoformat(start) <= when < datetime.fromisoformat(end)
    totals = {key: 0 for key in wanted}
    counts = {key: 0 for key in wanted}
    for order in orders:
        when = datetime.fromisoformat(order['date'])
        birth = births[order['customer_id']]
        product = order['product_id']
        abc = product in {'a', 'b', 'c'}
        a25 = age(birth, date(2026, 9, 25)) == 25
        at_order = age(birth, when.date()) == 25
        spring = period(when, '2026-03-01', '2026-06-01')
        first_half = period(when, '2026-01-01', '2026-07-01')
        included = {
            'C01': spring,
            'C02': a25,
            'C03': abc and first_half,
            'C04': period(when, '2026-01-01', '2026-10-01'),
            'C05': period(when, '2026-06-01', '2026-06-02'),
            'C06': period(when, '2025-01-01', '2026-01-01'),
            'C07': period(when, '2026-05-31', '2026-06-01'),
            'C08': age(birth, date(2026, 9, 24)) == 25,
            'C09': age(birth, date(2026, 9, 26)) == 25,
            'C10': at_order,
            'C11': age(birth, date(2026, 12, 1)) == 25,
            'C12': abc,
            'C13': product in {'a', 'c'} and period(when, '2026-04-01', '2026-05-01'),
            'C14': abc and period(when, '2026-10-01', '2026-12-01'),
            'C15': spring and a25,
            'C16': abc and a25,
            'C17': first_half and abc and a25,
            'C18': period(when, '2026-05-01', '2026-06-01') and at_order,
            'C19': period(when, '2026-09-01', '2026-10-01') and product == 'd' and a25,
            'C20': period(when, '2026-06-01', '2026-09-01'),
        }
        for key, include in included.items():
            if include:
                totals[key] += int(order['quantity_product']) * prices[product]
                counts[key] += 1
    calculated, evidence = [], []
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only = ON')
        for key in sorted(wanted):
            cursor = connection.execute(queries[key])
            result = cursor.fetchall()
            if [c[0] for c in cursor.description] != ['revenue_cents'] or len(result) != 1:
                raise SystemExit(f'{key}: expected one row and one column revenue_cents')
            amount = result[0][0]
            if type(amount) is not int or amount != totals[key]:
                raise SystemExit(f'{key}: SQL {amount} differs from CSV {totals[key]}')
            calculated.append({'case_id': key, 'sql': queries[key], 'revenue_cents': str(amount)})
            evidence.append({'case_id': key, 'sql_revenue_cents': amount,
                             'csv_revenue_cents': totals[key], 'csv_matching_lines': counts[key],
                             'match': 'true'})
            print(f'{key}: SQL={amount} CSV={totals[key]} OK ({counts[key]} lines)')
    path = ROOT / 'reference-td1.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        existing = list(csv.DictReader(stream))
    if len(existing) != 20 or {r['case_id'] for r in existing} != wanted:
        raise SystemExit('Existing reference file must contain exactly C01-C20')
    by_key = {r['case_id']: r for r in calculated}
    for row in existing:
        for field in ('sql', 'revenue_cents'):
            if row[field].strip() and row[field].strip() != by_key[row['case_id']][field]:
                raise SystemExit(f"Existing {row['case_id']} {field} differs: preserve and review manually")
    if args.write:
        # All computations and existing-value checks finish before either output is written.
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=['case_id', 'sql', 'revenue_cents'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(calculated)
        path.write_text(output.getvalue(), encoding='utf-8')
        with (ROOT / 'reports/reference-verification.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(evidence[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(evidence)
        print('Reference file and verification evidence written.')
    elif existing != calculated:
        raise SystemExit('Reference file incomplete: run with --write to fill blank fields')
    print('20/20 SQL and CSV computations agree. Human cross-check and instructor validation pending.')
    print('Run UTC:', datetime.now(timezone.utc).isoformat())

if __name__ == '__main__':
    main()
