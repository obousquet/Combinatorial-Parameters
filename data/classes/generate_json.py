import csv
import json
import re
from pathlib import Path

csv_to_schema_map = {
    'Name': 'name',
    'Description': 'definition',
    'Symbol': 'symbol',
}

def slugify(name):
    name = name.lower().replace(' ', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

schema_path = Path(__file__).parent / 'schema.json'
csv_path = Path(__file__).parent / 'Classes.csv'
out_dir = Path(__file__).parent

with open(schema_path) as f:
    schema = json.load(f)

columns = [col for col in schema['columns'] if col['name'] != 'id']

with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for idx, row in enumerate(reader, 1):
        entry = {}
        entry['id'] = idx
        for col in columns:
            schema_field = col['name']
            col_type = col.get('type', 'string')
            csv_field = None
            for k, v in csv_to_schema_map.items():
                if v == schema_field:
                    csv_field = k
                    break
            value = row.get(csv_field, '') if csv_field else ''
            # String replacements for definition and comments
            if schema_field in ['definition', 'comments']:
                value = value.replace('\\H', '\\mathcal{H}')
                value = value.replace('\\bydef', ':=')
                value = value.replace('\\X', '\\mathcal{X}')
                value = re.sub(r'\\abs\*{([^}]*)}', r'|\1|', value)
                value = re.sub(r'\\set\*{([^}]*)}', r'\\{\1\\}', value)
                value = re.sub(r'\{\\em ([^}]*)}', r'**\1**', value)
                value = value.replace('\\[', '$$').replace('\\]', '$$')
                value = re.sub(r'\\H(_\{[^}]+\})', r'\\mathcal{H}\1', value)
            if schema_field == 'symbol' and value:
                # Remove $...$ if present
                value = re.sub(r'^\$(.*)\$$', r'\1', value)
            if value:
                entry[schema_field] = value
        entry['short_name'] = slugify(row.get('Name', ''))
        filename = f"{idx:03d}_{entry['short_name']}.json"
        with open(out_dir / filename, 'w') as out:
            json.dump(entry, out, indent=2)

print('Class JSON files created.')
