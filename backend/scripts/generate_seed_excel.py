"""
Generate volunteers_seed.xlsx and residents_seed.xlsx from the CSV seed files.
Run from backend: python -m scripts.generate_seed_excel
"""
import csv
import sys
from pathlib import Path

# Add app to path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import openpyxl
    from openpyxl import Workbook
except ImportError:
    print("Install openpyxl: pip install openpyxl")
    sys.exit(1)

SEED_DIR = Path(__file__).resolve().parent.parent / "seed_data"
SEED_DIR.mkdir(exist_ok=True)


def csv_to_xlsx(csv_path: Path, xlsx_path: Path, encoding: str = "utf-8") -> None:
    with open(csv_path, encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    wb = Workbook()
    ws = wb.active
    if ws is None:
        raise RuntimeError("No active sheet")
    for row in rows:
        ws.append(row)
    wb.save(xlsx_path)
    print(f"Generated {xlsx_path.name}")


def main() -> None:
    volunteers_csv = SEED_DIR / "volunteers_seed.csv"
    residents_csv = SEED_DIR / "residents_seed.csv"
    if not volunteers_csv.exists() or not residents_csv.exists():
        print("Seed CSV files not found in seed_data/")
        sys.exit(1)
    csv_to_xlsx(volunteers_csv, SEED_DIR / "volunteers_seed.xlsx")
    csv_to_xlsx(residents_csv, SEED_DIR / "residents_seed.xlsx")


if __name__ == "__main__":
    main()
