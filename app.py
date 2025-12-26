import streamlit as st
import gspread
import pandas as pd # 데이터 표를 만들기 위해 추가
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# --- 1. 보안 설정 및 연결 (오류 수정 버전) ---
def get_gcp_clients():
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    gs_client = gspread.authorize(creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    return gs_client, calendar_service

# --- 2. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="스마트 스케줄러", layout="wide")

# CSS로 UI 꾸미기
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { color: #2E4053; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>📅 Smart Scheduler Pro</h1>", unsafe_allow_html=True)

# --- 3. 메인 로직 ---
try:
    gs_client, cal_service = get_gcp_clients()
    
    # ⚠️ 여기를 수정했습니다! 
    # 모든 시트를 다 가져오지 않고, 가장 최근에 수정한 시트 하나를 가져옵니다.
    # 만약 특정 시트를 열고 싶다면: gs_client.open("시트이름").sheet1
    all_sheets = gs_client.openall()
    if not all_sheets:
        st.error("구글 시트를 찾을 수 없습니다. 서비스 계정 이메일에 시트를 공유했는지 확인하세요.")
        st.stop()
    sheet = all_sheets[0].sheet1 

    menu = st.sidebar.radio("메뉴", ["일정 등록", "캘린더 보기", "알림 및 요약"])

    if menu == "일정 등록":
        st.subheader("📝 새로운 일정 추가")
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("일정 제목")
            category = st.selectbox("카테고리", ["회사", "개인"])
            date = st.date_input("날짜", datetime.now())
            time = st.time_input("시간", datetime.now().time())
        
        with col2:
            freq = st.selectbox("반복", ["안 함", "매주", "매달", "매년"])
            desc = st.text_area("상세 내용")

        if st.button("구글 시트 & 캘린더에 저장"):
            # 구글 시트에 저장
            row = [str(date), str(time), category, title, desc, freq]
            sheet.append_row(row)
            
            # 구글 캘린더에 이벤트 생성
            start_time = datetime.combine(date, time).isoformat()
            end_time = (datetime.combine(date, time) + timedelta(hours=1)).isoformat()
            
            event = {
                'summary': f"[{category}] {title}",
                'description': desc,
                'start': {'dateTime': start_time, 'timeZone': 'Asia/Seoul'},
                'end': {'dateTime': end_time, 'timeZone': 'Asia/Seoul'},
            }
            
            cal_service.events().insert(calendarId='primary', body=event).execute()
            st.success(f"✅ '{title}' 등록 완료!")

    elif menu == "캘린더 보기":
        st.subheader("📅 저장된 일정 목록")
        # 시트 데이터 가져와서 표로 보여주기
        records = sheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            st.table(df) # 깔끔한 표로 출력
        else:
            st.info("데이터가 없습니다.")

except Exception as e:
    st.error(f"연결 중 오류가 발생했습니다: {e}")
