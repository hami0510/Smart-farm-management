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
    st.session_state.farm_location["lon"],
    st.session_state.api_key,
)

if weather["wind_speed"] >= 10:
    st.warning(f"🌬️ **강풍 주의보급 수준입니다!** 현재 풍속 {weather['wind_speed']} m/s — 시설물 점검을 권장합니다.")
if any(k in weather["description"] for k in ["비", "폭우", "소나기"]):
    st.warning(f"🌧️ 강우 예보가 있습니다: {weather['description']} — 배수로를 미리 점검하세요.")

st.markdown("**☀️ 실시간 날씨**")
if weather["is_mock"]:
    st.caption("⚠️ " + ("가상 데이터 표시 중" if not weather["error"] else f"연동 실패: {weather['error']}"))

wc1, wc2, wc3, wc4 = st.columns(4)
wc1.metric("🌡️ 기온", f"{weather['temp']} ℃")
wc2.metric("💧 습도", f"{weather['humidity']} %")
wc3.metric("💨 풍속", f"{weather['wind_speed']} m/s")
wc4.metric("☁️ 날씨", weather["description"])

st.divider()

farm_logs = db.get_farm_logs()
schedules = db.get_schedules()
documents = db.get_documents()

# ============================================================
# 캘린더(좌, 넓게) + 오늘의 요약(우, 좁게 - 카드 3개)
# ============================================================
cal_col, summary_col = st.columns([2.3, 1], gap="large")

with summary_col:
    st.markdown("**📌 오늘의 요약**")

    upcoming = sorted([s for s in schedules if not s["done"]], key=lambda x: x["start_date"])
    if upcoming:
        s = upcoming[0]
        summary_card("📅", "#42A5F5", "#EEF6FD", f"{importance_badge(s['importance'])} {s['title']} ({calc_dday(s['start_date'])})")
    else:
        summary_card("📅", "#42A5F5", "#EEF6FD", "예정된 일정이 없습니다.")

    recent_logs = sorted(farm_logs, key=lambda x: x["log_date"], reverse=True)
    if recent_logs:
        log = recent_logs[0]
        summary_card("📝", "#66BB6A", "#EFF8EF", f"{log['log_date']} · [{log['work_type']}] {log['zone']}")
    else:
        summary_card("📝", "#66BB6A", "#EFF8EF", "작성된 영농일지가 없습니다.")

    recent_docs = sorted(documents, key=lambda x: x["upload_date"], reverse=True)
    if recent_docs:
        d = recent_docs[0]
        summary_card("📁", "#FFA726", "#FFF6EA", f"{d['filename']} · [{d['category']}]")
    else:
        summary_card("📁", "#FFA726", "#FFF6EA", "업로드된 자료가 없습니다.")

with cal_col:
    st.markdown("**🗓️ 일정 캘린더**")

    if not CALENDAR_AVAILABLE:
        st.warning("캘린더 기능을 사용하려면 `requirements.txt`에 `streamlit-calendar`를 추가해주세요.")
    else:
        IMPORTANCE_COLORS = {"높음": "#FF6B6B", "보통": "#FFA726", "낮음": "#66BB6A"}

        def _fc_end(end_date_str: str) -> str:
            d = datetime.strptime(end_date_str, "%Y-%m-%d").date() + timedelta(days=1)
            return d.strftime("%Y-%m-%d")

        events = [
            {
                "id": s["id"],
                "title": ("✅ " if s["done"] else "") + s["title"],
                "start": s["start_date"],
                "end": _fc_end(s["end_date"]),
                "color": IMPORTANCE_COLORS.get(s["importance"], "#999999"),
            }
            for s in schedules
        ]

        calendar_options = {
            "initialView": "dayGridMonth",
            "locale": "ko",
            "height": 560,
            "selectable": True,
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        }

        cal_result = calendar(events=events, options=calendar_options, key="farm_calendar")
        callback_type = cal_result.get("callback") if cal_result else None

        if callback_type == "dateClick":
            st.session_state["cal_add_date"] = cal_result["dateClick"]["date"][:10]
            st.session_state.pop("cal_selected_event", None)
        elif callback_type == "eventClick":
            st.session_state["cal_selected_event"] = cal_result["eventClick"]["event"]
            st.session_state.pop("cal_add_date", None)

        st.caption("빈 날짜 클릭 → 일정 추가 · 기존 일정 클릭 → 삭제")

        if st.session_state.get("cal_add_date"):
            add_date = st.session_state["cal_add_date"]
            with st.form("cal_add_schedule_form"):
                st.markdown(f"**📅 {add_date}에 새 일정 추가**")
                new_title = st.text_input("일정 제목")
                col1, col2 = st.columns(2)
                with col1:
                    new_importance = st.selectbox("중요도", IMPORTANCE_LEVELS)
                with col2:
                    new_category = st.selectbox("범주", SCHEDULE_CATEGORIES)

                fc1, fc2 = st.columns(2)
                save_clicked = fc1.form_submit_button("💾 저장", use_container_width=True)
                cancel_clicked = fc2.form_submit_button("취소", use_container_width=True)

                if save_clicked:
                    if not new_title:
                        st.error("일정 제목을 입력해주세요.")
                    else:
                        db.add_schedule(new_title, add_date, add_date, new_importance, new_category)
                        st.session_state.pop("cal_add_date", None)
                        st.success("일정이 추가되었습니다.")
                        st.rerun()
                if cancel_clicked:
                    st.session_state.pop("cal_add_date", None)
                    st.rerun()

        if st.session_state.get("cal_selected_event"):
            ev = st.session_state["cal_selected_event"]
            with st.container(border=True):
                st.markdown(f"**선택한 일정**: {ev.get('title', '')}")
                dc1, dc2 = st.columns(2)
                if dc1.button("🗑️ 이 일정 삭제", use_container_width=True):
                    db.delete_schedule(ev["id"])
                    st.session_state.pop("cal_selected_event", None)
                    st.success("일정이 삭제되었습니다.")
                    st.rerun()
                if dc2.button("닫기", use_container_width=True):
                    st.session_state.pop("cal_selected_event", None)
                    st.rerun()
