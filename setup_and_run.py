"""
One-shot setup script: generates data, trains models, seeds DB, then starts server.
Run: python setup_and_run.py
"""

import subprocess, sys, os

BASE = os.path.dirname(__file__)

steps = [
    ("Generating datasets",    [sys.executable, "data/generate_data.py"]),
    ("Cleaning & EDA",         [sys.executable, "data/clean_and_eda.py"]),
    ("Training ML models",     [sys.executable, "ml/train_models.py"]),
    ("Seeding database",       [sys.executable, "seed_db.py"]),
]

for label, cmd in steps:
    print(f"\n{'='*50}\n{label} …\n{'='*50}")
    result = subprocess.run(cmd, cwd=BASE)
    if result.returncode != 0:
        print(f"ERROR: '{label}' failed. Check output above.")
        sys.exit(1)

print("\n" + "="*50)
print("Starting SmartCart server …")
print("Visit: http://127.0.0.1:8000")
print("API docs: http://127.0.0.1:8000/docs")
print("="*50 + "\n")
subprocess.run(["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
               cwd=BASE)
