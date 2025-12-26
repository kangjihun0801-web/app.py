import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# --- 1. 보안 설정 및 연결 (Secrets 활용) ---
def get_gcp_clients():
    # Streamlit Secrets에서 JSON 정보를 가져옴
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    # 시트 및 캘린더 서비스 빌드
    gs_client = gspread.authorize(creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    return gs_client, calendar_service

# --- 2. 페이지 디자인 설정 ---
st.set_page_config(page_title="스마트 스케줄러", layout="wide")

# 배경색 및 디자인을 위한 간단한 CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #4CAF50; color: white; }
    .stTextInput>div>div>input { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Smart Scheduler Pro")
st.write("구글 시트 및 캘린더와 실시간으로 연동되는 일정 관리 앱입니다.")

# --- 3. 데이터 로드 및 UI ---
try:
    gs_client, cal_service = get_gcp_clients()
    
    # 구글 시트 열기 (본인의 시트 이름을 정확히 적으세요)
    # 예: client.open("My Schedule Sheet").sheet1
    sheet = gs_client.open_all()[0].sheet1 # 가장 최근에 만든 시트를 자동으로 엽니다.
    
    menu = st.sidebar.radio("메뉴", ["일정 등록", "캘린더 보기", "알림 및 요약"])

    if menu == "일정 등록":
        st.subheader("📝 새로운 일정 추가")
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("일정 제목 (예: 팀 주간 회의)")
            category = st.selectbox("카테고리", ["회사", "개인"])
            date = st.date_input("날짜", datetime.now())
            time = st.time_input("시간", datetime.now().time())
        
        with col2:
            freq = st.selectbox("반복", ["안 함", "매주", "매달", "매년"])
            desc = st.text_area("상세 내용")

        if st.button("구글 시트 & 캘린더에 저장"):
            # A. 구글 시트에 저장
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
            
            # primary는 기본 캘린더를 의미합니다.
            cal_service.events().insert(calendarId='primary', body=event).execute()
            
            st.success(f"✅ '{title}' 일정이 구글 시트와 캘린더에 동시 등록되었습니다!")

    elif menu == "캘린더 보기":
        st.subheader("📅 저장된 일정 목록 (구글 시트 기준)")
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("저장된 일정이 없습니다.")

except Exception as e:
    st.error(f"연결 중 오류가 발생했습니다: {e}")
    st.info("1. 서비스 계정 이메일을 구글 시트/캘린더에 공유했는지 확인하세요.")
    st.info("2. Streamlit Secrets에 JSON 내용을 올바르게 넣었는지 확인하세요.")
