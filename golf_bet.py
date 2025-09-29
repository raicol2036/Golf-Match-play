import streamlit as st
import pandas as pd
import io
from collections import Counter

st.set_page_config(page_title="鴻勁高球隊成績管理", layout="wide")
st.title("🏌️ 鴻勁高球隊成績管理")

# === 載入 CSV ===
players = pd.read_csv("players.csv", encoding="utf-8-sig")
courses = pd.read_csv("course_db.csv", encoding="utf-8-sig")

# 驗證欄位
if not set(["name","handicap","champion","runnerup"]).issubset(players.columns):
    st.error("❌ players.csv 必須包含: name, handicap, champion, runnerup")
    st.stop()
if not set(["course_name","area","hole","hcp","par"]).issubset(courses.columns):
    st.error("❌ course_db.csv 必須包含: course_name, area, hole, hcp, par")
    st.stop()

# --- Sidebar 分頁 ---
page = st.sidebar.radio("📑 選擇頁面", 
                        ["比賽設定", "成績輸入", "比賽結果與獎項", "匯出報表"], 
                        key="main_page")

# === 初始化 session_state ===
if "scores" not in st.session_state: st.session_state.scores = {}
if "course_selected" not in st.session_state: st.session_state.course_selected = None
if "selected_players" not in st.session_state: st.session_state.selected_players = []
if "winners" not in st.session_state: st.session_state.winners = None
if "awards" not in st.session_state: st.session_state.awards = {}
if "num_players" not in st.session_state: st.session_state.num_players = 4
if "match_summary" not in st.session_state: st.session_state.match_summary = None
if "match_df" not in st.session_state: st.session_state.match_df = None

# === 共用計算函式 ===
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

    # 總桿冠軍
    gross_champ = None
    for p, _ in gross_sorted:
        if players.loc[players["name"]==p,"champion"].values[0] == "No":
            gross_champ = p
            break

    # 總桿亞軍
    gross_runner = None
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

# ------------------ 分頁內容 ------------------

# === 比賽設定 ===
if page == "比賽設定":
    st.header("⚙️ 比賽設定")

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

    st.session_state.course_selected = course_selected
    st.success(f"✅ 已選擇：{selected_course} / 前九: {selected_front} / 後九: {selected_back}")

    st.session_state.num_players = st.number_input("請輸入參賽人數 (1~24)", 1, 24, 4)

# === 成績輸入 ===
elif page == "成績輸入":
    st.header("✍️ 輸入比賽成績")
    scores = {}
    selected_players = []

    for i in range(st.session_state.num_players):
        st.subheader(f"球員 {i+1}")
        cols = st.columns([1,2])
        with cols[0]:
            player_name = st.selectbox(f"選擇球員 {i+1}", players["name"].values, key=f"player_{i}")
            selected_players.append(player_name)
        with cols[1]:
            score_str = st.text_input(f"{player_name} 的成績 (18位數字)", key=f"scores_{i}", max_chars=18)

        if score_str and score_str.isdigit() and len(score_str) == 18:
            scores[player_name] = [int(x) for x in score_str]
        else:
            scores[player_name] = []

    st.session_state.scores = scores
    st.session_state.selected_players = selected_players

# === 比賽結果與獎項 ===
elif page == "比賽結果與獎項":
    st.header("🏆 比賽結果")

    if st.session_state.scores:
        winners = get_winners(st.session_state.scores, st.session_state.course_selected)
        st.session_state.winners = winners

        col1, col2 = st.columns(2)
        col1.write(f"🏅 總桿冠軍: {winners['gross_champion']}")
        col2.write(f"🥈 總桿亞軍: {winners['gross_runnerup']}")

        col3, col4 = st.columns(2)
        col3.write(f"🏅 淨桿冠軍: {winners['net_champion']}")
        col4.write(f"🥈 淨桿亞軍: {winners['net_runnerup']}")

        # Birdie 紀錄
        if winners["birdies"]:
            st.write("✨ Birdie 紀錄：")
            birdie_dict = {}
            for player, hole in winners["birdies"]:
                birdie_dict.setdefault(player, []).append(hole)
            for player, holes in birdie_dict.items():
                holes_sorted = sorted(holes)
                st.write(f"- {player} 第{'/'.join([str(h)+'洞' for h in holes_sorted])}")
        else:
            st.write("無 Birdie 紀錄")

        # ------------------ Match Play ------------------
        st.subheader("⚔️ Match Play 賭金結算 (單位 50)")
        bet_unit = 50
        scores = st.session_state.scores
        course_selected = st.session_state.course_selected
        match_results = []
        total_earnings = {p: 0 for p in scores.keys()}

        for i in range(18):
            hole_scores = {p: scores[p][i] for p in scores if scores[p]}
            min_score = min(hole_scores.values())
            winners_hole = [p for p,s in hole_scores.items() if s == min_score]

            if len(winners_hole) == 1:
                winner = winners_hole[0]
                for p in scores.keys():
                    if p == winner:
                        total_earnings[p] += bet_unit
                    else:
                        total_earnings[p] -= bet_unit
                match_results.append({"洞": i+1, "勝者": winner, "賭金單位": bet_unit})
            else:
                match_results.append({"洞": i+1, "勝者": "平手", "賭金單位": 0})

        match_df = pd.DataFrame(match_results)
        st.dataframe(match_df)
        summary_df = pd.DataFrame([{"球員": p, "總結算": total_earnings[p]} for p in total_earnings])
        st.subheader("💰 Match Play 總結")
        st.dataframe(summary_df.set_index("球員"))

        st.session_state.match_summary = summary_df
        st.session_state.match_df = match_df

        # ------------------ 獎項 ------------------
        st.subheader("🎯 獎項選擇")
        long_drive = st.multiselect("🏌️‍♂️ 遠距獎", players["name"].values, max_selections=2)
        near1 = st.multiselect("🎯 一近洞獎", players["name"].values, max_selections=2)
        num_n_near = st.number_input("N近洞獎數量", 0, 18, 0)
        n_near_awards = []
        for i in range(num_n_near):
            player = st.selectbox(f"N近洞獎 第{i+1}名", ["無"]+list(players["name"].values), key=f"n_near_{i}")
            if player != "無": n_near_awards.append(player)

        awards = {"遠距獎": long_drive, "一近洞獎": near1, "N近洞獎": n_near_awards}
        st.session_state.awards = awards

        st.subheader("🏅 特殊獎項結果")
        award_texts = []
        for k, v in awards.items():
            if k=="N近洞獎":
                counts = Counter(v)
                formatted = " ".join([f"{name}*{cnt}" for name, cnt in counts.items()])
                award_texts.append(f"**{k}** {formatted if formatted else '無'}")
            else:
                award_texts.append(f"**{k}** {', '.join(v) if v else '無'}")
        st.markdown(" ｜ ".join(award_texts))

# === 匯出報表 ===
elif page == "匯出報表":
    st.header("💾 匯出比賽結果")
    if st.session_state.winners:
        winners = st.session_state.winners
        awards = st.session_state.awards

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

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df_leader.to_excel(writer, sheet_name="Leaderboard", index=False)
            awards_df = pd.DataFrame([{"獎項": k, "得獎名單": ", ".join(v) if v else "無"} for k,v in awards.items()])
            awards_df.to_excel(writer, sheet_name="Awards", index=False)
            if st.session_state.match_summary is not None:
                st.session_state.match_summary.to_excel(writer, sheet_name="Match_Summary", index=False)
            if st.session_state.match_df is not None:
                st.session_state.match_df.to_excel(writer, sheet_name="Match_Detail", index=False)
        st.download_button("📥 下載 Excel", data=excel_buffer.getvalue(),
                           file_name="leaderboard.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")