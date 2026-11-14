"""
Build & validate the knowledge base (TF-IDF).

The service builds its index in memory at startup, so this script is a
check you can run before starting it: it loads the dataset, builds the
index, prints statistics and runs a few sample searches.

Usage (from the backend folder):
    python scripts/build_knowledge_base_tfidf.py
    python scripts/build_knowledge_base_tfidf.py --dataset data/my_tickets.xlsx
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base import build_index, load_tickets  # noqa: E402
from rag_engine_tfidf import RAGEngine  # noqa: E402

SAMPLE_QUERIES = [
    ("VPN Access", "VPN disconnects every few minutes when I work from home"),
    ("Email Issues", "Outlook on my phone is not syncing new mail"),
    ("Printer Issues", "printer says offline and nothing prints"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", help="Path to .xlsx/.csv dataset (default: data/demo_tickets.xlsx)")
    args = parser.parse_args()

    tickets, path = load_tickets(args.dataset)
    vectorizer, matrix = build_index(tickets)
    print("=" * 60)
    print("KNOWLEDGE BASE")
    print("=" * 60)
    print(f"Dataset          : {path}")
    print(f"Resolved tickets : {len(tickets)}")
    print(f"Unique issues    : {len({t['description'] for t in tickets})}")
    print(f"Unique fixes     : {len({t['resolution'] for t in tickets})}")
    print(f"TF-IDF matrix    : {matrix.shape[0]} tickets x {matrix.shape[1]} terms")
    print("\nTickets per category:")
    for category, count in Counter(t["category"] for t in tickets).most_common():
        print(f"  {category:<22} {count}")

    print("\n" + "=" * 60)
    print("SAMPLE SEARCHES")
    print("=" * 60)
    engine = RAGEngine(dataset_path=args.dataset)
    for category, query in SAMPLE_QUERIES:
        print(f"\n[{category}] {query}")
        for t in engine.find_similar_tickets(query, category, k=3):
            print(f"  {t['similarity_score']:.2f}  {t['ticket_id']}  {t['description']}")
    print("\nKnowledge base OK.")


if __name__ == "__main__":
    main()
