import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
import math

# 페이지 환경 설정
st.set_page_config(
    page_title="서울시 공영주차장 스마트 안내 시스템",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS (디자인 스타일링)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로딩 및 전처리 캐싱
@st.cache_data
def load_data():
    file_path = "서울시 공영주차장 안내 정보.csv"
    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except Exception:
        df = pd.read_csv(file_path, encoding='utf-8')
    
    # 주소에서 자치구 추출
    df['자치구'] = df['주소'].astype(str).str.extract(r'([가-힣]+구)')
    df['자치구'] = df['자치구'].fillna('기타/미분류')
    
    # 수치형 데이터 결측치 및 타입 변환
    num_cols = ['기본 주차 요금', '기본 주차 시간(분 단위)', '추가 단위 요금', '추가 단위 시간(분 단위)', '일 최대 요금', '총 주차면', '월 정기권 금액', '위도', '경도']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 범주형 결측치 처리
    df['주차장 종류명'] = df['주차장 종류명'].fillna('미상')
    df['유무료구분명'] = df['유무료구분명'].fillna('정보없음')
    df['야간무료개방여부명'] = df['야간무료개방여부명'].fillna('정보없음')
    
    return df

# 요금 계산 로직 함수
def calculate_parking_fee(row, parking_minutes):
    if parking_minutes <= 0:
        return 0
    
    base_fee = row['기본 주차 요금']
    base_time = row['기본 주차 시간(분 단위)']
    add_fee = row['추가 단위 요금']
    add_time = row['추가 단위 시간(분 단위)']
    max_daily = row['일 최대 요금']
    
    if base_time == 0 or base_fee == 0:
        return 0
    
    if parking_minutes <= base_time:
        fee = base_fee
    else:
        extra_time = parking_minutes - base_time
        if add_time > 0 and add_fee > 0:
            extra_units = math.ceil(extra_time / add_time)
            fee = base_fee + (extra_units * add_fee)
        else:
            fee = base_fee
            
    if max_daily > 0 and fee > max_daily:
        fee = max_daily
        
    return fee

# 데이터 불러오기
df_raw = load_data()

# 헤더
st.markdown('<div class="main-header">🅿️ 서울시 공영주차장 스마트 안내 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">서울시 공영주차장 맞춤 검색, 지도 안내, 예상 요금 계산 및 최저가/랜덤 추천 서비스를 제공합니다.</div>', unsafe_allow_html=True)

# 사이드바 : 조건 검색 필터
st.sidebar.header("🔍 검색 및 필터 설정")

# 1. 자치구 선택
gu_list = ["전체"] + sorted([g for g in df_raw['자치구'].unique() if g != '기타/미분류']) + ["기타/미분류"]
selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)

# 2. 검색어 입력
search_kw = st.sidebar.text_input("주차장명 / 주소 검색", "").strip()

# 3. 유무료 & 주차장 종류 필터
fee_type = st.sidebar.multiselect("유/무료 구분", options=df_raw['유무료구분명'].unique(), default=df_raw['유무료구분명'].unique())
parking_type = st.sidebar.multiselect("주차장 종류", options=df_raw['주차장 종류명'].unique(), default=df_raw['주차장 종류명'].unique())
night_free = st.sidebar.checkbox("야간 무료 개방 주차장만 보기", value=False)

# 필터링 적용
filtered_df = df_raw.copy()

if selected_gu != "전체":
    filtered_df = filtered_df[filtered_df['자치구'] == selected_gu]

if search_kw:
    filtered_df = filtered_df[
        filtered_df['주차장명'].str.contains(search_kw, case=False, na=False) | 
        filtered_df['주소'].str.contains(search_kw, case=False, na=False)
    ]

if fee_type:
    filtered_df = filtered_df[filtered_df['유무료구분명'].isin(fee_type)]

if parking_type:
    filtered_df = filtered_df[filtered_df['주차장 종류명'].isin(parking_type)]

if night_free:
    filtered_df = filtered_df[filtered_df['야간무료개방여부명'].str.contains("개방", na=False) & ~filtered_df['야간무료개방여부명'].str.contains("미개방", na=False)]

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 주차장 목록 & 지도", 
    "💰 요금 계산기 & 최저가 추천", 
    "🎲 랜덤 주차장 추천", 
    "📊 통계 및 시각화", 
    "📥 데이터 다운로드"
])

# ---------------------------------------------------------
# TAB 1: 주차장 목록 & 지도
# ---------------------------------------------------------
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("검색된 주차장 수", f"{len(filtered_df):,} 개")
    col2.metric("총 주차면 수", f"{int(filtered_df['총 주차면'].sum()):,} 면")
    avg_base_fee = filtered_df[filtered_df['기본 주차 요금'] > 0]['기본 주차 요금'].mean()
    col3.metric("평균 기본 요금", f"{int(avg_base_fee) if not np.isnan(avg_base_fee) else 0:,} 원")
    free_count = len(filtered_df[filtered_df['유무료구분명'] == '무료'])
    col4.metric("무료 주차장 수", f"{free_count:,} 개")

    st.markdown("---")
    
    st.subheader("🗺️ 지도 위치 확인")
    map_df = filtered_df[(filtered_df['위도'] > 33) & (filtered_df['위도'] < 43) & (filtered_df['경도'] > 124) & (filtered_df['경도'] < 132)]

    if len(map_df) > 0:
        center_lat = map_df['위도'].median()
        center_lon = map_df['경도'].median()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12 if selected_gu == "전체" else 14)
        
        display_map_df = map_df.head(300)
        if len(map_df) > 300:
            st.info(f"💡 지도 원활한 표시를 위해 상위 300개 위치만 표시합니다. (전체 {len(map_df)}개 위치 가능)")

        for _, row in display_map_df.iterrows():
            popup_html = f"""
            <div style='font-family: sans-serif; width: 220px;'>
                <h4 style='margin-bottom: 5px; color: #1E3A8A;'>{row['주차장명']}</h4>
                <p style='font-size: 12px; margin: 2px 0;'><b>주소:</b> {row['주소']}</p>
                <p style='font-size: 12px; margin: 2px 0;'><b>종류:</b> {row['주차장 종류명']} ({row['유무료구분명']})</p>
                <p style='font-size: 12px; margin: 2px 0;'><b>기본요금:</b> {int(row['기본 주차 요금']):,}원 / {int(row['기본 주차 시간(분 단위)'])}분</p>
                <p style='font-size: 12px; margin: 2px 0;'><b>전화번호:</b> {row['전화번호'] if pd.notna(row['전화번호']) else '정보없음'}</p>
            </div>
            """
            icon_color = 'green' if row['유무료구분명'] == '무료' else 'blue'
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=row['주차장명'],
                icon=folium.Icon(color=icon_color, icon='info-sign')
            ).add_to(m)

        st_folium(m, width=None, height=450)
    else:
        st.warning("선택된 주차장의 좌표 정보가 없습니다.")

    st.subheader("📋 상세 주차장 목록")
    display_cols = ['주차장명', '자치구', '주소', '주차장 종류명', '유무료구분명', '총 주차면', '기본 주차 요금', '기본 주차 시간(분 단위)', '전화번호']
    st.dataframe(filtered_df[display_cols].reset_index(drop=True), use_container_width=True)

# ---------------------------------------------------------
# TAB 2: 요금 계산기 & 최저가 추천
# ---------------------------------------------------------
with tab2:
    st.subheader("💡 이용시간 기준 예상 주차요금 계산 및 최저가 추천")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("##### ⏱️ 이용 예정 시간 설정")
        park_hours = st.number_input("이용 시간 (시간)", min_value=0, max_value=24, value=2, step=1)
        park_mins = st.number_input("이용 시간 (분)", min_value=0, max_value=59, value=0, step=10)
        total_minutes = (park_hours * 60) + park_mins
        
        calc_gu = st.selectbox("추천받을 자치구 선택", ["전체"] + sorted([g for g in df_raw['자치구'].unique() if g != '기타/미분류']))
        
        calc_button = st.button("🧮 요금 계산 및 최저가 추천 실행", type="primary")

    with col2:
        if calc_button or total_minutes > 0:
            target_df = df_raw.copy()
            if calc_gu != "전체":
                target_df = target_df[target_df['자치구'] == calc_gu]
            
            target_df = target_df[target_df['기본 주차 시간(분 단위)'] > 0].copy()
            target_df['예상요금'] = target_df.apply(lambda r: calculate_parking_fee(r, total_minutes), axis=1)
            target_df = target_df.sort_values(by=['예상요금', '총 주차면'], ascending=[True, False])
            
            st.markdown(f"#### 🏆 {total_minutes}분 ({park_hours}시간 {park_mins}분) 이용 시 가장 저렴한 주차장 TOP 5")
            
            top5 = target_df.head(5)
            
            if len(top5) > 0:
                for idx, (_, row) in enumerate(top5.iterrows(), 1):
                    fee_display = "FREE (무료)" if row['예상요금'] == 0 else f"{int(row['예상요금']):,} 원"
                    with st.expander(f"{idx}위: {row['주차장명']} — 예상 요금: {fee_display}", expanded=(idx==1)):
                        st.write(f"**주소:** {row['주소']}")
                        st.write(f"**구분:** {row['주차장 종류명']} | {row['유무료구분명']} | 야간무료: {row['야간무료개방여부명']}")
                        st.write(f"**기본 요금 체계:** {int(row['기본 주차 요금']):,}원 / {int(row['기본 주차 시간(분 단위)'])}분")
                        st.write(f"**추가 요금 체계:** {int(row['추가 단위 요금']):,}원 / {int(row['추가 단위 시간(분 단위)'])}분당")
                        st.write(f"**일 최대 요금:** {int(row['일 최대 요금']):,}원" if row['일 최대 요금'] > 0 else "**일 최대 요금:** 정보없음/제한없음")
                        st.write(f"**전화번호:** {row['전화번호'] if pd.notna(row['전화번호']) else '정보없음'}")
            else:
                st.warning("조건에 해당하는 주차장 정보가 없습니다.")

# ---------------------------------------------------------
# TAB 3: 랜덤 주차장 추천
# ---------------------------------------------------------
with tab3:
    st.subheader("🎲 행운의 랜덤 주차장 추천")
    st.write("어디로 갈지 고민이신가요? 조건에 맞는 공영주차장을 랜덤으로 추천해 드립니다!")
    
    col_r1, col_r2 = st.columns([1, 2])
    
    with col_r1:
        rand_gu = st.selectbox("랜덤 추천 자치구", ["전체"] + sorted([g for g in df_raw['자치구'].unique() if g != '기타/미분류']), key="rand_gu")
        rand_free_only = st.checkbox("무료 주차장 중에서만 추천", value=False)
        
        if st.button("🎲 주차장 랜덤 뽑기!", type="primary"):
            rand_target = df_raw.copy()
            if rand_gu != "전체":
                rand_target = rand_target[rand_target['자치구'] == rand_gu]
            if rand_free_only:
                rand_target = rand_target[rand_target['유무료구분명'] == '무료']
                
            if len(rand_target) > 0:
                selected_sample = rand_target.sample(n=1).iloc[0]
                st.session_state['random_pick'] = selected_sample
            else:
                st.session_state['random_pick'] = None
                st.error("조건에 일치하는 주차장이 없습니다.")

    with col_r2:
        if 'random_pick' in st.session_state and st.session_state['random_pick'] is not None:
            pick = st.session_state['random_pick']
            st.success(f"🎉 오늘의 추천 주차장: **{pick['주차장명']}**")
            
            st.info(f"""
            * **자치구:** {pick['자치구']}
            * **주소:** {pick['주소']}
            * **주차장 종류:** {pick['주차장 종류명']} ({pick['유무료구분명']})
            * **총 주차면수:** {int(pick['총 주차면'])} 면
            * **기본 요금:** {int(pick['기본 주차 요금']):,}원 / {int(pick['기본 주차 시간(분 단위)'])}분
            * **추가 요금:** {int(pick['추가 단위 요금']):,}원 / {int(pick['추가 단위 시간(분 단위)'])}분당
            * **야간 무료 개방:** {pick['야간무료개방여부명']}
            * **전화번호:** {pick['전화번호'] if pd.notna(pick['전화번호']) else '정보없음'}
            """)

# ---------------------------------------------------------
# TAB 4: 통계 및 시각화
# ---------------------------------------------------------
with tab4:
    st.subheader("📊 서울시 공영주차장 데이터 분석")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        gu_counts = df_raw['자치구'].value_counts().reset_index()
        gu_counts.columns = ['자치구', '주차장 수']
        fig1 = px.bar(gu_counts, x='자치구', y='주차장 수', title="자치구별 공영주차장 개수 현황", color='주차장 수', color_continuous_scale='Blues')
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_g2:
        type_counts = df_raw['유무료구분명'].value_counts().reset_index()
        type_counts.columns = ['유무료구분', '수량']
        fig2 = px.pie(type_counts, names='유무료구분', values='수량', title="서울시 전체 유/무료 주차장 비율", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig2, use_container_width=True)
        
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        kind_counts = df_raw['주차장 종류명'].value_counts().reset_index()
        kind_counts.columns = ['주차장 종류', '수량']
        fig3 = px.bar(kind_counts, x='주차장 종류', y='수량', title="주차장 유형별 분포", color='수량', color_continuous_scale='Greens')
        st.plotly_chart(fig3, use_container_width=True)
        
    with col_g4:
        fee_by_gu = df_raw[df_raw['기본 주차 요금'] > 0].groupby('자치구')['기본 주차 요금'].mean().reset_index()
        fee_by_gu = fee_by_gu.sort_values(by='기본 주차 요금', ascending=False)
        fig4 = px.bar(fee_by_gu, x='자치구', y='기본 주차 요금', title="자치구별 평균 기본 주차 요금(원)", color='기본 주차 요금', color_continuous_scale='Reds')
        st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------------
# TAB 5: 데이터 다운로드
# ---------------------------------------------------------
with tab5:
    st.subheader("📥 검색 및 필터링된 데이터 다운로드")
    st.write(f"현재 선택된 필터 조건에 해당하는 주차장 데이터 **총 {len(filtered_df):,}건** 입니다.")
    
    st.dataframe(filtered_df.head(10))
    
    csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📄 CSV 파일로 다운로드 (UTF-8)",
        data=csv_data,
        file_name="서울시_공영주차장_검색결과.csv",
        mime="text/csv",
        type="primary"
    )

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>서울시 공영주차장 안내 정보 데이터 기반 Web Application | Streamlit Cloud Ready</p>", unsafe_allow_html=True)
