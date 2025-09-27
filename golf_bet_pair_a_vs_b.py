import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="鴻勁高球隊", layout="wide")

# === 側邊選單 ===
page = st.sidebar.radio("選擇功能頁面", ["成績管理", "比分對戰"])

# === 共用資料 (讀取 CSV) ===
players = pd.read_csv("players.csv", encoding="utf-8-sig")
courses = pd.read_csv("course_db.csv", encoding="utf-8-sig")

# --------------------------------------------------
# 📄 Page 1: 成績管理
# --------------------------------------------------
if page == "成績管理":
    st.title("🏌️ 鴻勁高球隊成績管理")

    # === 驗證欄位 ===
    if not set(["name","handicap","champion","runnerup"]).issubset(players.columns):
        st.error("❌ players.csv 欄位必須包含: name, handicap, champion, runnerup")
        st.stop()
    if not set(["course_name","area","hole","hcp","par"]).issubset(courses.columns):
        st.error("❌ course_db.csv 欄位必須包含: course_name, area, hole, hcp, par")
        st.stop()

    st.header("0. 比賽設定")

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

    # === 設定比賽人數 ===
    st.header("1. 設定比賽人數")
    num_players = st.number_input("請輸入參賽人數 (1~24)", min_value=1, max_value=24, value=4, step=1)

    # === 輸入球員與成績 ===
    st.header("2. 輸入比賽成績 (連續輸入18位數字)")
    scores = {}
    selected_players = []

    for i in range(num_players):
        st.subheader(f"球員 {i+1}")
        cols = st.columns([1, 2])

        with cols[0]:
            player_name = st.selectbox(
                f"選擇球員 {i+1}",
                players["name"].values,
                key=f"player_{i}"
            )
            selected_players.append(player_name)

        with cols[1]:
            score_str = st.text_input(
                f"{player_name} 的成績 (18位數字)",
                key=f"scores_{i}",
                max_chars=18
            )

        if score_str:
            if score_str.isdigit() and len(score_str) == 18:
                scores[player_name] = [int(x) for x in score_str]
            else:
                st.error(f"⚠️ {player_name} 成績必須是剛好 18 位數字")
                scores[player_name] = []
        else:
            scores[player_name] = []

    # 存進 session_state 供 Page2 使用
    st.session_state["scores"] = scores
    st.session_state["selected_players"] = selected_players
    st.session_state["course_selected"] = course_selected

    # === 計算比賽結果 ===
    def calculate_gross(scores):
        return {p: sum(s) for p, s in scores.items() if s}

    def calculate_net(gross_scores):
        net_scores = {}
        for p, gross in gross_scores.items():
            hcp = int(players.loc[players["name"] == p, "handicap"].values[0])
            net_scores[p] = gross - hcp
        return net_scores

    def find_birdies(scores, course_selected):
        birdies = []
        for p, s in scores.items():
            for i, score in enumerate(s):
                if i < len(course_selected):
                    par = course_selected.iloc[i]["par"]
                    if score == par - 1:
                        hole_num = course_selected.iloc[i]["hole"]
                        birdies.append((p, hole_num))
        return birdies

    def get_winners(scores, course_selected):
        gross = calculate_gross(scores)
        net = calculate_net(gross)
        birdies = find_birdies(scores, course_selected)

        gross_sorted = sorted(gross.items(), key=lambda x: x[1])
        gross_champ, gross_runner = None, None
        for p, _ in gross_sorted:
            if players.loc[players["name"]==p,"champion"].values[0] == "No":
                gross_champ = p
                break
        for p, _ in gross_sorted:
            if p != gross_champ and players.loc[players["name"]==p,"runnerup"].values[0] == "No":
                gross_runner = p
                break

        exclude_players = [gross_champ, gross_runner]
        net_candidates = {p:s for p,s in net.items() if p not in exclude_players}
        net_sorted = sorted(net_candidates.items(), key=lambda x: x[1])
        net_champ, net_runner = None, None
        if len(net_sorted) > 0: net_champ = net_sorted[0][0]
        if len(net_sorted) > 1: net_runner = net_sorted[1][0]

        hcp_updates = {p: 0 for p in gross.keys()}
        if net_champ: hcp_updates[net_champ] = -2
        if net_runner: hcp_updates[net_runner] = -1
        hcp_new = {p: int(players.loc[players["name"] == p, "handicap"].values[0]) + hcp_updates[p] for p in gross.keys()}

        return {
            "gross": gross,
            "net": net,
            "gross_champion": gross_champ,
            "gross_runnerup": gross_runner,
            "net_champion": net_champ,
            "net_runnerup": net_runner,
            "birdies": birdies,
            "hcp_new": hcp_new,
        }

    if st.button("開始計算"):
        winners = get_winners(scores, course_selected)

        st.subheader("🏆 比賽結果")
        col1, col2 = st.columns(2)
        with col1: st.write(f"🏅 總桿冠軍: {winners['gross_champion']}")
        with col2: st.write(f"🥈 總桿亞軍: {winners['gross_runnerup']}")
        col3, col4 = st.columns(2)
        with col3: st.write(f"🏅 淨桿冠軍: {winners['net_champion']}")
        with col4: st.write(f"🥈 淨桿亞軍: {winners['net_runnerup']}")

        if winners["birdies"]:
            st.write("✨ Birdie 紀錄：")
            birdie_dict = {}
            for player, hole in winners["birdies"]:
                birdie_dict.setdefault(player, []).append(hole)
            for player, holes in birdie_dict.items():
                hole_text = "/".join([f"第{h}洞" for h in holes])
                st.write(f"- {player} {hole_text}")
        else:
            st.write("無 Birdie 紀錄")

        # Leaderboard
        st.subheader("📊 Leaderboard 排名表")
        player_hcps = {p: int(players.loc[players["name"] == p, "handicap"].values[0]) for p in winners["gross"].keys()}
        df_leader = pd.DataFrame({
            "球員": list(winners["gross"].keys()),
            "原始差點": [player_hcps[p] for p in winners["gross"].keys()],
            "總桿": list(winners["gross"].values()),
            "淨桿": [winners["net"][p] for p in winners["gross"].keys()],
            "總桿排名": pd.Series(winners["gross"]).rank(method="min").astype(int).values,
            "淨桿排名": pd.Series(winners["net"]).rank(method="min").astype(int).values,
            "差點更新": [winners["hcp_new"][p] for p in winners["gross"].keys()]
        })
        st.dataframe(df_leader.sort_values("淨桿排名"))

# --------------------------------------------------
# 📄 Page 2: 比分對戰
# --------------------------------------------------
elif page == "比分對戰":
    st.title("⚔️ 球員逐洞比分 Match Play")

    if "scores" not in st.session_state or "selected_players" not in st.session_state:
        st.warning("⚠️ 請先到『成績管理』頁面輸入球員與成績")
        st.stop()

    scores = st.session_state["scores"]
    selected_players = st.session_state["selected_players"]

    match_result = {p: {"win": 0, "lose": 0, "tie": 0} for p in selected_players}

    for i in range(18):
        hole_scores = {p: scores[p][i] for p in selected_players if scores[p]}
        if not hole_scores:
            continue
        min_score = min(hole_scores.values())
        winners = [p for p, s in hole_scores.items() if s == min_score]

        if len(winners) == 1:
            winner = winners[0]
            match_result[winner]["win"] += 1
            for p in selected_players:
                if p != winner:
                    match_result[p]["lose"] += 1
        else:
            for p in winners:
                match_result[p]["tie"] += 1
            for p in selected_players:
                if p not in winners:
                    match_result[p]["lose"] += 1

    df_match = pd.DataFrame([
        {
            "球員": p,
            "勝洞": r["win"],
            "負洞": r["lose"],
            "平洞": r["tie"],
            "淨勝洞": r["win"] - r["lose"]
        }
        for p, r in match_result.items()
    ])
    st.dataframe(df_match.set_index("球員"))