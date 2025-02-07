import os
import streamlit as st
from code.analysis import (
    match_statistics_impact_analysis,
    predictive_analytics
)
from code.utils.helpers import load_filtered_json_files, get_user_selection
from config import match_performance_translations, match_performance_binary, LEAGUE_COUNTRY_LOOKUP

def render_spinner(content_function, *args, **kwargs):
    with st.spinner("İçerik hazırlanıyor..."):
        content_function(*args, **kwargs)

def load_game_data(directories, league_display, season_display):
    country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")
    match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
    match_data_df_ended = match_data_df[match_data_df["status"] == "Ended"]

    if not match_data_df_ended.empty:
        max_round = match_data_df_ended["week"].max()
        max_round_next_day = max_round + 1
        games_data_next_day = match_data_df[match_data_df["week"] == max_round_next_day]

        if not games_data_next_day.empty:
            return games_data_next_day, max_round_next_day
        else:
            st.warning("Seçilen lig ve sezonda bir sonraki haftaya ait maçlar bulunamadı.")
            return None
    else:
        st.warning("Henüz yeterli veri bulunmamaktadır.")
        return None

def handle_eda_analysis(team_list, change_situations, change_body_parts, selected_category, extended_options):
    league, season, league_display, season_display, _, _, _ = get_user_selection(
        team_list,
        change_situations,
        change_body_parts,
        include_team=False,
        include_situation_type=False,
        include_body_part=False
    )
    if selected_category == "İstatistiklerin Maça Etkisi":
        selected_variable = st.sidebar.selectbox(
            label="İstatistikler:",
            options=extended_options,
            index=None,
            label_visibility="hidden",
            placeholder="Değişkenler",
            key="variable_subcategory",
        )

        if selected_variable is None:
            st.warning("Lütfen bir değişken seçin.")
            return

        render_spinner(
            match_statistics_impact_analysis.main,
            league,
            season,
            league_display,
            season_display,
            selected_variable
        )

def handle_predictive_analytics(team_list, change_situations, change_body_parts, selected_model):
    league, season, league_display, season_display, _, _, _ = get_user_selection(
        team_list,
        change_situations,
        change_body_parts,
        include_team=False,
        include_situation_type=False,
        include_body_part=False
    )
    directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/raw/')
    games_data_next_day, max_round_next_day = load_game_data(directories, league_display, season_display)

    if games_data_next_day is None:
        return

    games_list = [f"{row['home_team']} - {row['away_team']}" for index, row in games_data_next_day.iterrows()]
    selected_game = st.sidebar.selectbox(
        label="Maç:",
        options=games_list,
        index=None,
        label_visibility="hidden",
        placeholder="Gelecek Hafta Maçları"
    )

    if selected_game is None:
        st.warning("Lütfen bir maç seçin.")
        return

    if selected_model == "Dixon-Coles":
        plot_type = st.sidebar.radio(
            label="Gösterim Şekli:",
            options=["Matris", "Sıralı", "Özet"],
            index=None,
            label_visibility="hidden"
        )

        if plot_type is None:
            st.warning("Lütfen bir gösterim şekli seçin.")
            return

        if plot_type == "Özet":
            first_n_goals = st.sidebar.number_input(
                label="Gol Kombinasyonu:",
                min_value=2,
                max_value=121,
                value=10,
                label_visibility="hidden",
                placeholder="Gol Kombinasyonu"
            )
        else:
            first_n_goals = 10
    elif selected_model == "Bradley-Terry":
        plot_type = None
        first_n_goals = None

    render_spinner(
        predictive_analytics.main,
        league,
        season,
        league_display,
        season_display,
        selected_model,
        selected_game,
        max_round_next_day,
        plot_type,
        first_n_goals
    )

def display_eda_analysis(team_list, change_situations, change_body_parts, league, season):
    extended_options = []
    for stat in match_performance_translations.values():
        if stat in match_performance_binary:
            extended_options.append(f"{stat} (Başarı)")
            extended_options.append(f"{stat} (Toplam)")
        else:
            extended_options.append(stat)

    selected_category = st.sidebar.selectbox(
        label="Kategori:",
        options=["İstatistiklerin Maça Etkisi"],
        index=None,
        label_visibility="hidden",
        placeholder="Kategoriler"
    )

    if selected_category is None:
        st.warning("Lütfen bir kategori seçin.")
        return

    handle_eda_analysis(team_list, change_situations, change_body_parts, selected_category, extended_options)

def display_predictive_analytics(team_list, change_situations, change_body_parts, league, season):
    selected_model = st.sidebar.selectbox(
        label="Tahmin Yöntemi:",
        options=["Dixon-Coles", "Bradley-Terry"],
        index=None,
        label_visibility="hidden",
        placeholder="Tahmin Yöntemleri"
    )

    if selected_model is None:
        st.warning("Lütfen bir tahmin yöntemi seçin.")
        return

    handle_predictive_analytics(team_list, change_situations, change_body_parts, selected_model)