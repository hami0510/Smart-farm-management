# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
1) 오늘의 현황 (가로 카드 4개)
2) 일정 캘린더 (박스형 미니멀 스타일)
세로 공간을 절약하되, 내부 스크롤이 생기지 않도록 캘린더는 auto 높이 사용.
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

IMPORTANCE_COLORS = {"높음": "#FF6B6B", "보통": "#FFA726", "낮음": "#66BB6A"}


# ============================================================
# 공통 스타일
# ============================================================
st.markdown(
    """
    <style>
    /* 페이지 하단 여백만 축소 (상단은 툴바 가림 방지를 위해 유지) */
    .block-container { padding-bottom: 1rem !important; }

    /* 헤더 */
    .page-header { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
    .page-title { font-size: 1.55em; font-weight: 800; color: #1B5E20; }
    .page-sub { font-size: 0.8em; color: #888; }

    /* 오늘의 현황 카드 */
    .status-card {
        border-radius: 10px;
        padding: 9px 12px;
        min-height: 60px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.06);
    }
    .status-badge {
        width: 21px; height: 21px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 11px; flex-shrink: 0;
    }
    .status-label { font-size: 0.67em; font-weight: 700; letter-spacing: 0.03em; }
    .status-value { font-size: 0.85em; color: #2B2B2B; margin-top: 4px; line-height: 1.3; }

    /* 섹션 타이틀 */
    .section-title {
        font-size: 0.98em; font-weight: 700; color: #2E7D32;
        margin: 10px 0 6px 0;
    }
    .cal-legend { font-size: 0.75em; color: #999; font-weight: 400; }
    .cal-legend .dot {
        display: inline-block; width: 8px; height: 8px; border-radius: 50%;
        margin-right: 3px; vertical-align: middle;
    }

    /* ===== 캘린더: 박스형 미니멀 ===== */
    .fc { border: none !important; box-shadow: none !important; }
    .fc-theme-standard td, .fc-theme-standard th { border: none !important; }
    .fc-scrollgrid { border: none !important; }

    .fc-header-toolbar { margin-bottom: 0.5em !important; }
    .fc-toolbar-title { font-weight: 700; color: #222; font-size: 1.05em !important; }
    .fc-button {
        background: #FFFFFF !important;
        color: #333 !important;
        border: 1px solid #DDD !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        padding: 4px 12px !important;
        font-size: 0.85em !important;
    }
    .fc-button:hover { background: #F5F5F5 !important; }
    .fc-button-active { background: #EEE !important; }

    .fc-col-header-cell {
        background: transparent !important;
        border: none !important;
        font-weight: 600;
        color: #666;
        font-size: 0.82em;
        padding-bottom: 4px !important;
    }
    .fc-col-header-cell.fc-day-sun { color: #E53935 !important; }
    .fc-col-header-cell.fc-day-sat { color: #1E88E5 !important; }

    .fc-daygrid-day-frame {
        border: 1.5px solid #E6E6E6 !important;
        border-radius: 8px !important;
        margin: 2px !important;
        background: #FFFFFF;
        min-height: 46px !important;
        padding: 2px !important;
    }
    .fc-daygrid-day.fc-day-sun .fc-daygrid-day-number { color: #E53935; }
    .fc-daygrid-day.fc-day-sat .fc-daygrid-day-number { color: #1E88E5; }
    .fc-daygrid-day-number { font-weight: 500; color: #444; font-size: 0.84em; padding: 3px 6px !important; }
    .fc-day-other .fc-daygrid-day-frame { background: #FAFAFA; border-color: #F0F0F0 !important; }

    .fc-day-today .fc-daygrid-day-frame {
        border: 2px solid #222222 !important;
        background: #FFFFFF !important;
    }

    .fc-event {
        border-radius: 5px !important;
        border: none !important;
        padding: 1px 6px !important;
        font-size: 0.7em !important;
        font-weight: 500;
    }
    .fc-daygrid-more-link { font-size: 0.7em !important; }

    @media (max-width: 640px) {
        .page-title { font-size: 1.2em; }
        .status-card { padding: 7px 9px; min-height: 54px; }
        .status-badge { width: 18px; height: 18px; font-size: 9px; }
        .status-label { font-size: 0.6em; }
        .status-value { font-size: 0.76em; }
        .fc-daygrid-day-frame { min-height: 38px !important; }
        .fc-daygrid-day-number { font-size: 0.74em; }
        .fc-event { font-size: 0.62em !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def status_card(icon: str, accent: str, bg: str, label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="status-card" style="background:{bg}; border-left:4px solid {accent};">
            <div style="display:flex; align-items:center; gap:6px;">
                <div class="status-badge" style="background:{accent}; color:white;">{icon}</div>
                <div class="status-label" style="color:{accent};">{label}</div>
            </div>
            <div class="status-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 헤더 (타이틀 + 위치를 한 줄로)
# ============================================================
loc = st.session_state.farm_location
st.markdown(
    f"""
    <div class="page-header">
        <span class="page-title">🌾 스마트팜 종합 농가 관리 시스템</span>
        <span class="page-sub">📍 {loc['name']}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

weather = get_weather(loc["lat"], loc["lon"], st.session_state.api_key)

if weather["wind_speed"] >= 10:
    st.warning(f"🌬️ **강풍 주의!** 풍속 {weather['wind_speed']} m/s — 시설물 점검을 권장합니다.")
if any(k in weather["description"] for k in ["비", "폭우", "소나기"]):
    st.warning(f"🌧️ 강우 예보: {weather['description']} — 배수로를 미리 점검하세요.")

farm_logs = db.get_farm_logs()
schedules = db.get_schedules()
documents = db.get_documents()

# ============================================================
# 1) 오늘의 현황
# ============================================================
st.markdown('<div class="section-title">📋 오늘의 현황</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    mock_note = " (목업)" if weather["is_mock"] else ""
    status_card("☀️", "#00897B", "#DDF3EF", f"오늘 날씨{mock_note}",
                f"{weather['temp']}℃ · 💧{weather['humidity']}% · 💨{weather['wind_speed']}m/s")

with c2:
    upcoming = sorted([s for s in schedules if not s["done"]], key=lambda x: x["start_date"])
    if upcoming:
        s = upcoming[0]
        status_card("📅", "#1E88E5", "#DCEBFB", "다음 일정",
                    f"{importance_badge(s['importance'])} {s['title']} ({calc_dday(s['start_date'])})")
    else:
        status_card("📅", "#1E88E5", "#DCEBFB", "다음 일정", "예정된 일정이 없습니다.")

with c3:
    recent_logs = sorted(farm_logs, key=lambda x: x["log_date"], reverse=True)
    if recent_logs:
        log = recent_logs[0]
        status_card("📝", "#43A047", "#DFF3DE", "최근 영농일지",
                    f"{log['log_date']} · [{log['work_type']}] {log['zone']}")
    else:
        status_card("📝", "#43A047", "#DFF3DE", "최근 영농일지", "작성된 일지가 없습니다.")

with c4:
    recent_docs = sorted(documents, key=lambda x: x["upload_date"], reverse=True)
    if recent_docs:
        d = recent_docs[0]
        status_card("📁", "#FB8C00", "#FFE9CC", "최근 업로드 자료",
                    f"{d['filename']} · [{d['category']}]")
    else:
        status_card("📁", "#FB8C00", "#FFE9CC", "최근 업로드 자료", "업로드된 자료가 없습니다.")

# ============================================================
# 2) 일정 캘린더
# ============================================================
legend_html = " · ".join(
    f'<span class="dot" style="background:{c};"></span>{lv}' for lv, c in IMPORTANCE_COLORS.items()
)
st.markdown(
    f'<div class="section-title">🗓️ 일정 캘린더 '
    f'<span class="cal-legend">{legend_html} &nbsp;|&nbsp; 날짜 클릭 → 등록 · 일정 클릭 → 삭제</span>'
    f'</div>',
    unsafe_allow_html=True,
)

if not CALENDAR_AVAILABLE:
    st.warning("캘린더 기능을 사용하려면 `requirements.txt`에 `streamlit-calendar`를 추가해주세요.")
else:
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

    if "cal_initial_date" not in st.session_state:
        st.session_state["cal_initial_date"] = datetime.now().strftime("%Y-%m-%d")

    calendar_options = {
        "initialView": "dayGridMonth",
        "initialDate": st.session_state["cal_initial_date"],
        "locale": "ko",
        "height": "auto",          # 내부 스크롤바가 생기지 않도록 자동 높이
        "fixedWeekCount": False,   # 빈 주는 그리지 않음
        "dayMaxEventRows": 2,      # 칸당 이벤트 2개까지, 나머지는 '+더보기'
        "selectable": True,
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
    }

    cal_key = f"farm_calendar_{st.session_state['cal_initial_date']}"
    cal_result = calendar(events=events, options=calendar_options, key=cal_key)
    callback_type = cal_result.get("callback") if cal_result else None

    if callback_type == "dateClick":
        st.session_state["cal_add_date"] = cal_result["dateClick"]["date"][:10]
        st.session_state.pop("cal_selected_event", None)
    elif callback_type == "eventClick":
        st.session_state["cal_selected_event"] = cal_result["eventClick"]["event"]
        st.session_state.pop("cal_add_date", None)

    # ---- 새 일정 추가 (날짜 클릭 시에만 표시) ----
    if st.session_state.get("cal_add_date"):
        add_date = st.session_state["cal_add_date"]
        with st.form("cal_add_schedule_form"):
            st.markdown(f"**📅 {add_date} 새 일정 추가**")
            fc1, fc2, fc3 = st.columns([3, 1, 1])
            with fc1:
                new_title = st.text_input("일정 제목", label_visibility="collapsed", placeholder="일정 제목")
            with fc2:
                new_importance = st.selectbox("중요도", IMPORTANCE_LEVELS, label_visibility="collapsed")
            with fc3:
                new_category = st.selectbox("범주", SCHEDULE_CATEGORIES, label_visibility="collapsed")

            bc1, bc2 = st.columns(2)
            save_clicked = bc1.form_submit_button("💾 저장", use_container_width=True)
            cancel_clicked = bc2.form_submit_button("취소", use_container_width=True)

            if save_clicked:
                if not new_title:
                    st.error("일정 제목을 입력해주세요.")
                else:
                    db.add_schedule(new_title, add_date, add_date, new_importance, new_category)
                    st.session_state.pop("cal_add_date", None)
                    st.rerun()
            if cancel_clicked:
                st.session_state.pop("cal_add_date", None)
                st.rerun()

    # ---- 선택한 일정 삭제 (일정 클릭 시에만 표시) ----
    if st.session_state.get("cal_selected_event"):
        ev = st.session_state["cal_selected_event"]
        dc0, dc1, dc2 = st.columns([3, 1, 1])
        dc0.markdown(f"**선택한 일정**: {ev.get('title', '')}")
        if dc1.button("🗑️ 삭제", use_container_width=True):
            db.delete_schedule(ev["id"])
            st.session_state.pop("cal_selected_event", None)
            st.rerun()
        if dc2.button("닫기", use_container_width=True):
            st.session_state.pop("cal_selected_event", None)
            st.rerun()
