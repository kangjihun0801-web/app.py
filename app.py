import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Smart Scheduler", layout="wide")

# 데이터 저장 (간이 데이터베이스 역할 - 새로고침하면 초기화되므로 나중에는 DB 연결 필요)
if 'events' not in st.session_state:
    st.session_state.events = []
if 'notifications' not in st.session_state:
    st.session_state.notifications = []

# --- 사이드바: 메뉴 이동 ---
menu = st.sidebar.radio("메뉴 선택", ["일정 입력 및 분석", "내 캘린더", "할 일 리스트", "알림 센터"])

# --- 1. 일정 입력 및 분석 (요청 2, 3번 반영) ---
if menu == "일정 입력 및 분석":
    st.title("➕ 새 일정 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("직접 입력")
        title = st.text_input("일정 명")
        category = st.selectbox("카테고리", ["회사", "개인"])
        date = st.date_input("날짜 선택", datetime.now())
        freq = st.selectbox("반복 설정", ["안 함", "매주", "매달", "매년"])
        content = st.text_area("상세 내용")
        
        if st.button("일정 추가"):
            new_event = {"title": title, "category": category, "date": date, "freq": freq, "content": content}
            st.session_state.events.append(new_event)
            # 알림 추가 (요청 4번 반영)
            st.session_state.notifications.append(f"🔔 '{title}' 일정이 등록되었습니다. ({date})")
            st.success(f"'{title}' 일정이 저장되었습니다!")

    with col2:
        st.subheader("이메일 분석으로 등록")
        email_text = st.text_area("이메일 본문을 붙여넣으세요", height=200)
        if st.button("AI 분석 실행"):
            st.info("이메일에서 일정을 추출 중입니다... (API 연결 대기)")
            # 임시 데이터 추가
            st.session_state.events.append({"title": "추출된 회의", "category": "회사", "date": datetime.now().date(), "freq": "안 함", "content": "메일 기반 생성"})

# --- 2. 내 캘린더 (요청 1번 반영) ---
elif menu == "내 캘린더":
    st.title("📅 일정 확인")
    
    view_option = st.radio("보기 설정", ["전체 보기", "회사 일정만", "개인 일정만"], horizontal=True)
    
    df = pd.DataFrame(st.session_state.events)
    
    if not df.empty:
        if view_option == "회사 일정만":
            df = df[df['category'] == "회사"]
        elif view_option == "개인 일정만":
            df = df[df['category'] == "개인"]
            
        st.dataframe(df, use_container_width=True)
    else:
        st.write("등록된 일정이 없습니다.")

# --- 3. 할 일 리스트 (요청 5번 반영) ---
elif menu == "할 일 리스트":
    st.title("📝 할 일 정리")
    
    today = datetime.now().date()
    this_week = today + timedelta(days=7)
    this_month = today + timedelta(days=30)
    
    df = pd.DataFrame(st.session_state.events)
    
    if not df.empty:
        tab1, tab2, tab3 = st.tabs(["오늘", "이번 주", "이번 달"])
        
        with tab1:
            st.write("📍 오늘 할 일")
            st.table(df[df['date'] == today])
            
        with tab2:
            st.write("📍 이번 주 할 일")
            st.table(df[(df['date'] >= today) & (df['date'] <= this_week)])
            
        with tab3:
            st.write("📍 이번 달 할 일")
            st.table(df[(df['date'] >= today) & (df['date'] <= this_month)])
    else:
        st.write("할 일이 없습니다.")

# --- 4. 알림 센터 (요청 4번 반영) ---
elif menu == "알림 센터":
    st.title("🔔 알림 모아보기")
    if st.session_state.notifications:
        for note in reversed(st.session_state.notifications):
            st.info(note)
    else:
        st.write("새로운 알림이 없습니다.")
