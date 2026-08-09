"""Run the full pipeline in order: download -> preprocess -> analysis -> model."""
import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "scripts/01_download_data.py",
    "scripts/02_preprocess.py",
    "scripts/03_analysis.py",
    "scripts/04_model.py",
    "scripts/05_report.py",
    "scripts/06_analysis_v2.py",
    "scripts/07_report_v2.py",
    "scripts/08_analysis_v3.py",
    "scripts/09_report_v3.py",
    "scripts/10_plotly_chart.py",
    "scripts/11_report_jinja.py",
]

root = Path(__file__).resolve().parent
for script in SCRIPTS:
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, script], cwd=root, check=True)
