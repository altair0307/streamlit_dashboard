import streamlit as st
import psycopg2
import os

st.set_page_config(page_title="DB 연결 테스트", page_icon="🔌")
st.title("🔌 Streamlit <-> PostgreSQL 연결 테스트")

# 1. 환경 변수에서 주소 가져오기
db_url = os.environ.get("DATABASE_URL")

st.write("### 🔍 1. 환경 변수 확인")
if not db_url:
    st.error("❌ `DATABASE_URL` 환경 변수를 찾을 수 없습니다. Railway의 Streamlit 서비스 Variables 탭을 확인해 주세요.")
    st.stop()
else:
    st.success("✅ `DATABASE_URL` 환경 변수가 정상적으로 등록되어 있습니다.")

st.write("### 🔌 2. 데이터베이스 접속 및 조회 테스트")
try:
    # DB 연결 시도
    conn = psycopg2.connect(db_url)
    st.success("✅ 데이터베이스 서버에 성공적으로 접속했습니다!")

    # 데이터 개수 세어보기
    with conn.cursor() as cur:
        # 우리가 DBeaver에서 확인했던 그 테이블 이름!
        cur.execute("SELECT COUNT(*) FROM teen_trend_questions;")
        count = cur.fetchone()[0]
        
    st.info(f"🎉 축하합니다! `teen_trend_questions` 테이블 안에 현재 **{count}개**의 데이터가 들어있는 것을 확인했습니다.")

except psycopg2.Error as e:
    st.error("❌ 데이터베이스 접속 또는 조회에 실패했습니다.")
    st.error(f"상세 에러 내용: {e.pgerror}")
except Exception as e:
    st.error("❌ 알 수 없는 에러가 발생했습니다.")
    st.write(e)
