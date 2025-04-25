
import streamlit as st
import pandas as pd

# 載入資料
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players_db.csv")

st.set_page_config(page_title="高爾夫對賭 - 1 vs 3 完整版", layout="wide")
st.title("⛳ 高爾夫對賭 - 1 vs 3 完整版")

# 選擇球場
course_list = course_df["course_name"].unique().tolist()
selected_course = st.selectbox("選擇球場", course_list)

# 選擇區域
area_list = course_df[course_df["course_name"] == selected_course]["area"].unique().tolist()
col1, col2 = st.columns(2)
with col1:
    selected_front_area = st.selectbox("前九洞區域", area_list)
with col2:
    selected_back_area = st.selectbox("後九洞區域", area_list)

# 取得球道資訊
front = course_df[(course_df["course_name"] == selected_course) & (course_df["area"] == selected_front_area)]
back = course_df[(course_df["course_name"] == selected_course) & (course_df["area"] == selected_back_area)]
holes = pd.concat([front, back]).reset_index(drop=True)
hcp = holes["hcp"].tolist()
par = holes["par"].tolist()

# 球員設定
st.markdown("### 🎯 球員設定")
player_list = players_df["name"].tolist()
player_a = st.selectbox("選擇球員 A", player_list)

opponents = []
handicaps = []
bets = []

for i in range(3):
    st.markdown(f"#### 對手球員 B{i+1}")
    cols = st.columns([4, 1, 2])
    with cols[0]:
        opponent = st.selectbox(f"球員 B{i+1} 名稱", player_list, key=f"opponent_{i}")
    with cols[1]:
        hcp_val = st.number_input("差點：", 0, 30, 8, key=f"hcp_{i}")
    with cols[2]:
        bet_val = st.number_input("每洞賭金：", 10, 1000, 100, key=f"bet_{i}")
    opponents.append(opponent)
    handicaps.append(hcp_val)
    bets.append(bet_val)

# 建立成績輸入
st.markdown("### 📝 輸入每洞桿數")
score_data = {player_a: [], opponents[0]: [], opponents[1]: [], opponents[2]: []}
result_data = []

for i in range(18):
    st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    cols = st.columns(4)
    pa = cols[0].number_input(f"{player_a} 桿數", 1, 15, par[i], key=f"{player_a}_{i}")
    b1 = cols[1].number_input(f"{opponents[0]} 桿數", 1, 15, par[i], key=f"{opponents[0]}_{i}")
    b2 = cols[2].number_input(f"{opponents[1]} 桿數", 1, 15, par[i], key=f"{opponents[1]}_{i}")
    b3 = cols[3].number_input(f"{opponents[2]} 桿數", 1, 15, par[i], key=f"{opponents[2]}_{i}")
    score_data[player_a].append(pa)
    score_data[opponents[0]].append(b1)
    score_data[opponents[1]].append(b2)
    score_data[opponents[2]].append(b3)

# 計算勝負與賭金結果
st.markdown("### 📊 賽果統計")
wins = {player_a: 0}
losses = {player_a: 0}
total_earning = {player_a: 0}

for idx, opp in enumerate(opponents):
    wins[opp] = 0
    losses[opp] = 0
    total_earning[opp] = 0
    for i in range(18):
        h_diff = handicaps[idx]
        if hcp[i] <= h_diff:
            adj_opp = score_data[opp][i] - 1
        else:
            adj_opp = score_data[opp][i]
        adj_a = score_data[player_a][i]
        if adj_a < adj_opp:
            wins[player_a] += 1
            losses[opp] += 1
            total_earning[player_a] += bets[idx]
            total_earning[opp] -= bets[idx]
        elif adj_a > adj_opp:
            wins[opp] += 1
            losses[player_a] += 1
            total_earning[player_a] -= bets[idx]
            total_earning[opp] += bets[idx]

summary = pd.DataFrame({
    "勝場": [wins[player_a]] + [wins[o] for o in opponents],
    "敗場": [losses[player_a]] + [losses[o] for o in opponents],
    "賭金結果": [total_earning[player_a]] + [total_earning[o] for o in opponents]
}, index=[player_a] + opponents)

st.dataframe(summary)
