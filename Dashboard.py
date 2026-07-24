# -*- coding: utf-8 -*-
"""
🌾 스마트팜 종합 농가 관리 시스템
[STEP 2] 메인 진입점(app.py) - 대시보드 + 사이드바 설정

멀티페이지 구조:
- 이 파일(app.py)이 홈 화면(대시보드) 역할을 합니다.
- 영농일지 / 자료 관리함 / 일정 관리는 pages/ 폴더의 별도 파일로 추가될 예정이며,
  Streamlit이 자동으로 사이드바 상단에 페이지 이동 메뉴를 만들어줍니다.
"""

import streamlit as st

import db
from common import (
    init_common_session_state,
    render_sidebar_settings,
    get_weather,
    calc_dday,
    importance_badge,
)

# ------------------------------------------------------------
# 페이지 기본 설정 (반드시 다른 st 명령보다 먼저 호출)
# ------------------------------------------------------------
st.set_page_config(
    page_title="스마트팜 종합 농가 관리 시스템",
    page_icon="🌾",
    layout="wide",
)

# ------------------------------------------------------------
# DB 준비: 테이블이 없으면 생성 + 비어있으면 샘플 데이터 삽입
# ------------------------------------------------------------
db.init_db()
db.seed_sample_data_if_empty()

# ------------------------------------------------------------
# 세션 상태 초기화 (농장 위치, API 키)
# ------------------------------------------------------------
init_common_session_state()

# ------------------------------------------------------------
# 사이드바: 공통 설정 UI
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌾 스마트팜 관리")
    st.divider()

render_sidebar_settings()

# ------------------------------------------------------------
# 메인 화면: 대시보드
# ------------------------------------------------------------
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

# ---- 목업/오류 안내 ----
if weather["is_mock"]:
    if weather["error"]:
        st.info(f"⚠️ 실시간 날씨 연동에 실패해 가상 데이터를 표시 중입니다. (사유: {weather['error']})")
    else:
        st.info("⚠️ API 키가 입력되지 않아 가상(목업) 날씨 데이터를 표시 중입니다.")

# ---- 안전 경고 (강풍/폭우) ----
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

# DB에서 실제 데이터 조회
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
        st.caption("업로드된 자료가 없습니다. (자료 관리함 페이지는 다음 단계에서 추가됩니다)")
