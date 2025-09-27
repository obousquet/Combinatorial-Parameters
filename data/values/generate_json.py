import csv
import json
import re
from pathlib import Path

csv_to_schema_map = {
    'Parameter Name': 'parameter_id',
    'Class Name': 'class_id',
    'Value': 'value',
    'Value class': 'value_class',
}

def slugify(name):
    name = name.lower().replace(' ', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

schema_path = Path(__file__).parent / 'schema.json'
csv_path = Path(__file__).parent / 'Values.csv'
out_dir = Path(__file__).parent

with open(schema_path) as f:
    schema = json.load(f)

columns = [col for col in schema['columns'] if col['name'] != 'id']

with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for idx, row in enumerate(reader, 1):
        entry = {}
        entry['id'] = idx
        param = None
        param_full = None
        class_name = None
        class_name_full = None
        for col in columns:
            schema_field = col['name']
            col_type = col.get('type', 'string')
            csv_field = None
            for k, v in csv_to_schema_map.items():
                if v == schema_field:
                    csv_field = k
                    break
            value = row.get(csv_field, '') if csv_field else ''
            # String replacements for value and comments
            if schema_field in ['value', 'comments']:
                value = value.replace('\\H', '\\mathcal{H}')
                value = value.replace('\\bydef', ':=')
                value = value.replace('\\X', '\\mathcal{X}')
                value = re.sub(r'\\abs\*{([^}]*)}', r'|\1|', value)
                value = re.sub(r'\\set\*{([^}]*)}', r'\\{\1\\}', value)
                value = re.sub(r'\{\\em ([^}]*)}', r'**\1**', value)
                value = re.sub(r'\\\[([^\]]*)\\\]', r'$$\1$$', value)
                value = re.sub(r'\\H(_\{[^}]+\})', r'\\mathcal{H}\1', value)
            if schema_field == 'parameter_id' and value:
                param_full = value
                value = slugify(value)
                param = value
                value = '#parameters/' + value
            if schema_field == 'class_id' and value:
                class_name_full = value
                value = slugify(value)
                class_name = value
                value = '#classes/' + value
            # Handle enum mapping
            if col_type == 'enum':
                enum_map = {e['display_name'].lower(): e['value'] for e in col.get('enum', [])}
                value_lower = value.strip().lower()
                entry[schema_field] = enum_map.get(value_lower, value)
            # Handle boolean conversion
            elif col_type == 'boolean':
                entry[schema_field] = value.strip().upper() == 'TRUE'
            else:
                entry[schema_field] = value
        # Generate short_name from value and class_id
        entry['short_name'] = f"{param}_{class_name}"
        entry['name'] = f"{param_full} of {class_name_full}"
        filename = f"{idx:03d}_{entry['short_name']}.json"
        with open(out_dir / filename, 'w') as out:
            json.dump(entry, out, indent=2)

print('Value JSON files created.')
