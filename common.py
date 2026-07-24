# -*- coding: utf-8 -*-
"""
common.py
--------------------------------------------------
app.py와 views/*.py 여러 화면에서 공통으로 쓰는 것들을 모아둔 모듈.
- 상수 (작업유형, 카테고리 등)
- 세션 상태 초기화 (농장 위치는 고정값, API 키는 Secrets에서 자동 로드)
- 날씨 조회 함수 (실시간 + 목업)
- 사이드바 공통 UI (SNS 링크)
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
