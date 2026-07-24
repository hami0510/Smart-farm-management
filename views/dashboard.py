# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
좌측(좁게): 날씨 요약 + 오늘의 요약(탭)
우측(넓게): 일정 캘린더 (클릭으로 추가/삭제)
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

left_col, right_col = st.columns([1, 1.6], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown("**☀️ 실시간 날씨**")
        if weather["is_mock"]:
            st.caption("⚠️ " + ("가상 데이터 표시 중" if not weather["error"] else f"연동 실패: {weather['error']}"))
        wc1, wc2 = st.columns(2)
        wc1.metric("기온", f"{weather['temp']} ℃")
        wc2.metric("습도", f"{weather['humidity']} %")
        wc3, wc4 = st.columns(2)
        wc3.metric("풍속", f"{weather['wind_speed']} m/s")
        wc4.metric("날씨", weather["description"])

    st.markdown("**📌 오늘의 요약**")
    tab_sched, tab_log, tab_doc = st.tabs(["📅 일정", "📝 일지", "📁 자료"])

    with tab_sched:
        upcoming = sorted([s for s in schedules if not s["done"]], key=lambda x: x["start_date"])[:5]
        if upcoming:
            for s in upcoming:
                st.write(f"- {importance_badge(s['importance'])} **{s['title']}** ({calc_dday(s['start_date'])})")
        else:
            st.caption("등록된 일정이 없습니다.")

    with tab_log:
        recent_logs = sorted(farm_logs, key=lambda x: x["log_date"], reverse=True)[:5]
        if recent_logs:
            for log in recent_logs:
                st.write(f"- {log['log_date']} · [{log['work_type']}] {log['zone']}")
        else:
            st.caption("작성된 영농일지가 없습니다.")

    with tab_doc:
        recent_docs = sorted(documents, key=lambda x: x["upload_date"], reverse=True)[:5]
        if recent_docs:
            for d in recent_docs:
                st.write(f"- 📄 {d['filename']} · [{d['category']}]")
        else:
            st.caption("업로드된 자료가 없습니다.")

with right_col:
    st.markdown("**🗓️ 일정 캘린더**")

    if not CALENDAR_AVAILABLE:
        st.warning("캘린더 기능을 사용하려면 `requirements.txt`에 `streamlit-calendar`를 추가해주세요.")
    else:
        IMPORTANCE_COLORS = {"높음": "#FF4B4B", "보통": "#FFA500", "낮음": "#2ECC71"}

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

        custom_css = """
            .fc-day-today {
                box-shadow: inset 0 0 0 3px #FF4B4B !important;
                background-color: transparent !important;
            }
            .fc-daygrid-day-frame {
                padding: 2px !important;
            }
            .fc-event {
                cursor: pointer;
                font-size: 0.8em !important;
            }
        """

        cal_result = calendar(events=events, options=calendar_options, custom_css=custom_css, key="farm_calendar")
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
