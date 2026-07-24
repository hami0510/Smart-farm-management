# -*- coding: utf-8 -*-
"""
📁 자료 관리함 화면
--------------------------------------------------
- 계약서, 영수증, 장비메뉴얼 등 파일 업로드
- 파일 원본은 Supabase Storage에, 메타데이터는 Supabase DB에 저장
  → 새로고침/재배포 후에도 자료가 그대로 유지된다
- 목록 조회, 카테고리 필터, 개별 다운로드/삭제
"""

import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import db
from common import DOC_CATEGORIES

st.title("📁 회사/농가 자료 관리함")
st.caption("업로드된 파일은 클라우드(Supabase Storage)에 저장되어 새로고침해도 유지됩니다.")

tab_upload, tab_manage = st.tabs(["⬆️ 자료 업로드", "🗂️ 보관함"])

# ============================================================
# 1. 자료 업로드
# ============================================================
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
                # 파일명 충돌을 막기 위해 고유 ID를 붙여 저장
                file_id = str(uuid.uuid4())
                ext = Path(uploaded_file.name).suffix
                stored_name = f"{file_id}{ext}"

                try:
                    db.upload_file_to_storage(
                        stored_name=stored_name,
                        file_bytes=uploaded_file.getvalue(),
                        content_type=uploaded_file.type or "application/octet-stream",
                    )
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
                except Exception as e:
                    st.error(f"업로드에 실패했습니다: {e}")

# ============================================================
# 2. 보관함 (목록 / 다운로드 / 삭제)
# ============================================================
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
        for d in docs_view:
            colA, colB, colC, colD = st.columns([4, 2, 1.3, 1])
            colA.write(f"📄 **{d['filename']}**  \n_{d['description'] or '설명 없음'}_")
            colB.write(f"[{d['category']}]  \n{d['upload_date']}")

            file_bytes = db.download_file_from_storage(d["stored_name"])
            if file_bytes:
                colC.download_button(
                    "⬇️", data=file_bytes, file_name=d["filename"],
                    key=f"dl_{d['id']}", use_container_width=True,
                )
            else:
                colC.caption("파일 없음")

            if colD.button("🗑️", key=f"del_doc_{d['id']}", use_container_width=True):
                deleted = db.delete_document(d["id"])
                if deleted:
                    db.remove_file_from_storage(deleted["stored_name"])
                st.rerun()
