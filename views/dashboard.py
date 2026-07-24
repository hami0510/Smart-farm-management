# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
1) 오늘의 현황 (상단, 레이블+아이콘 배지가 있는 카드 4개)
2) 일정 캘린더 (하단, 전체 너비, 주말 색상 구분, 모바일 반응형)
디자인: 섹션 타이틀 위계 강화, 카드 색상 진하게, 캘린더 주말 강조 + 모바일 최적화
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
# 공통 스타일 주입 (+ 모바일 반응형)
# ============================================================
st.markdown(
    """
    <style>
    .fc {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid #E4EFDF;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
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
    .fc-button:hover { background: #3d8b40 !important; }
    .fc-button-active { background: #2E7D32 !important; }

    /* 평일 헤더 */
    .fc-col-header-cell { background: #F1F8F0; font-weight: 600; color: #4A6B4A; }
    /* 주말 색상 구분 */
    .fc-col-header-cell.fc-day-sun { background: #FBEAEA; color: #C62828; }
    .fc-col-header-cell.fc-day-sat { background: #E9F1FC; color: #1565C0; }
    .fc-daygrid-day.fc-day-sun { background: #FFFAFA; }
    .fc-daygrid-day.fc-day-sat { background: #FAFCFF; }
    .fc-day-sun .fc-daygrid-day-number { color: #C62828; }
    .fc-day-sat .fc-daygrid-day-number { color: #1565C0; }

    .fc-daygrid-day-frame { padding: 3px !important; }
    .fc-day-today .fc-daygrid-day-frame {
        background: #FFF1D6 !important;
        border-radius: 12px;
        box-shadow: inset 0 0 0 2px #FB8C00;
        margin: 3px;
    }
    .fc-daygrid-day-number { font-weight: 500; color: #4A5A4A; }
    .fc-event {
        border-radius: 8px !important;
        border: none !important;
        padding: 2px 8px !important;
        font-size: 0.78em !important;
        font-weight: 500;
    }

    /* 오늘의 현황 카드 */
    .status-card {
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 6px;
        min-height: 76px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .status-badge {
        width: 26px; height: 26px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; flex-shrink: 0;
    }
    .status-label {
        font-size: 0.7em; font-weight: 700; letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .status-value {
        font-size: 0.92em; color: #2B2B2B; margin-top: 6px; line-height: 1.35;
    }

    /* 섹션 타이틀 */
    .section-title-row {
        display: flex; align-items: center; gap: 8px; margin: 14px 0 4px 0;
    }
    .section-title-icon { font-size: 1.25em; }
    .section-title-text { font-size: 1.12em; font-weight: 700; }
    .section-title-underline {
        height: 3px; width: 46px; border-radius: 2px; margin: 4px 0 14px 0;
    }

    /* 모바일 반응형 (좁은 화면에서 카드/캘린더 글자·여백 축소) */
    @media (max-width: 640px) {
        .section-title-text { font-size: 1em; }
        .section-title-icon { font-size: 1.1em; }
        .status-card { padding: 10px 10px; min-height: 60px; margin-bottom: 8px; }
        .status-badge { width: 22px; height: 22px; font-size: 11px; }
        .status-label { font-size: 0.64em; }
        .status-value { font-size: 0.82em; margin-top: 4px; }
        .fc-toolbar-title { font-size: 1em !important; }
        .fc-button { padding: 4px 8px !important; font-size: 0.8em !important; }
        .fc-col-header-cell { font-size: 0.78em; }
        .fc-daygrid-day-number { font-size: 0.8em; }
        .fc-event { font-size: 0.68em !important; padding: 1px 4px !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def section_title(icon: str, text: str, color: str = "#2E7D32") -> None:
    st.markdown(
        f"""
        <div class="section-title-row">
            <div class="section-title-icon">{icon}</div>
            <div class="section-title-text" style="color:{color};">{text}</div>
        </div>
        <div class="section-title-underline" style="background:{color};"></div>
        """,
        unsafe_allow_html=True,
    )


def status_card(icon: str, accent_color: str, bg_color: str, label: str, value_text: str) -> None:
    st.markdown(
        f"""
        <div class="status-card" style="background:{bg_color}; border-left:5px solid {accent_color};">
            <div style="display:flex; align-items:center; gap:8px;">
                <div class="status-badge" style="background:{accent_color}; color:white;">{icon}</div>
                <div class="status-label" style="color:{accent_color};">{label}</div>
            </div>
            <div class="status-value">{value_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 상단 타이틀 + 안전 경고
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

farm_logs = db.get_farm_logs()
schedules = db.get_schedules()
documents = db.get_documents()

# ============================================================
# 1) 오늘의 현황
# ============================================================
section_title("📋", "오늘의 현황", "#2E7D32")

status1, status2, status3, status4 = st.columns(4)

with status1:
    mock_note = " (목업)" if weather["is_mock"] else ""
    status_card(
        "☀️", "#00897B", "#DDF3EF",
        f"오늘 날씨{mock_note}",
        f"{weather['temp']}℃ · 💧{weather['humidity']}% · 💨{weather['wind_speed']}m/s",
    )

with status2:
    upcoming = sorted([s for s in schedules if not s["done"]], key=lambda x: x["start_date"])
    if upcoming:
        s = upcoming[0]
        status_card("📅", "#1E88E5", "#DCEBFB", "다음 일정", f"{importance_badge(s['importance'])} {s['title']} ({calc_dday(s['start_date'])})")
    else:
        status_card("📅", "#1E88E5", "#DCEBFB", "다음 일정", "예정된 일정이 없습니다.")

with status3:
    recent_logs = sorted(farm_logs, key=lambda x: x["log_date"], reverse=True)
    if recent_logs:
        log = recent_logs[0]
        status_card("📝", "#43A047", "#DFF3DE", "최근 영농일지", f"{log['log_date']} · [{log['work_type']}] {log['zone']}")
    else:
        status_card("📝", "#43A047", "#DFF3DE", "최근 영농일지", "작성된 영농일지가 없습니다.")

with status4:
    recent_docs = sorted(documents, key=lambda x: x["upload_date"], reverse=True)
    if recent_docs:
        d = recent_docs[0]
        status_card("📁", "#FB8C00", "#FFE9CC", "최근 업로드 자료", f"{d['filename']} · [{d['category']}]")
    else:
        status_card("📁", "#FB8C00", "#FFE9CC", "최근 업로드 자료", "업로드된 자료가 없습니다.")

# ============================================================
# 2) 일정 캘린더
# ============================================================
section_title("🗓️", "일정 캘린더", "#2E7D32")

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
        "aspectRatio": 1.35,
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
