# -*- coding: utf-8 -*-
"""
🌾 스마트팜 종합 농가 관리 시스템
--------------------------------------------------
진입점(app.py): DB 연결 확인 후 st.navigation으로 4개 화면을 연결한다.
"""

import streamlit as st

import db
from common import init_common_session_state, render_sidebar_links, render_sidebar_backup

st.set_page_config(
    page_title="스마트팜 종합 농가 관리 시스템",
    page_icon="🌾",
    layout="wide",
)

db.init_db()
init_common_session_state()

with st.sidebar:
    st.markdown("## 🌾 스마트팜 관리")

render_sidebar_links()
render_sidebar_backup()

dashboard_page = st.Page("views/dashboard.py", title="대시보드", icon="🏠", default=True)
farmlog_page = st.Page("views/farmlog.py", title="영농일지", icon="📝")
documents_page = st.Page("views/documents.py", title="자료관리함", icon="📁")
schedule_page = st.Page("views/schedule.py", title="일정관리", icon="📅")

pg = st.navigation([dashboard_page, farmlog_page, documents_page, schedule_page])
pg.run()
