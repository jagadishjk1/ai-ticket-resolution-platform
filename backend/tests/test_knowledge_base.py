"""Unit tests for dataset loading and index building."""
import pandas as pd
import pytest

from knowledge_base import build_index, detect_columns, load_tickets


def test_demo_dataset_loads_resolved_unique_tickets():
    tickets, path = load_tickets()
    assert path.name == "demo_tickets.xlsx"
    assert 150 <= len(tickets) <= 300
    assert all(t["status"].lower() in {"resolved", "closed"} for t in tickets)
    keys = {(t["description"], t["resolution"]) for t in tickets}
    assert len(keys) == len(tickets), "duplicate tickets should be removed"


def test_unresolved_and_duplicate_rows_are_skipped(tmp_path):
    df = pd.DataFrame(
        {
            "Ticket ID": ["A1", "A2", "A3", "A4"],
            "Category": ["VPN Access"] * 4,
            "Description": ["VPN fails", "VPN fails", "VPN slow", "VPN drops"],
            "Resolution": ["Reset VPN", "Reset VPN", "Split tunnel", "Fix driver"],
            "Status": ["Resolved", "Closed", "Open", "In Progress"],
        }
    )
    path = tmp_path / "tickets.xlsx"
    df.to_excel(path, index=False)
    tickets, _ = load_tickets(str(path))
    assert [t["ticket_id"] for t in tickets] == ["A1"]


def test_detect_columns_requires_core_fields():
    mapping = detect_columns(["Ticket ID", "Category", "Description", "Resolution", "Priority"])
    assert mapping["description"] == "Description"
    assert mapping["ticket_id"] == "Ticket ID"
    with pytest.raises(ValueError):
        detect_columns(["Category", "Description"])  # no resolution column


def test_resolved_date_is_not_mistaken_for_resolution():
    mapping = detect_columns(["Category", "Description", "Resolved Date", "Resolution"])
    assert mapping["resolution"] == "Resolution"


def test_index_has_one_row_per_ticket():
    tickets, _ = load_tickets()
    _, matrix = build_index(tickets)
    assert matrix.shape[0] == len(tickets)
