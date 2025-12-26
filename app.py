import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# --- 1. 보안 설정 및 연결 (Scopes 보강) ---
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

# --- 2. 세련된 UI를 위한 CSS 설정 ---
st.set_page_config(page_title="Smart Planner", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp { background-color: #F0F2F6; }
    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"] { background-color: #262730; color: white; }
    /* 버튼 커스텀 */
    .stButton>button {
        background-color: #4CAF50; color: white; border-radius: 8px;
        height: 3em; width: 100%; border: none; font-weight: bold;
    }
    .stButton>button:hover { background-color: #45a049; border: none; }
    /* 카드 디자인 */
    .metric-card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 메인 로직 시작 ---
try:
    gs_client, cal_service = get_gcp_clients()
    all_sheets = gs_client.openall()
    sheet = all_sheets[0].sheet1 # 첫 번째 시트 사용

    # 사이드바 메뉴
    st.sidebar.title("📌 Menu")
    menu = st.sidebar.selectbox("이동할 화면", ["Dashboard", "일정 등록", "상세 리스트"])

    if menu == "Dashboard":
        st.markdown("# 🚀 오늘의 일정 요약")
        
        # 데이터 가져오기 및 날짜 처리
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        today = datetime.now().date()
        
        if not df.empty:
            df['날짜'] = pd.to_datetime(df['날짜']).dt.date
            
            # 필터링 (요청사항 5 반영)
            today_tasks = df[df['날짜'] == today]
            week_tasks = df[(df['날짜'] >= today) & (df['날짜'] <= today + timedelta(days=7))]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='metric-card'><h3>오늘</h3><h2>{len(today_tasks)}건</h2></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card'><h3>이번 주</h3><h2>{len(week_tasks)}건</h2></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card'><h3>전체 일정</h3><h2>{len(df)}건</h2></div>", unsafe_allow_html=True)
            
            st.subheader("📍 오늘 해야 할 일")
            if not today_tasks.empty:
                st.table(today_tasks[['시간', '카테고리', '제목']])
            else:
                st.write("오늘은 자유시간입니다! 🎉")

    elif menu == "일정 등록":
        st.markdown("# ➕ 일정 추가하기")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("일정 명")
                category = st.radio("카테고리", ["회사", "개인"], horizontal=True) # 요청사항 1
                date = st.date_input("날짜 선택", today)
            with col2:
                time = st.time_input("시간 선택", datetime.now().time())
                freq = st.selectbox("반복 설정", ["안 함", "매주", "매달", "매년"]) # 요청사항 3
                desc = st.text_area("상세 내용")

            if st.button("구글 연동 및 저장"):
                # 구글 시트 저장
                sheet.append_row([str(date), str(time), category, title, desc, freq])
                
                # 구글 캘린더 연동 (보안 토큰 전송)
                start_dt = datetime.combine(date, time).isoformat()
                end_dt = (datetime.combine(date, time) + timedelta(hours=1)).isoformat()
                event = {
                    'summary': f"[{category}] {title}",
                    'description': f"{desc} (반복: {freq})",
                    'start': {'dateTime': start_dt, 'timeZone': 'Asia/Seoul'},
                    'end': {'dateTime': end_dt, 'timeZone': 'Asia/Seoul'},
                }
                cal_service.events().insert(calendarId='primary', body=event).execute()
                
                st.balloons()
                st.success("구글 시트와 캘린더에 성공적으로 저장되었습니다!")

    elif menu == "상세 리스트":
        st.markdown("# 📂 전체 일정 관리")
        records = sheet.get_all_records()
        if records:
            df = pd.DataFrame(records)
            # 회사/개인 필터 (요청사항 1)
            cat_filter = st.multiselect("카테고리 선택", ["회사", "개인"], default=["회사", "개인"])
            filtered_df = df[df['카테고리'].isin(cat_filter)]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

except Exception as e:
    st.error(f"연결 오류가 발생했습니다: {e}")
    st.info("해결방법 3을 확인 후 Streamlit 앱을 Reboot 하세요.")
