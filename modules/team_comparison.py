import os
import streamlit as st
from code.analysis.xg_time_series import main as xg_time_series_main
from code.analysis.xg_actual_vs_expected import main as xg_actual_vs_expected_main
from code.analysis.xg_strengths_vs_weaknesses import main as xg_strengths_vs_weaknesses_main
from code.analysis.xg_ladder import main as xg_ladder_main
from code.analysis.performance import main as performance_main
from code.utils.helpers import load_filtered_json_files, get_user_selection
from config import match_performances

def display_team_comparison(team_list, change_situations, change_body_parts):
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
                "Kümülatif xG ve Gol (Haftalık Seri)",
                "Kümülatif xG ve Gol Farkı (Haftalık Seri)",
                "Gerçekleşen ile Beklenen Gol Farkı",
                "Üretilen xG ve Yenen xG (xGA)",
                "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)",
                "xG Merdiveni"
            ],
            key="xg_analysis_type"
        )

        with st.spinner("İçerik hazırlanıyor..."):
            if analysis_type == "Seçin":
                st.warning("Lütfen bir analiz tipi seçin.")
            elif analysis_type in ["Kümülatif xG ve Gol (Haftalık Seri)", "Kümülatif xG ve Gol Farkı (Haftalık Seri)"]:
                xg_time_series_main(
                    league,
                    season,
                    league_display,
                    season_display,
                    plot_type = analysis_type
                )
            elif analysis_type == "Gerçekleşen ile Beklenen Gol Farkı":
                xg_actual_vs_expected_main(league, season, league_display, season_display)
            elif analysis_type in ["Üretilen xG ve Yenen xG (xGA)", "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)"]:
                league, season, _, league_display, season_display, _, _ = get_user_selection(
                    team_list, change_situations, change_body_parts, include_situation_type=False, include_team=False, include_body_part=False, key_prefix="xg_strengths_wekanesses"
                )

                category = st.sidebar.selectbox(
                    "Kategori:",
                    ["Hepsi", "Senaryo", "Vücut Bölgesi"],
                    key="category_selectbox"
                )

                situation_type = None
                body_part_type = None

                if category == "Senaryo":
                    situation_type_display = st.sidebar.selectbox(
                        "Senaryo Tipi:",
                        ["Seçin"] + list(change_situations.values()),
                        key="situation_type_selectbox"
                    )
                    situation_type = situation_type_display if situation_type_display != "Seçin" else None

                elif category == "Vücut Bölgesi":
                    body_part_display = st.sidebar.selectbox(
                        "Vücut Parçası Tipi:",
                        ["Seçin"] + list(change_body_parts.values()),
                        key="body_part_selectbox"
                    )
                    body_part_type = body_part_display if body_part_display != "Seçin" else None

                if category == "Hepsi":
                        xg_strengths_vs_weaknesses_main(
                            league,
                            season,
                            league_display,
                            season_display,
                            situation_type=None,
                            body_part_type=None,
                            category=None,
                            plot_type = analysis_type
                        )

                elif category in ["Senaryo", "Vücut Bölgesi"]:
                    if category == "Senaryo" and situation_type is None:
                        st.warning("Lütfen bir senaryo tipi seçin.")
                    elif category == "Vücut Bölgesi" and body_part_type is None:
                        st.warning("Lütfen bir vücut parçası tipi seçin.")
                    else:
                        xg_strengths_vs_weaknesses_main(
                            league,
                            season,
                            league_display,
                            season_display,
                            situation_type,
                            body_part_type,
                            category="situation" if category == "Senaryo" else "body_part",
                            plot_type = analysis_type
                        )

                else:
                    st.warning("Lütfen bir kategori seçin.")

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
        league, season, _, league_display, season_display, _, _ = get_user_selection(
            team_list, change_situations, change_body_parts, include_situation_type=False, include_team=False, include_body_part=False, key_prefix="performance_section"
        )

        subcategory = st.sidebar.selectbox(
            "İstatistik:", ["Seçin"] + match_performances, key="performance_subcategory"
        )

        if subcategory == "Seçin":
            st.warning("Lütfen bir istatistik seçin.")
        else:
            with st.spinner("İçerik hazırlanıyor..."):
                performance_main(subcategory, league, season, league_display, season_display)