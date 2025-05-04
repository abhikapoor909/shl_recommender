from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE_PATH = BASE_DIR / "shlproducts.csv"

LLM_MODEL_NAME = "llama3-8b-8192"
COHERE_EMBEDDING_MODEL_NAME = "embed-english-v3.0"

NUM_DOCS_TO_RETRIEVE = 20
NUM_DOCS_TO_RETURN = 10
JOB_ROLE_REPETITION = 9

CSV_TO_JSON_MAP = {
    "Relative_URL": "url",
    "Adaptive/IRT": "adaptive_support",
    "description": "description",
    "Assessment Length": "duration",
    "Remote Testing": "remote_support",
    "Test Type": "test_type",
    "Assessment Name": "assessment_name",
}

EXPECTED_CSV_COLS = list(CSV_TO_JSON_MAP.keys())
CONTENT_CSV_COLS = ["Assessment Name", "description", "Test Type"]
METADATA_CSV_COLS = EXPECTED_CSV_COLS

TARGET_JSON_FIELDS = [
    "url",
    "adaptive_support",
    "description",
    "duration",
    "remote_support",
    "test_type",
    "assessment_name",
]

TARGET_FIELD_TO_METADATA_KEY = {
    json_field: csv_col.lower().replace(' ', '_').replace('/', '_')
    for csv_col, json_field in CSV_TO_JSON_MAP.items()
    if json_field in TARGET_JSON_FIELDS
}
TARGET_FIELD_TO_METADATA_KEY["row_index"] = "row_index"

for field in TARGET_JSON_FIELDS:
    if field not in TARGET_FIELD_TO_METADATA_KEY and field != 'assessment_name':
        original_csv_col = [csv_col for csv_col, json_val in CSV_TO_JSON_MAP.items() if json_val == field]
        if not original_csv_col:
            raise ValueError(f"Configuration Error: Target JSON field '{field}' listed in "
                             f"TARGET_JSON_FIELDS but was not found as a value in CSV_TO_JSON_MAP.")
        else:
            raise ValueError(f"Configuration Error: Target JSON field '{field}' (from CSV column '{original_csv_col[0]}') "
                             f"listed in TARGET_JSON_FIELDS but failed to generate a key in TARGET_FIELD_TO_METADATA_KEY.")

if 'assessment_name' in TARGET_JSON_FIELDS and 'assessment_name' not in TARGET_FIELD_TO_METADATA_KEY:
    assessment_name_csv_col = [csv_col for csv_col, json_val in CSV_TO_JSON_MAP.items() if json_val == 'assessment_name']
    if assessment_name_csv_col:
        TARGET_FIELD_TO_METADATA_KEY['assessment_name'] = assessment_name_csv_col[0].lower().replace(' ', '_').replace('/', '_')
    else:
        raise ValueError("Configuration Error: 'assessment_name' is in TARGET_JSON_FIELDS, "
                         "but 'Assessment Name' (or equivalent) is missing as a key in CSV_TO_JSON_MAP.")

print("--- Configured Mappings ---")
print("CSV_TO_JSON_MAP:", CSV_TO_JSON_MAP)
print("TARGET_FIELD_TO_METADATA_KEY:", TARGET_FIELD_TO_METADATA_KEY)
print("--------------------------")