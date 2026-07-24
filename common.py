# -*- coding: utf-8 -*-
"""
common.py
--------------------------------------------------
app.py와 views/*.py 여러 화면에서 공통으로 쓰는 것들을 모아둔 모듈.
- 상수 (작업유형, 카테고리 등)
- 세션 상태 초기화 (농장 위치, API 키)
- 날씨 조회 함수 (실시간 + 목업)
- 주소 -> 위경도 변환 (지오코딩)
- 사이드바 공통 UI (위치 설정)
- 자잘한 유틸 함수 (D-Day 계산 등)
"""

import random
from datetime import datetime, date

import requests
import streamlit as st

try:
    from streamlit_js_eval import get_geolocation
    GEO_AVAILABLE = True
except ImportError:
    GEO_AVAILABLE = False


# ============================================================
# 상수
# ============================================================
WORK_TYPES = ["파종", "비료/영양제", "방제", "수확", "기타"]
DOC_CATEGORIES = ["재무/영수증", "장비메뉴얼", "계약서", "기타"]
SCHEDULE_CATEGORIES = ["수확예정", "방제일", "납품일", "기타"]
IMPORTANCE_LEVELS = ["높음", "보통", "낮음"]


# ============================================================
# 세션 상태 초기화 (모든 페이지 진입 시 맨 먼저 호출)
# ============================================================
def init_common_session_state() -> None:
    if "farm_location" not in st.session_state:
        st.session_state.farm_location = {
            "lat": 37.5665,
            "lon": 126.9780,
            "name": "서울 (기본값)",
        }
    if "api_key" not in st.session_state:
        # Streamlit Cloud의 Secrets에 등록된 키를 자동으로 불러옴
        # (로컬 실행 시 secrets가 없어도 에러 없이 빈 값으로 처리됨)
        try:
            st.session_state.api_key = st.secrets.get("OPENWEATHER_API_KEY", "")
        except Exception:
            st.session_state.api_key = ""


# ============================================================
# 날씨 조회
# ============================================================
def get_mock_weather() -> dict:
    """API 키가 없거나 오류 발생 시 사용할 가상 날씨 데이터."""
    return {
        "temp": round(random.uniform(15, 29), 1),
        "humidity": random.randint(35, 85),
        "wind_speed": round(random.uniform(0.5, 13.0), 1),
        "description": random.choice(["맑음", "구름 조금", "구름 많음", "흐림", "비", "약한 비"]),
        "is_mock": True,
        "error": None,
    }


def get_weather(lat: float, lon: float, api_key: str) -> dict:
    """실시간 날씨를 가져온다. 키가 없거나 실패하면 목업 데이터 반환."""
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


# ============================================================
# 주소 -> 위경도 변환 (OpenWeatherMap Geocoding API 사용, 같은 키 재사용)
# ============================================================
def geocode_address(address: str, api_key: str) -> dict | None:
    """
    주소/지역명을 위경도로 변환한다.
    도시/군/구 단위 이름에서 가장 잘 동작한다 (예: "전북 김제시", "제주 서귀포시").
    상세 도로명 주소는 정확도가 떨어질 수 있음.
    """
    if not api_key or not address:
        return None
    try:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {"q": address, "limit": 1, "appid": api_key}
        resp = requests.get(url, params=params, timeout=6)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        r = results[0]
        # 지역명이 여러 언어로 섞여 나올 수 있어, 사용자가 입력한 원문 주소를 이름으로 사용
        return {"lat": r["lat"], "lon": r["lon"], "name": address}
    except Exception:
        return None


# ============================================================
# 사이드바 공통 UI (위치 설정)
# 모든 페이지 상단에서 render_sidebar_settings() 한 번만 호출하면 됨
# ============================================================
def render_sidebar_settings() -> None:
    with st.sidebar:
        with st.expander("📍 농장 위치 설정", expanded=False):
            loc = st.session_state.farm_location
            st.caption(f"현재 위치: **{loc['name']}** ({loc['lat']:.4f}, {loc['lon']:.4f})")

            # ---- 주소/지역명으로 검색 ----
            address_in = st.text_input(
                "주소 또는 지역명 검색",
                placeholder="예: 전북 김제시, 제주 서귀포시 등",
            )
            if st.button("🔍 이 주소로 위치 설정", use_container_width=True):
                if not st.session_state.api_key:
                    st.error("주소 검색에는 날씨 API 키가 필요합니다. (관리자에게 문의)")
                else:
                    result = geocode_address(address_in, st.session_state.api_key)
                    if result:
                        st.session_state.farm_location = result
                        st.success(f"'{address_in}' 위치로 설정했습니다.")
                        st.rerun()
                    else:
                        st.error("주소를 찾을 수 없습니다. 시/군/구 단위로 다시 입력해보세요.")

            st.divider()

            # ---- 실시간 GPS 자동 감지 ----
            if GEO_AVAILABLE:
                st.caption("또는 현재 계신 곳의 위치를 자동으로 가져올 수 있습니다.")
                if st.button("📡 현재 위치로 자동 감지", use_container_width=True):
                    gloc = get_geolocation()
                    if gloc and "coords" in gloc:
                        st.session_state.farm_location = {
                            "lat": gloc["coords"]["latitude"],
                            "lon": gloc["coords"]["longitude"],
                            "name": "현재 위치(자동 감지)",
                        }
                        st.success("현재 위치를 반영했습니다!")
                        st.rerun()
                    else:
                        st.info("위치 권한을 허용해주세요. 팝업이 안 보이면 다시 눌러주세요.")


# ============================================================
# 유틸 함수
# ============================================================
def calc_dday(target_date_str: str) -> str:
    """날짜 문자열을 받아 'D-3', 'D-DAY', 'D+2' 형식으로 변환."""
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
