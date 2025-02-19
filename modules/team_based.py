import streamlit as st
from code.analysis import (
    goal_path,
    shot_location
)
from code.utils.helpers import get_user_selection

def render_spinner(content_function, *args, **kwargs):
    with st.spinner("İçerik hazırlanıyor..."):
        content_function(*args, **kwargs)

def handle_goal_path(team_list, change_situations, change_body_parts):
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

    side = st.sidebar.radio(
        label="Attığı-Yediği:",
        options=["Attığı","Yediği"],
        index=None,
        label_visibility="hidden"
    )

    if side is None:
        st.warning("Lütfen bir taraf seçin.")
        return

    plot_type = st.sidebar.radio(
        label="Harita Tipi:",
        options=["Birleştir","Ayrıştır"],
        index=None,
        label_visibility="hidden"
    )

    if plot_type is None:
        st.warning("Lütfen bir harita tipi seçin.")
        return

    render_spinner(
        goal_path.main,
        league,
        season,
        league_display,
        season_display,
        team,
        plot_type,
        side
    )

def handle_shot_location(team_list, change_situations, change_body_parts):
    league, season, league_display, season_display, team, situation_type, _ = get_user_selection(
        team_list,
        change_situations,
        change_body_parts,
        include_body_part=False
    )
    if not team:
        st.warning("Lütfen bir takım seçin.")
        return
    if not situation_type:
        st.warning("Lütfen bir senaryo tipi seçin.")
        return
    else:
        render_spinner(
            shot_location.main,
            league,
            season,
            league_display,
            season_display,
            team,
            situation_type
        )

def display_team_based(team_list, change_situations, change_body_parts, league, season):
    section = st.sidebar.selectbox(
        "Kategori:",
        options=["Gol Ağı", "Şut Lokasyonu"],
        index=None,
        label_visibility="hidden",
        placeholder="Kategoriler"
    )

    if section is None:
        st.warning("Lütfen bir kategori seçin.")
        return

    if section == "Gol Ağı":
        handle_goal_path(team_list, change_situations, change_body_parts)
    elif section == "Şut Lokasyonu":
        handle_shot_location(team_list, change_situations, change_body_parts)