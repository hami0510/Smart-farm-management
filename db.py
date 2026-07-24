# -*- coding: utf-8 -*-
"""
db.py
--------------------------------------------------
스마트팜 관리 시스템의 SQLite 데이터베이스 연결 및 CRUD 함수 모음.

- 앱 최초 실행 시 data/smartfarm.db 파일과 테이블이 자동으로 생성됩니다.
- 모든 페이지(app.py, pages/*.py)는 이 모듈의 함수만 호출해서 데이터를 다룹니다.
  (SQL 쿼리를 각 페이지에 직접 쓰지 않고 여기로 모아서 관리하기 쉽게 함)
"""

import sqlite3
import uuid
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "smartfarm.db"

DATA_DIR.mkdir(exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """DB 연결을 반환한다. row를 dict처럼 다룰 수 있도록 row_factory 설정."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# 1. 테이블 초기화
# ============================================================
def init_db() -> None:
    """테이블이 없으면 생성한다. (이미 있으면 아무 일도 하지 않음)"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS farm_logs (
            id TEXT PRIMARY KEY,
            log_date TEXT NOT NULL,
            zone TEXT NOT NULL,
            work_type TEXT NOT NULL,
            detail TEXT NOT NULL,
            materials TEXT,
            harvest_kg REAL DEFAULT 0,
            sales INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            importance TEXT NOT NULL,
            category TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            upload_date TEXT NOT NULL,
            size_kb REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def seed_sample_data_if_empty() -> None:
    """테이블이 비어있을 때만 샘플 데이터를 넣는다. (최초 1회)"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM farm_logs")
    if cur.fetchone()[0] == 0:
        today = date.today().strftime("%Y-%m-%d")
        cur.execute(
            "INSERT INTO farm_logs (id, log_date, zone, work_type, detail, materials, harvest_kg, sales) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), today, "1동", "방제", "진딧물 예방을 위한 친환경 방제 작업 실시", "친환경 방제제 500ml", 0.0, 0),
        )
        cur.execute(
            "INSERT INTO farm_logs (id, log_date, zone, work_type, detail, materials, harvest_kg, sales) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), today, "2동", "수확", "완숙 토마토 1차 수확 진행", "-", 85.5, 342000),
        )

    cur.execute("SELECT COUNT(*) FROM schedules")
    if cur.fetchone()[0] == 0:
        today = date.today().strftime("%Y-%m-%d")
        cur.execute(
            "INSERT INTO schedules (id, title, start_date, end_date, importance, category, done) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "2동 토마토 2차 수확 예정", today, today, "높음", "수확예정", 0),
        )
        cur.execute(
            "INSERT INTO schedules (id, title, start_date, end_date, importance, category, done) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "친환경 방제제 정기 살포", today, today, "보통", "방제일", 0),
        )

    conn.commit()
    conn.close()


# ============================================================
# 2. 영농일지 (farm_logs) CRUD
# ============================================================
def get_farm_logs() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM farm_logs ORDER BY log_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_farm_log(log_date, zone, work_type, detail, materials, harvest_kg, sales) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO farm_logs (id, log_date, zone, work_type, detail, materials, harvest_kg, sales) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), log_date, zone, work_type, detail, materials, harvest_kg, sales),
    )
    conn.commit()
    conn.close()


def delete_farm_log(log_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM farm_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()


# ============================================================
# 3. 일정 (schedules) CRUD
# ============================================================
def get_schedules() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM schedules ORDER BY start_date ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_schedule(title, start_date, end_date, importance, category) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO schedules (id, title, start_date, end_date, importance, category, done) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (str(uuid.uuid4()), title, start_date, end_date, importance, category),
    )
    conn.commit()
    conn.close()


def update_schedule_done(schedule_id: str, done: bool) -> None:
    conn = get_connection()
    conn.execute("UPDATE schedules SET done = ? WHERE id = ?", (1 if done else 0, schedule_id))
    conn.commit()
    conn.close()


def delete_schedule(schedule_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()


# ============================================================
# 4. 자료(문서) (documents) CRUD
# ============================================================
def get_documents() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY upload_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_document(filename, stored_name, category, description, upload_date, size_kb) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO documents (id, filename, stored_name, category, description, upload_date, size_kb) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), filename, stored_name, category, description, upload_date, size_kb),
    )
    conn.commit()
    conn.close()


def delete_document(doc_id: str) -> dict | None:
    """삭제 전 해당 문서 정보를 반환한다 (실제 파일 삭제는 호출부에서 처리)."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return dict(row) if row else None
