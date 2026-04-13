import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os

# 1. 페이지 설정
st.set_page_config(page_title="익명 투표 대시보드", page_icon="📊", layout="wide")
st.title("📊 10대 익명 투표 분석 대시보드 (Live)")

# 2. DB 연결 함수 (캐싱을 통해 부하 방지)
@st.cache_resource
def init_connection():
    # Railway에 설정해둔 DATABASE_URL 환경변수를 불러옵니다.
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("데이터베이스 연결 정보(DATABASE_URL)가 없습니다. Railway 환경 변수를 확인해주세요.")
        st.stop()
    return psycopg2.connect(db_url)

conn = init_connection()

# 3. 데이터 불러오기 (TTL=600: 10분마다 DB를 새로 조회하여 갱신)
@st.cache_data(ttl=600)
def load_data():
    # teen_trend_questions 테이블에서 데이터 가져오기
    # (실제 테이블에 created_at이나 updated_at 컬럼이 있다면 ORDER BY에 활용하세요)
    query = """
        SELECT 
            topic,
            generated_guestion
        FROM teen_trend_questions;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columns)
    
    # 데이터 전처리: vote_count 숫자 변환
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    # --- 상단: 핵심 지표 ---
    st.subheader("💡 실시간 핵심 요약 지표")
    col1, col2, col3 = st.columns(3)
    
    total_questions = len(df)
    total_votes = df['vote_count'].sum()
    top_category = df['main_label'].mode()[0] if not df['main_label'].empty else "데이터 없음"
    
    col1.metric("총 질문 데이터", f"{total_questions:,.0f} 개")
    col2.metric("총 누적 투표 수", f"{total_votes:,.0f} 회")
    col3.metric("가장 많은 카테고리", top_category)
    
    st.divider()

    # --- 중단: 차트 영역 ---
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader("🏷️ 카테고리별 질문 분포")
        category_counts = df['main_label'].value_counts().reset_index()
        category_counts.columns = ['카테고리', '질문 수']
        
        fig_pie = px.pie(category_counts, names='카테고리', values='질문 수', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with right_col:
        st.subheader("🔥 실시간 핫플레이스 (투표 TOP 5)")
        top_5_questions = df.nlargest(5, 'vote_count').copy()
        
        # 텍스트 길면 자르기 (18자)
        top_5_questions['short_question'] = top_5_questions['question_text'].apply(
            lambda x: x[:18] + '...' if len(x) > 18 else x
        )
        
        fig_bar = px.bar(
            top_5_questions, 
            x='vote_count', 
            y='short_question', 
            orientation='h',
            text='vote_count', 
            color='vote_count', 
            color_continuous_scale='Blues',
            custom_data=['question_text']
        )
        
        fig_bar.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>투표 수: %{x:,.0f}회<extra></extra>",
            textposition='outside'
        )
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': ''}, 
            xaxis={'title': ''}, 
            margin=dict(t=10, b=0, l=0, r=40), 
            height=350, 
            coloraxis_showscale=False 
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- 하단: 최근 갱신된 질문 및 데이터 탐색 ---
    st.subheader("✨ 최근 갱신된 투표 질문")
    
    # 최근 갱신된 질문을 보여주기 위해 question_id 기준 내림차순 정렬 (가장 큰 번호가 최신)
    # 만약 DB에 created_at 같은 날짜 컬럼이 있다면 그것을 기준으로 정렬하면 더 정확합니다.
    latest_questions = df.sort_values(by='question_id', ascending=False).head(10)
    
    st.markdown("**가장 최근에 추가된 10개의 질문입니다.**")
    st.dataframe(
        latest_questions[['question_id', 'question_text', 'main_label', 'vote_count']].set_index('question_id'), 
        use_container_width=True
    )

except Exception as e:
    st.error("데이터베이스에서 데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
