"""Shared pytest setup: make backend modules importable and force offline mode."""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Tests must not call the real Hugging Face API.
os.environ["HUGGINGFACE_API_TOKEN"] = ""
os.environ.setdefault("MIN_SIMILARITY", "0.2")
