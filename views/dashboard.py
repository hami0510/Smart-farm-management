# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
실시간(또는 목업) 날씨, 강풍/폭우 안전 경고, 오늘의 핵심 요약,
그리고 클릭으로 일정을 추가/삭제할 수 있는 캘린더를 보여준다.
"""

from datetime import datetime, timedelta

import streamlit as st

import db
from common import (
    get_weather,
    calc_dday,
    importance_badge,
    SCHEDULE_CATEGORIES,
    IMPORTANCE_LEVELS,
)

try:
    from streamlit_calendar import calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

# ============================================================
# 1. 날씨
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

if weather["is_mock"]:
    if weather["error"]:
        st.info(f"⚠️ 실시간 날씨 연동에 실패해 가상 데이터를 표시 중입니다. (사유: {weather['error']})")
    else:
        st.info("⚠️ API 키가 입력되지 않아 가상(목업) 날씨 데이터를 표시 중입니다.")

if weather["wind_speed"] >= 10:
    st.warning(f"🌬️ **강풍 주의보급 수준입니다!** 현재 풍속 {weather['wind_speed']} m/s — 시설물 점검을 권장합니다.")
if any(k in weather["description"] for k in ["비", "폭우", "소나기"]):
    st.warning(f"🌧️ 강우 예보가 있습니다: {weather['description']} — 배수로를 미리 점검하세요.")

st.subheader("☀️ 실시간 날씨")
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡️ 기온", f"{weather['temp']} ℃")
c2.metric("💧 습도", f"{weather['humidity']} %")
c3.metric("💨 풍속", f"{weather['wind_speed']} m/s")
c4.metric("☁️ 날씨 상태", weather["description"])

# ============================================================
# 2. 오늘의 핵심 요약
# ============================================================
st.divider()
st.subheader("📌 오늘의 핵심 요약")

farm_logs = db.get_farm_logs()
schedules = db.get_schedules()
documents = db.get_documents()

s1, s2, s3 = st.columns(3)

with s1:
    st.markdown("**📅 다가오는 일정**")
    upcoming = sorted([s for s in schedules if not s["done"]], key=lambda x: x["start_date"])[:4]
    if upcoming:
        for s in upcoming:
            st.write(f"- {importance_badge(s['importance'])} **{s['title']}** ({calc_dday(s['start_date'])})")
    else:
        st.caption("등록된 일정이 없습니다.")

with s2:
    st.markdown("**📝 최근 영농일지**")
    recent_logs = sorted(farm_logs, key=lambda x: x["log_date"], reverse=True)[:4]
    if recent_logs:
        for log in recent_logs:
            st.write(f"- {log['log_date']} · [{log['work_type']}] {log['zone']}")
    else:
        st.caption("작성된 영농일지가 없습니다.")

with s3:
    st.markdown("**📁 최근 업로드 자료**")
    recent_docs = sorted(documents, key=lambda x: x["upload_date"], reverse=True)[:4]
    if recent_docs:
        for d in recent_docs:
            st.write(f"- 📄 {d['filename']} · [{d['category']}]")
    else:
        st.caption("업로드된 자료가 없습니다.")

# ============================================================
# 3. 일정 캘린더 (클릭으로 추가/삭제)
# ============================================================
st.divider()
st.subheader("🗓️ 일정 캘린더")

if not CALENDAR_AVAILABLE:
    st.warning("캘린더 기능을 사용하려면 `requirements.txt`에 `streamlit-calendar`를 추가해주세요.")
else:
    IMPORTANCE_COLORS = {"높음": "#FF4B4B", "보통": "#FFA500", "낮음": "#2ECC71"}

    def _fc_end(end_date_str: str) -> str:
        # FullCalendar는 all-day 이벤트의 end를 '포함하지 않는 날짜'로 취급하므로 +1일 처리
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
        "height": 620,
        "selectable": True,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
    }

    # 오늘 날짜 칸을 굵은 테두리로 강조
    custom_css = """
        .fc-day-today {
            border: 3px solid #FF4B4B !important;
        }
        .fc-event {
            cursor: pointer;
        }
    """

    cal_result = calendar(events=events, options=calendar_options, custom_css=custom_css, key="farm_calendar")
    callback_type = cal_result.get("callback") if cal_result else None

    # ---- 빈 날짜 클릭 -> 새 일정 추가 폼 열기 ----
    if callback_type == "dateClick":
        st.session_state["cal_add_date"] = cal_result["dateClick"]["date"][:10]
        st.session_state.pop("cal_selected_event", None)

    # ---- 기존 일정(이벤트) 클릭 -> 삭제 옵션 열기 ----
    elif callback_type == "eventClick":
        st.session_state["cal_selected_event"] = cal_result["eventClick"]["event"]
        st.session_state.pop("cal_add_date", None)

    st.caption("빈 날짜를 클릭하면 일정을 추가하고, 이미 있는 일정을 클릭하면 삭제할 수 있습니다.")

    # ---- 새 일정 추가 폼 ----
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

    # ---- 선택한 일정 삭제 옵션 ----
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
