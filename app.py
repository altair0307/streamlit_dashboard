import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="10대 트렌드 통합 분석", page_icon="📊", layout="wide")

# ==========================================
# 🎨 2. 테마 감지 및 배경색 제어 (CSS)
# ==========================================
theme_param = st.query_params.get("theme", None)
css_code = ""

if theme_param == "dark":
    pass # 기본 다크모드 유지
elif theme_param == "light":
    css_code = "<style>.stApp { background-color: #f6faff !important; }</style>"
else:
    # 일반 접속 시 OS 설정 감지
    css_code = """
    <style>
    @media (prefers-color-scheme: light) {
        .stApp { background-color: #f6faff !important; }
    }
    </style>
    """

if css_code:
    st.markdown(css_code, unsafe_allow_html=True)


# ==========================================
# 🚀 3. URL 파라미터를 통한 화면 라우팅
# ==========================================
# 주소창의 ?page= 값을 읽어 화면 결정 (기본값: csv)
target_page = st.query_params.get("page", "csv")


# ==========================================
# 📊 [화면 A] 라벨링 분석 대시보드 (CSV 데이터)
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
        
        # 핵심 요약 지표
        st.subheader("💡 핵심 요약 지표")
        col1, col2, col3 = st.columns(3)
        total_questions = len(df)
        total_votes = df['vote_count'].sum()
        top_category = df['main_label'].mode()[0] if not df['main_label'].empty else "데이터 없음"
        
        col1.metric("총 질문 데이터", f"{total_questions:,.0f} 개")
        col2.metric("총 누적 투표 수", f"{total_votes:,.0f} 회")
        col3.metric("가장 많은 카테고리", top_category)
        
        st.divider()

        # 시각화 영역
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.subheader("🏷️ 카테고리별 질문 분포")
            category_counts = df['main_label'].value_counts().reset_index()
            category_counts.columns = ['카테고리', '질문 수']
            fig_pie = px.pie(category_counts, names='카테고리', values='질문 수', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True, theme="streamlit")

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
            st.plotly_chart(fig_bar, use_container_width=True, theme="streamlit")
            
        st.divider()

        # 상세 데이터 탐색
        st.subheader("🔍 세부 데이터 탐색")
        categories = ["전체 보기"] + list(df['main_label'].dropna().unique())
        selected_category = st.selectbox("카테고리를 선택해서 모아보기:", categories)
        
        if selected_category == "전체 보기":
            filtered_df = df
        else:
            filtered_df = df[df['main_label'] == selected_category]
        
        display_columns = ['question_id', 'question_text', 'vote_count', 'main_label']
        existing_columns = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(filtered_df[existing_columns].set_index('question_id') if 'question_id' in existing_columns else filtered_df[existing_columns], use_container_width=True)

    except Exception as e:
        st.error("CSV 데이터를 불러오는 중 오류가 발생했습니다.")
        st.exception(e)


# ==========================================
# 🤖 [화면 B] N8N 트렌드 봇 대시보드 (Live DB)
# ==========================================
def show_n8n_dashboard():
    st.title("🤖 N8N 실시간 생성 질문 대시보드")
    st.caption("🔗 실시간 데이터베이스 연동 모드 (Private Network)")

    @st.cache_resource
    def init_connection():
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            st.error("🚨 DATABASE_URL 환경변수가 없습니다.")
            st.stop()
        return psycopg2.connect(db_url)

    try:
        conn = init_connection()

        @st.cache_data(ttl=300)
        def load_db_data():
            query = "SELECT id, topic, generated_question FROM teen_trend_questions;"
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                return pd.DataFrame(cur.fetchall(), columns=columns)

        db_df = load_db_data()
        
        if db_df.empty:
            st.warning("⚠️ 저장된 데이터가 없습니다.")
            return

        # 지표 요약
        col1, col2, col3 = st.columns(3)
        col1.metric("총 생성 질문", f"{len(db_df):,} 개")
        col2.metric("활성 주제 수", f"{db_df['topic'].nunique()} 개")
        col3.metric("최근 업데이트", "실시간 연동")
        
        st.divider()

        # 주제별 시각화
        st.subheader("🏷️ 주제별 생성 분포")
        l, r = st.columns(2)
        counts = db_df['topic'].value_counts().reset_index()
        counts.columns = ['주제', '질문 수']
        
        with l:
            f1 = px.pie(counts, names='주제', values='질문 수', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(f1, use_container_width=True, theme="streamlit")
        with r:
            f2 = px.bar(counts.head(10), x='질문 수', y='주제', orientation='h', color='질문 수', color_continuous_scale='Purples')
            f2.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            st.plotly_chart(f2, use_container_width=True, theme="streamlit")

        st.divider()

        # 리스트 출력
        st.subheader("✨ 최근 생성 질문 리스트 (최신순)")
        st.dataframe(db_df.sort_values('id', ascending=False).set_index('id'), use_container_width=True)

    except Exception as e:
        st.error("DB 접속 중 오류가 발생했습니다.")
        st.exception(e)


# ==========================================
# 🎯 4. 최종 화면 출력
# ==========================================
if target_page == "csv":
    show_labeling_dashboard()
elif target_page == "db":
    show_n8n_dashboard()
else:
    st.error("잘못된 URL 접근입니다.")
