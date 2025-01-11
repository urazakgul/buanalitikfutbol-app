import streamlit as st
from code.analysis import (
    xg_time_series,
    xg_actual_vs_expected,
    xg_strengths_vs_weaknesses,
    xg_defensive_efficiency,
    performance,
    team_rating,
    team_similarity,
    goal_creation_patterns,
    team_win_rate,
    geometry
)
from code.utils.helpers import get_user_selection
from config import match_performances, game_stats_group_name

def render_spinner(content_function, *args, **kwargs):
    with st.spinner("İçerik hazırlanıyor..."):
        content_function(*args, **kwargs)

def process_xg_analysis(league, season, league_display, season_display, team_list_by_season, change_situations, change_body_parts):
    analysis_type = st.sidebar.selectbox(
        label="xG Analiz Tipleri",
        options=[
            "Kümülatif xG ve Gol (Haftalık Seri)",
            "Kümülatif xG ve Gol Farkı (Haftalık Seri)",
            "Gerçekleşen ile Beklenen Gol Farkı",
            "Üretilen xG ve Yenen xG (xGA)",
            "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)",
            "xG Bazlı Savunma Verimliliği",
        ],
        index=None,
        label_visibility="hidden",
        placeholder="xG Analiz Tipleri",
        key="xg_analysis_type"
    )

    if analysis_type in [
        "Kümülatif xG ve Gol (Haftalık Seri)",
        "Kümülatif xG ve Gol Farkı (Haftalık Seri)",
    ]:
        render_spinner(xg_time_series.main, league, season, league_display, season_display, plot_type=analysis_type)
    elif analysis_type == "Gerçekleşen ile Beklenen Gol Farkı":
        render_spinner(xg_actual_vs_expected.main, league, season, league_display, season_display)
    elif analysis_type in [
        "Üretilen xG ve Yenen xG (xGA)",
        "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)",
    ]:
        render_spinner(
            xg_strengths_vs_weaknesses.main,
            league,
            season,
            league_display,
            season_display,
            situation_type=None,
            body_part_type=None,
            category=None,
            plot_type=analysis_type,
        )
    elif analysis_type == "xG Bazlı Savunma Verimliliği":
        render_spinner(xg_defensive_efficiency.main, league, season, league_display, season_display)

def display_team_comparison(team_list_by_season, change_situations, change_body_parts, league, season):
    section = st.sidebar.selectbox(
        label="Kategoriler",
        options=[
            "xG (Beklenen Gol)",
            "Maç Performansı",
            "Reyting",
            "Benzerlik",
            "Gol Üretim Şekilleri",
            "Kazanma Oranı",
            "Geometri"
        ],
        index=None,
        label_visibility="hidden",
        placeholder="Kategoriler",
        key="categories"
    )

    if section is None:
        st.warning("Lütfen bir kategori seçin.")
        return

    league, season, league_display, season_display, _, _, _ = get_user_selection(
        team_list_by_season,
        change_situations,
        change_body_parts,
        include_situation_type=False,
        include_team=False,
        include_body_part=False,
        key_prefix=f"{section.lower()}_section",
    )

    if section == "xG (Beklenen Gol)":
        process_xg_analysis(
            league, season, league_display, season_display, team_list_by_season, change_situations, change_body_parts
        )
    elif section == "Maç Performansı":
        subcategory = st.sidebar.selectbox(
            label="İstatistikler",
            options=match_performances,
            index=None,
            label_visibility="hidden",
            placeholder="İstatistikler",
            key="performance_subcategory"
        )
        if not subcategory:
            st.warning("Lütfen bir istatistik seçin.")
            return
        render_spinner(performance.main, subcategory, league, season, league_display, season_display)
    elif section == "Reyting":
        subcategory = st.sidebar.selectbox(
            label="Analiz Tipleri",
            options=[
                "Ortalama-Standart Sapma (Genel)",
                "Ortalama-Standart Sapma (İç Saha)",
                "Ortalama-Standart Sapma (Deplasman)",
            ],
            index=None,
            label_visibility="hidden",
            placeholder="Analiz Tipleri",
            key="rating_subcategory"
        )
        if not subcategory:
            st.warning("Lütfen bir analiz tipi seçin.")
            return
        render_spinner(team_rating.main, subcategory, league, season, league_display, season_display)
    elif section == "Benzerlik":
        similarity_algorithm = st.sidebar.selectbox(
            label="Benzerlik Algoritmaları",
            options=["Kosinüs Benzerliği", "Temel Bileşen Analizi"],
            index=None,
            label_visibility="hidden",
            placeholder="Benzerlik Algoritmaları",
            key="similarity_algorithm"
        )

        if similarity_algorithm is None:
            st.warning("Lütfen bir benzerlik algoritması seçin.")
            return

        include_team = similarity_algorithm != "Temel Bileşen Analizi"

        league, season, league_display, season_display, team, _, _ = get_user_selection(
            team_list_by_season,
            change_situations,
            change_body_parts,
            include_situation_type=False,
            include_team=include_team,
            include_body_part=False,
            key_prefix="similarity_section",
        )

        if include_team and not team:
            st.warning("Lütfen bir takım seçin.")
        else:
            filtered_game_stats_group_name = [
                category for category in game_stats_group_name if category != "Genel Görünüm"
            ]
            selected_categories = st.sidebar.multiselect(
                label="İstatistik Kategorileri:",
                options=filtered_game_stats_group_name,
                default=filtered_game_stats_group_name,
                key="similarity_categories",
            )

            if not selected_categories:
                st.warning("Lütfen en az bir istatistik kategorisi seçin.")
            else:
                render_spinner(
                    team_similarity.main,
                    league,
                    season,
                    league_display,
                    season_display,
                    team if include_team else None,
                    selected_categories,
                    similarity_algorithm
                )
    elif section == "Gol Üretim Şekilleri":
        category = st.sidebar.selectbox(
            label="Gol Üretim Şekilleri",
            options=[
                "Senaryo",
                "Vücut Bölgesi",
                "Zaman Dilimi",
                "Kale Lokasyonu",
                "Oyuncu Pozisyonu",
                "İç Saha-Deplasman"
            ],
            index=None,
            label_visibility="hidden",
            placeholder="Gol Üretim Şekilleri",
            key="goal_type_category",
        )
        if not category:
            st.warning("Lütfen bir gol üretim şekli seçin.")
            return
        subcategory = st.sidebar.selectbox(
            label="Gol Payı Tipleri",
            options=["Takım Payına Göre", "Takımlar Arası Paya Göre"],
            index=None,
            label_visibility="hidden",
            placeholder="Gol Payı Tipleri",
            key="goal_type_{category}_subcategory",
        )
        if not subcategory:
            st.warning("Lütfen bir gol payı tipi seçin.")
            return
        render_spinner(
            goal_creation_patterns.main,
            category,
            subcategory,
            league,
            season,
            league_display,
            season_display
        )
    elif section == "Kazanma Oranı":
        render_spinner(
            team_win_rate.main,
            league, season,
            league_display,
            season_display
        )
    elif section == "Geometri":
        category = st.sidebar.selectbox(
            label="Geometrik Analizler:",
            options=[
                "Kompaktlık",
                "Dikey Yayılım",
                "Yatay Yayılım"
            ],
            index=None,
            label_visibility="hidden",
            placeholder="Geometrik Analizler",
            key="geometry_category",
        )
        if not category:
            st.warning("Lütfen bir analiz tipi seçin.")
            return
        render_spinner(
            geometry.main,
            category,
            league,
            season,
            league_display,
            season_display
        )