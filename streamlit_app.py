"""Streamlit Community Cloud entry point (main file path: streamlit_app.py)."""
import runpy
from pathlib import Path

runpy.run_path(Path(__file__).resolve().parent / "app" / "app.py", run_name="__main__")
