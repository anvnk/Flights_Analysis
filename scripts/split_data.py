import argparse
from collections import Counter
import csv
from datetime import date
import hashlib
import json
from pathlib import Path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    source = root / 'data/raw/flights_data.csv'
    original_hash = sha256(source)
    with source.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    for row in rows:
        date.fromisoformat(row['searchDate'])
    # Stable sort keeps the original order within each observation date.
    rows.sort(key=lambda r: r['searchDate'])
    counts = Counter(r['searchDate'] for r in rows)
    dates = sorted(counts)
    if len(dates) < 4:
        raise ValueError('At least four distinct search dates are required.')
    cumulative = []
    running = 0
    for day in dates:
        running += counts[day]
        cumulative.append(running)
    n = len(rows)
    # Leave at least one complete date group for each following partition.
    first = min(range(len(dates)-3), key=lambda i: (abs(cumulative[i]-0.6*n), i))
    initial_n = cumulative[first]
    remaining = n-initial_n
    second = min(range(first+1, len(dates)-2),
                 key=lambda i: (abs(cumulative[i]-(initial_n+remaining/3)), i))
    third = min(range(second+1, len(dates)-1),
                key=lambda i: (abs(cumulative[i]-(initial_n+2*remaining/3)), i))
    boundaries = [0, cumulative[first], cumulative[second], cumulative[third], n]
    paths = ['data/initial/initial.csv', 'data/incoming/batch_01.csv',
             'data/incoming/batch_02.csv', 'data/incoming/batch_03.csv']
    report = {'source': 'data/raw/flights_data.csv', 'source_sha256': original_hash,
              'total_rows': n, 'date_column': 'searchDate',
              'method': 'Chronological, with complete searchDate groups; approximately 60% initial and 3 batches',
              'partitions': []}
    restored = []
    previous_max = None
    for i, relative in enumerate(paths):
        part = rows[boundaries[i]:boundaries[i+1]]
        output = root / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(part)
        with output.open(encoding='utf-8-sig', newline='') as f:
            saved = list(csv.DictReader(f))
        assert saved == part, 'Saved values differ from source.'
        assert saved and (previous_max is None or previous_max < saved[0]['searchDate'])
        previous_max = saved[-1]['searchDate']
        restored.extend(saved)
        report['partitions'].append({'file': relative, 'rows': len(saved),
                                     'percent': round(len(saved)/n*100, 4),
                                     'searchDate_min': saved[0]['searchDate'],
                                     'searchDate_max': saved[-1]['searchDate'],
                                     'sha256': sha256(output)})
    assert restored == rows, 'Partitions must preserve all source records exactly once.'
    assert sha256(source) == original_hash, 'Raw input changed.'
    report['validation'] = {'all_rows_preserved': True, 'values_preserved': True,
                            'dates_do_not_overlap': True, 'raw_unchanged': True}
    (root / 'split_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
