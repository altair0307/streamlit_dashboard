import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os

# ==========================================
# 1. 페이지 설정 (앱 전체에 적용되므로 최상단에 선언)
# ==========================================
st.set_page_config(page_title="통합 분석 대시보드", page_icon="📊", layout="wide")

# ==========================================
# 📌 사이드바 메뉴 구성 영역
# ==========================================
st.sidebar.title("📂 대시보드 메뉴")
page = st.sidebar.radio(
    "보고 싶은 화면을 선택하세요:",
    ("📊 라벨링 분석 (CSV)", "🤖 N8N 트렌드 봇 (Live DB)")
)

st.sidebar.divider()
st.sidebar.info("💡 2개의 대시보드가 성공적으로 통합되었습니다.")


# ==========================================
# 📊 [페이지 1] 라벨링 분석 대시보드 (CSV 정적 데이터)
# ==========================================
def show_labeling_dashboard():
    st.title("📊 10대 익명 투표 분석 대시보드")

    @st.cache_data
    def load_csv_data():
        csv_url = "https://raw.githubusercontent.com/altair0307/streamlit_dashboard/refs/heads/main/question_labeling_refined_final.csv" 
        df = pd.read_csv(csv_url)
        df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
        return df

    try:
        df = load_csv_data()
        
        # 핵심 지표
        st.subheader("💡 핵심 요약 지표")
        col1, col2, col3 = st.columns(3)
        
        total_questions = len(df)
        total_votes = df['vote_count'].sum()
        top_category = df['main_label'].mode()[0] if not df['main_label'].empty else "데이터 없음"
        
        col1.metric("총 질문 데이터", f"{total_questions:,.0f} 개")
        col2.metric("총 누적 투표 수", f"{total_votes:,.0f} 회")
        col3.metric("가장 많은 카테고리", top_category)
        
        st.divider()

        # 차트 영역
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
            st.subheader("🔥 가장 투표를 많이 받은 TOP 5")
            top_5_questions = df.nlargest(5, 'vote_count').copy()
            top_5_questions['short_question'] = top_5_questions['question_text'].apply(
                lambda x: x[:18] + '...' if len(x) > 18 else x
            )
            
            fig_bar = px.bar(
                top_5_questions, x='vote_count', y='short_question', orientation='h',
                text='vote_count', color='vote_count', color_continuous_scale='Blues',
                custom_data=['question_text'] 
            )
            fig_bar.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>투표 수: %{x:,.0f}회<extra></extra>",
                textposition='outside'
            )
            fig_bar.update_layout(
                yaxis={'categoryorder':'total ascending', 'title': ''}, 
                xaxis={'title': ''}, margin=dict(t=10, b=0, l=0, r=40), 
                height=350, coloraxis_showscale=False 
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.divider()

        # 데이터 탐색 (필터 테이블)
        st.subheader("🔍 세부 데이터 탐색")
        categories = ["전체 보기"] + list(df['main_label'].dropna().unique())
        selected_category = st.selectbox("카테고리를 선택해서 모아보기:", categories)
        
        if selected_category == "전체 보기":
            filtered_df = df
        else:
            filtered_df = df[df['main_label'] == selected_category]
        
        display_columns = ['question_id', 'question_text', 'vote_count', 'main_label']
        existing_columns = [col for col in display_columns if col in filtered_df.columns]
        
        if 'question_id' in existing_columns:
            st.dataframe(filtered_df[existing_columns].set_index('question_id'), use_container_width=True)
        else:
            st.dataframe(filtered_df[existing_columns], use_container_width=True)

    except Exception as e:
        st.error("데이터를 불러오거나 시각화하는 중 오류가 발생했습니다.")
        st.exception(e)


# ==========================================
# 🤖 [페이지 2] N8N 트렌드 봇 대시보드 (Live DB)
# ==========================================
def show_n8n_dashboard():
    st.title("🤖 N8N 실시간 생성 질문 대시보드")

    # DB 연결 함수
    @st.cache_resource
    def init_connection():
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            st.error("🚨 환경 변수(DATABASE_URL)가 설정되지 않았습니다.")
            st.stop()
        return psycopg2.connect(db_url)

    conn = init_connection()

    # 데이터 불러오기 (캐싱 - 5분마다 갱신)
    @st.cache_data(ttl=300)
    def load_db_data():
        # DBeaver에서 확인한 정확한 컬럼명 사용
        query = "SELECT id, topic, generated_question FROM teen_trend_questions;"
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

    try:
        db_df = load_db_data()
        
        if db_df.empty:
            st.warning("⚠️ 현재 데이터베이스에 저장된 질문이 없습니다. n8n 워크플로우를 실행해주세요.")
            return

        # 요약 지표
        st.subheader("💡 실시간 데이터 요약")
        col1, col2, col3 = st.columns(3)
        
        total_q = len(db_df)
        unique_topics = db_df['topic'].nunique()
        most_common_topic = db_df['topic'].mode()[0] if not db_df['topic'].empty else "N/A"
        
        col1.metric("총 생성 질문 수", f"{total_q:,} 개")
        col2.metric("활성화된 주제 수", f"{unique_topics} 개")
        col3.metric("가장 많이 다뤄진 주제", most_common_topic)
        
        st.divider()

        # 시각화: 주제별 질문 생성 빈도
        st.subheader("🏷️ 주제(Topic)별 생성 질문 분포")
        
        left_col, right_col = st.columns(2)
        topic_counts = db_df['topic'].value_counts().reset_index()
        topic_counts.columns = ['주제', '질문 수']
        
        with left_col:
            fig_pie = px.pie(topic_counts, names='주제', values='질문 수', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie.update_layout(margin=dict(t=20, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        with right_col:
            fig_bar = px.bar(topic_counts.head(10), x='질문 수', y='주제', orientation='h',
                             color='질문 수', color_continuous_scale='Purples')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=20, b=0, l=0, r=0),
                                  coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # 전체 데이터 탐색
        st.subheader("✨ 가장 최근에 생성된 질문 리스트")
        
        topic_list = ["전체"] + list(db_df['topic'].unique())
        selected_topic = st.selectbox("특정 주제로 필터링:", topic_list, key="db_filter")
        
        if selected_topic == "전체":
            display_df = db_df
        else:
            display_df = db_df[db_df['topic'] == selected_topic]
        
        # id 기준 내림차순 정렬 (가장 최근에 들어온 데이터가 위로 오게)
        st.dataframe(
            display_df.set_index('id').sort_index(ascending=False),
            use_container_width=True
        )

    except Exception as e:
        st.error("N8N 대시보드를 구성하는 중 예상치 못한 오류가 발생했습니다.")
        st.exception(e)


# ==========================================
# 🚀 선택된 메뉴에 따라 화면 출력
# ==========================================
if page == "📊 라벨링 분석 (CSV)":
    show_labeling_dashboard()
elif page == "🤖 N8N 트렌드 봇 (Live DB)":
    show_n8n_dashboard()
