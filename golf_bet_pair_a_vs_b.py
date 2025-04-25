import streamlit as st
import pandas as pd

st.set_page_config(page_title="高爾夫對賭 - 1 vs 4 完整版", layout="wide")
st.title("⛳ 高爾夫對賭 - 1 vs 4 完整版")

# 載入球場與球員資料庫
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players_db.csv")

# 選擇球場與區域
course_name = st.selectbox("選擇球場", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("前九洞區域", zones)
zone_back = st.selectbox("後九洞區域", zones)

# 前後九洞資料
holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

st.markdown("### 🎯 球員設定")
player_list = ["請選擇球員"] + players_df["name"].tolist()

# 主球員選擇
player_a = st.selectbox("選擇主球員 A", player_list)
if player_a == "請選擇球員":
    st.warning("⚠️ 請選擇主球員 A 才能繼續操作。")
    st.stop()

# 主球員差點設定
handicaps = {player_a: st.number_input(f"{player_a} 差點", 0, 54, 0, key="hcp_main")}
opponents = []
bets = {}

# 選擇對手 B1~B4
for i in range(1, 5):
    st.markdown(f"#### 對手球員 B{i}")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f"球員 B{i} 名稱", player_list, key=f"b{i}_name")
    if name == "請選擇球員":
        st.warning(f"⚠️ 請選擇對手球員 B{i}。")
        st.stop()
    if name in [player_a] + opponents:
        st.warning(f"⚠️ {name} 已被選擇，請勿重複。")
        st.stop()
    opponents.append(name)
    with cols[1]:
        handicaps[name] = st.number_input("差點：", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

# 初始化資料結構
score_data = {player: [] for player in [player_a] + opponents}
total_earnings = {player: 0 for player in [player_a] + opponents}

st.markdown("### 📝 輸入每洞成績與賭金")

for i in range(18):
    st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    cols = st.columns(5)

    # 主球員輸入
    score_main = cols[0].number_input(f"{player_a} 桿數", 1, 15, par[i], key=f"{player_a}_score_{i}")
    score_data[player_a].append(score_main)

    for idx, op in enumerate(opponents):
        key = f"{op}_score_{i}_{idx}"
        score_op = cols[idx + 1].number_input("", 1, 15, par[i], key=key, label_visibility="collapsed")
        score_data[op].append(score_op)

        # 差點讓桿邏輯（差點高者被讓桿）
        adj_score_main = score_main
        adj_score_op = score_op

        if handicaps[op] > handicaps[player_a] and hcp[i] <= (handicaps[op] - handicaps[player_a]):
            adj_score_op -= 1
        elif handicaps[player_a] > handicaps[op] and hcp[i] <= (handicaps[player_a] - handicaps[op]):
            adj_score_main -= 1

        # 勝負邏輯 + Birdie 加倍
        if adj_score_op < adj_score_main:
            emoji = "👑"
            win_bonus = 2 if score_op < par[i] else 1
            total_earnings[op] += bets[op] * win_bonus
            total_earnings[player_a] -= bets[op] * win_bonus
        elif adj_score_op > adj_score_main:
            emoji = "👽"
            win_bonus = 2 if score_main < par[i] else 1
            total_earnings[op] -= bets[op] * win_bonus
            total_earnings[player_a] += bets[op] * win_bonus
        else:
            emoji = "⚖️"

        # Birdie 小鳥圖示
        birdie_icon = " 🐦" if score_op < par[i] else ""

        with cols[idx + 1]:
            st.markdown(
                f"<div style='text-align:center; margin-bottom:-10px'><strong>{op} 桿數 {emoji}{birdie_icon}</strong></div>",
                unsafe_allow_html=True
            )

# 統整總結結果（賭金＋勝負平）
summary_data = []
for player in [player_a] + opponents:
    summary_data.append({
        "球員": player,
        "總賭金結算": total_earnings[player],
        "勝": result_tracker[player]["win"],
        "負": result_tracker[player]["lose"],
        "平": result_tracker[player]["tie"]
    })

st.markdown("### 📊 總結結果（含勝負平統計）")
summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df.set_index("球員"))
