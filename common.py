# -*- coding: utf-8 -*-
"""
common.py
--------------------------------------------------
app.py와 views/*.py 여러 화면에서 공통으로 쓰는 것들을 모아둔 모듈.
- 상수 (작업유형, 카테고리 등)
- 세션 상태 초기화 (농장 위치는 고정값, API 키는 Secrets에서 자동 로드)
- 날씨 조회 함수 (실시간 + 목업)
- 사이드바 공통 UI (SNS 링크 / 데이터 백업)
- 자잘한 유틸 함수 (D-Day 계산 등)
"""

import random
from datetime import datetime, date

import requests
import streamlit as st

WORK_TYPES = ["파종", "비료/영양제", "방제", "수확", "기타"]
DOC_CATEGORIES = ["재무/영수증", "장비메뉴얼", "계약서", "기타"]
SCHEDULE_CATEGORIES = ["수확예정", "방제일", "납품일", "기타"]
IMPORTANCE_LEVELS = ["높음", "보통", "낮음"]

# 농장 위치 고정값 (충남 당진시 고대면 당진포리 140-14)
FIXED_FARM_LOCATION = {
    "lat": 36.9611,
    "lon": 126.5600,
    "name": "충남 당진시 고대면 당진포리 140-14",
}

SNS_LINKS = [
    {"label": "📷 인스타그램", "url": "https://www.instagram.com/farmerhakssi"},
    {"label": "▶️ 유튜브", "url": "https://www.youtube.com/@farmerhak"},
]


def init_common_session_state() -> None:
    if "farm_location" not in st.session_state:
        # 농장 위치는 고정값 사용 (사용자가 변경할 수 없음)
        st.session_state.farm_location = FIXED_FARM_LOCATION
    if "api_key" not in st.session_state:
        try:
            st.session_state.api_key = st.secrets.get("OPENWEATHER_API_KEY", "")
        except Exception:
            st.session_state.api_key = ""


def get_mock_weather() -> dict:
    return {
        "temp": round(random.uniform(15, 29), 1),
        "humidity": random.randint(35, 85),
        "wind_speed": round(random.uniform(0.5, 13.0), 1),
        "description": random.choice(["맑음", "구름 조금", "구름 많음", "흐림", "비", "약한 비"]),
        "is_mock": True,
        "error": None,
    }


def get_weather(lat: float, lon: float, api_key: str) -> dict:
    if not api_key:
        return get_mock_weather()
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "kr"}
        resp = requests.get(url, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "description": data["weather"][0]["description"],
            "is_mock": False,
            "error": None,
        }
    except Exception as e:
        mock = get_mock_weather()
        mock["error"] = str(e)
        return mock


def render_sidebar_links() -> None:
    """사이드바 하단에 SNS 링크 버튼을 표시한다."""
    with st.sidebar:
        st.divider()
        st.caption("SNS")
        for link in SNS_LINKS:
            st.link_button(link["label"], link["url"], use_container_width=True)


def _build_backup_zip() -> bytes:
    """영농일지·일정·자료목록을 CSV로 묶은 ZIP 파일을 만든다."""
    import io
    import zipfile

    import pandas as pd

    import db

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        datasets = {
            "영농일지.csv": db.get_farm_logs(),
            "일정.csv": db.get_schedules(),
            "자료목록.csv": db.get_documents(),
        }
        for name, rows in datasets.items():
            df = pd.DataFrame(rows) if rows else pd.DataFrame()
            zf.writestr(name, df.to_csv(index=False).encode("utf-8-sig"))

        readme = (
            "스마트팜 관리 시스템 백업\n"
            f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "· 영농일지.csv / 일정.csv / 자료목록.csv 를 포함합니다.\n"
            "· 자료관리함에 올린 실제 파일(PDF·사진 등)은 용량 문제로 이 백업에 포함되지 않습니다.\n"
            "  파일 원본은 자료관리함 화면에서 개별로 내려받아 보관해주세요.\n"
        )
        zf.writestr("백업안내.txt", readme.encode("utf-8-sig"))

    return buf.getvalue()


def render_sidebar_backup() -> None:
    """
    사이드바에 데이터 백업 기능을 표시한다.
    무료 플랜의 Supabase는 자동 백업이 없으므로 수동 백업 수단을 제공한다.
    """
    with st.sidebar:
        st.divider()
        with st.expander("💾 데이터 백업"):
            st.caption(
                "현재 사용 중인 무료 클라우드(Supabase)는 **자동 백업이 제공되지 않습니다.** "
                "실수로 삭제하거나 계정에 문제가 생기면 복구가 어려우므로, "
                "월 1회 정도 내려받아 PC나 구글드라이브에 보관해두시길 권장합니다."
            )
            if st.button("📦 백업 파일 만들기", use_container_width=True):
                try:
                    st.session_state["backup_zip"] = _build_backup_zip()
                    st.session_state["backup_time"] = datetime.now().strftime("%Y%m%d_%H%M")
                except Exception as e:
                    st.error(f"백업 생성 실패: {e}")

            if st.session_state.get("backup_zip"):
                st.download_button(
                    "⬇️ 백업 내려받기",
                    data=st.session_state["backup_zip"],
                    file_name=f"스마트팜백업_{st.session_state.get('backup_time', '')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
                st.caption("※ 업로드한 파일 원본은 포함되지 않습니다 (기록 데이터만).")


def calc_dday(target_date_str: str) -> str:
    target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    diff = (target - date.today()).days
    if diff == 0:
        return "D-DAY"
    elif diff > 0:
        return f"D-{diff}"
    else:
        return f"D+{abs(diff)}"


def importance_badge(level: str) -> str:
    colors = {"높음": "🔴", "보통": "🟡", "낮음": "🟢"}
    return f"{colors.get(level, '⚪')} {level}"
