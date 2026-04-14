import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 (앱 전체에 적용되므로 최상단에 한 번만 선언해야 합니다)
st.set_page_config(page_title="통합 대시보드", page_icon="📊", layout="wide")

# ==========================================
# 📌 사이드바 메뉴 구성 영역
# ==========================================
st.sidebar.title("📂 대시보드 메뉴")
page = st.sidebar.radio(
    "보고 싶은 화면을 선택하세요:",
    ("📊 라벨링 분석 (CSV)", "🤖 N8N 트렌드 봇 (Live DB)")
)

st.sidebar.divider()
st.sidebar.info("💡 나중에 파일을 추가하거나 코드를 합칠 때, 이 메뉴에 항목을 계속 늘려나갈 수 있습니다.")


# ==========================================
# 📊 [페이지 1] 라벨링 분석 대시보드 (현재 제공해주신 코드)
# ==========================================
def show_labeling_dashboard():
    st.title("📊 10대 익명 투표 분석 대시보드")

    # 데이터 불러오기 (캐싱)
    @st.cache_data
    def load_data():
        csv_url = "https://raw.githubusercontent.com/altair0307/streamlit_dashboard/refs/heads/main/question_labeling_refined_final.csv" 
        df = pd.read_csv(csv_url)
        df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
        return df

    try:
        df = load_data()
        
        # 핵심 지표 (Metrics)
        st.subheader("💡 핵심 요약 지표")
        col1, col2, col3 = st.columns(3)
        
        total_questions = len(df)
        total_votes = df['vote_count'].sum()
        top_category = df['main_label'].mode()[0] if not df['main_label'].empty else "데이터 없음"
        
        col1.metric("총 질문 데이터", f"{total_questions:,.0f} 개")
        col2.metric("총 누적 투표 수", f"{total_votes:,.0f} 회")
        col3.metric("가장 많은 카테고리", top_category)
        
        st.divider()

        # 차트 영역 (Plotly 활용)
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

        # 데이터 탐색 (필터링 테이블)
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
# 🤖 [페이지 2] N8N 트렌드 봇 대시보드 (나중에 채워넣을 공간)
# ==========================================
def show_n8n_dashboard():
    st.title("🤖 N8N 트렌드 봇 대시보드 (Live)")
    st.warning("🚧 현재 페이지는 준비 중입니다. 나중에 여기에 DB 연동 코드를 추가하세요!")
    
    # 예시: 나중에 이곳에 psycopg2 연결 및 데이터 불러오기 코드를 작성하시면 됩니다.


# ==========================================
# 🚀 선택된 메뉴에 따라 화면 출력
# ==========================================
if page == "📊 라벨링 분석 (CSV)":
    show_labeling_dashboard()
elif page == "🤖 N8N 트렌드 봇 (Live DB)":
    show_n8n_dashboard()
