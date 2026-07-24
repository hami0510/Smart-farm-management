# -*- coding: utf-8 -*-
"""
db.py
--------------------------------------------------
Supabase(Postgres + Storage) 연동 모듈.

- 영농일지(farm_logs), 일정(schedules), 자료 메타데이터(documents)는 Postgres 테이블에 저장
- 업로드 파일 원본은 Supabase Storage 버킷에 저장
- 클라우드에 저장되므로 새로고침/재배포/앱 재시작 후에도 데이터가 유지된다

필요 설정 (Streamlit Secrets):
    SUPABASE_URL = "https://xxxx.supabase.co"
    SUPABASE_KEY = "eyJhbGciOi..."   # anon public key
"""

import uuid
from datetime import date
from urllib.parse import quote

import streamlit as st

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# 업로드 파일을 보관할 Storage 버킷 이름
STORAGE_BUCKET = "farm-documents"


# ============================================================
# 연결
# ============================================================
@st.cache_resource
def get_client():
    """Supabase 클라이언트를 생성한다 (앱 전체에서 1회만 생성되도록 캐시)."""
    if not SUPABASE_AVAILABLE:
        st.error("`supabase` 패키지가 설치되지 않았습니다. requirements.txt를 확인해주세요.")
        st.stop()
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error(
            "Supabase 접속 정보가 없습니다.\n\n"
            "Streamlit Cloud → Manage app → Settings → Secrets에 "
            "`SUPABASE_URL`과 `SUPABASE_KEY`를 등록해주세요."
        )
        st.stop()
    return create_client(url, key)


def init_db() -> None:
    """
    테이블은 Supabase 대시보드에서 SQL로 미리 생성하므로 여기서는 연결 확인만 한다.
    """
    get_client()


def seed_sample_data_if_empty() -> None:
    """테이블이 비어있을 때만 샘플 데이터를 넣는다 (최초 1회)."""
    sb = get_client()
    today = date.today().strftime("%Y-%m-%d")

    if not sb.table("farm_logs").select("id").limit(1).execute().data:
        sb.table("farm_logs").insert([
            {
                "id": str(uuid.uuid4()), "log_date": today, "zone": "1동", "work_type": "방제",
                "detail": "진딧물 예방을 위한 친환경 방제 작업 실시",
                "materials": "친환경 방제제 500ml", "harvest_kg": 0.0, "sales": 0,
            },
            {
                "id": str(uuid.uuid4()), "log_date": today, "zone": "2동", "work_type": "수확",
                "detail": "완숙 토마토 1차 수확 진행",
                "materials": "-", "harvest_kg": 85.5, "sales": 342000,
            },
        ]).execute()

    if not sb.table("schedules").select("id").limit(1).execute().data:
        sb.table("schedules").insert([
            {
                "id": str(uuid.uuid4()), "title": "2동 토마토 2차 수확 예정",
                "start_date": today, "end_date": today,
                "importance": "높음", "category": "수확예정", "done": False,
            },
            {
                "id": str(uuid.uuid4()), "title": "친환경 방제제 정기 살포",
                "start_date": today, "end_date": today,
                "importance": "보통", "category": "방제일", "done": False,
            },
        ]).execute()


# ============================================================
# 영농일지 (farm_logs)
# ============================================================
def get_farm_logs() -> list[dict]:
    sb = get_client()
    res = sb.table("farm_logs").select("*").order("log_date", desc=True).execute()
    return res.data or []


def add_farm_log(log_date, zone, work_type, detail, materials, harvest_kg, sales) -> None:
    sb = get_client()
    sb.table("farm_logs").insert({
        "id": str(uuid.uuid4()),
        "log_date": log_date,
        "zone": zone,
        "work_type": work_type,
        "detail": detail,
        "materials": materials,
        "harvest_kg": float(harvest_kg),
        "sales": int(sales),
    }).execute()


def delete_farm_log(log_id: str) -> None:
    sb = get_client()
    sb.table("farm_logs").delete().eq("id", log_id).execute()


# ============================================================
# 일정 (schedules)
# ============================================================
def get_schedules() -> list[dict]:
    sb = get_client()
    res = sb.table("schedules").select("*").order("start_date").execute()
    return res.data or []


def add_schedule(title, start_date, end_date, importance, category) -> None:
    sb = get_client()
    sb.table("schedules").insert({
        "id": str(uuid.uuid4()),
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "importance": importance,
        "category": category,
        "done": False,
    }).execute()


def update_schedule_done(schedule_id: str, done: bool) -> None:
    sb = get_client()
    sb.table("schedules").update({"done": bool(done)}).eq("id", schedule_id).execute()


def delete_schedule(schedule_id: str) -> None:
    sb = get_client()
    sb.table("schedules").delete().eq("id", schedule_id).execute()


# ============================================================
# 자료(문서) 메타데이터 (documents) + Storage 파일
# ============================================================
def get_documents() -> list[dict]:
    sb = get_client()
    res = sb.table("documents").select("*").order("upload_date", desc=True).execute()
    return res.data or []


def add_document(filename, stored_name, category, description, upload_date, size_kb) -> None:
    sb = get_client()
    sb.table("documents").insert({
        "id": str(uuid.uuid4()),
        "filename": filename,
        "stored_name": stored_name,
        "category": category,
        "description": description,
        "upload_date": upload_date,
        "size_kb": float(size_kb),
    }).execute()


def delete_document(doc_id: str) -> dict | None:
    """DB에서 문서 정보를 삭제하고, 삭제된 레코드를 반환한다 (Storage 파일 삭제는 호출부에서)."""
    sb = get_client()
    res = sb.table("documents").select("*").eq("id", doc_id).execute()
    row = res.data[0] if res.data else None
    sb.table("documents").delete().eq("id", doc_id).execute()
    return row


def upload_file_to_storage(stored_name: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> None:
    """업로드된 파일을 Supabase Storage 버킷에 저장한다."""
    sb = get_client()
    sb.storage.from_(STORAGE_BUCKET).upload(
        path=stored_name,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )


@st.cache_data(ttl=600, show_spinner=False)
def download_file_from_storage(stored_name: str) -> bytes | None:
    """Storage에서 파일 내용을 내려받는다. 실패 시 None. (10분 캐시)"""
    sb = get_client()
    try:
        return sb.storage.from_(STORAGE_BUCKET).download(stored_name)
    except Exception:
        return None


def get_public_url(stored_name: str) -> str | None:
    """브라우저에서 바로 열 수 있는 공개 URL을 반환한다 (버킷이 Public일 때)."""
    sb = get_client()
    try:
        return sb.storage.from_(STORAGE_BUCKET).get_public_url(stored_name)
    except Exception:
        return None


def remove_file_from_storage(stored_name: str) -> None:
    """Storage에서 파일을 삭제한다."""
    sb = get_client()
    try:
        sb.storage.from_(STORAGE_BUCKET).remove([stored_name])
    except Exception:
        pass
