import csv
import json
import re
from pathlib import Path

csv_to_schema_map = {
    '\ufeff"Type"': 'relationship_type',
    'Parameter A Name': 'parameter_1_id',
    'Parameter B Name': 'parameter_2_id',
    'Source': 'details',
    'Witness Name': 'witness',
    'Variant': 'variant',
}

variant_map = {
    'Relative': 'relative',
    'Monotonic': 'monotonic',
    'p-Monotonic': 'p_monotonic',
}

type_map = {
    'A>=B': 'larger',
    'A>=cB': 'larger_c',
    'A=B': 'equivalence',
    'A>=c\log B': 'log',
    'A>=c\sqrt{B}': 'sqrt',
    'A>=cB/\log n': 'inv_log',
}

def slugify(name):
    name = name.lower().replace(' ', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

schema_path = Path(__file__).parent / 'schema.json'
csv_path = Path(__file__).parent / 'Relationships.csv'
out_dir = Path(__file__).parent

with open(schema_path) as f:
    schema = json.load(f)

columns = [col for col in schema['columns'] if col['name'] != 'id']

with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for idx, row in enumerate(reader, 1):
        entry = {}
        entry['id'] = idx
        p1 = None
        p1_full = None
        p2 = None
        p2_full = None
        for col in columns:
            schema_field = col['name']
            col_type = col.get('type', 'string')
            csv_field = None
            for k, v in csv_to_schema_map.items():
                if v == schema_field:
                    csv_field = k
                    break
            value = row.get(csv_field, '') if csv_field else ''
            if schema_field == 'parameter_1_id' and value:
                p1_full = value
                value = slugify(value)
                p1 = value
                value = '#parameters/' + value
            if schema_field == 'parameter_2_id' and value:
                p2_full = value
                value = slugify(value)
                p2 = value
                value = '#parameters/' + value
            if schema_field == 'witness' and value:
                value = slugify(value)
                value = '#classes/' + value
            if schema_field == 'relationship_type' and value:
                value = type_map.get(value, value)
            if schema_field == 'variant' and value:
                value = variant_map.get(value, value)
            if col_type == 'boolean':
                entry[schema_field] = value.strip().upper() == 'TRUE'
            elif value:
                entry[schema_field] = value
        # Generate short_name from Type and Parameter A
        entry['short_name'] = f"{p1}_{p2}"
        entry['name'] = f"{p1_full} / {p2_full}"
        filename = f"{idx:03d}_{entry['short_name']}.json"
        with open(out_dir / filename, 'w') as out:
            json.dump(entry, out, indent=2)

print('Relationship JSON files created.')
