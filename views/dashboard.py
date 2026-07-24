# -*- coding: utf-8 -*-
"""
🏠 대시보드 화면
--------------------------------------------------
실시간(또는 목업) 날씨, 강풍/폭우 안전 경고, 오늘의 핵심 요약을 보여준다.
"""

import streamlit as st

import db
from common import get_weather, calc_dday, importance_badge

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
