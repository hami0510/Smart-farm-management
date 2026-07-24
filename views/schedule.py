# -*- coding: utf-8 -*-
"""
📅 일정 관리 화면
--------------------------------------------------
- 일정 등록 (제목 / 시작일 / 종료일 / 중요도 / 범주)
- 스케줄러 뷰: D-Day 순 정렬, 완료 체크, 삭제
"""

import streamlit as st
from datetime import date

import db
from common import SCHEDULE_CATEGORIES, IMPORTANCE_LEVELS, calc_dday, importance_badge

st.title("📅 일정 관리")

tab_add, tab_view = st.tabs(["➕ 일정 등록", "📋 스케줄러 뷰"])

with tab_add:
    with st.form("schedule_form", clear_on_submit=True):
        title = st.text_input("일정 제목", placeholder="예: 3동 고추 수확")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", value=date.today())
        with col2:
            end_date = st.date_input("종료일", value=date.today())
        col3, col4 = st.columns(2)
        with col3:
            importance = st.selectbox("중요도", IMPORTANCE_LEVELS)
        with col4:
            category = st.selectbox("범주", SCHEDULE_CATEGORIES)

        submitted = st.form_submit_button("💾 일정 저장", use_container_width=True)
        if submitted:
            if not title:
                st.error("일정 제목을 입력해주세요.")
            elif end_date < start_date:
                st.error("종료일은 시작일보다 빠를 수 없습니다.")
            else:
                db.add_schedule(
                    title,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    importance,
                    category,
                )
                st.success("일정이 등록되었습니다.")
                st.rerun()

with tab_view:
    schedules = db.get_schedules()
    if not schedules:
        st.info("등록된 일정이 없습니다.")
    else:
        show_done = st.checkbox("완료된 일정도 표시", value=False)

        visible = schedules if show_done else [s for s in schedules if not s["done"]]
        visible = sorted(visible, key=lambda x: x["start_date"])

        for s in visible:
            col1, col2, col3 = st.columns([0.6, 6, 1.5])
            with col1:
                checked = st.checkbox("", value=bool(s["done"]), key=f"chk_{s['id']}")
                if checked != bool(s["done"]):
                    db.update_schedule_done(s["id"], checked)
                    st.rerun()
            with col2:
                strike = "~~" if s["done"] else ""
                st.markdown(
                    f"{strike}**{s['title']}**{strike}  \n"
                    f"{importance_badge(s['importance'])} · [{s['category']}] · "
                    f"{s['start_date']} ~ {s['end_date']} · **{calc_dday(s['start_date'])}**"
                )
            with col3:
                if st.button("🗑️ 삭제", key=f"del_sch_{s['id']}", use_container_width=True):
                    db.delete_schedule(s["id"])
                    st.rerun()
            st.divider()
