"""
🌱 SEED SCRIPT
Tạo db/career_chatbot.db từ db/schema.sql, nạp dữ liệu trực tiếp từ
CAREER_DB trong src/tools.py để db luôn đồng bộ với dữ liệu mock hiện tại của tool.

Chạy: python db/seed.py
Kết quả: db/career_chatbot.db
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tools import CAREER_DB  # noqa: E402

DB_PATH = Path(__file__).resolve().parent / "career_chatbot.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def build_database() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    for career_id, career in CAREER_DB.items():
        riasec = career["riasec"]
        conn.execute(
            """
            INSERT INTO careers (
                career_id, name, description, required_skills,
                salary_range, growth_outlook, education,
                riasec_r, riasec_i, riasec_a, riasec_s, riasec_e, riasec_c
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                career_id,
                career["name"],
                career["description"],
                json.dumps(career["required_skills"], ensure_ascii=False),
                career["salary_range"],
                career["growth_outlook"],
                career["education"],
                riasec["R"], riasec["I"], riasec["A"], riasec["S"], riasec["E"], riasec["C"],
            ),
        )

    conn.commit()
    conn.close()

    print(f"Da tao {DB_PATH}")
    print(f"  - careers: {len(CAREER_DB)}")


if __name__ == "__main__":
    build_database()
