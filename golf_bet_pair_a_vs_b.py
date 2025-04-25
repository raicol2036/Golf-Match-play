
import streamlit as st
import pandas as pd

st.set_page_config(page_title="高爾夫對賭 - 1 vs 3 完整版", layout="wide")
st.title("⛳ 高爾夫對賭 - 1 vs 3 完整版")

# --- 讀取資料庫 ---
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players_db.csv")

# --- 選擇球場名稱 ---
all_courses = course_df["球場名稱"].unique().tolist()
selected_course = st.selectbox("選擇球場", all_courses)

# 區域下拉選單僅限所選球場
filtered = course_df[course_df["球場名稱"] == selected_course]
available_zones = filtered["區域"].unique().tolist()

col1, col2 = st.columns(2)
with col1:
    front_zone = st.selectbox("前九洞區域", available_zones, key="front_zone")
with col2:
    back_zone = st.selectbox("後九洞區域", available_zones, key="back_zone")

# 擷取前後洞數據
front_holes = course_df[(course_df["球場名稱"] == selected_course) & (course_df["區域"] == front_zone)]
back_holes = course_df[(course_df["球場名稱"] == selected_course) & (course_df["區域"] == back_zone)]
par = front_holes["Par"].tolist() + back_holes["Par"].tolist()
hcp = front_holes["HCP"].tolist() + back_holes["HCP"].tolist()

# --- 球員設定 ---
st.subheader("🎯 球員設定")
col1, col2 = st.columns(2)
with col1:
    player_a = st.selectbox("選擇球員 A", players_df["name"].tolist(), key="sel_a")
    handicap_a = int(players_df[players_df["name"] == player_a]["handicap"].values[0])

opponents = []
handicaps = {}
bets = {}

for idx in range(3):
    st.markdown(f"#### 對手球員 B{idx+1}")
    col1, col2, col3 = st.columns(3)
    with col1:
        player_list = players_df[players_df["name"] != player_a]["name"].tolist()
        name = st.selectbox(f"球員 B{idx+1} 名稱", player_list, key=f"sel_b{idx}")
    with col2:
        hcp_val = int(players_df[players_df["name"] == name]["handicap"].values[0])
        st.markdown(f"差點：**{hcp_val}**")
    with col3:
        bet_val = st.number_input("每洞賭金", 0, 1000, 100, key=f"bet_b{idx+1}")
    opponents.append(name)
    handicaps[name] = hcp_val
    bets[name] = bet_val

# --- 成績輸入 ---
st.subheader("📝 輸入每洞成績")

scores = {player_a: [], **{p: [] for p in opponents}}

for i in range(18):
    st.markdown(f"### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    col_group = st.columns(1 + len(opponents))
    with col_group[0]:
        scores[player_a].append(st.number_input(f"{player_a} 桿數", 1, 15, par[i], key=f"a_{i}"))
    for j, op in enumerate(opponents):
        with col_group[j+1]:
            scores[op].append(st.number_input(f"{op} 桿數", 1, 15, par[i], key=f"{op}_{i}"))

# --- 計算勝負 ---
st.subheader("🏆 結果分析")

results = {op: {"勝洞": 0, "負洞": 0, "平洞": 0, "淨收益": 0} for op in opponents}

for i in range(18):
    for op in opponents:
        hcp_diff = handicaps[op] - handicap_a
        stroke_holes = sorted(range(18), key=lambda x: hcp[x])[:abs(hcp_diff)]
        a_score = scores[player_a][i] - (1 if hcp_diff < 0 and i in stroke_holes else 0)
        b_score = scores[op][i] - (1 if hcp_diff > 0 and i in stroke_holes else 0)

        if a_score < b_score:
            results[op]["勝洞"] += 1
            results[op]["淨收益"] += bets[op]
        elif a_score > b_score:
            results[op]["負洞"] += 1
            results[op]["淨收益"] -= bets[op]
        else:
            results[op]["平洞"] += 1

# --- 顯示結果 ---
st.subheader("📊 賽果總結")

df_result = pd.DataFrame.from_dict(results, orient="index")
df_result["對手"] = df_result.index
df_result = df_result[["對手", "勝洞", "負洞", "平洞", "淨收益"]]
st.dataframe(df_result)
