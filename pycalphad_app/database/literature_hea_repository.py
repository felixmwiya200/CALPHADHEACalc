"""
literature_hea_repository.py - Indexed High-Entropy Alloy Literature Database
Loads and parses App/data/database_of_HEAs.csv containing hundreds of experimental
and theoretical HEA compositions with synthesis routes, crystal structures, and citations.
"""

import os
import csv
from typing import List, Dict, Any, Optional


class LiteratureHEARepository:
    _RECORDS: Optional[List[Dict[str, str]]] = None

    @classmethod
    def _load(cls) -> List[Dict[str, str]]:
        if cls._RECORDS is None:
            import sys
            candidate_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "App", "data", "database_of_HEAs.csv"),
                os.path.join(getattr(sys, "_MEIPASS", ""), "App", "data", "database_of_HEAs.csv"),
                os.path.join(os.getcwd(), "App", "data", "database_of_HEAs.csv"),
            ]
            csv_path = None
            for p in candidate_paths:
                if p and os.path.exists(p):
                    csv_path = p
                    break

            records = []
            if csv_path and os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        records.append({
                            "Alloy": row.get("Alloy", "").strip(),
                            "Phase": row.get("Phase", "").strip(),
                            "Type": row.get("Experimental or theoretical", "").strip(),
                            "Synthesis": row.get("Experimental details", "").strip(),
                            "Paper": row.get("Paper", "").strip()
                        })
            cls._RECORDS = records
        return cls._RECORDS

    @classmethod
    def count(cls) -> int:
        return len(cls._load())

    @classmethod
    def search_by_alloy(cls, query: str) -> List[Dict[str, str]]:
        records = cls._load()
        q = query.lower()
        return [r for r in records if q in r["Alloy"].lower()]

    @classmethod
    def get_top_alloys(cls, limit: int = 25) -> List[Dict[str, str]]:
        records = cls._load()
        return records[:limit]
