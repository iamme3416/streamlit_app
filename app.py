import streamlit as st
import random

st.set_page_config(
    page_title="✨ MBTI 진로 추천",
    page_icon="🚀",
    layout="wide"
)

# CSS
st.markdown("""
<style>

.stApp{
background: linear-gradient(135deg,#667eea,#764ba2,#ff6ec4,#7873f5);
background-size:400% 400%;
animation: gradient 12s ease infinite;
color:white;
}

@keyframes gradient{
0%{background-position:0% 50%;}
50%{background-position:100% 50%;}
100%{background-position:0% 50%;}
}

.big{
font-size:55px;
font-weight:bold;
text-align:center;
color:white;
}

.card{
background:white;
padding:25px;
border-radius:25px;
box-shadow:0px 10px 25px rgba(0,0,0,.3);
color:black;
margin:15px;
}

.job{
font-size:26px;
font-weight:bold;
color:#6C63FF;
}

.desc{
font-size:18px;
}

</style>
""",unsafe_allow_html=True)

st.markdown("<div class='big'>🌟 MBTI 진로 추천 사이트 🌟</div>",unsafe_allow_html=True)

st.write("")
st.write("## 😊 나의 MBTI를 선택해 보세요!")

mbti_data = {

"INTJ":{
"emoji":"🧠👑📚",
"jobs":["AI 개발자 🤖","데이터 과학자 📊","대학교수 🎓","연구원 🔬","CEO 💼"],
"text":"전략적인 사고와 분석 능력이 뛰어난 유형입니다."
},

"INTP":{
"emoji":"💡🧩⚙️",
"jobs":["프로그래머 💻","게임 개발자 🎮","수학자 ➗","물리학자 🌌","발명가 🔧"],
"text":"호기심이 많고 새로운 아이디어를 좋아합니다."
},

"ENTJ":{
"emoji":"👑🚀🔥",
"jobs":["기업 대표 💼","변호사 ⚖️","기획자 📈","프로젝트 매니저 📋","창업가 🚀"],
"text":"리더십이 뛰어나고 목표 달성을 잘합니다."
},

"ENTP":{
"emoji":"😎💥🎯",
"jobs":["마케터 📢","유튜버 🎥","창업가 🚀","PD 🎬","광고기획자 🎨"],
"text":"창의력이 풍부하고 새로운 도전을 좋아합니다."
},

"INFJ":{
"emoji":"🌿❤️📖",
"jobs":["상담교사 👩‍🏫","심리상담사 😊","작가 ✍️","사회복지사 🤝","교육자 📚"],
"text":"배려심이 많고 사람을 돕는 일을 좋아합니다."
},

"INFP":{
"emoji":"🌈🎨💖",
"jobs":["일러스트레이터 🎨","작가 📖","음악가 🎵","디자이너 🖌️","상담사 😊"],
"text":"감수성이 풍부하고 창의력이 뛰어납니다."
},

"ENFJ":{
"emoji":"🌞🤗🎉",
"jobs":["교사 👨‍🏫","강사 🎤","HR 담당자 👥","상담사 ❤️","아나운서 🎙️"],
"text":"사람들과 함께 성장하는 것을 좋아합니다."
},

"ENFP":{
"emoji":"🥳🎈✨",
"jobs":["배우 🎭","크리에이터 📹","여행작가 🌍","광고기획자 📺","MC 🎤"],
"text":"에너지가 넘치고 사람들과 어울리기를 좋아합니다."
},

"ISTJ":{
"emoji":"📋🏛️📚",
"jobs":["공무원 🏢","회계사 💰","은행원 🏦","품질관리 👨‍💼","경찰 👮"],
"text":"책임감이 강하고 꼼꼼합니다."
},

"ISFJ":{
"emoji":"🤍🏥🌸",
"jobs":["간호사 🩺","교사 👨‍🏫","사회복지사 🤝","행정직 📑","약사 💊"],
"text":"성실하고 배려심이 많습니다."
},

"ESTJ":{
"emoji":"📈💼🏆",
"jobs":["관리자 👔","군인 🎖️","경영자 🏢","공무원 📋","경찰 👮"],
"text":"조직을 이끄는 능력이 뛰어납니다."
},

"ESFJ":{
"emoji":"🥰🎀🤝",
"jobs":["승무원 ✈️","간호사 🩺","교사 📚","호텔리어 🏨","상담사 😊"],
"text":"친절하고 협동심이 강합니다."
},

"ISTP":{
"emoji":"🛠️🏍️⚙️",
"jobs":["정비사 🔧","파일럿 ✈️","엔지니어 👨‍💻","드론 전문가 🚁","소방관 🚒"],
"text":"문제를 해결하는 능력이 뛰어납니다."
},

"ISFP":{
"emoji":"🎨🌺🎵",
"jobs":["플로리스트 💐","사진작가 📸","패션디자이너 👗","웹디자이너 💻","요리사 🍳"],
"text":"예술적 감각이 뛰어납니다."
},

"ESTP":{
"emoji":"🏎️🔥😎",
"jobs":["운동선수 ⚽","영업사원 💼","파일럿 ✈️","기업가 🚀","경찰 👮"],
"text":"도전 정신이 강하고 실행력이 뛰어납니다."
},

"ESFP":{
"emoji":"🎤🎉🌟",
"jobs":["연예인 🌟","댄서 💃","유튜버 🎥","MC 🎤","배우 🎭"],
"text":"사람들에게 즐거움을 주는 것을 좋아합니다."
}

}

mbti = st.selectbox(
"👇 MBTI 선택",
list(mbti_data.keys())
)

if st.button("🚀 진로 추천 받기!",use_container_width=True):

    st.balloons()
    st.snow()

    info = mbti_data[mbti]

    st.markdown(f"""
    <div class="card">
    <h1>{info['emoji']} {mbti}</h1>

    <p class="desc">{info['text']}</p>

    <hr>

    <p class="job">💼 추천 직업</p>

    <ul>
    <li>{info['jobs'][0]}</li>
    <li>{info['jobs'][1]}</li>
    <li>{info['jobs'][2]}</li>
    <li>{info['jobs'][3]}</li>
    <li>{info['jobs'][4]}</li>
    </ul>

    </div>
    """,unsafe_allow_html=True)

    quotes = [
        "🌟 당신의 가능성은 무한합니다!",
        "🚀 꿈꾸는 사람이 세상을 바꿉니다.",
        "🔥 오늘의 도전이 내일의 성공입니다.",
        "💎 재능보다 중요한 것은 꾸준함입니다.",
        "🎯 자신에게 맞는 길을 찾는 것이 가장 중요합니다."
    ]

    st.success(random.choice(quotes))

    st.progress(random.randint(75,100))

    st.metric("😊 적성 일치도",f"{random.randint(85,99)}%")
