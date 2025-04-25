
import streamlit as st
import pandas as pd

# 載入球場與球員資料庫
course_df = pd.read_csv("course_db.csv")  # 欄位: course_name, area, hole, hcp
player_df = pd.read_csv("players_db.csv")  # 欄位: name

st.set_page_config(page_title="高爾夫對賭 - 1 vs 3 完整版", layout="wide")
st.title("⛳ 高爾夫對賭 - 1 vs 3 完整版")

# 第一步：選擇球場
course_list = course_df["course_name"].unique().tolist()
selected_course = st.selectbox("選擇球場", course_list)

# 第二步：設定前9洞與後9洞球區
course_areas = course_df[course_df["course_name"] == selected_course]["area"].unique().tolist()
col1, col2 = st.columns(2)
with col1:
    front_area = st.selectbox("前九洞區域", course_areas, key="front")
with col2:
    back_area = st.selectbox("後九洞區域", course_areas, key="back")

# 第三步：設定球員
st.subheader("🎯 球員設定")
player_names = player_df["name"].dropna().unique().tolist()

col_a, col_money = st.columns([2, 1])
with col_a:
    player_a = st.selectbox("選擇球員 A", player_names)
with col_money:
    default_bet = st.number_input("每洞賭金", 0, 1000, 100)

opponents = []
for i in range(3):
    st.markdown(f"### 對手球員 B{i+1}")
    col_name, col_hcp = st.columns(2)
    with col_name:
        opponent = st.selectbox(f"球員 B{i+1} 名稱", player_names, key=f"opponent_{i}")
    with col_hcp:
        hcp = st.number_input("差點：", 0, 54, 8, key=f"hcp_{i}")
    opponents.append({"name": opponent, "hcp": hcp})

st.success("✅ 球場與球員資料設定完成")
