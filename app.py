import streamlit as st
import psycopg2
import os
import pandas as pd

st.set_page_config(page_title="DB 스캐너", page_icon="🔍")
st.title("🔍 Streamlit 접속 위치 스캔 결과")

db_url = os.environ.get("DATABASE_URL")

try:
    conn = psycopg2.connect(db_url)
    st.success("✅ 서버 접속 성공! 현재 연결된 창고 안을 살펴봅니다...")

    # public 스키마에 있는 모든 테이블 이름 가져오기
    query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    tables = pd.read_sql(query, conn)
    
    if tables.empty:
        st.warning("⚠️ 창고가 완전히 텅 비어있습니다! (테이블 0개)")
        st.info("👉 DBeaver로 접속했던 DB와 완전히 다른 빈 DB 주소가 입력된 상태입니다.")
    else:
        st.write(f"📂 현재 연결된 DB에 있는 테이블 목록 (총 {len(tables)}개):")
        st.dataframe(tables, use_container_width=True)
        
        # 힌트 제공
        table_list = tables['table_name'].tolist()
        if 'workflow_entity' in table_list or 'execution_entity' in table_list:
            st.error("🚨 잠시만요! 이곳은 n8n 시스템이 사용하는 'n8n 내장 DB'입니다!")
            st.write("데이터를 저장하기 위해 만든 DB 주소가 아니라, n8n 앱 구동용 주소를 잘못 복사하셨습니다.")

except Exception as e:
    st.error("❌ 알 수 없는 에러가 발생했습니다.")
    st.write(e)
