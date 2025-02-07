import os
import streamlit as st
from code.analysis import player_heatmap, player_shot_location, player_rating
from code.utils.helpers import load_filtered_json_files, get_user_selection
from config import LEAGUE_COUNTRY_LOOKUP

def render_spinner(content_function, *args, **kwargs):
    with st.spinner("İçerik hazırlanıyor..."):
        content_function(*args, **kwargs)

def load_team_data(team, data_type, directories, league_display, season_display):
    country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")
    match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
    specific_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, data_type)

    match_data_df = match_data_df[["game_id", "tournament", "season", "week", "home_team", "away_team"]]

    if data_type == "coordinates_data":
        merged_data = specific_data_df.merge(
            match_data_df,
            on=["game_id", "tournament", "season", "week"],
            how="left"
        )
        merged_data["team_name"] = merged_data.apply(
            lambda row: row["home_team"] if row["team"] == "home" else row["away_team"],
            axis=1
        )
    elif data_type == "shots_data":
        specific_data_df = specific_data_df[[
            "tournament", "season", "week", "game_id", "player_name", "is_home", "shot_type", "goal_type",
            "situation", "goal_mouth_location", "player_coordinates_x", "player_coordinates_y"
        ]]
        merged_data = specific_data_df.merge(
            match_data_df,
            on=["tournament", "season", "week", "game_id"],
            how="left"
        )
        merged_data["team_name"] = merged_data.apply(
            lambda row: row["home_team"] if row["is_home"] else row["away_team"],
            axis=1
        )
        merged_data = merged_data[merged_data["goal_type"] != "own"]
    elif data_type == "lineups_data":
        merged_data = specific_data_df.merge(
            match_data_df,
            on=["tournament", "season", "week", "game_id"],
            how="left"
        )
        merged_data["team_name"] = merged_data.apply(
            lambda row: row["home_team"] if row["team"] == "home" else row["away_team"],
            axis=1
        )
        merged_data = merged_data[merged_data["stat_name"] == "rating"]

    team_data = merged_data[merged_data["team_name"] == team]
    return team_data[["player_name"]].drop_duplicates()

def handle_player_section(section, team_list, change_situations, change_body_parts):
    league, season, league_display, season_display, team, _, _ = get_user_selection(
        team_list,
        change_situations,
        change_body_parts,
        include_situation_type=False,
        include_body_part=False
    )

    if not team:
        st.warning("Lütfen bir takım seçin.")
        return

    directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/raw/')
    data_type = (
        "coordinates_data" if section == "Isı Haritası" else
        "shots_data" if section == "Şut Lokasyonu" else
        "lineups_data" if section == "Reyting" else None
    )
    team_data = load_team_data(team, data_type, directories, league_display, season_display)
    players_list = team_data["player_name"].tolist()

    selected_player = st.sidebar.selectbox(
        "Oyuncular",
        sorted(players_list),
        index=None,
        label_visibility="hidden",
        placeholder="Oyuncular",
        key=f"{section.lower().replace(' ', '_')}_player_name"
    )

    if not selected_player:
        st.warning("Lütfen bir oyuncu seçin.")
    else:
        if section == "Isı Haritası":
            render_spinner(player_heatmap.main, league, season, league_display, season_display, team, selected_player)
        elif section == "Şut Lokasyonu":
            render_spinner(player_shot_location.main, league, season, league_display, season_display, team, selected_player)
        elif section == "Reyting":
            render_spinner(player_rating.main, league, season, league_display, season_display, team, selected_player)

def display_player_based(team_list, change_situations, change_body_parts, league, season):
    section = st.sidebar.selectbox(
        "Kategori:",
        options=["Isı Haritası", "Şut Lokasyonu", "Reyting"],
        index=None,
        label_visibility="hidden",
        placeholder="Kategoriler"
    )

    if not section:
        st.warning("Lütfen bir kategori seçin.")
        return

    handle_player_section(section, team_list, change_situations, change_body_parts)