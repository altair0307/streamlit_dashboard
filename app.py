import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="익명 투표 대시보드", page_icon="📊", layout="wide")
st.title("📊 10대 익명 투표 분석 대시보드")

# 2. 데이터 불러오기 (캐싱)
@st.cache_data
def load_data():
    # ★ 아래 변수에 가장 최신 CSV 파일의 실제 GitHub Raw 주소를 넣어주세요! ★
    csv_url = "https://raw.githubusercontent.com/altair0307/streamlit_dashboard/refs/heads/main/question_labeling_refined_final.csv" 
    
    # CSV 읽어오기
    df = pd.read_csv(csv_url)
    
    # 데이터 전처리: vote_count를 숫자로 확실하게 변환
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    # 3. 핵심 지표 (Metrics) - 깔끔하게 3개만 배치
    st.subheader("💡 핵심 요약 지표")
    col1, col2, col3 = st.columns(3)
    
    total_questions = len(df)
    total_votes = df['vote_count'].sum()
    
    # 이번 데이터의 핵심 카테고리 컬럼인 'main_label'을 사용합니다.
    top_category = df['main_label'].mode()[0] if not df['main_label'].empty else "데이터 없음"
    
    col1.metric("총 질문 데이터", f"{total_questions:,.0f} 개")
    col2.metric("총 누적 투표 수", f"{total_votes:,.0f} 회")
    col3.metric("가장 많은 카테고리", top_category)
    
    st.divider()

    # 4. 차트 영역 (Plotly 활용)
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader("🏷️ 카테고리별 질문 분포")
        # 'main_label' 기준 분포 확인
        category_counts = df['main_label'].value_counts().reset_index()
        category_counts.columns = ['카테고리', '질문 수']
        
        # 도넛 모양 파이 차트 생성
        fig_pie = px.pie(category_counts, names='카테고리', values='질문 수', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with right_col:
        st.subheader("🔥 가장 투표를 많이 받은 TOP 5")
        
        # 1. 투표수 기준으로 상위 5개 추출 후 복사 (경고 방지)
        top_5_questions = df.nlargest(5, 'vote_count').copy()
        
        # 2. 질문 길이가 길면 차트가 찌그러지므로 18자에서 자르기
        top_5_questions['short_question'] = top_5_questions['question_text'].apply(
            lambda x: x[:18] + '...' if len(x) > 18 else x
        )
        
        # 3. 차트 생성
        fig_bar = px.bar(
            top_5_questions, 
            x='vote_count', 
            y='short_question', 
            orientation='h',
            text='vote_count', # 바 끝에 투표수 숫자 직접 표시
            color='vote_count', 
            color_continuous_scale='Blues',
            custom_data=['question_text'] # 마우스 오버용으로 전체 질문 데이터 숨겨두기
        )
        
        # 4. 차트 디테일 설정
        fig_bar.update_traces(
            # 마우스 올렸을 때 뜨는 툴팁 디자인 설정
            hovertemplate="<b>%{customdata[0]}</b><br>투표 수: %{x:,.0f}회<extra></extra>",
            textposition='outside' # 숫자를 바깥쪽에 깔끔하게 배치
        )
        
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': ''}, # y축 정렬 및 제목 숨김
            xaxis={'title': ''}, # x축 제목 숨김 (숫자가 이미 막대에 있으므로)
            margin=dict(t=10, b=0, l=0, r=40), # 우측 여백을 조금 주어 숫자가 안 잘리게 함
            height=350, # 차트 높이를 적당히 고정해 촘촘해지는 것 방지
            coloraxis_showscale=False # 우측 불필요한 컬러바 숨김
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.divider()

    # 5. 데이터 탐색 (필터링 테이블)
    st.subheader("🔍 세부 데이터 탐색")
    
    # 카테고리 선택 드롭다운 필터 ('main_label' 사용)
    categories = ["전체 보기"] + list(df['main_label'].dropna().unique())
    selected_category = st.selectbox("카테고리를 선택해서 모아보기:", categories)
    
    if selected_category == "전체 보기":
        filtered_df = df
    else:
        filtered_df = df[df['main_label'] == selected_category]
    
    # 표에 보여줄 핵심 컬럼만 지정 (manual_review_... 등 불필요한 열 숨김)
    display_columns = ['question_id', 'question_text', 'vote_count', 'main_label']
    
    # 실제 존재하는 컬럼만 필터링하여 출력 (에러 방지용)
    existing_columns = [col for col in display_columns if col in filtered_df.columns]
    
    if 'question_id' in existing_columns:
        st.dataframe(filtered_df[existing_columns].set_index('question_id'), use_container_width=True)
    else:
        st.dataframe(filtered_df[existing_columns], use_container_width=True)

except Exception as e:
    st.error("데이터를 불러오거나 시각화하는 중 오류가 발생했습니다. 코드 내의 GitHub Raw 주소가 정확한지 확인해주세요!")
    st.exception(e)
