import os
import streamlit as st
from code.analysis.xg_racer import main as xg_racer_main
from code.utils.helpers import load_filtered_json_files, get_user_selection
from config import LEAGUE_COUNTRY_LOOKUP

def render_spinner(content_function, *args, **kwargs):
    with st.spinner("İçerik hazırlanıyor..."):
        content_function(*args, **kwargs)

def display_xg_analysis(team_list, change_situations, change_body_parts):
    league, season, league_display, season_display, _, _, _ = get_user_selection(
        team_list,
        change_situations,
        change_body_parts,
        include_situation_type=False,
        include_team=False,
        include_body_part=False,
        key_prefix="xg_section"
    )

    analysis_type = st.sidebar.selectbox(
        "xG Analiz Tipleri",
        ["xG Merdiveni"],
        index=None,
        label_visibility="hidden",
        placeholder="xG Analiz Tipleri",
        key="xg_analysis_type"
    )

    if not analysis_type:
        st.warning("Lütfen bir analiz tipi seçin.")
        return

    if analysis_type == "xG Merdiveni":
        directories = os.path.join(os.path.dirname(__file__), "../data/sofascore/raw/")
        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")
        match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        match_data_df = match_data_df[match_data_df["status"] == "Ended"]
        match_data_df = match_data_df[["week", "home_team", "away_team"]]

        rounds = match_data_df["week"].unique()
        selected_round = st.sidebar.selectbox(
            "Haftalar",
            sorted(rounds),
            index=None,
            label_visibility="hidden",
            placeholder="Haftalar",
            key="xg_ladder_round"
        )

        if not selected_round:
            st.warning("Lütfen bir hafta seçin.")
            return

        filtered_games = match_data_df[match_data_df["week"] == selected_round]
        team_pairs = filtered_games.apply(lambda row: f"{row['home_team']} - {row['away_team']}", axis=1)

        selected_match = st.sidebar.selectbox(
            "Maçlar",
            list(team_pairs),
            index=None,
            label_visibility="hidden",
            placeholder="Maçlar",
            key="xg_ladder_match"
        )

        if not selected_match:
            st.warning("Lütfen bir maç seçin.")
            return

        home_team, away_team = selected_match.split(" - ")
        xg_racer_main(
            league,
            season,
            league_display,
            season_display,
            selected_round,
            home_team,
            away_team
        )

def display_match_comparison(team_list, change_situations, change_body_parts, league, season):
    section = st.sidebar.selectbox(
        label="Kategori:",
        options=["xG (Beklenen Gol)"],
        index=None,
        label_visibility="hidden",
        placeholder="Kategoriler"
    )

    if not section:
        st.warning("Lütfen bir kategori seçin.")
        return

    if section == "xG (Beklenen Gol)":
        render_spinner(display_xg_analysis, team_list, change_situations, change_body_parts)