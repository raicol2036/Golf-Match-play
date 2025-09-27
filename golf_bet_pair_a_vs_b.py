import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
from io import BytesIO

st.set_page_config(page_title="高爾夫比分1對多", layout="wide")
st.title("⛳ 高爾夫對賭")

# 自定義數字輸入欄位
def numeric_input_html(label, key):
    value = st.session_state.get(key, "")
    html(f"""
        <label for="{key}" style="font-weight:bold">{label}</label><br>
        <input id="{key}" name="{key}" inputmode="numeric" pattern="[0-9]*" maxlength="18"
               style="width:100%; font-size:1.1em; padding:0.5em;" value="{value}" />
        <script>
        const input = window.parent.document.getElementById('{key}');
        input.addEventListener('input', () => {{
            const value = input.value;
            window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: '{key}', value}}, '*');
        }});
        </script>
    """, height=100)

# ---------- 讀取資料 ----------
try:
    course_df = pd.read_csv("course_db.csv")
    st.success("✅ 成功載入 course_db.csv")
except Exception as e:
    st.error(f"❌ 無法讀取 course_db.csv：{e}")
    st.stop()

try:
    players_df = pd.read_csv("players_db.csv")
    if "name" not in players_df.columns:
        st.error("❌ players_db.csv 缺少必要欄位 'name'")
        st.stop()
    st.success("✅ 成功載入 players_db.csv")
except Exception as e:
    st.error(f"❌ 無法讀取 players_db.csv：{e}")
    st.stop()

# ---------- 球場選擇 ----------
course_name = st.selectbox("選擇球場", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("前九洞區域", zones)
zone_back = st.selectbox("後九洞區域", zones)

holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

# ---------- 球員設定 ----------
st.markdown("### 🎯 球員設定")
player_list = ["請選擇球員"] + players_df["name"].tolist()
player_list_with_done = player_list + ["✅ Done"]

player_a = st.selectbox("選擇主球員 A", player_list)
if player_a == "請選擇球員":
    st.warning("⚠️ 請選擇主球員 A")
    st.stop()

numeric_input_html("主球員快速成績輸入（18位數）", key=f"quick_{player_a}")
handicaps = {player_a: st.number_input(f"{player_a} 差點", 0, 54, 0, key="hcp_main")}

opponents, bets = [], {}
for i in range(1, 5):
    st.markdown(f"#### 對手球員 B{i}")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f"球員 B{i} 名稱", player_list_with_done, key=f"b{i}_name")
    if name == "請選擇球員":
        st.warning(f"⚠️ 請選擇球員 B{i}")
        st.stop()
    if name == "✅ Done":
        break
    if name in [player_a] + opponents:
        st.warning(f"⚠️ {name} 已被選擇")
        st.stop()
    opponents.append(name)
    numeric_input_html(f"{name} 快速成績輸入（18位數）", key=f"quick_{name}")
    with cols[1]:
        handicaps[name] = st.number_input("差點", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

all_players = [player_a] + opponents
score_data = {p: [] for p in all_players}
total_earnings = {p: 0 for p in all_players}
result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in all_players}

# ---------- 快速輸入處理（修正版） ----------
for p in all_players:
    value = st.session_state.get(f"quick_{p}", "")
    if value and len(value) == 18 and value.isdigit():
        scores = [int(c) for c in value]
        for i, s in enumerate(scores):
            key = f"{p}_score_{i}"
            st.session_state[key] = s  # 🔑 回填到 session_state
    elif value:
        st.error(f"⚠️ {p} 快速成績需為18位數字串")

# ---------- 成績輸入與比較 ----------
st.markdown("### 📝 輸入每洞成績與賭金")

for i in range(18):
    st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    cols = st.columns(1 + len(opponents))

    # 主球員
    score_main = cols[0].number_input("", 1, 15, key=f"{player_a}_score_{i}", label_visibility="collapsed")
    score_data[player_a].append(score_main)

    # 對手逐一比較
    for idx, op in enumerate(opponents):
        score_op = cols[idx + 1].number_input("", 1, 15, key=f"{op}_score_{i}", label_visibility="collapsed")
        score_data[op].append(score_op)

        # --- 逐洞一對一讓桿 ---
        adj_main, adj_op = score_main, score_op
        diff = abs(handicaps[player_a] - handicaps[op])
        if diff > 0 and hcp[i] <= diff:
            if handicaps[player_a] < handicaps[op]:  # 主讓對手
                adj_op -= 1
            else:  # 對手讓主
                adj_main -= 1

        # 勝負判斷
        if adj_op < adj_main:
            emoji = "👑"
            bonus = 2 if score_op < par[i] else 1
            total_earnings[op] += bets[op] * bonus
            total_earnings[player_a] -= bets[op] * bonus
            result_tracker[op]["win"] += 1
            result_tracker[player_a]["lose"] += 1
        elif adj_op > adj_main:
            emoji = "👽"
            bonus = 2 if score_main < par[i] else 1
            total_earnings[player_a] += bets[op] * bonus
            total_earnings[op] -= bets[op] * bonus
            result_tracker[player_a]["win"] += 1
            result_tracker[op]["lose"] += 1
        else:
            emoji = "⚖️"
            result_tracker[player_a]["tie"] += 1
            result_tracker[op]["tie"] += 1

        # 統一排版顯示
        birdie_main = "🐦" if score_main < par[i] else ""
        birdie_op = "🐦" if score_op < par[i] else ""
        with cols[0]:
            st.markdown(f"<div style='text-align:center'><b>{player_a} {score_main} ({adj_main}){birdie_main}</b></div>", unsafe_allow_html=True)
        with cols[idx + 1]:
            st.markdown(f"<div style='text-align:center'><b>{op} {score_op} ({adj_op}) {emoji}{birdie_op}</b></div>", unsafe_allow_html=True)

# ---------- 總結 ----------
st.markdown("### 📊 總結結果")
summary_data = []
for p in all_players:
    summary_data.append({
        "球員": p,
        "總賭金結算": total_earnings[p],
        "勝": result_tracker[p]["win"],
        "負": result_tracker[p]["lose"],
        "平": result_tracker[p]["tie"]
    })
summary_df = pd.DataFrame(summary_data)

st.dataframe(summary_df.set_index("球員"))

# ---------- 匯出功能 ----------
st.markdown("### 💾 匯出比賽結果")

# 匯出 CSV
csv = summary_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="⬇️ 下載 CSV",
    data=csv,
    file_name="golf_results.csv",
    mime="text/csv"
)

# 匯出 Excel
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    summary_df.to_excel(writer, index=False, sheet_name="比賽結果")
excel_data = output.getvalue()
st.download_button(
    label="⬇️ 下載 Excel",
    data=excel_data,
    file_name="golf_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)