# -*- coding: utf-8 -*-
"""
📝 영농일지 화면
--------------------------------------------------
- 일지 작성 (사진 첨부 지원)
- 일지 목록 조회 + 검색/필터 + CSV 다운로드
- 통계: 월별 수확량·매출 추이, 작업 유형 분포
"""

import uuid
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import db
from common import WORK_TYPES

st.title("📝 영농일지")

tab_write, tab_list, tab_stats = st.tabs(["✍️ 일지 작성", "📚 일지 조회/검색", "📊 통계"])

# ============================================================
# 1. 일지 작성
# ============================================================
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

        photo = st.file_uploader(
            "📷 사진 첨부 (선택) — 병해 기록, 생육 상태 등",
            type=["png", "jpg", "jpeg"],
        )

        submitted = st.form_submit_button("➕ 일지 저장", use_container_width=True)
        if submitted:
            if not zone or not detail:
                st.error("구역/동과 작업 상세 내용은 필수 입력 항목입니다.")
            else:
                photo_name = None
                try:
                    if photo is not None:
                        ext = Path(photo.name).suffix
                        photo_name = f"log_{uuid.uuid4()}{ext}"
                        db.upload_file_to_storage(
                            stored_name=photo_name,
                            file_bytes=photo.getvalue(),
                            content_type=photo.type or "image/jpeg",
                        )

                    db.add_farm_log(
                        log_date.strftime("%Y-%m-%d"),
                        zone,
                        work_type,
                        detail,
                        materials or "-",
                        harvest_kg,
                        sales,
                        photo_name,
                    )
                    st.success("영농일지가 저장되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장에 실패했습니다: {e}")

# ============================================================
# 2. 일지 조회 / 검색 / 필터 / CSV 다운로드
# ============================================================
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
            photo_mark = " 📷" if row.get("photo_name") else ""
            with st.expander(f"📅 {row['log_date']} · [{row['work_type']}] {row['zone']}{photo_mark}"):
                st.write(f"**상세 내용**: {row['detail']}")
                st.write(f"**사용 농자재**: {row['materials']}")

                if row.get("photo_name"):
                    photo_url = db.get_public_url(row["photo_name"])
                    if photo_url:
                        st.image(photo_url, width=360)

                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("수확량", f"{row['harvest_kg']} kg")
                cc2.metric("매출액", f"{int(row['sales']):,} 원")
                if cc3.button("🗑️ 삭제", key=f"del_log_{row['id']}"):
                    db.delete_farm_log(row["id"])
                    st.rerun()

        st.divider()
        csv_cols = [c for c in filtered.columns if c not in ("id", "photo_name")]
        csv_data = filtered[csv_cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ CSV로 다운로드",
            data=csv_data,
            file_name=f"영농일지_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ============================================================
# 3. 통계
# ============================================================
with tab_stats:
    logs = db.get_farm_logs()
    df = pd.DataFrame(logs)

    if df.empty:
        st.info("통계를 표시할 데이터가 없습니다. 영농일지를 먼저 작성해주세요.")
    else:
        df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
        df = df.dropna(subset=["log_date"])
        df["연월"] = df["log_date"].dt.strftime("%Y-%m")
        df["harvest_kg"] = pd.to_numeric(df["harvest_kg"], errors="coerce").fillna(0)
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0)

        # ---- 요약 지표 ----
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 일지 수", f"{len(df)} 건")
        m2.metric("총 수확량", f"{df['harvest_kg'].sum():,.1f} kg")
        m3.metric("총 매출액", f"{int(df['sales'].sum()):,} 원")
        avg_price = (df["sales"].sum() / df["harvest_kg"].sum()) if df["harvest_kg"].sum() > 0 else 0
        m4.metric("kg당 평균 단가", f"{int(avg_price):,} 원")

        st.divider()

        # ---- 월별 추이 ----
        monthly = df.groupby("연월").agg(
            수확량_kg=("harvest_kg", "sum"),
            매출액_원=("sales", "sum"),
        ).sort_index()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📦 월별 수확량 (kg)**")
            st.bar_chart(monthly["수확량_kg"], height=260)
        with c2:
            st.markdown("**💰 월별 매출액 (원)**")
            st.bar_chart(monthly["매출액_원"], height=260)

        st.divider()

        # ---- 작업 유형 / 구역별 분포 ----
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**🔧 작업 유형별 건수**")
            st.bar_chart(df["work_type"].value_counts(), height=240)
        with c4:
            st.markdown("**🏠 구역별 수확량 (kg)**")
            zone_sum = df.groupby("zone")["harvest_kg"].sum().sort_values(ascending=False)
            st.bar_chart(zone_sum, height=240)

        with st.expander("📋 월별 상세 표 보기"):
            show = monthly.copy()
            show["수확량_kg"] = show["수확량_kg"].round(1)
            show["매출액_원"] = show["매출액_원"].astype(int)
            st.dataframe(show, use_container_width=True)
