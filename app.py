import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os

# 1. 페이지 설정
st.set_page_config(page_title="트렌드 질문 분석 대시보드", page_icon="🤖", layout="wide")
st.title("📊 AI 생성 트렌드 질문 분석 대시보드")

# 2. DB 연결 함수
@st.cache_resource
def init_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("환경 변수(DATABASE_URL)가 설정되지 않았습니다.")
        st.stop()
    return psycopg2.connect(db_url)

conn = init_connection()

# 3. 데이터 불러오기 (캐싱 적용)
@st.cache_data(ttl=300) # 5분마다 갱신
def load_data():
    # 요청하신 id, topic, generated_question 컬럼만 호출합니다.
    query = """
        SELECT 
            id, 
            topic, 
            generated_question 
        FROM teen_trend_questions;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(cur.fetchall(), columns=columns)
        return df
        
    except psycopg2.Error as e:
        st.error("🚨 데이터베이스 조회 중 오류가 발생했습니다.")
        st.error(f"상세 내용: {e.pgerror}")
        st.stop()

# 4. 화면 구성
try:
    df = load_data()
    
    # --- 상단: 요약 지표 ---
    st.subheader("💡 데이터 요약")
    col1, col2, col3 = st.columns(3)
    
    total_q = len(df)
    unique_topics = df['topic'].nunique()
    most_common_topic = df['topic'].mode()[0] if not df['topic'].empty else "N/A"
    
    col1.metric("총 생성 질문 수", f"{total_q:,} 개")
    col2.metric("활성화된 주제 수", f"{unique_topics} 개")
    col3.metric("가장 많이 다뤄진 주제", most_common_topic)
    
    st.divider()

    # --- 중단: 시각화 ---
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader("🏷️ 주제(Topic)별 분포")
        topic_counts = df['topic'].value_counts().reset_index()
        topic_counts.columns = ['주제', '질문 수']
        
        # 주제별 비중을 보여주는 파이 차트
        fig_pie = px.pie(topic_counts, names='주제', values='질문 수', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Safe)
        fig_pie.update_layout(margin=dict(t=20, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with right_col:
        st.subheader("📝 주제별 질문 생성 빈도")
        # 주제별 빈도를 보여주는 가로 막대 그래프
        fig_bar = px.bar(topic_counts.head(10), x='질문 수', y='주제', orientation='h',
                         color='질문 수', color_continuous_scale='Purples')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=20, b=0, l=0, r=0),
                              coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- 하단: 전체 데이터 탐색 ---
    st.subheader("🔍 전체 질문 데이터 리스트")
    
    # 필터링 옵션
    topic_list = ["전체"] + list(df['topic'].unique())
    selected_topic = st.selectbox("특정 주제로 필터링:", topic_list)
    
    if selected_topic == "전체":
        display_df = df
    else:
        display_df = df[df['topic'] == selected_topic]
    
    # 테이블 출력 (id를 인덱스로 사용)
    st.dataframe(
        display_df.set_index
