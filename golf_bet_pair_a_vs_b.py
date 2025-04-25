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
handicap_a = st.number_input(f"{player_a} 差點", 0, 54, 0)

opponents = []
opponent_handicaps = {}
bets = {}

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
    opponent_handicaps[opponent] = hcp_val
    bets[opponent] = bet_val

# 記錄分數
st.markdown("### 📝 輸入每洞桿數與比分")
scores = {player_a: [], opponents[0]: [], opponents[1]: [], opponents[2]: []}
adjusted_scores = {player_a: []}
win_stats = {p: 0 for p in [player_a] + opponents}

for hole_idx in range(18):
    st.subheader(f"第{hole_idx + 1}洞 (Par {par[hole_idx]}, HCP {hcp[hole_idx]})")
    cols = st.columns(4)

    # 主球員輸入
    with cols[0]:
        score_a = st.number_input(f"{player_a} 桿數", 1, 15, par[hole_idx], key=f"A_score_{hole_idx}")
    scores[player_a].append(score_a)
    adjusted_scores[player_a].append(score_a)

    # 對手逐一比較
    for i, op in enumerate(opponents):
        with cols[i + 1]:
            score_op = st.number_input(f"{op} 桿數", 1, 15, par[hole_idx], key=f"{op}_score_{hole_idx}")

            # 差點讓桿邏輯
            diff = opponent_handicaps[op] - handicap_a
            adjusted_op_score = score_op - 1 if diff > 0 and hcp[hole_idx] <= diff else score_op

            scores[op].append(score_op)

            # 勝負比較與符號
            if adjusted_op_score < score_a:
                result_icon = "👑"
                win_stats[op] += 1
            elif adjusted_op_score > score_a:
                result_icon = "👽"
                win_stats[player_a] += 1
            else:
                result_icon = "⚖️"
            st.markdown(f"**{score_op} {result_icon}**")

# 統計結果
st.markdown("---")
st.markdown("### 📊 結果統計")

summary = pd.DataFrame({
    "勝場": [win_stats[player_a]] + [win_stats[o] for o in opponents],
}, index=[player_a] + opponents)

st.dataframe(summary)
