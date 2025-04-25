
import streamlit as st
import pandas as pd

st.set_page_config(page_title="高爾夫配對賭局 A vs B", layout="wide")
st.title("⛳ 高爾夫對賭 - A vs B")

# 球場設定
course_db = {
    "台中國際(東區)": {"par": [4, 4, 3, 5, 4, 4, 3, 5, 4], "hcp": [2, 8, 5, 4, 7, 1, 9, 3, 6]},
    "台中國際(西區)": {"par": [5, 4, 3, 4, 4, 3, 4, 5, 4], "hcp": [3, 6, 9, 8, 1, 4, 7, 2, 5]},
}

course = st.selectbox("選擇球場", list(course_db.keys()))
par = course_db[course]["par"]
hcp = course_db[course]["hcp"]

# 基本設定
col1, col2 = st.columns(2)
with col1:
    player_a = st.text_input("球員 A 名稱", value="Alice")
    handicap_a = st.number_input("球員 A 差點", 0, 36, 0)
with col2:
    player_b = st.text_input("球員 B 名稱", value="Bob")
    handicap_b = st.number_input("球員 B 差點", 0, 36, 0)

# 差點差值 → 讓桿洞
diff = handicap_b - handicap_a
hcp_sorted = sorted(range(9), key=lambda i: hcp[i])
a_gets_strokes = []
if diff > 0:
    a_gets_strokes = hcp_sorted[:diff]

# 賭金輸入
st.subheader("輸入每洞成績與賭金")
score_data = []
for i in range(9):
    st.markdown(f"### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    col1, col2, col3 = st.columns(3)
    with col1:
        a_score = st.number_input(f"{player_a} 桿數", 1, 15, par[i], key=f"a_{i}")
    with col2:
        b_score = st.number_input(f"{player_b} 桿數", 1, 15, par[i], key=f"b_{i}")
    with col3:
        bet = st.number_input("本洞賭金", 0, 1000, 100, key=f"bet_{i}")

    # 讓桿邏輯
    a_adj = a_score
    b_adj = b_score
    if i in a_gets_strokes:
        a_adj -= 1

    if a_adj < b_adj:
        winner = player_a
        gain = bet
    elif a_adj > b_adj:
        winner = player_b
        gain = -bet
    else:
        winner = "平手"
        gain = 0

    score_data.append({
        "洞數": f"{i+1}",
        player_a: a_score,
        player_b: b_score,
        "讓桿洞": "是" if i in a_gets_strokes else "否",
        "勝者": winner,
        "賭金差": gain
    })

# 結果表格與統計
df = pd.DataFrame(score_data)
st.dataframe(df)

a_wins = df["勝者"].tolist().count(player_a)
b_wins = df["勝者"].tolist().count(player_b)
total_gain = df["賭金差"].sum()

st.subheader("🎯 總結結果")
st.markdown(f"""
- {player_a} 勝：{a_wins} 洞
- {player_b} 勝：{b_wins} 洞
- 淨勝：{a_wins - b_wins} 洞
- 賭金結果：{total_gain:+} 元（{player_a if total_gain > 0 else player_b if total_gain < 0 else '平手'} 獲勝）
""")
