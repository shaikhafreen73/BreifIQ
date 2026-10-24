import pandas as pd
import json


def read_file(filepath):
    """
    Reads tabular data from CSV, TSV, XLSX, XLS, or JSON files.
    Robustly handles encoding, delimiters, and missing values.
    """
    path_lower = filepath.lower()

    if path_lower.endswith(".csv"):
        # Try multiple encodings
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]:
            try:
                # Try comma first, then autodetect separator
                data = pd.read_csv(filepath, encoding=encoding)
                return data
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        # Fallback with python engine
        return pd.read_csv(filepath, sep=None, engine="python", on_bad_lines="skip")

    elif path_lower.endswith(".tsv"):
        return pd.read_csv(filepath, sep="\t")

    elif path_lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)

    elif path_lower.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        if isinstance(raw_data, list):
            return pd.DataFrame(raw_data)
        elif isinstance(raw_data, dict):
            # Try records orientation or wrap
            try:
                return pd.DataFrame(raw_data)
            except:
                return pd.DataFrame([raw_data])
        else:
            raise ValueError("Unsupported JSON structure for tabular dataset.")

    else:
        raise ValueError(f"Unsupported tabular file format: {filepath}")