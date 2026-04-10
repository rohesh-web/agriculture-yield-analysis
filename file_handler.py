import csv
import os

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_report(report, output_path):
    with open(output_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to {output_path}")

def safe_load(filepath):
    try:
        return load_data(filepath)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
    except PermissionError:
        print("[ERROR] Cannot read file.")
    except Exception as e:
        print(f"[ERROR] {e}")
    return []