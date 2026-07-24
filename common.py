# -*- coding: utf-8 -*-
"""
common.py
--------------------------------------------------
app.py와 pages/*.py 여러 화면에서 공통으로 쓰는 것들을 모아둔 모듈.
- 상수 (작업유형, 카테고리 등)
- 세션 상태 초기화 (농장 위치, API 키)
- 날씨 조회 함수 (실시간 + 목업)
- 사이드바 공통 UI (위치 설정 / API 키 입력)
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
        # Streamlit Cloud의 Secrets에 등록된 키가 있으면 자동으로 불러옴
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
# 사이드바 공통 UI (위치 설정 + API 키)
# 모든 페이지 상단에서 render_sidebar_settings() 한 번만 호출하면 됨
# ============================================================
def render_sidebar_settings() -> None:
    with st.sidebar:
        with st.expander("📍 농장 위치 설정", expanded=False):
            if GEO_AVAILABLE:
                st.caption("버튼을 누르면 브라우저(PC/모바일)에 위치 권한을 요청합니다.")
                if st.button("📡 현재 위치로 자동 감지", use_container_width=True):
                    loc = get_geolocation()
                    if loc and "coords" in loc:
                        st.session_state.farm_location = {
                            "lat": loc["coords"]["latitude"],
                            "lon": loc["coords"]["longitude"],
                            "name": "현재 위치(자동 감지)",
                        }
                        st.success("현재 위치를 반영했습니다!")
                        st.rerun()
                    else:
                        st.info("위치 권한을 허용해주세요. 팝업이 안 보이면 다시 눌러주세요.")
            else:
                st.warning(
                    "실시간 위치 자동 감지를 사용하려면 아래 패키지를 설치하세요:\n\n"
                    "`pip install streamlit-js-eval`"
                )

            st.caption("또는 직접 좌표를 입력할 수 있습니다.")
            lat_in = st.number_input(
                "위도(Latitude)", value=float(st.session_state.farm_location["lat"]), format="%.4f"
            )
            lon_in = st.number_input(
                "경도(Longitude)", value=float(st.session_state.farm_location["lon"]), format="%.4f"
            )
            name_in = st.text_input("위치 이름", value=st.session_state.farm_location["name"])
            if st.button("💾 위치 저장", use_container_width=True):
                st.session_state.farm_location = {"lat": lat_in, "lon": lon_in, "name": name_in}
                st.success("농장 위치가 저장되었습니다.")
                st.rerun()

        with st.expander("🔑 OpenWeatherMap API 키", expanded=False):
            st.session_state.api_key = st.text_input(
                "API Key", value=st.session_state.api_key, type="password",
                placeholder="아직 없다면 비워두세요 (자동으로 가상 데이터 표시)",
            )
            st.caption("키가 없어도 앱은 정상 작동하며, 가상(목업) 날씨 데이터가 대신 표시됩니다.")

            with st.expander("🆕 무료 API 키 발급 방법 (약 5분)"):
                st.markdown(
                    """
**1단계. 회원가입**
- https://openweathermap.org/api 접속 → **Sign Up** 클릭 → 이메일/비밀번호 입력 (Free 플랜)

**2단계. 이메일 인증**
- 가입 시 입력한 메일함에서 인증 링크 클릭

**3단계. API 키 확인**
- 로그인 후 우측 상단 **My API keys** 메뉴 이동 → `Default` 키 복사

**4단계. 앱에 입력**
- 복사한 키를 위 'API Key' 입력창에 붙여넣기

⚠️ 발급 직후엔 활성화까지 최대 2시간 정도 걸릴 수 있어요. 그동안은 자동으로 목업 데이터가 표시됩니다.
                    """
                )


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
