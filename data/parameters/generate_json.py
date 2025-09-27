import csv
import json
import re
from pathlib import Path

csv_to_schema_map = {
    'Name': 'name',
    'Symbol': 'symbol',
    'Description': 'description',
    'Definition': 'definition',
    'Bit-flipping stable': 'symmetric',
    'Monotonic': 'monotonic',
    'p-Monotonic': 'p_monotonic',
    'Doubly monotonic': 'doubly_monotonic',
    'Strictly monotonic': 'strictly_monotonic',
    'Notes': 'comments',
    'References': 'comments',  # If you want to merge references into comments
    'Category': 'category',
}

def slugify(name):
    # Lowercase, replace spaces with underscores, remove non-alphanum except underscores
    name = name.lower().replace(' ', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

schema_path = Path(__file__).parent / 'schema.json'
csv_path = Path(__file__).parent / 'Parameters.csv'
out_dir = Path(__file__).parent

# Load schema
with open(schema_path) as f:
    schema = json.load(f)

# Get column info (ignore 'id')
columns = [col for col in schema['columns'] if col['name'] != 'id']

# Read CSV
with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for idx, row in enumerate(reader, 1):
        # Build entry using mapping and schema
        entry = {}
        entry['id'] = idx
        for col in columns:
            schema_field = col['name']
            col_type = col.get('type', 'string')
            # Find corresponding CSV column
            csv_field = None
            for k, v in csv_to_schema_map.items():
                if v == schema_field:
                    csv_field = k
                    break
            value = row.get(csv_field, '') if csv_field else ''
            # String replacements for definition and comments
            if schema_field in ['definition', 'comments']:
                # Replace \H_{...} with \mathcal{H}_{...}
                value = re.sub(r'\\H_\{([^}]+)\}', r'\\mathcal{H}\\_{\1}', value)
                value = value.replace('\\H', '\\mathcal{H}')
                value = value.replace('\\bydef', ':=')
                value = value.replace('\\X', '\\mathcal{X}')
                # Replace \set*{...} with \{...\}
                value = re.sub(r'\\set\*{([^}]*)}', r'\\{\1\\}', value)
                # Replace \abs*{...} with |...|
                value = re.sub(r'\\abs\*{([^}]*)}', r'|\1|', value)
                # Replace {\em ...} with **...**
                value = re.sub(r'\{\\em ([^}]*)}', r'**\1**', value)
                # Replace \emph{...} with **...**
                value = re.sub(r'\\emph{([^}]*)}', r'**\1**', value)
                # Replace \[...\] with $$...$$
                value = value.replace('\\[', '$$').replace('\\]', '$$')
            # Handle enum mapping
            if col_type == 'enum':
                enum_map = {e['display_name'].lower(): e['value'] for e in col.get('enum', [])}
                value_lower = value.strip().lower()
                entry[schema_field] = enum_map.get(value_lower, value)
            # Handle boolean conversion
            elif col_type == 'boolean':
                entry[schema_field] = value.strip().upper() == 'TRUE'
            elif value:
                # We only populate if there is a value.
                entry[schema_field] = value
        # Generate short_name from Name
        entry['short_name'] = slugify(row.get('Name', ''))
        # Write JSON file
        filename = f"{idx:03d}_{entry['short_name']}.json"
        with open(out_dir / filename, 'w') as out:
            json.dump(entry, out, indent=2)

print('Parameter JSON files created.')
