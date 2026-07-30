import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from googleapiclient.discovery import build
import urllib.parse as urlparse
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="유튜브 댓글 스마트 분석기",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FF0000;
        margin-bottom: 0.2rem;
    }
    .sub-title {
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

# 유튜브 URL에서 비디오 ID 추출
def extract_video_id(url):
    if not url:
        return None
    
    parsed_url = urlparse.urlparse(url)
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = urlparse.parse_qs(parsed_url.query)
            return p.get('v', [None])[0]
        elif parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
        elif parsed_url.path.startswith('/shorts/'):
            return parsed_url.path.split('/')[2]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    
    match = re.search(r"[a-zA-Z0-9_-]{11}", url)
    if match:
        return match.group(0)
    
    return None

# 유튜브 API 호출 및 댓글 수집
def get_youtube_comments(api_key, video_id, max_comments=100):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        comments_data = []
        next_page_token = None
        
        # 영상 비디오 상세 정보 추출
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()
        
        video_info = {}
        if video_response.get('items'):
            item = video_response['items'][0]
            video_info['title'] = item['snippet']['title']
            video_info['channel'] = item['snippet']['channelTitle']
            video_info['published_at'] = item['snippet']['publishedAt']
            video_info['view_count'] = item['statistics'].get('viewCount', '0')
            video_info['like_count'] = item['statistics'].get('likeCount', '0')
            video_info['comment_count'] = item['statistics'].get('commentCount', '0')

        # 댓글 수집 반복문
        while len(comments_data) < max_comments:
            request_size = min(100, max_comments - len(comments_data))
            
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=request_size,
                pageToken=next_page_token,
                order='time'
            ).execute()
            
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments_data.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textOriginal'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })
                
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        df = pd.DataFrame(comments_data)
        if not df.empty:
            df['published_at'] = pd.to_datetime(df['published_at'])
            
        return video_info, df
        
    except Exception as e:
        st.error(f"⚠️ YouTube API 호출 중 오류가 발생했습니다: {str(e)}")
        return None, None

# OS별 한글 폰트 경로 탐색
def get_korean_font_path():
    possible_fonts = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux (Streamlit Cloud - packages.txt 설치시)
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",                      # Windows
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf" # macOS
    ]
    for font in possible_fonts:
        if os.path.exists(font):
            return font
    return None

# 메인 UI
st.markdown('<div class="main-title">🎬 유튜브 댓글 스마트 분석기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">YouTube API를 연결하여 영상의 댓글 추이, 사용자 반응도, 워드클라우드를 분석합니다.</div>', unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("⚙️ 분석 설정")

api_key = st.sidebar.text_input("YouTube Data API v3 Key", type="password", help="Google Cloud Console에서 발급받은 API 키를 입력하세요.")
video_url = st.sidebar.text_input("YouTube 영상 URL", placeholder="https://www.youtube.com/watch?v=...")
max_comments = st.sidebar.slider("수집할 댓글 개수", min_value=50, max_value=2000, value=200, step=50)

run_button = st.sidebar.button("🚀 댓글 수집 및 분석 시작", type="primary")

# 실행 제어
if run_button:
    if not api_key:
        st.warning("🔑 YouTube API Key를 입력해주세요.")
    elif not video_url:
        st.warning("🔗 YouTube 영상 URL을 입력해주세요.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ 올바른 유튜브 영상 URL을 인식하지 못했습니다.")
        else:
            with st.spinner("⏳ 유튜브 데이터 및 댓글을 수집하는 중입니다..."):
                video_info, df_comments = get_youtube_comments(api_key, video_id, max_comments)
                
            if df_comments is not None and not df_comments.empty:
                # ---------------------------------------------------------
                # 1. 영상 기본 정보 및 플레이어
                # ---------------------------------------------------------
                st.subheader("📌 분석 대상 영상")
                col_vid1, col_vid2 = st.columns([1, 1])
                
                with col_vid1:
                    st.video(f"https://www.youtube.com/watch?v={video_id}")
                    
                with col_vid2:
                    if video_info:
                        st.markdown(f"### {video_info.get('title', '')}")
                        st.write(f"**채널명:** {video_info.get('channel', '')}")
                        st.write(f"**게시일:** {video_info.get('published_at', '')[:10]}")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("조회수", f"{int(video_info.get('view_count', 0)):,} 회")
                        m2.metric("좋아요 수", f"{int(video_info.get('like_count', 0)):,} 개")
                        m3.metric("전체 댓글 수", f"{int(video_info.get('comment_count', 0)):,} 개")
                        
                        st.success(f"✅ 요청한 **{len(df_comments):,}개**의 댓글 수집 완료!")

                st.markdown("---")
                
                # 탭 구성
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📈 시간대별 작성 추이", 
                    "👍 댓글 반응도 (좋아요 분석)", 
                    "☁️ 한글 워드클라우드", 
                    "📋 댓글 데이터 보기"
                ])
                
                # ---------------------------------------------------------
                # TAB 1: 시간대별 작성 추이
                # ---------------------------------------------------------
                with tab1:
                    st.subheader("⏰ 시간 흐름에 따른 댓글 작성 추이")
                    
                    df_time = df_comments.copy()
                    
                    # 일자별 집계
                    df_time['date'] = df_time['published_at'].dt.date
                    daily_counts = df_time.groupby('date').size().reset_index(name='count')
                    
                    fig_daily = px.line(
                        daily_counts, 
                        x='date', 
                        y='count', 
                        title="일자별 댓글 작성 수 추이",
                        markers=True
                    )
                    fig_daily.update_traces(line_color='#FF0000')
                    st.plotly_chart(fig_daily, use_container_width=True)
                    
                    # 시간대별(0~23시) 집계
                    df_time['hour'] = df_time['published_at'].dt.hour
                    hourly_counts = df_time.groupby('hour').size().reset_index(name='count')
                    
                    fig_hourly = px.bar(
                        hourly_counts, 
                        x='hour', 
                        y='count', 
                        title="시간대별(0시~23시) 댓글 작성 분포",
                        labels={'hour': '시간(Hour)', 'count': '댓글 수'},
                        color='count',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig_hourly, use_container_width=True)

                # ---------------------------------------------------------
                # TAB 2: 댓글 반응도 (좋아요 분석)
                # ---------------------------------------------------------
                with tab2:
                    st.subheader("🔥 가장 많은 공감을 얻은 TOP 5 댓글")
                    
                    top_liked = df_comments.sort_values(by='likes', ascending=False).head(5)
                    
                    for idx, (_, row) in enumerate(top_liked.iterrows(), 1):
                        with st.expander(f"TOP {idx} (👍 좋아요 {row['likes']:,}개) - 작성자: {row['author']}", expanded=(idx==1)):
                            st.write(f"**댓글 내용:** {row['text']}")
                            st.caption(f"작성일시: {row['published_at'].strftime('%Y-%m-%d %H:%M:%S')}")

                    st.markdown("---")
                    st.subheader("📊 댓글 좋아요 분포")
                    
                    fig_like_dist = px.histogram(
                        df_comments, 
                        x='likes', 
                        nbins=30, 
                        title="댓글별 좋아요 수 분포",
                        labels={'likes': '좋아요 수', 'count': '댓글 개수'},
                        color_discrete_sequence=['#FF2B2B']
                    )
                    st.plotly_chart(fig_like_dist, use_container_width=True)

                # ---------------------------------------------------------
                # TAB 3: 한글 워드클라우드
                # ---------------------------------------------------------
                with tab3:
                    st.subheader("☁️ 댓글 주요 단어 워드클라우드")
                    
                    all_text = " ".join(df_comments['text'].dropna().tolist())
                    words = re.findall(r'[가-힣a-zA-Z0-9]{2,}', all_text)
                    
                    # 불용어(Stopwords) 제거
                    stopwords = set(['너무', '진짜', '완전', '보고', '그냥', '이제', '오늘', '하나', '영상', '유튜브', '댓글'])
                    filtered_words = [w for w in words if w not in stopwords]
                    clean_text = " ".join(filtered_words)
                    
                    font_path = get_korean_font_path()
                    
                    if clean_text.strip():
                        try:
                            wc = WordCloud(
                                font_path=font_path,
                                background_color='white',
                                width=800,
                                height=400,
                                max_words=100,
                                colormap='Reds'
                            ).generate(clean_text)
                            
                            fig_wc, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig_wc)
                        except Exception as wc_err:
                            st.error(f"워드클라우드 생성 중 오류 발생: {wc_err}")
                    else:
                        st.info("워드클라우드를 생성할 충분한 단어가 없습니다.")

                # ---------------------------------------------------------
                # TAB 4: 댓글 데이터 보기 및 다운로드
                # ---------------------------------------------------------
                with tab4:
                    st.subheader("📋 수집된 댓글 데이터 목록")
                    st.dataframe(df_comments, use_container_width=True)
                    
                    csv_bytes = df_comments.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📄 CSV 파일로 다운로드 (UTF-8)",
                        data=csv_bytes,
                        file_name=f"youtube_comments_{video_id}.csv",
                        mime="text/csv",
                        type="primary"
                    )

            else:
                st.warning("수집된 댓글이 없거나, 영상의 댓글이 비활성화되어 있습니다.")

else:
    st.info("👈 왼쪽 사이드바에서 **YouTube API 키**와 **영상 URL**을 입력한 뒤 [🚀 댓글 수집 및 분석 시작] 버튼을 눌러주세요.")
