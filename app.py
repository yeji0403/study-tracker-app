
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

st.set_page_config(page_title="감정평가사 학습 루틴 트래커", layout="wide")

params = st.query_params
is_widget_mode = params.get("mode", [""])[0] == "today"

CSV_FILE = "study_tracker_data.csv"
GOALS_FILE = "monthly_goals.csv"
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
df["시작일"] = pd.to_datetime(df["시작일"])
today = pd.to_datetime(date.today())
months = sorted(df["월"].unique())

goal_dict = {}
if os.path.exists(GOALS_FILE):
    goal_df = pd.read_csv(GOALS_FILE)
    goal_dict = dict(zip(goal_df["월"], goal_df["목표"]))

if not is_widget_mode:
    st.title("📘 감정평가사 학습 루틴 관리")

if not is_widget_mode:
    st.sidebar.header("🗂️ 주차 필터")
    selected_month = st.sidebar.selectbox("월 선택", months)
    filtered_df = df[df["월"] == selected_month].sort_values("시작일").reset_index()

    total_tasks = len(filtered_df)
    completed_tasks = filtered_df["학습 완료"].sum()
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    st.sidebar.markdown(f"### ✅ 완료율: {completion_rate:.1f}%")
    st.sidebar.progress(completion_rate / 100)

    st.sidebar.markdown("---")
    st.sidebar.markdown("🎯 목표 설정")
    st.sidebar.text_area("중점 관리 항목", key="focus_area")

    st.markdown("## 📝 이달의 목표")
    goal_key = f"monthly_goal_{selected_month}"
    default_text = goal_dict.get(selected_month, "")
    updated_text = st.text_area(f"📝 {selected_month} 목표를 작성하세요", value=default_text, height=100, key=goal_key)
    goal_dict[selected_month] = updated_text
    goal_df = pd.DataFrame({"월": list(goal_dict.keys()), "목표": list(goal_dict.values())})
    goal_df.to_csv(GOALS_FILE, index=False)

    st.markdown(f"### 📅 {selected_month} 학습 계획")
    for i, row in filtered_df.iterrows():
        with st.container():
            cols = st.columns([1, 2, 4, 4, 1])
            cols[0].markdown(f"**{row['주차']}**")
            new_subject = cols[1].selectbox("과목", subject_options, index=subject_options.index(row["과목"]) if row["과목"] in subject_options else 0, key=f"subject_{row['index']}")
            new_plan = cols[2].text_area("세부 계획", value=row["세부 계획"], height=150, key=f"plan_{row['index']}")
            new_q = cols[3].text_area("Gemini 질문 예시", value=row["Gemini 질문 예시"], height=150, key=f"gemini_{row['index']}")
            new_done = cols[4].checkbox("", value=row["학습 완료"], key=f"check_{row['index']}")

            st.session_state.df.at[row["index"], "과목"] = new_subject
            st.session_state.df.at[row["index"], "세부 계획"] = new_plan
            st.session_state.df.at[row["index"], "Gemini 질문 예시"] = new_q
            st.session_state.df.at[row["index"], "학습 완료"] = new_done

    st.session_state.df.to_csv(CSV_FILE, index=False)

    with st.expander("📌 미완료 루틴 리마인더", expanded=False):
        undone_df = st.session_state.df[~st.session_state.df["학습 완료"]].sort_values("시작일")
        if undone_df.empty:
            st.success("🎉 모든 학습 루틴을 완료하셨습니다!")
        else:
            for i, row in undone_df.iterrows():
                cols = st.columns([2, 2, 4, 3, 1])
                cols[0].markdown(f"📅 {row['월']} {row['주차']}")
                cols[1].markdown(f"📝 {row['과목']}")
                cols[2].markdown(row["세부 계획"] or "_(세부 계획 없음)_")
                cols[3].markdown(row["Gemini 질문 예시"] or "_(예시 없음)_")
                st.session_state.df.at[row.name, "학습 완료"] = cols[4].checkbox("완료", value=row["학습 완료"], key=f"remind_check_{row.name}")

    with st.expander("📊 과목별 진도율 통계", expanded=False):
        subject_summary = st.session_state.df.groupby("과목")["학습 완료"].mean().sort_values()
        subject_percent = (subject_summary * 100).round(1)
        st.bar_chart(subject_summary)
        for subject, value in subject_percent.items():
            st.write(f"{subject}: {value}% 완료")

    st.markdown("---")
    st.download_button(
        "📥 전체 루틴 다운로드 (CSV)",
        data=st.session_state.df.drop(columns=["시작일", "고유주차"]).to_csv(index=False).encode('utf-8'),
        file_name=f"감정평가사_학습루틴_{date.today()}.csv",
        mime='text/csv'
    )

    st.caption("✅ 월을 선택하면 주차별 루틴을 확인하고 수정할 수 있습니다. 변경사항은 자동 저장됩니다.")
