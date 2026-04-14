import streamlit as st
import psycopg2
import os
import pandas as pd

st.set_page_config(page_title="DB 연결 확인", page_icon="🔌")
st.title("🔌 PostgreSQL 연결 및 테이블 확인 도구")

db_url = os.environ.get("DATABASE_URL")

if not db_url:
    st.error("🚨 DATABASE_URL 환경 변수가 설정되어 있지 않습니다. Railway 설정(Variables)을 확인해주세요.")
    st.stop()

st.write("데이터베이스 연결을 시도합니다...")

try:
    # 1. DB 연결 시도
    conn = psycopg2.connect(db_url)
    st.success("✅ PostgreSQL 데이터베이스에 성공적으로 연결되었습니다! (인증 및 접속 통과)")

    # 2. 현재 DB에 존재하는 모든 테이블 목록 가져오기 (public 스키마 기준)
    query_tables = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """
    with conn.cursor() as cur:
        cur.execute(query_tables)
        tables = cur.fetchall()

    if not tables:
        st.warning("⚠️ 연결은 성공했지만, 만들어진 테이블이 하나도 없습니다. (빈 데이터베이스입니다)")
    else:
        table_names = [table[0] for table in tables]
        st.write(f"📂 현재 데이터베이스에 총 **{len(table_names)}**개의 테이블이 발견되었습니다.")
        st.dataframe(pd.DataFrame({"존재하는 테이블 이름": table_names}), use_container_width=True)

        # 3. 만약 우리가 찾던 테이블이 있다면 컬럼 구조까지 파악하기
        target_table = 'teen_trend_questions'
        
        if target_table in table_names:
            st.info(f"🎯 '{target_table}' 테이블을 찾았습니다! 내부 컬럼 구조는 다음과 같습니다:")
            
            query_columns = f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{target_table}';
            """
            cur.execute(query_columns)
            columns = cur.fetchall()
            st.dataframe(pd.DataFrame(columns, columns=["컬럼 이름", "데이터 타입"]), use_container_width=True)
            
        else:
            st.error(f"❌ 데이터베이스에 '{target_table}' 테이블이 없습니다!")
            st.write("👉 해결책: 위 표에 나온 '존재하는 테이블 이름' 중 진짜 테이블을 찾아 코드를 수정하거나, DB에 테이블을 새로 만들어야 합니다.")

except Exception as e:
    st.error("🚨 데이터베이스 연결에 실패했습니다!")
    st.write("Railway의 DATABASE_URL 변수 값이 올바른지, DB 서비스가 켜져 있는지 확인해 주세요.")
    st.exception(e)
