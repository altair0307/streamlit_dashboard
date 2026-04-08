import streamlit as st
import pandas as pd
import psycopg2
import os

# 1. 페이지 기본 설정 (가장 먼저 와야 함)
st.set_page_config(page_title="익명 투표 앱 대시보드", page_icon="📊", layout="wide")
st.title("📊 트렌드 & 투표 현황 대시보드")

# 2. DB 연결 함수 (캐싱을 통해 매번 연결하는 부하 방지)
@st.cache_resource
def init_connection():
    # Railway의 PostgreSQL 환경 변수를 그대로 사용합니다.
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "데이터베이스_주소"),
        database=os.environ.get("PGDATABASE", "DB이름"),
        user=os.environ.get("PGUSER", "유저명"),
        password=os.environ.get("PGPASSWORD", "비밀번호"),
        port=os.environ.get("PGPORT", "5432")
    )

conn = init_connection()

# 3. 데이터 불러오기 함수 (10분마다 캐시 갱신)
@st.cache_data(ttl=600)
def load_data(query):
    with conn.cursor() as cur:
        cur.execute(query)
        # 컬럼명 가져오기
        columns = [desc[0] for desc in cur.description]
        # 데이터프레임으로 변환
        return pd.DataFrame(cur.fetchall(), columns=columns)

# ==========================================
# 📈 대시보드 레이아웃 구성
# ==========================================

# 상단 요약 지표 (Metrics)
st.header("💡 주간 요약 지표")
col1, col2, col3 = st.columns(3)

try:
    # 예시: 총 투표 수, 생성된 질문 수 등을 DB에서 쿼리해옵니다. (테이블명은 실제에 맞게 수정 필요)
    # total_votes = load_data("SELECT COUNT(*) FROM votes;")["count"][0]
    
    col1.metric("총 투표 참여 수", "1,245 건", "+15%")
    col2.metric("새로 생성된 트렌드 질문", "34 개", "+5 개")
    col3.metric("가장 핫한 키워드", "마라탕", "검색량 1위")
except Exception as e:
    st.error("지표를 불러오는 중 오류가 발생했습니다. DB 테이블을 확인해주세요.")

st.divider()

# 좌우 화면 분할하여 차트 배치
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("🔥 키워드별 트렌드 지수 (최근 7일)")
    # DB에서 트렌드 데이터를 가져왔다고 가정 (pytrends 데이터)
    # trend_df = load_data("SELECT date, keyword, score FROM trend_data;")
    
    # 임시 더미 데이터 (실제 데이터로 교체하세요)
    dummy_trend = pd.DataFrame({
        "날짜": pd.date_range(start="2026-04-01", periods=7),
        "마라탕": [50, 60, 55, 80, 90, 85, 100],
        "수능": [80, 75, 70, 72, 65, 60, 55]
    }).set_index("날짜")
    
    st.line_chart(dummy_trend)

with right_col:
    st.subheader("🗳️ 카테고리별 투표 생성 비율")
    # DB에서 카테고리별 통계를 가져왔다고 가정
    # category_df = load_data("SELECT category, COUNT(*) as count FROM questions GROUP BY category;")
    
    # 임시 더미 데이터
    dummy_pie = pd.DataFrame({
        "카테고리": ["학교생활", "연애", "뷰티/패션", "음식", "기타"],
        "비율": [35, 25, 20, 15, 5]
    })
    # Streamlit 내장 bar_chart나 Plotly를 사용해 예쁘게 시각화
    st.bar_chart(dummy_pie.set_index("카테고리"))
