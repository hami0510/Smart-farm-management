# -*- coding: utf-8 -*-
"""
🌾 스마트팜 종합 농가 관리 시스템
--------------------------------------------------
진입점(app.py): DB/세션 초기화 후 st.navigation으로 4개 화면을 연결한다.
각 화면의 사이드바 표시 이름을 여기서 한글로 직접 지정한다.
"""

import streamlit as st

import db
from common import init_common_session_state, render_sidebar_settings

# ------------------------------------------------------------
# 페이지 기본 설정 (반드시 다른 st 명령보다 먼저 호출)
# ------------------------------------------------------------
st.set_page_config(
    page_title="스마트팜 종합 농가 관리 시스템",
    page_icon="🌾",
    layout="wide",
)

# ------------------------------------------------------------
# DB 준비 + 세션 상태 초기화
# ------------------------------------------------------------
db.init_db()
db.seed_sample_data_if_empty()
init_common_session_state()

# ------------------------------------------------------------
# 사이드바 상단 타이틀 + 공통 설정(위치)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌾 스마트팜 관리")
    st.divider()

render_sidebar_settings()

# ------------------------------------------------------------
# 화면(페이지) 등록 - 표시 이름을 모두 한글로 통일
# ------------------------------------------------------------
dashboard_page = st.Page("views/dashboard.py", title="대시보드", icon="🏠", default=True)
farmlog_page = st.Page("views/farmlog.py", title="영농일지", icon="📝")
documents_page = st.Page("views/documents.py", title="자료관리함", icon="📁")
schedule_page = st.Page("views/schedule.py", title="일정관리", icon="📅")

pg = st.navigation([dashboard_page, farmlog_page, documents_page, schedule_page])
pg.run()
