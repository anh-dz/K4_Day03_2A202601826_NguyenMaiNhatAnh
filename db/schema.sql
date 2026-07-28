-- ============================================================
-- 🗄️ DATABASE SCHEMA — CHATBOT ĐỊNH HƯỚNG SỰ NGHIỆP
-- Dialect: SQLite -> db/career_chatbot.db
-- File: db/schema.sql
--
-- Đồng bộ theo CAREER_DB trong src/tools.py.
-- tools.py chỉ còn 3 tool phục vụ trực tiếp việc ĐỊNH HƯỚNG:
--   run_personality_assessment, match_profile_to_careers, get_career_detail
-- nên schema cũng chỉ giữ đúng 1 bảng careers tương ứng.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------- careers (từ CAREER_DB) ----------
CREATE TABLE IF NOT EXISTS careers (
    career_id           TEXT PRIMARY KEY,           -- vd: "ai_engineer"
    name                 TEXT NOT NULL,
    description           TEXT NOT NULL,
    required_skills       TEXT NOT NULL,              -- JSON array string
    salary_range           TEXT,                        -- vd: "Junior: 15-25tr | Middle: 25-45tr | Senior: 45-80tr VNĐ/tháng"
    growth_outlook         TEXT,
    education               TEXT,

    riasec_r  INTEGER NOT NULL DEFAULT 0 CHECK (riasec_r BETWEEN 0 AND 5),
    riasec_i  INTEGER NOT NULL DEFAULT 0 CHECK (riasec_i BETWEEN 0 AND 5),
    riasec_a  INTEGER NOT NULL DEFAULT 0 CHECK (riasec_a BETWEEN 0 AND 5),
    riasec_s  INTEGER NOT NULL DEFAULT 0 CHECK (riasec_s BETWEEN 0 AND 5),
    riasec_e  INTEGER NOT NULL DEFAULT 0 CHECK (riasec_e BETWEEN 0 AND 5),
    riasec_c  INTEGER NOT NULL DEFAULT 0 CHECK (riasec_c BETWEEN 0 AND 5)
);
