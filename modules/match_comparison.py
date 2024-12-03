import os
import streamlit as st
from code.analysis.xg_ladder import main as xg_ladder_main
from code.utils.helpers import load_filtered_json_files, get_user_selection
# from config import match_performances

def display_match_comparison(team_list, change_situations, change_body_parts):
    section = st.sidebar.radio(
        "Kategori:",
        options=["xG (Beklenen Gol)", "Maç Performansı"],
        index=None,
        label_visibility='hidden'
    )

    if section == "xG (Beklenen Gol)":
        league, season, _, league_display, season_display, _, _ = get_user_selection(
            team_list, change_situations, change_body_parts, include_situation_type=False, include_team=False, include_body_part=False, key_prefix="xg_section"
        )
        analysis_type = st.sidebar.selectbox(
            "xG Analiz Tipi:",
            [
                "Seçin",
                "xG Merdiveni"
            ],
            key="xg_analysis_type"
        )

        with st.spinner("İçerik hazırlanıyor..."):
            if analysis_type == "Seçin":
                st.warning("Lütfen bir analiz tipi seçin.")

            elif analysis_type == "xG Merdiveni":
                directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/raw/')
                matches_data = load_filtered_json_files(directories, 'matches', league, season)
                matches_data = matches_data[['round', 'home_team', 'away_team']]
                rounds = matches_data['round'].unique()
                selected_round = st.sidebar.selectbox("Hafta:", ["Seçin"] + sorted(rounds), key="xg_ladder_round")
                if selected_round and selected_round != "Seçin":
                    filtered_matches = matches_data[matches_data['round'] == selected_round]
                    team_pairs = filtered_matches.apply(lambda row: f"{row['home_team']} - {row['away_team']}", axis=1)
                    selected_match = st.sidebar.selectbox("Maç:", ["Seçin"] + list(team_pairs), key="xg_ladder_match")
                    if selected_match and selected_match != "Seçin":
                        home_team, away_team = selected_match.split(" - ")
                        xg_ladder_main(league, season, league_display, season_display, selected_round, home_team, away_team)

    elif section == "Maç Performansı":
        pass