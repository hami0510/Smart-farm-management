# -*- coding: utf-8 -*-
"""
📁 자료 관리함 화면
--------------------------------------------------
- 계약서, 영수증, 장비메뉴얼 등 파일 업로드
- 업로드된 파일은 로컬 디스크(data/uploads/)에 저장, 메타데이터는 SQLite에 저장
- 목록 조회, 카테고리 필터, 개별 다운로드/삭제
"""

import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from pathlib import Path

import db
from common import DOC_CATEGORIES

BASE_DIR = Path(__file__).parent.parent  # views/ 폴더의 상위 = 프로젝트 루트
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.title("📁 회사/농가 자료 관리함")
st.caption("업로드된 파일은 로컬 디스크(`data/uploads/`)에 저장되어 새로고침해도 유지됩니다.")

tab_upload, tab_manage = st.tabs(["⬆️ 자료 업로드", "🗂️ 보관함"])

with tab_upload:
    with st.form("doc_upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "파일 선택 (PDF, PNG, JPG, XLSX, CSV)",
            type=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"],
        )
        category = st.selectbox("문서 카테고리", DOC_CATEGORIES)
        description = st.text_area("문서 설명", placeholder="예: 2026년 7월 농자재 구매 영수증")

        submitted = st.form_submit_button("📤 업로드", use_container_width=True)
        if submitted:
            if uploaded_file is None:
                st.error("파일을 선택해주세요.")
            else:
                file_id = str(uuid.uuid4())
                ext = Path(uploaded_file.name).suffix
                stored_name = f"{file_id}{ext}"
                stored_path = UPLOAD_DIR / stored_name

                with open(stored_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                db.add_document(
                    filename=uploaded_file.name,
                    stored_name=stored_name,
                    category=category,
                    description=description,
                    upload_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    size_kb=round(uploaded_file.size / 1024, 1),
                )
                st.success(f"'{uploaded_file.name}' 업로드 완료!")
                st.rerun()

with tab_manage:
    docs = db.get_documents()
    if not docs:
        st.info("업로드된 자료가 없습니다.")
    else:
        cat_filter = st.multiselect("카테고리 필터", DOC_CATEGORIES, default=[])
        docs_view = docs if not cat_filter else [d for d in docs if d["category"] in cat_filter]

        if docs_view:
            docs_df = pd.DataFrame(docs_view)[
                ["filename", "category", "upload_date", "size_kb", "description"]
            ]
            docs_df.columns = ["파일명", "카테고리", "업로드일", "크기(KB)", "설명"]
            st.dataframe(docs_df, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("**개별 파일 다운로드 / 삭제**")
        for d in sorted(docs_view, key=lambda x: x["upload_date"], reverse=True):
            file_path = UPLOAD_DIR / d["stored_name"]
            colA, colB, colC, colD = st.columns([4, 2, 1.3, 1])
            colA.write(f"📄 **{d['filename']}**  \n_{d['description'] or '설명 없음'}_")
            colB.write(f"[{d['category']}]  \n{d['upload_date']}")
            if file_path.exists():
                with open(file_path, "rb") as f:
                    colC.download_button(
                        "⬇️", data=f.read(), file_name=d["filename"],
                        key=f"dl_{d['id']}", use_container_width=True,
                    )
            else:
                colC.caption("파일 없음")
            if colD.button("🗑️", key=f"del_doc_{d['id']}", use_container_width=True):
                deleted = db.delete_document(d["id"])
                if deleted and (UPLOAD_DIR / deleted["stored_name"]).exists():
                    os.remove(UPLOAD_DIR / deleted["stored_name"])
                st.rerun()
