"""
Export UserContract to a JSON Schema file, the committed contract artifact.

Run from the project root (so `framework` is importable):
    python -m framework.contract.export_schema

Re-run it whenever UserContract changes, then review the diff on
schemas/user_v1.json in your PR. That diff IS the contract change.
"""

import json
from pathlib import Path

from framework.contract.user_contract import UserContract

SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "user_v1.json"

def export_schema() -> Path:
    schema = UserContract.model_json_schema()#convert Python class into a JSON Schema
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys + indent keep the file stable, so git diffs show only real changes
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    return SCHEMA_PATH


if __name__ == "__main__":
    print(f"Schema written to {export_schema()}")