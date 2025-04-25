import streamlit as st
import pandas as pd

st.set_page_config(page_title="高爾夫對賭 - 1 vs 3 完整版", layout="wide")
st.title("⛳ 高爾夫對賭 - 1 vs 3 完整版")

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
# 主球員 A
player_list = players_df["name"].tolist()
player_a = st.selectbox("選擇主球員 A", player_list)

# 差點設定
handicaps = {}
handicaps[player_a] = st.number_input(f"{player_a} 差點", 0, 54, 0, key="hcp_main")

# 對手球員 B1~B3 與差點與賭金設定
opponents = []
bets = {}
for i in range(1, 4):
    st.markdown(f"#### 對手球員 B{i}")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f"球員 B{i} 名稱", player_list, key=f"b{i}_name")
        opponents.append(name)
    with cols[1]:
        handicaps[name] = st.number_input(f"差點：", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

# 每洞成績輸入
score_data = {player_a: [], opponents[0]: [], opponents[1]: [], opponents[2]: []}
total_earnings = {player_a: 0}
for op in opponents:
    total_earnings[op] = 0

st.markdown("### 📝 輸入每洞成績與賭金")
for i in range(18):
    st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    cols = st.columns(4)
    hole_idx = i

    # 主球員 A 輸入
    score_main = cols[0].number_input(f"{player_a} 桿數", 1, 15, par[i], key=f"{player_a}_score_{i}")
    score_data[player_a].append(score_main)

    for idx, op in enumerate(opponents):
        key = f"{op}_score_{i}_{idx}"  # 確保 key 唯一
        score_op = cols[idx + 1].number_input(f"{op} 桿數", 1, 15, par[i], key=key)
        score_data[op].append(score_op)

        # 差點讓桿邏輯（由差點低的對差點高的讓桿）
        adj_score_main = score_main
        adj_score_op = score_op
        diff = handicaps[player_a] - handicaps[op]
        if diff > 0 and hcp[i] <= diff:
            adj_score_op -= 1
        elif diff < 0 and hcp[i] <= -diff:
            adj_score_main -= 1

        # 勝負與圖示
        if adj_score_op < adj_score_main:
            result = "👑"
            total_earnings[op] += bets[op]
            total_earnings[player_a] -= bets[op]
        elif adj_score_op > adj_score_main:
            result = "👽"
            total_earnings[op] -= bets[op]
            total_earnings[player_a] += bets[op]
        else:
            result = "⚖️"

# 顯示總結果
st.markdown("### 📊 總結結果")
result_df = pd.DataFrame({
    "球員": [player_a] + opponents,
    "總賭金結算": [total_earnings[player_a]] + [total_earnings[op] for op in opponents]
})
st.dataframe(result_df.set_index("球員"))
