import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="익명 투표 라벨링 대시보드", page_icon="📊", layout="wide")
st.title("📊 10대 익명 투표 라벨링 분석 대시보드")

# 2. 데이터 불러오기 (캐싱)
@st.cache_data
def load_data():
    # ★ 아래 변수에 "새로 올리신 파일"의 실제 GitHub Raw 주소를 넣어주세요! ★
    # 예시: "https://raw.githubusercontent.com/.../question_labeling_auto_completed_cleaned.csv"
    csv_url = "https://raw.githubusercontent.com/altair0307/streamlit_dashboard/refs/heads/main/question_labeling_auto_completed_cleaned.csv" 
    
    # CSV 읽어오기
    df = pd.read_csv(csv_url)
    
    # 데이터 전처리: vote_count를 숫자로 확실하게 변환
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    # 3. 핵심 지표 (Metrics) - 수동 리뷰 제외, 3개로 깔끔하게 구성
    st.subheader("💡 핵심 요약 지표")
    col1, col2, col3 = st.columns(3)
    
    total_questions = len(df)
    total_votes = df['vote_count'].sum()
    top_category = df['refined_main_label'].mode()[0] if not df['refined_main_label'].empty else "데이터 없음"
    
    col1.metric("총 질문 데이터", f"{total_questions:,.0f} 개")
    col2.metric("총 누적 투표 수", f"{total_votes:,.0f} 회")
    col3.metric("가장 많은 카테고리", top_category)
    
    st.divider()

    # 4. 차트 영역 (Plotly 활용)
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader("🏷️ 카테고리별 질문 분포")
        # 메인 라벨 기준 분포 확인
        category_counts = df['refined_main_label'].value_counts().reset_index()
        category_counts.columns = ['카테고리', '질문 수']
        
        # 도넛 모양 파이 차트 생성
        fig_pie = px.pie(category_counts, names='카테고리', values='질문 수', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with right_col:
        st.subheader("🔥 가장 투표를 많이 받은 TOP 5 질문")
        # 투표수 기준으로 정렬 후 상위 5개 추출
        top_5_questions = df.nlargest(5, 'vote_count')
        
        # 가로형 막대 차트 생성
        fig_bar = px.bar(top_5_questions, x='vote_count', y='question_text', orientation='h',
                         labels={'vote_count':'투표 수', 'question_text':''},
                         color='vote_count', color_continuous_scale='Blues')
        # 투표수 많은 게 가장 위로 오도록 정렬 설정
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0)) 
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # 5. 데이터 탐색 (필터링 테이블)
    st.subheader("🔍 세부 데이터 탐색")
    
    # 카테고리 선택 드롭다운 필터
    categories = ["전체 보기"] + list(df['refined_main_label'].dropna().unique())
    selected_category = st.selectbox("카테고리를 선택해서 모아보기:", categories)
    
    if selected_category == "전체 보기":
        filtered_df = df
    else:
        filtered_df = df[df['refined_main_label'] == selected_category]
    
    # 분석에 방해되는 긴 텍스트와 불필요한 리뷰용 컬럼들은 숨김 처리
    display_columns = ['question_id', 'question_text', 'vote_count', 'refined_main_label']
    
    # 실제 존재하는 컬럼만 선택해서 에러 방지
    existing_columns = [col for col in display_columns if col in filtered_df.columns]
    
    # 깔끔한 표 형태로 출력 (인덱스를 ID로 설정하여 더 깔끔하게)
    if 'question_id' in existing_columns:
        st.dataframe(filtered_df[existing_columns].set_index('question_id'), use_container_width=True)
    else:
        st.dataframe(filtered_df[existing_columns], use_container_width=True)

except Exception as e:
    st.error("데이터를 불러오거나 시각화하는 중 오류가 발생했습니다. 코드 내의 GitHub Raw 주소가 정확한지 확인해주세요!")
    st.exception(e)
