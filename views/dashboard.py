# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
1행: 실시간 날씨 (한 줄, 카드형)
2행: 일정 캘린더(넓게, 좌) + 오늘의 요약(좁게, 우 상단 카드 3개)
디자인: 둥근 모서리 + 부드러운 그림자 + 포인트 컬러로 카드형 UI 적용
"""

from datetime import datetime, timedelta

import streamlit as st

import db
from common import get_weather, calc_dday, importance_badge, SCHEDULE_CATEGORIES, IMPORTANCE_LEVELS

try:
    from streamlit_calendar import calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False


# ============================================================
# 카드형 디자인을 위한 공통 스타일 주입
# ============================================================
st.markdown(
    """
    <style>
    /* 날씨 metric 카드 */
    div[data-testid="stMetric"] {
        background: #F6FBF4;
        border: 1px solid #E4EFDF;
        border-radius: 16px;
        padding: 14px 18px 10px 18px;
        box-shadow: 0 2px 8px rgba(46, 125, 50, 0.06);
    }
    div[data-testid="stMetric"] label {
        color: #6B8F6B !important;
    }

    /* 캘린더 전체를 카드처럼 */
    .fc {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid #E4EFDF;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        font-family: inherit;
    }
    .fc-toolbar-title {
        font-weight: 700;
        color: #2E7D32;
        font-size: 1.2em !important;
    }
    .fc-button {
        background: #4CAF50 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }
    .fc-button:hover {
        background: #3d8b40 !important;
    }
    .fc-button-active {
        background: #2E7D32 !important;
    }
    .fc-col-header-cell {
        background: #F1F8F0;
        font-weight: 600;
        color: #4A6B4A;
    }
    .fc-daygrid-day-frame {
        padding: 3px !important;
    }
    /* 오늘 날짜: 각진 테두리 대신 둥근 하이라이트 박스 */
    .fc-day-today .fc-daygrid-day-frame {
        background: #FFF4E0 !important;
        border-radius: 12px;
        box-shadow: inset 0 0 0 2px #FFA726;
        margin: 3px;
    }
    .fc-daygrid-day-number {
        font-weight: 500;
        color: #4A5A4A;
    }
    .fc-event {
        border-radius: 8px !important;
        border: none !important;
        padding: 2px 8px !important;
        font-size: 0.78em !important;
        font-weight: 500;
    }

    /* 오늘의 요약 카드 */
    .summary-card {
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .summary-card .main-text {
        font-size: 0.94em;
        color: #333;
    }
    .summary-card .sub-text {
        font-size: 0.78em;
        color: #8A8A8A;
        margin-top: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def summary_card(icon: str, accent_color: str, bg_color: str, main_text: str) -> None:
    st.markdown(
        f"""
        <div class="summary-card" style="background:{bg_color}; border-left:4px solid {accent_color};">
            <div class="main-text">{icon} {main_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 상단 타이틀 + 날씨
# ============================================================
st.title("🌾 스마트팜 종합 농가 관리 시스템")
st.caption(
    f"현재 등록된 농장 위치: **{st.session_state.farm_location['name']}**  "
    f"({st.session_state.farm_location['lat']:.4f}, {st.session_state.farm_location['lon']:.4f})"
)

weather = get_weather(
    st.session_state.farm_location["lat"],
    st.session_state.farm_location
