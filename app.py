import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# --- 1. 보안 설정 및 연결 ---
def get_gcp_clients():
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/calendar"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    gs_client = gspread.authorize(creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    return gs_client, calendar_service

# --- 2. 다크 모드 및 색상 강조 CSS ---
st.set_page_config(page_title="Dark Planner Pro", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 다크 모드 */
    .stApp { background-color: #121212; color: white; }
    /* 텍스트 기본색 흰색 */
    h1, h2, h3, p, span, label { color: #ffffff !important; }
    /* 사이드바 다크 스타일 */
    section[data-testid="stSidebar"] { background-color: #1e1e1e; }
    /* 강조색: 파란색 버튼 */
    .stButton>button {
        background-color: #2196F3; color: white; border-radius: 5px;
        border: none; font-weight: bold;
    }
    /* 강조색: 노란색 경고/알림 */
    .stAlert { background-color: #333300; color: #FFEB3B; border: 1px solid #FFEB3B; }
    /* 빨간색 강조 (마감 등) */
    .critical-text { color: #FF5252; font-weight: bold; }
    /* 데이터프레임 다크 조절 */
    .stDataFrame { background-color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 메인 로직 ---
try:
    gs_client, cal_service = get_gcp_clients()
    all_sheets = gs_client.openall()
    sheet = all_sheets[0].sheet1

    # 사이드바 메뉴
    st.sidebar.markdown("<h2 style='color: #FFEB3B;'>📅 Menu</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("이동", ["종합 달력", "신규 일정 등록", "전체 리스트"])

    # 데이터 로드
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    # 1. 종합 달력 (첫 화면)
    if menu == "종합 달력":
        st.markdown("<h1 style='text-align: center;'>🗓️ My Smart Calendar</h1>", unsafe_allow_html=True)
        
        # 달력 데이터 형식 변환
        calendar_events = []
        for _, row in df.iterrows():
            color = "#2196F3" if row['카테고리'] == "회사" else "#FFEB3B"
            if row['반복'] != "안 함": color = "#FF5252" # 반복 일정은 빨간색 강조
            
            calendar_events.append({
                "title": f"[{row['카테고리']}] {row['제목']}",
                "start": f"{row['날짜']}T{row['시간']}",
                "color": color
            })

        calendar_options = {
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay",
            },
            "initialView": "dayGridMonth",
            "editable": True,
            "selectable": True,
        }
        
        # 달력 컴포넌트 실행
        calendar(events=calendar_events, options=calendar_options)
        
        st.markdown("""
            <div style='display: flex; gap: 20px; justify-content: center; margin-top: 20px;'>
                <span style='color: #2196F3;'>● 회사(파랑)</span>
                <span style='color: #FFEB3B;'>● 개인(노랑)</span>
                <span style='color: #FF5252;'>● 반복(빨강)</span>
            </div>
        """, unsafe_allow_html=True)

    # 2. 신규 일정 등록
    elif menu == "신규 일정 등록":
        st.markdown("<h1>➕ <span style='color: #2196F3;'>새 일정</span> 등록</h1>", unsafe_allow_html=True)
        with st.form("event_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("일정 제목")
                category = st.selectbox("분류", ["회사", "개인"])
                date = st.date_input("날짜", datetime.now())
            with col2:
                time = st.time_input("시간", datetime.now().time())
                freq = st.selectbox("반복", ["안 함", "매주", "매달", "매년"])
                desc = st.text_area("상세 내용")
            
            submit = st.form_submit_button("구글 캘린더에 동기화")
            
            if submit:
                # 시트 저장
                sheet.append_row([str(date), str(time), category, title, desc, freq])
                
                # 캘린더 저장
                start_dt = datetime.combine(date, time).isoformat()
                end_dt = (datetime.combine(date, time) + timedelta(hours=1)).isoformat()
                event = {
                    'summary': f"[{category}] {title}",
                    'description': desc,
                    'start': {'dateTime': start_dt, 'timeZone': 'Asia/Seoul'},
                    'end': {'dateTime': end_dt, 'timeZone': 'Asia/Seoul'},
                }
                cal_service.events().insert(calendarId='primary', body=event).execute()
                st.success("✅ 일정이 성공적으로 등록되었습니다!")

    # 3. 전체 리스트
    elif menu == "전체 리스트":
        st.markdown("<h1>📂 <span style='color: #FFEB3B;'>전체 일정</span> 목록</h1>", unsafe_allow_html=True)
        if not df.empty:
            st.dataframe(df.style.set_properties(**{'background-color': '#1e1e1e', 'color': 'white'}))
        else:
            st.info("등록된 데이터가 없습니다.")

except Exception as e:
    st.error(f"오류 발생: {e}")
