import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# --- 1. 보안 설정 및 연결 ---
def get_gcp_clients():
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    # 연결 도구 생성
    gs_client = gspread.authorize(creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    return gs_client, calendar_service

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="스마트 스케줄러", layout="wide")

st.title("📅 Smart Scheduler Pro")

try:
    gs_client, cal_service = get_gcp_clients()
    
    # ⚠️ 중요: 여기에 본인의 구글 시트 이름을 정확히 적으세요!
    # 예: "나의 일정표" 또는 "Untitled spreadsheet"
    SHEET_NAME = "나의 일정표" # <--- 본인의 구글 시트 제목으로 수정하세요!
    
    # 시트 열기 (가장 확실한 방법인 open() 사용)
    try:
        sheet = gs_client.open(캘린더).sheet1
    except Exception:
        # 이름을 모를 경우 가장 최근 시트 하나를 가져옴 (openall 사용)
        sheet = gs_client.openall()[0].sheet1

    menu = st.sidebar.radio("메뉴", ["일정 등록", "캘린더 보기"])

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
            # A. 구글 시트에 저장 (첫 행에 제목이 없으면 오류 날 수 있어 append_row 사용)
            row = [str(date), str(time), category, title, desc, freq]
            sheet.append_row(row)
            
            # B. 구글 캘린더에 이벤트 생성
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
        # 데이터가 있는지 확인 후 출력
        data = sheet.get_all_values()
        if data:
            df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(data)
            st.table(df)
        else:
            st.info("데이터가 없습니다.")

except Exception as e:
    st.error(f"연결 중 오류가 발생했습니다: {e}")
    st.info("시트 이름을 확인하거나, 서비스 계정이 시트에 '편집자'로 초대되었는지 확인해 주세요.")
