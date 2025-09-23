import streamlit as st
import pandas as pd
from streamlit.components.v1 import html

st.set_page_config(page_title="高爾夫比分1對多", layout="wide")
st.title("⛳ 高爾夫Match play - 1 vs N")

# 自定義數字輸入欄位，強制 inputmode = numeric
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

# 載入資料
import pandas as pd
import streamlit as st

st.set_page_config(page_title="球場與球員資料載入", layout="centered")

# ---------- 讀取球場資料 ----------
try:
    course_df = pd.read_csv("course_db.csv")
    st.success("✅ 成功載入 course_db.csv")
    
except FileNotFoundError:
    st.error("❌ 找不到 course_db.csv，請確認檔案與程式在同一資料夾。")
    st.stop()
except Exception as e:
    st.error(f"讀取 course_db.csv 發生錯誤：{e}")
    st.stop()

# ---------- 讀取球員資料 ----------
try:
    players_df = pd.read_csv("players_db.csv")
    if "name" not in players_df.columns:
        st.error("❌ players_db.csv 缺少必要欄位 'name'，請檢查檔案格式。")
        st.stop()
    st.success("✅ 成功載入 players_db.csv")
except FileNotFoundError:
    st.error("❌ 找不到 players_db.csv，請確認檔案與程式在同一資料夾。")
    st.stop()
except Exception as e:
    st.error(f"讀取 players_db.csv 發生錯誤：{e}")
    st.stop()

# ---------- 後續流程入口 ----------
st.caption("✅ 資料載入完成，可進入主球員設定、讓桿、單洞賭金與比分表生成。")


# 球場與區域
course_name = st.selectbox("選擇球場", course_df["course_name"].unique())
zones = course_df[course_df["course_name"] == course_name]["area"].unique()
zone_front = st.selectbox("前九洞區域", zones)
zone_back = st.selectbox("後九洞區域", zones)

holes_front = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_front)].sort_values("hole")
holes_back = course_df[(course_df["course_name"] == course_name) & (course_df["area"] == zone_back)].sort_values("hole")
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes["par"].tolist()
hcp = holes["hcp"].tolist()

st.markdown("### 🎯 球員設定")
player_list = ["請選擇球員"] + players_df["name"].tolist()
player_list_with_done = player_list + ["✅ Done"]

# 主球員
player_a = st.selectbox("選擇主球員 A", player_list)
if player_a == "請選擇球員":
    st.warning("⚠️ 請選擇主球員 A 才能繼續操作。")
    st.stop()

numeric_input_html("主球員快速成績輸入（18位數）", key=f"quick_{player_a}")
handicaps = {player_a: st.number_input(f"{player_a} 差點", 0, 54, 0, key="hcp_main")}

opponents = []
bets = {}

# 對手最多四人，可 Done 結束
for i in range(1, 5):
    st.markdown(f"#### 對手球員 B{i}")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f"球員 B{i} 名稱", player_list_with_done, key=f"b{i}_name")
    if name == "請選擇球員":
        st.warning(f"⚠️ 請選擇對手球員 B{i}。")
        st.stop()
    if name == "✅ Done":
        break
    if name in [player_a] + opponents:
        st.warning(f"⚠️ {name} 已被選擇，請勿重複。")
        st.stop()
    opponents.append(name)
    numeric_input_html(f"{name} 快速成績輸入（18位數）", key=f"quick_{name}")
    with cols[1]:
        handicaps[name] = st.number_input("讓桿(前後各讓)：", -18, 18, 0, key=f"hcp_b{i}")
    with cols[2]:
        bets[name] = st.number_input("每洞賭金", 10, 1000, 100, key=f"bet_b{i}")

# 初始化
all_players = [player_a] + opponents
score_data = {p: [] for p in all_players}
total_earnings = {p: 0 for p in all_players}
result_tracker = {p: {"win": 0, "lose": 0, "tie": 0} for p in all_players}

# 處理快速成績
quick_scores = {}
for p in all_players:
    value = st.session_state.get(f"quick_{p}", "")
    if value and len(value) == 18 and value.isdigit():
        quick_scores[p] = [int(c) for c in value]
        if not all(1 <= s <= 15 for s in quick_scores[p]):
            st.error(f"⚠️ {p} 的每洞桿數需為 1~15。")
            quick_scores[p] = []
    elif value:
        st.error(f"⚠️ {p} 快速成績輸入需為18位數字串。")

st.markdown("### 📝 輸入每洞成績與賭金")

for i in range(18):
    st.markdown(f"#### 第{i+1}洞 (Par {par[i]}, HCP {hcp[i]})")
    cols = st.columns(1 + len(opponents))

    # 主球員輸入（只顯示🐦）
    default_score = quick_scores[player_a][i] if player_a in quick_scores else par[i]
    score_main = cols[0].number_input("", 1, 15, default_score, key=f"{player_a}_score_{i}", label_visibility="collapsed")
    score_data[player_a].append(score_main)
    birdie_main = " 🐦" if score_main < par[i] else ""
    with cols[0]:
        st.markdown(
            f"<div style='text-align:center; margin-bottom:-10px'><strong>{player_a} 桿數{birdie_main}</strong></div>",
            unsafe_allow_html=True
        )

    for idx, op in enumerate(opponents):
        default_score = quick_scores[op][i] if op in quick_scores else par[i]
        score_op = cols[idx + 1].number_input("", 1, 15, default_score, key=f"{op}_score_{i}", label_visibility="collapsed")
        score_data[op].append(score_op)

        # 差點讓桿
        adj_main = score_main
        adj_op = score_op
        if handicaps[op] > handicaps[player_a] and hcp[i] <= (handicaps[op] - handicaps[player_a]):
            adj_op -= 1
        elif handicaps[player_a] > handicaps[op] and hcp[i] <= (handicaps[player_a] - handicaps[op]):
            adj_main -= 1

        # 勝負與賭金處理
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
            total_earnings[op] -= bets[op] * bonus
            total_earnings[player_a] += bets[op] * bonus
            result_tracker[player_a]["win"] += 1
            result_tracker[op]["lose"] += 1
        else:
            emoji = "⚖️"
            result_tracker[player_a]["tie"] += 1
            result_tracker[op]["tie"] += 1

        birdie_icon = " 🐦" if score_op < par[i] else ""
        with cols[idx + 1]:
            st.markdown(
                f"<div style='text-align:center; margin-bottom:-10px'><strong>{op} 桿數 {emoji}{birdie_icon}</strong></div>",
                unsafe_allow_html=True
            )

# 📊 總結
st.markdown("### 📊 總結結果（含勝負平統計）")
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
