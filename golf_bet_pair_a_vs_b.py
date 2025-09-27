import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
from io import BytesIO

st.set_page_config(page_title="高爾夫比分1對多", layout="wide")
st.title("⛳ 高爾夫對賭（快速輸入版＋逐洞明細）")

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
course_df = pd.read_csv("course_db.csv")
players_df = pd.read_csv("players_db.csv")

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
        st.stop()
    if name == "✅ Done":
        break
    if name in [player_a] + opponents:
        st.stop()
    opponents.append(name)
    numeric_input_html(f"{name} 快速成績輸入（18位數）", key=f"quick_{name}")
    with cols[1]:
        handicaps[name] = st.number_input("差點", 0, 54, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

all_players = [player_a] + opponents

# ---------- 快速輸入轉換 ----------
scores = {}
for p in all_players:
    value = st.session_state.get(f"quick_{p}", "")
    if value and len(value) == 18 and value.isdigit():
        scores[p] = [int(c) for c in value]
    else:
        st.warning(f"⚠️ {p} 請輸入18位數字串")
        st.stop()

# ---------- 計算勝負 ----------
total_earnings = {p: 0 for p in all_players}
result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in all_players}
detail_rows = []

for i in range(18):
    score_main = scores[player_a][i]
    for op in opponents:
        score_op = scores[op][i]

        adj_main, adj_op = score_main, score_op
        diff = abs(handicaps[player_a] - handicaps[op])
        if diff > 0 and hcp[i] <= diff:
            if handicaps[player_a] < handicaps[op]:
                adj_op -= 1
            else:
                adj_main -= 1

        # 勝負判斷
        if adj_op < adj_main:
            emoji = "👑"
            bonus = 2 if score_op < par[i] else 1
            earn_main, earn_op = -bets[op] * bonus, bets[op] * bonus
            total_earnings[op] += earn_op
            total_earnings[player_a] += earn_main
            result_tracker[op]["win"] += 1
            result_tracker[player_a]["lose"] += 1
        elif adj_op > adj_main:
            emoji = "👽"
            bonus = 2 if score_main < par[i] else 1
            earn_main, earn_op = bets[op] * bonus, -bets[op] * bonus
            total_earnings[player_a] += earn_main
            total_earnings[op] += earn_op
            result_tracker[player_a]["win"] += 1
            result_tracker[op]["lose"] += 1
        else:
            emoji = "⚖️"
            earn_main, earn_op = 0, 0
            result_tracker[player_a]["tie"] += 1
            result_tracker[op]["tie"] += 1

        # 記錄逐洞明細
        detail_rows.append({
            "洞": i + 1,
            "Par": par[i],
            "HCP": hcp[i],
            "球員": player_a,
            "原始桿數": score_main,
            "調整後": adj_main,
            "對手": op,
            "對手原始桿數": score_op,
            "對手調整後": adj_op,
            "結果": emoji,
            "主球員變動": earn_main,
            "對手變動": earn_op
        })

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

# ---------- 逐洞明細 ----------
st.markdown("### 📒 逐洞明細表")
detail_df = pd.DataFrame(detail_rows)
st.dataframe(detail_df)

# ---------- 匯出功能 ----------
st.markdown("### 💾 匯出比賽結果")
# 匯出 CSV
csv = detail_df.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ 下載逐洞明細 (CSV)", csv, "golf_details.csv", "text/csv")

# 匯出 Excel
output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    summary_df.to_excel(writer, index=False, sheet_name="總結結果")
    detail_df.to_excel(writer, index=False, sheet_name="逐洞明細")
excel_data = output.getvalue()
st.download_button(
    "⬇️ 下載完整報表 (Excel)",
    excel_data,
    "golf_results.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)