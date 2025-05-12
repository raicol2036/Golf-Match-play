""import streamlit as st
import pandas as pd

st.set_page_config(page_title='高爾夫Match play-1 vs N', layout='wide')
st.title('⛳ 高爾夫Match play - 1 vs N')

# 載入資料
course_df = pd.read_csv('course_db.csv')
players_df = pd.read_csv('players_db.csv')

# 球場與區域
course_name = st.selectbox('選擇球場', course_df['course_name'].unique())
zones = course_df[course_df['course_name'] == course_name]['area'].unique()
zone_front = st.selectbox('前九洞區域', zones)
zone_back = st.selectbox('後九洞區域', zones)

holes_front = course_df[(course_df['course_name'] == course_name) & (course_df['area'] == zone_front)].sort_values('hole')
holes_back = course_df[(course_df['course_name'] == course_name) & (course_df['area'] == zone_back)].sort_values('hole')
holes = pd.concat([holes_front, holes_back]).reset_index(drop=True)
par = holes['par'].tolist()
hcp = holes['hcp'].tolist()

st.markdown('### 🎯 球員設定')
player_list = ['請選擇球員'] + players_df['name'].tolist()
player_list_with_done = players_df['name'].tolist() + ['✅ Done']

# 主球員
player_a = st.selectbox('選擇主球員 A', player_list)
if player_a == '請選擇球員':
    st.warning('⚠️ 請選擇主球員 A 才能繼續操作。')
    st.stop()

handicaps = {player_a: st.number_input(f'{player_a} 差點', 0, 54, 0, key='hcp_main')}

opponents = []
bets = {}

# 對手最多四人，可 Done 結束
for i in range(1, 5):
    st.markdown(f'#### 對手球員 B{i}')
    cols = st.columns([2, 1, 1])
    with cols[0]:
        name = st.selectbox(f'球員 B{i} 名稱', player_list_with_done, key=f'b{i}_name')
    if name == '請選擇球員':
        st.warning(f'⚠️ 請選擇對手球員 B{i}。')
        st.stop()
    if name == '✅ Done':
        break
    if name in [player_a] + opponents:
        st.warning(f'⚠️ {name} 已被選擇，請勿重複。')
        st.stop()
    opponents.append(name)
    with cols[1]:
        handicaps[name] = st.number_input('差點：', 0, 54, 0, key=f'hcp_b{i}')
    with cols[2]:
        bets[name] = st.number_input('每洞賭金', 10, 1000, 100, key=f'bet_b{i}')

# 初始化
all_players = [player_a] + opponents
score_data = {p: [] for p in all_players}
total_earnings = {p: 0 for p in all_players}
result_tracker = {p: {'win': 0, 'lose': 0, 'tie': 0} for p in all_players}

# 快速成績輸入
st.markdown('### ⏱️ 快速成績輸入')
for p in all_players:
    input_value = st.text_input(f'{p} 成績（18位數）', key=f'quick_input_{p}')
    if len(input_value) == 18 and input_value.isdigit():
        score_data[p] = [int(x) for x in list(input_value)]
    else:
        st.warning(f'{p} 的成績輸入需為18位數字！')

# 讓桿計算
def calculate_handicap_adjustments(player, opponent, hcp_list):
    diff = abs(handicaps[player] - handicaps[opponent])
    adjustments = [0] * 18
    if diff > 0:
        for hcp_index in sorted(hcp_list)[:diff]:
            adjustments[hcp_index - 1] = 1
    return adjustments

handicap_adjustments = {}
for p in all_players:
    handicap_adjustments[p] = calculate_handicap_adjustments(player_a, p, hcp)

st.markdown('### 🏌️ 成績結果')
for hole in range(18):
    cols = st.columns(len(all_players))
    for idx, p in enumerate(all_players):
        adjusted_score = score_data[p][hole] - handicap_adjustments[p][hole]
        cols[idx].write(f'{p}: {adjusted_score}')

# 逐洞勝負判定與賭金結算
st.markdown('### 💰 賭金與勝負結算')
for hole in range(18):
    winner = None
    lowest_score = float('inf')
    for p in all_players:
        adjusted_score = score_data[p][hole] - handicap_adjustments[p][hole]
        if adjusted_score < lowest_score:
            lowest_score = adjusted_score
            winner = p
        elif adjusted_score == lowest_score:
            winner = None
    
    if winner:
        st.write(f'第 {hole + 1} 洞贏家：**{winner}** 🎉')
        total_earnings[winner] += sum(bets.values())
        result_tracker[winner]['win'] += 1
    else:
        st.write(f'第 {hole + 1} 洞：⚖️ 平手')
        for p in all_players:
            result_tracker[p]['tie'] += 1

# 統計總結
st.markdown('### 📊 總結結果')
summary_df = pd.DataFrame([
    {
        '球員': p,
        '總賭金結算': total_earnings[p],
        '勝': result_tracker[p]['win'],
        '負': result_tracker[p]['lose'],
        '平': result_tracker[p]['tie']
    } for p in all_players
])
st.dataframe(summary_df.set_index('球員'))
""
