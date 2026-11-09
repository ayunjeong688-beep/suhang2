import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, time
from pathlib import Path
import io

# ---------------------------------------------------------
# 콩팥 건강 지킴이
# 개인 건강 기록용 프로토타입
# 주의: 의료 진단/치료/복약 지시를 제공하지 않습니다.
# ---------------------------------------------------------

st.set_page_config(
    page_title="콩팥 건강 지킴이",
    page_icon="💚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path("kidney_health.db")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .stApp { background: #F5F9F7; }
    .block-container { max-width: 900px; padding-top: 1.4rem; padding-bottom: 3rem; }
    .hero {
        background: linear-gradient(135deg, #E3F3EC 0%, #F1F8F4 100%);
        border: 1px solid #D7EAE0; border-radius: 22px;
        padding: 22px 22px 18px 22px; margin-bottom: 16px;
    }
    .hero h1 { color: #205C48; font-size: 1.8rem; margin: 0 0 6px 0; }
    .hero p { color: #547568; margin: 0; font-size: .94rem; }
    .small-note { color: #687B73; font-size: .82rem; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #E3ECE7;
        border-radius: 16px; padding: 12px;
    }
    div.stButton > button {
        border-radius: 12px; min-height: 2.8rem; font-weight: 600;
    }
    div[data-testid="stForm"] {
        background: white; border: 1px solid #E3ECE7;
        border-radius: 16px; padding: 14px;
    }
    .section-card {
        background: white; border: 1px solid #E3ECE7;
        border-radius: 16px; padding: 15px; margin: 8px 0;
    }
    .warning {
        background: #FFF8E8; border: 1px solid #F1DCA8;
        color: #755A1A; border-radius: 12px; padding: 12px 14px;
        font-size: .88rem;
    }
    .success-note {
        background: #EAF5EF; border: 1px solid #D4E9DC;
        color: #285D47; border-radius: 12px; padding: 12px 14px;
    }
</style>
""", unsafe_allow_html=True)


def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            instruction TEXT,
            times TEXT NOT NULL,
            start_date TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS medicine_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            check_date TEXT NOT NULL,
            check_time TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 1,
            UNIQUE(medicine_id, check_date, check_time)
        );
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            foods TEXT NOT NULL,
            low_salt_practice INTEGER NOT NULL,
            memo TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date TEXT NOT NULL,
            blood_pressure TEXT,
            weight REAL,
            memo TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_date TEXT NOT NULL,
            hospital TEXT,
            department TEXT,
            purpose TEXT,
            questions TEXT,
            completed INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS health_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_date TEXT NOT NULL,
            note_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT
        );
        """)


def query_df(sql, params=()):
    with connect() as con:
        return pd.read_sql_query(sql, con, params=params)


def execute(sql, params=()):
    with connect() as con:
        con.execute(sql, params)
        con.commit()


def today_str():
    return date.today().isoformat()


def safe_text(value):
    return "" if pd.isna(value) else str(value)


init_db()

# Header
st.markdown("""
<div class="hero">
  <h1>💚 콩팥 건강 지킴이</h1>
  <p>약 복용 · 식사 · 건강 기록을 한곳에서 관리해요.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="warning">
<b>꼭 확인해 주세요</b><br>
이 앱은 개인 기록을 정리하는 도구이며 의료 진단이나 치료 지침이 아닙니다.
약의 종류·용량·복용 시간과 식사 제한은 반드시 담당 의료진의 안내를 따르세요.
투석 여부와 개인별 식사 기준이 확인되기 전에는 임의로 제한 항목을 추가하지 않습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="warning">
<b>배포 전 개인정보 주의</b><br>
현재 버전은 SQLite 파일에 기록을 저장하는 시제품입니다. Streamlit Cloud에서는 서버 재시작·재배포 시 데이터가 유지되지 않을 수 있고,
주소를 아는 사람이 접근할 수 있는 공개 앱에는 실제 약 이름이나 건강 기록을 입력하면 안 됩니다.
실제 사용 전에는 비밀번호 로그인과 영구 저장이 가능한 개인 데이터베이스를 추가하고 접근 권한을 제한해야 합니다.
</div>
""", unsafe_allow_html=True)

menu = st.radio(
    "메뉴",
    ["🏠 오늘", "💊 약 복용", "🥗 식사 기록", "📈 건강 기록", "🏥 병원 일정", "📝 건강 메모", "📤 기록 내보내기"],
    horizontal=True,
    label_visibility="collapsed",
)

# ---------------------- TODAY ----------------------
if menu == "🏠 오늘":
    st.subheader("오늘의 건강 관리")
    st.caption(f"{date.today().strftime('%Y년 %m월 %d일')} 기준")

    meds = query_df("SELECT * FROM medicines WHERE active=1 ORDER BY name")
    checks = query_df(
        "SELECT * FROM medicine_checks WHERE check_date=? AND completed=1",
        (today_str(),)
    )
    total_slots = sum(len([x for x in safe_text(r["times"]).split(",") if x.strip()]) for _, r in meds.iterrows())
    done_slots = len(checks)
    meals_today = query_df("SELECT * FROM meals WHERE meal_date=?", (today_str(),))
    health_today = query_df("SELECT * FROM health_records WHERE record_date=?", (today_str(),))
    upcoming = query_df(
        "SELECT * FROM appointments WHERE completed=0 AND visit_date>=? ORDER BY visit_date LIMIT 3",
        (today_str(),)
    )

    c1, c2 = st.columns(2)
    c1.metric("등록된 약", f"{len(meds)}개")
    c2.metric("오늘 약 복용 체크", f"{done_slots}회 / {total_slots}회")
    c3, c4 = st.columns(2)
    c3.metric("오늘 식사 기록", f"{len(meals_today)}건")
    c4.metric("오늘 건강 기록", f"{len(health_today)}건")

    st.markdown("#### 오늘 확인할 일")
    if total_slots == 0:
        st.info("아직 등록된 약이 없어요. '약 복용' 메뉴에서 처방받은 약과 시간을 입력해 주세요.")
    elif done_slots < total_slots:
        st.info("오늘의 약 복용 체크가 모두 완료되지는 않았어요. 실제 복용 여부를 확인한 뒤 체크해 주세요.")
    else:
        st.success("등록된 오늘의 복용 일정이 모두 체크되어 있어요. 체크는 실제 복용 여부를 확인한 뒤에만 해 주세요.")

    if len(upcoming):
        st.markdown("#### 다가오는 병원 일정")
        for _, row in upcoming.iterrows():
            st.markdown(
                f"<div class='section-card'><b>📅 {row['visit_date']}</b><br>"
                f"{safe_text(row['hospital'])} · {safe_text(row['department'])}<br>"
                f"<span class='small-note'>{safe_text(row['purpose'])}</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.caption("등록된 예정 병원 일정이 없어요.")

    st.caption("약 복용과 식사 기록은 위쪽 메뉴에서 선택할 수 있어요.")

# ---------------------- MEDICINES ----------------------
elif menu == "💊 약 복용":
    st.subheader("약 복용 관리")
    st.caption("처방전이나 약 봉투에 적힌 정보를 그대로 입력하세요. 이 앱은 복용량이나 시간을 추천하지 않습니다.")

    with st.expander("＋ 복용 중인 약 등록", expanded=True):
        with st.form("add_medicine", clear_on_submit=True):
            name = st.text_input("약 이름 *", placeholder="약 봉투에 적힌 이름")
            instruction = st.text_input("처방된 복용 방법 (선택)", placeholder="예: 처방전의 안내를 그대로 입력")
            times = st.text_input("복용 시간 *", placeholder="예: 08:00, 20:00")
            start = st.date_input("복용 시작일", value=date.today())
            st.caption("시간은 쉼표로 구분해 입력해 주세요. 예: 08:00, 13:00, 20:00")
            submitted = st.form_submit_button("약 등록하기", use_container_width=True)
            if submitted:
                valid_times = []
                for t in times.split(","):
                    t = t.strip()
                    try:
                        datetime.strptime(t, "%H:%M")
                        valid_times.append(t)
                    except ValueError:
                        pass
                if not name.strip():
                    st.error("약 이름을 입력해 주세요.")
                elif not valid_times or len(valid_times) != len([x for x in times.split(",") if x.strip()]):
                    st.error("복용 시간을 HH:MM 형식으로 입력해 주세요. 예: 08:00, 20:00")
                else:
                    execute(
                        "INSERT INTO medicines(name,instruction,times,start_date,created_at) VALUES(?,?,?,?,?)",
                        (name.strip(), instruction.strip(), ",".join(valid_times), start.isoformat(), datetime.now().isoformat())
                    )
                    st.success("약이 등록되었어요.")
                    st.rerun()

    meds = query_df("SELECT * FROM medicines WHERE active=1 ORDER BY name")
    if meds.empty:
        st.info("등록된 약이 없어요.")
    else:
        st.markdown("#### 오늘의 복용 확인")
        for _, med in meds.iterrows():
            times_list = [x.strip() for x in safe_text(med["times"]).split(",") if x.strip()]
            with st.container(border=True):
                st.markdown(f"**💊 {med['name']}**")
                if safe_text(med["instruction"]):
                    st.caption(f"처방된 복용 방법: {med['instruction']}")
                for t in times_list:
                    existing = query_df(
                        "SELECT completed FROM medicine_checks WHERE medicine_id=? AND check_date=? AND check_time=?",
                        (int(med["id"]), today_str(), t)
                    )
                    is_done = (not existing.empty and int(existing.iloc[0]["completed"]) == 1)
                    key = f"med_{med['id']}_{today_str()}_{t}"
                    checked = st.checkbox(f"{t} 복용 확인", value=is_done, key=key)
                    if checked != is_done:
                        if checked:
                            execute(
                                "INSERT OR REPLACE INTO medicine_checks(medicine_id,check_date,check_time,completed) VALUES(?,?,?,1)",
                                (int(med["id"]), today_str(), t)
                            )
                        else:
                            execute(
                                "DELETE FROM medicine_checks WHERE medicine_id=? AND check_date=? AND check_time=?",
                                (int(med["id"]), today_str(), t)
                            )
                        st.rerun()
                if st.button(f"등록 해제: {med['name']}", key=f"deactivate_{med['id']}"):
                    execute("UPDATE medicines SET active=0 WHERE id=?", (int(med["id"]),))
                    st.rerun()

    st.markdown("""
    <div class="warning">
    약을 놓쳤거나 복용했는지 기억나지 않을 때 임의로 두 배 복용하지 마세요.
    약사 또는 처방한 의료진에게 확인하세요. 이 앱은 알람을 보내지 않으며, 앱을 직접 열어 체크해야 합니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 지난 복용 기록")
    history = query_df("""
        SELECT m.name AS 약이름, c.check_date AS 날짜, c.check_time AS 시간,
               CASE WHEN c.completed=1 THEN '복용 확인' ELSE '미확인' END AS 상태
        FROM medicine_checks c JOIN medicines m ON m.id=c.medicine_id
        ORDER BY c.check_date DESC, c.check_time DESC LIMIT 50
    """)
    if not history.empty:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.caption("아직 체크된 복용 기록이 없어요.")

# ---------------------- MEALS ----------------------
elif menu == "🥗 식사 기록":
    st.subheader("식사 기록")
    st.caption("싱겁게 먹기 실천과 실제 식사 내용을 기록해요. 음식의 적정량이나 영양 제한은 의료진·영양사의 안내를 따르세요.")

    with st.form("meal_form", clear_on_submit=True):
        meal_date = st.date_input("식사 날짜", value=date.today())
        meal_type = st.selectbox("식사 구분", ["아침", "점심", "저녁", "간식"])
        foods = st.text_area("먹은 음식", placeholder="예: 밥, 생선구이, 나물, 국")
        low_salt = st.radio("오늘 이 식사는 싱겁게 먹으려고 노력했나요?", ["네", "아니요", "잘 모르겠어요"], horizontal=True)
        memo = st.text_area("추가 메모 (선택)", placeholder="예: 외식함, 국물은 적게 먹음 등")
        save_meal = st.form_submit_button("식사 저장하기", use_container_width=True)
        if save_meal:
            if not foods.strip():
                st.error("먹은 음식을 입력해 주세요.")
            else:
                execute(
                    "INSERT INTO meals(meal_date,meal_type,foods,low_salt_practice,memo,created_at) VALUES(?,?,?,?,?,?)",
                    (meal_date.isoformat(), meal_type, foods.strip(), 1 if low_salt == "네" else (0 if low_salt == "아니요" else -1), f"{low_salt}. {memo.strip()}".strip(), datetime.now().isoformat())
                )
                st.success("식사 기록을 저장했어요.")
                st.rerun()

    st.markdown("#### 최근 식사 기록")
    meals = query_df("SELECT meal_date AS 날짜, meal_type AS 구분, foods AS 음식, memo AS 메모 FROM meals ORDER BY meal_date DESC, id DESC LIMIT 30")
    if not meals.empty:
        st.dataframe(meals, use_container_width=True, hide_index=True)
    else:
        st.info("아직 식사 기록이 없어요.")

    st.markdown("""
    <div class="warning">
    '싱겁게 먹기'는 기록용 체크 항목입니다. 이 앱은 음식 사진이나 이름만으로 나트륨·칼륨·인·단백질 함량을 정확히 판정하지 않습니다.
    가공식품, 국물, 양념 등 구체적인 주의사항은 담당 의료진 또는 신장 전문 영양사에게 확인해 주세요.
    </div>
    """, unsafe_allow_html=True)

# ---------------------- HEALTH ----------------------
elif menu == "📈 건강 기록":
    st.subheader("건강 수치 기록")
    st.caption("혈압과 체중을 기록하고 병원에서 확인한 검사 결과를 메모할 수 있어요.")

    with st.form("health_form", clear_on_submit=True):
        record_date = st.date_input("기록 날짜", value=date.today())
        bp = st.text_input("혈압 (선택)", placeholder="예: 120/80")
        weight = st.number_input("체중 kg (모르면 0)", min_value=0.0, max_value=400.0, value=0.0, step=0.1)
        memo = st.text_area("검사 결과 또는 몸 상태 메모", placeholder="의료진이 설명한 내용을 기록하세요.")
        save_health = st.form_submit_button("건강 기록 저장", use_container_width=True)
        if save_health:
            if not bp.strip() and weight == 0 and not memo.strip():
                st.error("기록할 내용을 하나 이상 입력해 주세요.")
            else:
                execute(
                    "INSERT INTO health_records(record_date,blood_pressure,weight,memo,created_at) VALUES(?,?,?,?,?)",
                    (record_date.isoformat(), bp.strip(), None if weight == 0 else weight, memo.strip(), datetime.now().isoformat())
                )
                st.success("건강 기록을 저장했어요.")
                st.rerun()

    records = query_df("SELECT record_date AS 날짜, blood_pressure AS 혈압, weight AS 체중_kg, memo AS 메모 FROM health_records ORDER BY record_date DESC, id DESC")
    if not records.empty:
        st.markdown("#### 기록 목록")
        st.dataframe(records, use_container_width=True, hide_index=True)
        weight_df = records.dropna(subset=["체중_kg"]).copy()
        if not weight_df.empty:
            weight_df["체중_kg"] = pd.to_numeric(weight_df["체중_kg"], errors="coerce")
            weight_df = weight_df.dropna(subset=["체중_kg"]).sort_values("날짜")
            if len(weight_df) >= 2:
                st.markdown("#### 체중 기록 변화")
                st.line_chart(weight_df.set_index("날짜")["체중_kg"])
    else:
        st.info("아직 건강 기록이 없어요.")

    st.caption("혈압·체중의 목표 범위나 이상 여부를 앱이 판정하지 않습니다. 측정 방법과 해석은 의료진의 안내를 따르세요.")

# ---------------------- APPOINTMENTS ----------------------
elif menu == "🏥 병원 일정":
    st.subheader("병원 방문 및 진료 일정")
    with st.form("appointment_form", clear_on_submit=True):
        visit_date = st.date_input("진료 예정일", value=date.today())
        hospital = st.text_input("병원 이름")
        department = st.text_input("진료과", placeholder="예: 신장내과")
        purpose = st.text_input("방문 목적", placeholder="예: 정기 진료, 검사 결과 상담")
        questions = st.text_area("의사에게 물어볼 내용", placeholder="진료 전에 궁금한 점을 적어 두세요.")
        save_appt = st.form_submit_button("일정 저장", use_container_width=True)
        if save_appt:
            execute(
                "INSERT INTO appointments(visit_date,hospital,department,purpose,questions) VALUES(?,?,?,?,?)",
                (visit_date.isoformat(), hospital.strip(), department.strip(), purpose.strip(), questions.strip())
            )
            st.success("병원 일정이 저장되었어요.")
            st.rerun()

    appts = query_df("SELECT * FROM appointments ORDER BY visit_date DESC")
    if not appts.empty:
        st.markdown("#### 등록된 일정")
        for _, row in appts.iterrows():
            with st.container(border=True):
                st.markdown(f"**📅 {row['visit_date']} · {safe_text(row['hospital'])}**")
                st.write(f"{safe_text(row['department'])} · {safe_text(row['purpose'])}")
                if safe_text(row["questions"]):
                    st.caption(f"질문: {row['questions']}")
                if not int(row["completed"]):
                    if st.button("진료 완료로 표시", key=f"appt_done_{row['id']}"):
                        execute("UPDATE appointments SET completed=1 WHERE id=?", (int(row["id"]),))
                        st.rerun()
                else:
                    st.success("진료 완료")
    else:
        st.info("등록된 병원 일정이 없어요.")

# ---------------------- NOTES ----------------------
elif menu == "📝 건강 메모":
    st.subheader("건강 메모")
    with st.form("note_form", clear_on_submit=True):
        note_date = st.date_input("날짜", value=date.today())
        note_type = st.selectbox("메모 종류", ["몸 상태", "의료진 설명", "식사 관련 안내", "기타"])
        content = st.text_area("내용", placeholder="몸 상태나 병원에서 들은 안내를 기록하세요.")
        save_note = st.form_submit_button("메모 저장", use_container_width=True)
        if save_note:
            if not content.strip():
                st.error("메모 내용을 입력해 주세요.")
            else:
                execute(
                    "INSERT INTO health_notes(note_date,note_type,content,created_at) VALUES(?,?,?,?)",
                    (note_date.isoformat(), note_type, content.strip(), datetime.now().isoformat())
                )
                st.success("메모를 저장했어요.")
                st.rerun()

    notes = query_df("SELECT note_date AS 날짜, note_type AS 종류, content AS 내용 FROM health_notes ORDER BY note_date DESC, id DESC")
    if not notes.empty:
        st.dataframe(notes, use_container_width=True, hide_index=True)
    else:
        st.info("저장된 메모가 없어요.")

# ---------------------- EXPORT ----------------------
elif menu == "📤 기록 내보내기":
    st.subheader("건강 기록 내보내기")
    st.write("필요할 때 기록을 내려받아 병원 진료 시 참고 자료로 활용할 수 있어요. 의료진에게 보여주기 전 개인정보가 포함되어 있는지 확인하세요.")

    tables = {
        "약 목록": "SELECT name AS 약이름, instruction AS 처방된_복용방법, times AS 등록된_복용시간, start_date AS 시작일, active AS 사용중 FROM medicines",
        "약 복용 체크": """SELECT m.name AS 약이름, c.check_date AS 날짜, c.check_time AS 시간, c.completed AS 복용체크
                           FROM medicine_checks c JOIN medicines m ON m.id=c.medicine_id""",
        "식사 기록": "SELECT meal_date AS 날짜, meal_type AS 식사구분, foods AS 음식, low_salt_practice AS 싱겁게먹기_실천, memo AS 메모 FROM meals",
        "건강 기록": "SELECT record_date AS 날짜, blood_pressure AS 혈압, weight AS 체중_kg, memo AS 메모 FROM health_records",
        "병원 일정": "SELECT visit_date AS 날짜, hospital AS 병원, department AS 진료과, purpose AS 목적, questions AS 질문, completed AS 완료 FROM appointments",
        "건강 메모": "SELECT note_date AS 날짜, note_type AS 종류, content AS 내용 FROM health_notes",
    }

    dataframes = {name: query_df(sql) for name, sql in tables.items()}
    total_rows = sum(len(df) for df in dataframes.values())
    st.metric("저장된 전체 기록", f"{total_rows}건")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in dataframes.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    output.seek(0)

    st.download_button(
        "📥 엑셀 파일로 다운로드",
        data=output.getvalue(),
        file_name=f"콩팥_건강기록_{today_str()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("""
    <div class="warning">
    <b>개인정보 보호 안내</b><br>
    이 파일에는 약 이름, 건강 수치, 진료 내용 등 민감한 건강 정보가 포함될 수 있습니다.
    다른 사람과 공유하거나 공개된 장소에 저장하지 마세요.
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.markdown("""
<div class="small-note">
💚 콩팥 건강 지킴이 · 개인 건강 기록용<br>
이 앱은 의료진의 진단, 처방, 약사 상담 또는 응급 진료를 대체하지 않습니다.
앱의 복용 체크는 알림이 아니므로 정해진 시간에 휴대폰 알람도 별도로 설정해 주세요.
</div>
""", unsafe_allow_html=True)
