import os
import streamlit as st
from code.analysis.player_heatmap import main as player_heatmap_main
from code.analysis.player_shot_location import main as player_shot_location_main
from code.utils.helpers import load_filtered_json_files, get_user_selection

def display_player_based(team_list, change_situations, change_body_parts):
    section = st.sidebar.radio(
        "Kategori:",
        options=["Isı Haritası", "Şut Lokasyonu"],
        index=None,
        label_visibility='hidden'
    )

    if section == "Isı Haritası":
        league, season, team, league_display, season_display, _, _ = get_user_selection(
            team_list, change_situations, change_body_parts, include_situation_type=False, include_body_part=False
        )
        if team == "Takım seçin" or not team:
            st.warning("Lütfen bir takım seçin.")
        else:
            with st.spinner("Veriler yükleniyor..."):
                directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/raw/')
                matches_data = load_filtered_json_files(directories, "matches", league, season)
                heatmaps_data = load_filtered_json_files(directories, 'heatmaps', league, season)
                matches_data = matches_data[['game_id', 'tournament', 'season', 'round', 'home_team', 'away_team']]
                players_data = heatmaps_data.merge(
                    matches_data,
                    on=['game_id', 'tournament', 'season', 'round'],
                    how='left'
                )
                players_data['team_name'] = players_data.apply(
                    lambda row: row['home_team'] if row['team'] == 'home' else row['away_team'],
                    axis=1
                )
                players_data = players_data[players_data['team_name'] == team]
                players_data = players_data[['player_name']].drop_duplicates()
                players_list = players_data['player_name'].tolist()
            selected_player = st.sidebar.selectbox("Oyuncu:", ["Oyuncu Seçin"] + sorted(players_list), key="player_heatmap_player_name")
            if team == "Takım seçin" or not team:
                st.warning("Lütfen bir takım seçin.")
            elif selected_player == "Oyuncu Seçin" or not selected_player:
                st.warning("Lütfen bir oyuncu seçin.")
            else:
                with st.spinner("İçerik hazırlanıyor..."):
                    player_heatmap_main(
                        league=league,
                        season=season,
                        team=team,
                        league_display=league_display,
                        season_display=season_display,
                        player=selected_player
                    )
    elif section == "Şut Lokasyonu":
        league, season, team, league_display, season_display, _, _ = get_user_selection(
            team_list, change_situations, change_body_parts, include_situation_type=False, include_body_part=False
        )
        if team == "Takım seçin" or not team:
            st.warning("Lütfen bir takım seçin.")
        else:
            with st.spinner("Veriler yükleniyor..."):
                directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/raw/')
                matches_data = load_filtered_json_files(directories, "matches", league, season)
                shot_maps_data = load_filtered_json_files(directories, 'shot_maps', league, season)
                matches_data = matches_data[["tournament", "season", "round", "game_id", "home_team", "away_team"]]
                shot_maps_data = shot_maps_data[[
                    "tournament", "season", "round", "game_id", "player_name", "is_home", "shot_type",
                    "situation", "goal_mouth_location", "player_coordinates_x", "player_coordinates_y"
                ]]
                shot_maps_data = shot_maps_data.merge(
                    matches_data,
                    on=["tournament", "season", "round", "game_id"],
                    how="left"
                )
                shot_maps_data["team_name"] = shot_maps_data.apply(
                    lambda row: row["home_team"] if row["is_home"] else row["away_team"], axis=1
                )
                players_data = shot_maps_data[shot_maps_data['team_name'] == team]
                players_data = players_data[['player_name']].drop_duplicates()
                players_list = players_data['player_name'].tolist()
            selected_player = st.sidebar.selectbox("Oyuncu:", ["Oyuncu Seçin"] + sorted(players_list), key="player_shotmap_player_name")
            if team == "Takım seçin" or not team:
                st.warning("Lütfen bir takım seçin.")
            elif selected_player == "Oyuncu Seçin" or not selected_player:
                st.warning("Lütfen bir oyuncu seçin.")
            else:
                with st.spinner("İçerik hazırlanıyor..."):
                    player_shot_location_main(
                        league=league,
                        season=season,
                        team=team,
                        league_display=league_display,
                        season_display=season_display,
                        player=selected_player
                    )