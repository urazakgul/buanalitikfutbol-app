import streamlit as st
from code.analysis import (
    match_statistics_impact_analysis
)
from code.utils.helpers import get_user_selection
from config import match_performance_translations, match_performance_binary

def render_spinner(content_function, *args, **kwargs):
    with st.spinner("İçerik hazırlanıyor..."):
        content_function(*args, **kwargs)

def handle_analysis(team_list, change_situations, change_body_parts, selected_variable):
    league, season, league_display, season_display, _, _, _ = get_user_selection(
        team_list,
        change_situations,
        change_body_parts,
        include_team=False,
        include_situation_type=False,
        include_body_part=False
    )
    render_spinner(
        match_statistics_impact_analysis.main,
        league,
        season,
        league_display,
        season_display,
        selected_variable
    )

def display_analysis(team_list, change_situations, change_body_parts, league, season):
    extended_options = []
    for stat in match_performance_translations.values():
        if stat in match_performance_binary:
            extended_options.append(f"{stat} (Başarı)")
            extended_options.append(f"{stat} (Toplam)")
        else:
            extended_options.append(stat)

    section = st.sidebar.selectbox(
        "Kategori:",
        options=["İstatistiklerin Maça Etkisi"],
        index=None,
        label_visibility="hidden",
        placeholder="Kategoriler"
    )

    if section is None:
        st.warning("Lütfen bir kategori seçin.")
        return

    selected_variable = st.sidebar.selectbox(
        "İstatistikler",
        options=extended_options,
        index=None,
        label_visibility="hidden",
        placeholder="Değişkenler",
        key="variable_subcategory",
    )

    if selected_variable is None:
        st.warning("Lütfen bir değişken seçin.")
        return

    if section == "İstatistiklerin Maça Etkisi":
        handle_analysis(team_list, change_situations, change_body_parts, selected_variable)