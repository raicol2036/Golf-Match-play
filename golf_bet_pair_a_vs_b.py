import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="鴻勁高球隊", layout="wide")

# === 側邊選單 ===
page = st.sidebar.radio("選擇功能頁面", ["成績管理", "比分對戰"])

# === 共用資料 (讀取 CSV) ===
players = pd.read_csv("players.csv", encoding="utf-8-sig")
courses = pd.read_csv("course_db.csv", encoding="utf-8-sig")

# 驗證欄位
if not set(["name","handicap","champion","runnerup"]).issubset(players.columns):
    st.error("❌ players.csv 欄位必須包含: name, handicap, champion, runnerup")
    st.stop()
if not set(["course_name","area","hole","hcp","par"]).issubset(courses.columns):
    st.error("❌ course_db.csv 欄位必須包含: course_name, area, hole, hcp, par")
    st.stop()

# --------------------------------------------------
# 📄 Page 1: 成績管理
# --------------------------------------------------
if page == "成績管理":
    st.title("🏌️ 鴻勁高球隊成績管理")

    # Step 1: 選擇球場
    course_names = courses["course_name"].unique()
    selected_course = st.selectbox("🏌️‍♂️ 選擇球場", course_names)
    course_filtered = courses[courses["course_name"] == selected_course]

    all_areas = course_filtered["area"].unique()
    selected_front = st.selectbox("前九洞區域", all_areas)
    back_options = [a for a in all_areas if a != selected_front]
    selected_back = st.selectbox("後九洞區域", back_options)

    course_selected = pd.concat([
        course_filtered[course_filtered["area"] == selected_front].sort_values("hole"),
        course_filtered[course_filtered["area"] == selected_back].sort_values("hole")
    ]).reset_index(drop=True)

    st.success(f"✅ 已選擇：{selected_course} / 前九: {selected_front} / 後九: {selected_back} （共 {len(course_selected)} 洞）")

    # Step 2: 設定人數
    st.header("1. 設定比賽人數")
    num_players = st.number_input("請輸入參賽人數 (1~24)", min_value=1, max_value=24, value=4, step=1)

    # Step 3: 選擇球員 & 輸入成績
    st.header("2. 輸入比賽成績 (連續輸入18位數字)")
    scores = {}
    selected_players = []

    for i in range(num_players):
        st.subheader(f"球員 {i+1}")
        cols = st.columns([1, 2])
        with cols[0]:
            player_name = st.selectbox(f"選擇球員 {i+1}", players["name"].values, key=f"player_{i}")
            selected_players.append(player_name)
        with cols[1]:
            score_str = st.text_input(f"{player_name} 的成績 (18位數字)", key=f"scores_{i}", max_chars=18)

        if score_str:
            if score_str.isdigit() and len(score_str) == 18:
                scores[player_name] = [int(x) for x in score_str]
            else:
                st.error(f"⚠️ {player_name} 成績必須是剛好 18 位數字")
                scores[player_name] = []
        else:
            scores[player_name] = []

    # 存到 session_state，供比分對戰使用
    st.session_state["scores"] = scores
    st.session_state["selected_players"] = selected_players
    st.session_state["course_selected"] = course_selected

    # Step 4: 計算與顯示結果 (略，保留你原本的總桿/淨桿/獎項/Leaderboard邏輯)
    # ...

# --------------------------------------------------
# 📄 Page 2: 比分對戰
# --------------------------------------------------
elif page == "比分對戰":
    st.title("⚔️ 球員逐洞比分 Match Play")

    if "scores" not in st.session_state or "selected_players" not in st.session_state:
        st.warning("請先到『成績管理』頁面輸入球員與成績")
        st.stop()

    scores = st.session_state["scores"]
    selected_players = st.session_state["selected_players"]
    course_selected = st.session_state["course_selected"]
    par = course_selected["par"].tolist()
    hcp = course_selected["hcp"].tolist()

    # Step 1: 選擇主球員
    player_a = st.selectbox("選擇主球員 A", selected_players)

    # Step 2: 對手設定
    opponents = [p for p in selected_players if p != player_a]
    handicaps, bets = {}, {}

    for op in opponents:
        st.markdown(f"### 對手：{op}")
        cols = st.columns([1, 1])
        with cols[0]:
            handicaps[op] = st.number_input(f"{op} 對 {player_a} 讓桿", -18, 18, 0, key=f"hcp_{op}")
        with cols[1]:
            bets[op] = st.number_input("每洞賭金", 50, 1000, 100, step=50, key=f"bet_{op}")

    # Step 3: 開始比分計算
    if st.button("開始比分計算"):
        total_earnings = {p: 0 for p in selected_players}
        result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in selected_players}

        for i in range(18):
            score_main = scores[player_a][i]
            for op in opponents:
                score_op = scores[op][i]

                adj_main, adj_op = score_main, score_op
                if handicaps[op] > 0 and hcp[i] <= handicaps[op]:
                    adj_op -= 1

                if adj_op < adj_main:  # 對手勝
                    bonus = 2 if score_op < par[i] else 1
                    total_earnings[op] += bets[op] * bonus
                    total_earnings[player_a] -= bets[op] * bonus
                    result_tracker[op]["win"] += 1
                    result_tracker[player_a]["lose"] += 1
                elif adj_op > adj_main:  # 主球員勝
                    bonus = 2 if score_main < par[i] else 1
                    total_earnings[player_a] += bets[op] * bonus
                    total_earnings[op] -= bets[op] * bonus
                    result_tracker[player_a]["win"] += 1
                    result_tracker[op]["lose"] += 1
                else:  # 平手
                    result_tracker[player_a]["tie"] += 1
                    result_tracker[op]["tie"] += 1

        # 輸出總結
        df_summary = pd.DataFrame([
            {
                "球員": p,
                "總賭金": total_earnings[p],
                "勝": result_tracker[p]["win"],
                "負": result_tracker[p]["lose"],
                "平": result_tracker[p]["tie"]
            }
            for p in selected_players
        ])
        st.dataframe(df_summary.set_index("球員"))