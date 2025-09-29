 elif page == "比賽結果與獎項":
    st.header("🏆 比賽結果")

    if st.session_state.scores:
        winners = get_winners(st.session_state.scores, st.session_state.course_selected)
        st.session_state.winners = winners

        col1, col2 = st.columns(2)
        col1.write(f"🏅 總桿冠軍: {winners['gross_champion']}")
        col2.write(f"🥈 總桿亞軍: {winners['gross_runnerup']}")

        col3, col4 = st.columns(2)
        col3.write(f"🏅 淨桿冠軍: {winners['net_champion']}")
        col4.write(f"🥈 淨桿亞軍: {winners['net_runnerup']}")

        if winners["birdies"]:
            st.write("✨ Birdie 紀錄：")
            birdie_dict = {}
            for player, hole in winners["birdies"]:
                birdie_dict.setdefault(player, []).append(hole)
            for player, holes in birdie_dict.items():
                holes_sorted = sorted(holes)
                st.write(f"- {player} 第{'/'.join([str(h)+'洞' for h in holes_sorted])}")
        else:
            st.write("無 Birdie 紀錄")

        # ------------------ Match Play 對賭計算 ------------------
        st.subheader("⚔️ Match Play 賭金結算 (單位 50)")

        bet_unit = 50
        scores = st.session_state.scores
        course_selected = st.session_state.course_selected
        match_results = []
        total_earnings = {p: 0 for p in scores.keys()}

        for i in range(18):
            hole_scores = {p: scores[p][i] for p in scores if scores[p]}
            min_score = min(hole_scores.values())
            winners_hole = [p for p,s in hole_scores.items() if s == min_score]

            if len(winners_hole) == 1:
                winner = winners_hole[0]
                for p in scores.keys():
                    if p == winner:
                        total_earnings[p] += bet_unit
                        match_results.append({"洞": i+1, "勝者": p, "賭金變動": f"+{bet_unit} {p}"})
                    else:
                        total_earnings[p] -= bet_unit
            else:
                match_results.append({"洞": i+1, "勝者": "平手", "賭金變動": "0"})

        # 顯示逐洞表
        match_df = pd.DataFrame(match_results)
        st.dataframe(match_df)

        # 顯示總結
        st.subheader("💰 Match Play 總結")
        summary_df = pd.DataFrame([{"球員": p, "總結算": total_earnings[p]} for p in total_earnings])
        st.dataframe(summary_df.set_index("球員"))

        # ------------------ 獎項選擇 ------------------
        st.subheader("🎯 獎項選擇")
        long_drive = st.multiselect("🏌️‍♂️ 遠距獎", players["name"].values, max_selections=2)
        near1 = st.multiselect("🎯 一近洞獎", players["name"].values, max_selections=2)
        num_n_near = st.number_input("N近洞獎數量", 0, 18, 0)
        n_near_awards = []
        for i in range(num_n_near):
            player = st.selectbox(f"N近洞獎 第{i+1}名", ["無"]+list(players["name"].values), key=f"n_near_{i}")
            if player != "無": n_near_awards.append(player)

        awards = {"遠距獎": long_drive, "一近洞獎": near1, "N近洞獎": n_near_awards}
        st.session_state.awards = awards

        # 顯示獎項結果
        st.subheader("🏅 特殊獎項結果")
        award_texts = []
        for k, v in awards.items():
            if k=="N近洞獎":
                counts = Counter(v)
                formatted = " ".join([f"{name}*{cnt}" for name, cnt in counts.items()])
                award_texts.append(f"**{k}** {formatted if formatted else '無'}")
            else:
                award_texts.append(f"**{k}** {', '.join(v) if v else '無'}")
        st.markdown(" ｜ ".join(award_texts))