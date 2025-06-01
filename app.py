import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="감정평가사 학습 루틴 트래커", layout="wide")

# URL 파라미터 확인
params = st.experimental_get_query_params()
is_widget_mode = params.get("mode", [""])[0] == "today"

if not is_widget_mode:
    st.title("📘 감정평가사 학습 루틴 관리")

# 자동 생성된 주차별 학습 계획
@st.cache_data
def generate_schedule():
    start_date = date(2025, 6, 3)
    subjects = ["민법", "경제학", "회계학", "부동산학", "감정평가관계법규"]
    weeks = []
    for i in range(156):
        week_start = start_date + timedelta(weeks=i)
        month = f"{week_start.year}-{week_start.month:02}"
        week_of_month = ((week_start.day - 1) // 7) + 1
        week_label = f"{week_of_month}주차"
        subject = subjects[i % len(subjects)]
        weeks.append([month, i, week_label, subject, week_start, "", "", False])
    return pd.DataFrame(weeks, columns=["월", "고유주차", "주차", "과목", "시작일", "세부 계획", "Gemini 질문 예시", "학습 완료"])

if "df" not in st.session_state:
    st.session_state.df = generate_schedule()

df = st.session_state.df.copy()

# 📌 오늘의 목표 위젯
st.markdown("## 📌 오늘의 목표")
today = date.today()
today_week = df[df["시작일"] <= today].iloc[-1] if not df[df["시작일"] <= today].empty else None
if today_week is not None:
    st.markdown(f"**주차:** {today_week['월']} {today_week['주차']}")
    st.markdown(f"**과목:** {today_week['과목']}")
    st.markdown(f"**세부 계획:** {today_week['세부 계획'] or '_(아직 입력되지 않음)_' }")
    st.markdown(f"**Gemini 질문 예시:** {today_week['Gemini 질문 예시'] or '_(예시 없음)_' }")
else:
    st.info("아직 시작된 학습 루틴이 없습니다.")

if not is_widget_mode:
    st.sidebar.header("🗂️ 주차 필터")
    months = sorted(df["월"].unique())
    selected_month = st.sidebar.selectbox("월 선택", months)
    filtered_df = df[df["월"] == selected_month].sort_values("시작일").reset_index()

    total_tasks = len(filtered_df)
    completed_tasks = filtered_df["학습 완료"].sum()
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    st.sidebar.markdown(f"### ✅ 완료율: {completion_rate:.1f}%")
    st.sidebar.progress(completion_rate / 100)

    st.sidebar.markdown("---")
    st.sidebar.markdown("🎯 목표 설정")
    st.sidebar.text_input("이번 달 목표", key="monthly_goal")
    st.sidebar.text_area("중점 관리 항목", key="focus_area")

    st.markdown(f"### 📅 {selected_month} 학습 계획")
    for i, row in filtered_df.iterrows():
        with st.container():
            cols = st.columns([1, 1, 1, 4, 3, 1])
            cols[0].markdown(f"**{row['주차']}**")
            cols[1].markdown(f"_{row['과목']}_")
            new_plan = cols[3].text_input("세부 계획", value=row["세부 계획"], key=f"plan_{row['index']}")
            new_q = cols[4].text_input("Gemini 질문 예시", value=row["Gemini 질문 예시"], key=f"gemini_{row['index']}")
            new_done = cols[5].checkbox("", value=row["학습 완료"], key=f"check_{row['index']}")

            st.session_state.df.at[row["index"], "세부 계획"] = new_plan
            st.session_state.df.at[row["index"], "Gemini 질문 예시"] = new_q
            st.session_state.df.at[row["index"], "학습 완료"] = new_done

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

    st.caption("✅ 좌측에서 월을 선택하면 해당 주차의 루틴만 간결하게 확인하고 수정할 수 있습니다. 목표와 진도율도 함께 관리해보세요.")
