
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

# 根據選擇的球場篩選區域
area_list = course_df[course_df["course_name"] == selected_course]["area"].unique().tolist()
col1, col2 = st.columns(2)
with col1:
    selected_front_area = st.selectbox("前九洞區域", area_list)
with col2:
    selected_back_area = st.selectbox("後九洞區域", area_list)

# 讀取 1~18 洞的 Par 與 HCP（準備計算時使用）
front_par_hcp = course_df[(course_df["course_name"] == selected_course) & (course_df["area"] == selected_front_area)]
back_par_hcp = course_df[(course_df["course_name"] == selected_course) & (course_df["area"] == selected_back_area)]
combined_course = pd.concat([front_par_hcp, back_par_hcp]).reset_index(drop=True)
par = [4] * 18
hcp = combined_course["hcp"].tolist()

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
        bet_val = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_{i}")
    opponents.append(opponent)
    handicaps.append(hcp_val)
    bets.append(bet_val)

# 顯示確認用資料
st.markdown("---")
st.markdown("### ✅ 設定確認")
st.write("球員 A:", player_a)
for i in range(3):
    st.write(f"對手 B{i+1}: {opponents[i]}（差點 {handicaps[i]}，每洞賭金 {bets[i]}）")
