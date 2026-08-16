"""SQLite 数据访问层：建表、入题、查询、练习进度。

题库 questions + 作答流水 practice_log，schema 见 database/schema.sql。
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from config import DB_PATH, ROOT

DEFAULT_SCHEMA = ROOT / "database" / "schema.sql"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection, schema: Path | None = None) -> None:
    """执行 schema.sql 建表。"""
    sql = (schema or DEFAULT_SCHEMA).read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def upsert_question(conn: sqlite3.Connection, q: dict) -> int:
    """插入一道题，source_id 冲突时更新。返回题目 id。"""
    choices_json = json.dumps(q.get("choices") or {}, ensure_ascii=False)
    source_id = q["source_id"]
    conn.execute(
        """INSERT INTO questions (source_id, subject, stem, choices, answer, explanation)
           VALUES (:source_id, :subject, :stem, :choices, :answer, :explanation)
           ON CONFLICT(source_id) DO UPDATE SET
             subject=excluded.subject, stem=excluded.stem,
             choices=excluded.choices, answer=excluded.answer,
             explanation=excluded.explanation""",
        {
            "source_id": source_id,
            "subject": q.get("subject", ""),
            "stem": q.get("stem", ""),
            "choices": choices_json,
            "answer": q.get("answer", ""),
            "explanation": q.get("explanation") or None,
        },
    )
    conn.commit()
    row = conn.execute("SELECT id FROM questions WHERE source_id=?", (source_id,)).fetchone()
    return row["id"]


def count_questions(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) c FROM questions").fetchone()["c"]


def list_questions(conn: sqlite3.Connection, subject: str | None = None) -> list[sqlite3.Row]:
    if subject:
        return conn.execute(
            "SELECT * FROM questions WHERE subject=? ORDER BY id", (subject,)).fetchall()
    return conn.execute("SELECT * FROM questions ORDER BY id").fetchall()


def subjects(conn: sqlite3.Connection) -> list[str]:
    return [r["subject"] for r in conn.execute(
        "SELECT DISTINCT subject FROM questions ORDER BY subject").fetchall()]


def get_questions_with_stats(conn: sqlite3.Connection, subject: str | None = None):
    """题目 + 累计作答/正确率，供 trainer。"""
    sql = """SELECT q.*,
        (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id) as attempts,
        (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id AND l.correct=1) as correct
        FROM questions q"""
    args: tuple = ()
    if subject:
        sql += " WHERE q.subject=?"
        args = (subject,)
    sql += " ORDER BY q.id"
    return conn.execute(sql, args).fetchall()


def get_wrong_questions(conn: sqlite3.Connection, subject: str | None = None,
                        min_attempts: int = 1) -> list[sqlite3.Row]:
    """错题本：答错过且正确率<100% 的题（可限章节）。"""
    sql = """SELECT q.*,
        (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id) as attempts,
        (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id AND l.correct=1) as correct
        FROM questions q
        WHERE EXISTS (SELECT 1 FROM practice_log l WHERE l.qid=q.id AND l.correct=0)
          AND (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id) >= ?
          AND (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id AND l.correct=1)
              < (SELECT COUNT(*) FROM practice_log l WHERE l.qid=q.id)"""
    args: tuple = (min_attempts,)
    if subject:
        sql += " AND q.subject=?"
        args += (subject,)
    sql += " ORDER BY q.id"
    return conn.execute(sql, args).fetchall()


def overall_stats(conn: sqlite3.Connection, subject: str | None = None) -> dict:
    """整体统计：题数、作答次数、正确率、错题数，按章节汇总。"""
    where, args = "", ()
    if subject:
        where, args = " WHERE q.subject=?", (subject,)
    total = conn.execute(f"SELECT COUNT(*) c FROM questions q{where}", args).fetchone()["c"]
    answered = conn.execute(
        f"""SELECT COUNT(DISTINCT l.qid) c FROM practice_log l
            JOIN questions q ON q.id=l.qid {where}""", args).fetchone()["c"]
    correct_pct = conn.execute(
        f"""SELECT CASE WHEN COUNT(*)=0 THEN NULL ELSE
            ROUND(100.0*SUM(l.correct)/COUNT(*),1) END v
            FROM practice_log l JOIN questions q ON q.id=l.qid {where}""",
        args).fetchone()["v"]
    wrong_pct = conn.execute(
        f"""SELECT CASE WHEN COUNT(*)=0 THEN NULL ELSE
            ROUND(100.0*SUM(1-l.correct)/COUNT(*),1) END v
            FROM practice_log l JOIN questions q ON q.id=l.qid {where}""",
        args).fetchone()["v"]
    return {"total": total, "answered": answered,
            "correct_pct": correct_pct, "wrong_pct": wrong_pct}


def stats_by_subject(conn: sqlite3.Connection) -> list[dict]:
    """各章节统计。"""
    rows = conn.execute(
        """SELECT q.subject, COUNT(DISTINCT q.id) total,
              COUNT(DISTINCT l.qid) answered,
              SUM(l.correct) correct_count, COUNT(l.id) attempts
           FROM questions q LEFT JOIN practice_log l ON l.qid=q.id
           GROUP BY q.subject ORDER BY q.subject""").fetchall()
    out = []
    for r in rows:
        pct = None
        if r["attempts"]:
            pct = round(100.0 * r["correct_count"] / r["attempts"], 1)
        out.append({"subject": r["subject"], "total": r["total"],
                    "answered": r["answered"], "accuracy": pct})
    return out
