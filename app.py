
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

st.set_page_config(page_title="감정평가사 학습 루틴 트래커", layout="wide")

params = st.query_params
is_widget_mode = params.get("mode", [""])[0] == "today"

CSV_FILE = "study_tracker_data.csv"
subject_options = ["민법", "경제학", "회계학", "부동산학", "감정평가관계법규"]

@st.cache_data
def generate_schedule():
    start_date = date(2025, 6, 3)
    weeks = []
    for i in range(156):
        week_start = start_date + timedelta(weeks=i)
        month = f"{week_start.year}-{week_start.month:02}"
        week_of_month = ((week_start.day - 1) // 7) + 1
        week_label = f"{week_of_month}주차"
        subject = subject_options[i % len(subject_options)]
        weeks.append([month, i, week_label, subject, week_start, "", "", False])
    return pd.DataFrame(weeks, columns=["월", "고유주차", "주차", "과목", "시작일", "세부 계획", "Gemini 질문 예시", "학습 완료"])

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["학습 완료"] = df["학습 완료"].astype(bool)
else:
    df = generate_schedule()

if "df" not in st.session_state:
    st.session_state.df = df.copy()

df = st.session_state.df.copy()

if not is_widget_mode:
    st.title("📘 감정평가사 학습 루틴 관리")

st.markdown("## 📌 오늘의 목표")
today = date.today()
today_week = df[df["시작일"] <= str(today)].iloc[-1] if not df[df["시작일"] <= str(today)].empty else None
if today_week is not None:
    st.markdown(f"**주차:** {today_week['월']} {today_week['주차']}")
    st.markdown(f"**과목:** {today_week['과목']}")
    st.markdown(f"**세부 계획:** {today_week['세부 계획'] or '_(아직 입력되지 않음)_' }")
    st.markdown(f"**Gemini 질문 예시:** {today_week['Gemini 질문 예시'] or '_(예시 없음)_' }")
else:
    st.info("아직 시작된 학습 루틴이 없습니다.")
