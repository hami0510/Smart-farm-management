# -*- coding: utf-8 -*-
"""
📝 영농일지 화면
--------------------------------------------------
- 일지 작성 (작성일자 / 구역 / 작업유형 / 상세내용 / 농자재 / 수확량 / 매출)
- 일지 목록 조회 + 검색/필터 + CSV 다운로드
"""

import streamlit as st
import pandas as pd
from datetime import date

import db
from common import WORK_TYPES

st.title("📝 영농일지")

tab_write, tab_list = st.tabs(["✍️ 일지 작성", "📚 일지 조회/검색"])

with tab_write:
    with st.form("farm_log_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            log_date = st.date_input("작성일자", value=date.today())
        with col2:
            zone = st.text_input("구역/동", placeholder="예: 1동, 2동")
        with col3:
            work_type = st.selectbox("작업 유형", WORK_TYPES)

        detail = st.text_area("작업 상세 내용", placeholder="오늘 진행한 작업 내용을 입력하세요")

        col4, col5 = st.columns(2)
        with col4:
            materials = st.text_input("사용 농자재", placeholder="예: 유기질 비료 20kg")
        with col5:
            harvest_kg = st.number_input("수확량 (kg)", min_value=0.0, step=0.5)

        sales = st.number_input("매출액 (원)", min_value=0, step=1000)

        submitted = st.form_submit_button("➕ 일지 저장", use_container_width=True)
        if submitted:
            if not zone or not detail:
                st.error("구역/동과 작업 상세 내용은 필수 입력 항목입니다.")
            else:
                db.add_farm_log(
                    log_date.strftime("%Y-%m-%d"),
                    zone,
                    work_type,
                    detail,
                    materials or "-",
                    harvest_kg,
                    sales,
                )
                st.success("영농일지가 저장되었습니다.")
                st.rerun()

with tab_list:
    logs = db.get_farm_logs()
    logs_df = pd.DataFrame(logs)

    if logs_df.empty:
        st.info("아직 작성된 영농일지가 없습니다.")
    else:
        f1, f2, f3 = st.columns(3)
        with f1:
            filter_type = st.multiselect("작업 유형 필터", WORK_TYPES, default=[])
        with f2:
            date_range = st.date_input(
                "기간 필터", value=(), help="시작일과 종료일을 선택하세요 (선택 안 하면 전체)"
            )
        with f3:
            keyword = st.text_input("🔍 상세 내용 검색", placeholder="키워드 입력")

        filtered = logs_df.copy()
        if filter_type:
            filtered = filtered[filtered["work_type"].isin(filter_type)]
        if keyword:
            filtered = filtered[filtered["detail"].str.contains(keyword, case=False, na=False)]
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_d, end_d = date_range
            filtered = filtered[
                (filtered["log_date"] >= start_d.strftime("%Y-%m-%d"))
                & (filtered["log_date"] <= end_d.strftime("%Y-%m-%d"))
            ]

        filtered = filtered.sort_values("log_date", ascending=False)
        st.caption(f"검색 결과: {len(filtered)}건")

        for _, row in filtered.iterrows():
            with st.expander(f"📅 {row['log_date']} · [{row['work_type']}] {row['zone']}"):
                st.write(f"**상세 내용**: {row['detail']}")
                st.write(f"**사용 농자재**: {row['materials']}")
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("수확량", f"{row['harvest_kg']} kg")
                cc2.metric("매출액", f"{row['sales']:,} 원")
                if cc3.button("🗑️ 삭제", key=f"del_log_{row['id']}"):
                    db.delete_farm_log(row["id"])
                    st.rerun()

        st.divider()
        csv_data = filtered.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ CSV로 다운로드",
            data=csv_data,
            file_name=f"영농일지_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
