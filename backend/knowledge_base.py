"""
Knowledge Base - loading the ticket dataset and building the TF-IDF index.

Shared by the RAG engine (at startup) and scripts/build_knowledge_base_tfidf.py,
so the index and the search query are always built the same way.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
DEFAULT_DATASET = DATA_DIR / "demo_tickets.xlsx"
LEGACY_DATASET = DATA_DIR / "Sample-Data.xlsx"

# Only tickets in these states have a confirmed, working resolution.
RESOLVED_STATUSES = {"resolved", "closed"}

# Header names accepted for each field (compared lower-case, spaces -> "_").
COLUMN_CANDIDATES = {
    "category": ["category", "categories", "issue_type", "ticket_category", "type"],
    "description": ["description", "ticket_description", "issue_description", "issue", "problem", "summary"],
    "resolution": ["resolution", "solution", "fix", "resolution_notes", "workaround"],
    "ticket_id": ["ticket_id", "ticketid", "id", "case_id", "incident_id"],
    "priority": ["priority", "severity"],
    "status": ["status", "state"],
}
REQUIRED_COLUMNS = ("category", "description", "resolution")


def resolve_dataset_path(path: Optional[str] = None) -> Path:
    """Pick the dataset: explicit argument > DATASET_PATH env var > demo dataset > legacy sample."""
    candidates = [path, os.getenv("DATASET_PATH"), DEFAULT_DATASET, LEGACY_DATASET]
    for candidate in candidates:
        if not candidate:
            continue
        p = Path(candidate)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        if p.exists():
            return p
    raise FileNotFoundError(
        f"No ticket dataset found. Expected {DEFAULT_DATASET}. "
        "Run: python scripts/generate_demo_dataset.py"
    )


def detect_columns(columns) -> Dict[str, str]:
    """Map canonical field names to the actual column names in the file."""
    normalized = {str(c).strip().lower().replace(" ", "_"): c for c in columns}
    mapping = {}
    for field, names in COLUMN_CANDIDATES.items():
        for name in names:
            if name in normalized:
                mapping[field] = normalized[name]
                break
    missing = [f for f in REQUIRED_COLUMNS if f not in mapping]
    if missing:
        raise ValueError(
            f"Dataset is missing required column(s): {', '.join(missing)}. "
            f"Found: {list(columns)}"
        )
    return mapping


def _clean(value, default: str = "") -> str:
    # pd.isna covers None, NaN, NaT and pandas 3's pd.NA
    if value is None or (not isinstance(value, (list, tuple)) and pd.isna(value)):
        return default
    text = str(value).strip()
    return text if text and text.lower() != "nan" else default


def load_tickets(path: Optional[str] = None) -> Tuple[List[Dict], Path]:
    """Read the dataset and return clean, de-duplicated, resolved tickets."""
    dataset_path = resolve_dataset_path(path)
    if dataset_path.suffix.lower() == ".csv":
        df = pd.read_csv(dataset_path)
    else:
        df = pd.read_excel(dataset_path)
    mapping = detect_columns(df.columns)

    tickets: List[Dict] = []
    seen = set()
    skipped_unresolved = 0
    for idx, row in df.iterrows():
        status = _clean(row[mapping["status"]], "Resolved") if "status" in mapping else "Resolved"
        if status.lower() not in RESOLVED_STATUSES:
            skipped_unresolved += 1
            continue
        description = _clean(row[mapping["description"]])
        resolution = _clean(row[mapping["resolution"]])
        if not description or not resolution:
            continue
        key = (description.lower(), resolution.lower())
        if key in seen:  # identical ticket already indexed
            continue
        seen.add(key)
        tickets.append({
            "ticket_id": _clean(row[mapping["ticket_id"]], f"T{idx + 1:04d}") if "ticket_id" in mapping else f"T{idx + 1:04d}",
            "category": _clean(row[mapping["category"]], "General"),
            "description": description,
            "resolution": resolution,
            "priority": _clean(row[mapping["priority"]], "Medium") if "priority" in mapping else "Medium",
            "status": status,
        })

    logger.info(
        "Loaded %d tickets from %s (%d rows in file, %d unresolved skipped)",
        len(tickets), dataset_path.name, len(df), skipped_unresolved,
    )
    if not tickets:
        raise ValueError(f"No usable resolved tickets in {dataset_path}")
    return tickets, dataset_path


def ticket_text(category: str, description: str) -> str:
    """Text used for BOTH indexing and querying, so the two always match.

    Only the description is compared. The category is deliberately left out:
    otherwise a query would "match" every ticket of its category through the
    category words alone. The engine uses the category as a ranking bonus instead.
    """
    return description


def build_index(tickets: List[Dict]):
    """Fit the TF-IDF vectorizer and return (vectorizer, matrix).

    Two TF-IDF views of the text are combined:
    - word unigrams/bigrams capture exact terms ("paper jam", "blue screen");
    - character 3-5 grams tolerate word forms and typos
      ("disconnects" ~ "disconnecting", "printers" ~ "printer").
    """
    vectorizer = FeatureUnion([
        ("words", TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])
    matrix = vectorizer.fit_transform(
        [ticket_text(t["category"], t["description"]) for t in tickets]
    )
    return vectorizer, matrix
