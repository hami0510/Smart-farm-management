# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
1) 오늘의 현황 (가로 카드 4개, 모바일에서는 세로 스택)
2) 일정 캘린더 (박스형 미니멀 스타일 + 대한민국 공휴일 표시)

중요: 캘린더는 iframe 안에서 렌더링되므로 st.markdown의 CSS가 적용되지 않는다.
      캘린더 스타일은 반드시 calendar(custom_css=...) 로 전달해야 한다.
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

try:
    import holidays as kr_holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False

IMPORTANCE_COLORS = {"높음": "#FF6B6B", "보통": "#FFA726", "낮음": "#66BB6A"}

# 제헌절은 2008년부터 공휴일이 아니므로 제외
EXCLUDED_HOLIDAYS = {"제헌절"}


@st.cache_data(ttl=86400)
def get_korean_holidays(years: tuple) -> dict:
    """대한민국 공휴일을 {날짜문자열: 명칭} 형태로 반환 (음력 명절/대체공휴일 포함)."""
    if not HOLIDAYS_AVAILABLE:
        return {}
    result = {}
    for d, name in kr_holidays.SouthKorea(years=list(years)).items():
        if name in EXCLUDED_HOLIDAYS:
            continue
        result[d.strftime("%Y-%m-%d")] = name
    return result


# ============================================================
# 페이지 스타일 (카드/타이틀 - 캘린더 제외)
# ============================================================
st.markdown(
    """
    <style>
    .block-container { padding-bottom: 1rem !important; }

    .page-header { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
    .page-title { font-size: 1.5em; font-weight: 800; color: #1B5E20; }
    .page-sub { font-size: 0.8em; color: #888; }

    .status-card {
        border-radius: 10px;
        padding: 9px 12px;
        min-height: 58px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.06);
    }
    .status-badge {
        width: 20px; height: 20px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 11px; flex-shrink: 0;
    }
    .status-label { font-size: 0.66em; font-weight: 700; letter-spacing: 0.03em; }
    .status-value { font-size: 0.84em; color: #2B2B2B; margin-top: 4px; line-height: 1.3; }

    .section-title {
        font-size: 0.98em; font-weight: 700; color: #2E7D32;
        margin: 10px 0 2px 0;
    }
    .cal-legend { font-size: 0.74em; color: #999; margin-bottom: 6px; }
    .cal-legend .dot {
        display: inline-block; width: 8px; height: 8px; border-radius: 50%;
        margin-right: 3px; vertical-align: middle;
    }

    @media (max-width: 640px) {
        .page-title { font-size: 1.15em; }
        .page-sub { font-size: 0.72em; }
        .status-card { padding: 7px 10px; min-height: 0; }
        .status-badge { width: 17px; height: 17px; font-size: 9px; }
        .status-label { font-size: 0.62em; }
        .status-value { font-size: 0.78em; margin-top: 2px; }
        .section-title { font-size: 0.9em; }
        .cal-legend { font-size: 0.68em; }
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
# 헤더
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
st.markdown('<div class="section-title">🗓️ 일정 캘린더</div>', unsafe_allow_html=True)

legend_html = " · ".join(
    f'<span class="dot" style="background:{c};"></span>{lv}' for lv, c in IMPORTANCE_COLORS.items()
)
st.markdown(
    f'<div class="cal-legend">{legend_html} · '
    f'<span class="dot" style="background:#FFEBEE; border:1px solid #D32F2F;"></span>공휴일'
    f' &nbsp;|&nbsp; 날짜 클릭 → 등록 · 일정 클릭 → 삭제</div>',
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

    # ---- 대한민국 공휴일을 캘린더에 표시 (앞뒤 연도까지 포함) ----
    base_year = datetime.strptime(st.session_state.get("cal_initial_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").year
    holiday_map = get_korean_holidays((base_year - 1, base_year, base_year + 1))
    for hdate, hname in holiday_map.items():
        events.append({
            "id": f"holiday_{hdate}",
            "title": hname,
            "start": hdate,
            "allDay": True,
            "color": "#FFEBEE",
            "textColor": "#D32F2F",
            "editable": False,
            "classNames": ["holiday-event"],
        })

    if "cal_initial_date" not in st.session_state:
        st.session_state["cal_initial_date"] = datetime.now().strftime("%Y-%m-%d")

    calendar_options = {
        "initialView": "dayGridMonth",
        "initialDate": st.session_state["cal_initial_date"],
        "locale": "ko",
        "height": "auto",
        "fixedWeekCount": False,
        "dayMaxEventRows": 3,
        "selectable": True,
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
    }

    # iframe 내부에 적용되는 캘린더 전용 CSS (반드시 custom_css로 전달)
    calendar_css = """
        .fc { border: none !important; box-shadow: none !important; font-family: inherit; }
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
            padding: 4px 10px !important;
            font-size: 0.85em !important;
        }
        .fc-button:hover { background: #F5F5F5 !important; }
        .fc-button-active { background: #EEEEEE !important; }

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
        .fc-daygrid-day-number {
            font-weight: 500; color: #444; font-size: 0.84em; padding: 3px 5px !important;
        }
        .fc-day-other .fc-daygrid-day-frame { background: #FAFAFA; border-color: #F0F0F0 !important; }

        .fc-day-today .fc-daygrid-day-frame {
            border: 2px solid #222222 !important;
            background: #FFFFFF !important;
        }

        .fc-event {
            border-radius: 5px !important;
            border: none !important;
            padding: 1px 5px !important;
            font-size: 0.7em !important;
            font-weight: 500;
        }
        .fc-daygrid-more-link { font-size: 0.7em !important; }

        /* 공휴일 이벤트 */
        .holiday-event {
            font-weight: 600 !important;
            background: #FFEBEE !important;
        }

        /* ---- 모바일 최적화 ---- */
        @media (max-width: 640px) {
            .fc-toolbar-title { font-size: 0.95em !important; }
            .fc-button { padding: 3px 8px !important; font-size: 0.75em !important; }
            .fc-col-header-cell { font-size: 0.68em; }
            .fc-daygrid-day-frame {
                min-height: 34px !important;
                margin: 1px !important;
                border-radius: 6px !important;
                border-width: 1px !important;
            }
            .fc-daygrid-day-number { font-size: 0.66em; padding: 2px 3px !important; }
            .fc-event { font-size: 0.55em !important; padding: 0px 3px !important; }
            .fc-daygrid-more-link { font-size: 0.55em !important; }
        }
    """

    cal_key = f"farm_calendar_{st.session_state['cal_initial_date']}"
    cal_result = calendar(
        events=events,
        options=calendar_options,
        custom_css=calendar_css,
        key=cal_key,
    )
    callback_type = cal_result.get("callback") if cal_result else None

    if callback_type == "dateClick":
        st.session_state["cal_add_date"] = cal_result["dateClick"]["date"][:10]
        st.session_state.pop("cal_selected_event", None)
    elif callback_type == "eventClick":
        clicked = cal_result["eventClick"]["event"]
        # 공휴일은 삭제 대상이 아니므로 무시
        if not str(clicked.get("id", "")).startswith("holiday_"):
            st.session_state["cal_selected_event"] = clicked
            st.session_state.pop("cal_add_date", None)

    # ---- 새 일정 추가 ----
    if st.session_state.get("cal_add_date"):
        add_date = st.session_state["cal_add_date"]
        with st.form("cal_add_schedule_form"):
            st.markdown(f"**📅 {add_date} 새 일정 추가**")
            new_title = st.text_input("일정 제목", label_visibility="collapsed", placeholder="일정 제목")
            fc1, fc2 = st.columns(2)
            with fc1:
                new_importance = st.selectbox("중요도", IMPORTANCE_LEVELS)
            with fc2:
                new_category = st.selectbox("범주", SCHEDULE_CATEGORIES)

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

    # ---- 선택한 일정 삭제 ----
    if st.session_state.get("cal_selected_event"):
        ev = st.session_state["cal_selected_event"]
        st.markdown(f"**선택한 일정**: {ev.get('title', '')}")
        dc1, dc2 = st.columns(2)
        if dc1.button("🗑️ 삭제", use_container_width=True):
            db.delete_schedule(ev["id"])
            st.session_state.pop("cal_selected_event", None)
            st.rerun()
        if dc2.button("닫기", use_container_width=True):
            st.session_state.pop("cal_selected_event", None)
            st.rerun()
