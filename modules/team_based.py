import streamlit as st
from code.analysis.goal_path import main as goal_path_main
from code.analysis.shot_location import main as shot_location_main
from code.utils.helpers import get_user_selection

def display_team_based(team_list, change_situations, change_body_parts):
    section = st.sidebar.radio(
        "Kategori:",
        options=["Gol Ağı", "Şut Lokasyonu"],
        index=None,
        label_visibility='hidden'
    )

    if section == "Gol Ağı":
        with st.spinner("İçerik hazırlanıyor..."):
            league, season, team, league_display, season_display, _, _ = get_user_selection(
                team_list, change_situations, change_body_parts, include_situation_type=False, include_body_part=False
            )
            goal_path_main(
                league=league,
                season=season,
                team=team,
                league_display=league_display,
                season_display=season_display
            )
    elif section == "Şut Lokasyonu":
        with st.spinner("İçerik hazırlanıyor..."):
            league, season, team, league_display, season_display, situation_type, _ = get_user_selection(
                team_list, change_situations, change_body_parts, include_body_part=False
            )
            shot_location_main(
                league=league,
                season=season,
                team=team,
                league_display=league_display,
                season_display=season_display,
                situation_type=situation_type
            )