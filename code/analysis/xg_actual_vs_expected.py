import os
import numpy as np
import streamlit as st
from code.utils.helpers import add_download_button, load_filtered_json_files
from config import PLOT_STYLE
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_actual_vs_expected_xg_plot(xg_xga_gerceklesen_teams, league_display, season_display, last_round):

    fig, ax = plt.subplots(figsize=(12, 10))

    ax.scatter(
        xg_xga_gerceklesen_teams["xgDiff"],
        xg_xga_gerceklesen_teams["xgConcededDiff"],
        alpha=0
    )

    mean_xgDiff = 0
    mean_xgConcededDiff = 0

    ax.axhline(y=mean_xgConcededDiff, color="darkred", linestyle="--", linewidth=2, label="Gerçekleşen - xGA = 0")
    ax.axvline(x=mean_xgDiff, color="darkblue", linestyle="--", linewidth=2, label="Gerçekleşen - xG = 0")

    def getImage(path):
        return OffsetImage(plt.imread(path), zoom=.4, alpha=1)

    for index, row in xg_xga_gerceklesen_teams.iterrows():
        logo_path = f"./imgs/team_logo/{row['team_name']}.png"
        ab = AnnotationBbox(getImage(logo_path), (row["xgDiff"], row["xgConcededDiff"]), frameon=False)
        ax.add_artist(ab)

    ax.set_xlabel("Gerçekleşen - xG", labelpad=20, fontsize=12)
    ax.set_ylabel("Gerçekleşen - xGA", labelpad=20, fontsize=12)
    ax.set_title(
        f"{league_display} {season_display} Sezonu Geçmiş {last_round} Hafta Takımların Gerçekleşen ile Beklenen Gol Farkı",
        fontsize=16,
        pad=75
    )
    ax.grid(True, linestyle="--", alpha=0.7)

    fig.text(
        0.99, -0.1,
        "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com\nKümülatif değerlerdir.",
        horizontalalignment="right",
        verticalalignment="bottom",
        fontsize=10,
        fontstyle="italic",
        color="gray"
    )

    offset = 2.5
    annotations = [
        ("İyi Defans\nİyi Hücum",
         xg_xga_gerceklesen_teams["xgDiff"].max(),
         xg_xga_gerceklesen_teams["xgConcededDiff"].min() - offset),
        ("İyi Defans\nKötü Hücum",
         xg_xga_gerceklesen_teams["xgDiff"].min(),
         xg_xga_gerceklesen_teams["xgConcededDiff"].min() - offset),
        ("Kötü Defans\nİyi Hücum",
         xg_xga_gerceklesen_teams["xgDiff"].max(),
         xg_xga_gerceklesen_teams["xgConcededDiff"].max() + offset),
        ("Kötü Defans\nKötü Hücum",
         xg_xga_gerceklesen_teams["xgDiff"].min(),
         xg_xga_gerceklesen_teams["xgConcededDiff"].max() + offset)
    ]

    for text, x, y in annotations:
        ax.text(
            x, y, text,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=12,
            bbox=dict(facecolor="none", edgecolor="none")
        )

    ax.invert_yaxis()

    file_name = f"{league_display}_{season_display}_{last_round}_Gerçekleşen ile Beklenen Gol Farkı.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league, season)
        points_table_data = load_filtered_json_files(directories, "points_table", league, season)

        points_table_data = points_table_data[points_table_data["category"] == "Total"][["team_name", "scores_for", "scores_against"]]

        shot_maps_data = shot_maps_data.merge(matches_data, on=["tournament", "season", "round", "game_id"])
        shot_maps_data["team_name"] = shot_maps_data.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)

        xg_xga_df = shot_maps_data.groupby(["game_id","team_name"])["xg"].sum().reset_index()

        for game_id in xg_xga_df["game_id"].unique():
            game_data = xg_xga_df[xg_xga_df["game_id"] == game_id]
            match_info = matches_data[matches_data["game_id"] == game_id]

            if not match_info.empty:
                home_team = match_info["home_team"].values[0]
                away_team = match_info["away_team"].values[0]

                for index, row in game_data.iterrows():
                    opponent_xg = game_data.loc[game_data["team_name"] != row["team_name"], "xg"].values

                    if opponent_xg.size > 0:
                        xg_xga_df.at[index, "xga"] = opponent_xg[0]
                    else:
                        if row["team_name"] not in [home_team, away_team]:
                            xg_xga_df.at[index, "xga"] = 0

        team_totals_df = xg_xga_df.groupby("team_name")[["xg", "xga"]].sum().reset_index()
        xg_xga_teams = team_totals_df.rename(columns={"xga":"xgConceded"})

        actual_xg_xga_diffs = points_table_data.merge(
            xg_xga_teams,
            on="team_name"
        )
        actual_xg_xga_diffs["xgDiff"] = actual_xg_xga_diffs["scores_for"] - actual_xg_xga_diffs["xg"]
        actual_xg_xga_diffs["xgConcededDiff"] = actual_xg_xga_diffs["scores_against"] - actual_xg_xga_diffs["xgConceded"]
        xg_xga_gerceklesen_teams = actual_xg_xga_diffs[["team_name","xgDiff","xgConcededDiff"]]

        last_round = matches_data["round"].max()

        create_actual_vs_expected_xg_plot(xg_xga_gerceklesen_teams, league_display, season_display, last_round)

    except Exception as e:
        st.error("Uygun veri bulunamadı.")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/buanalitikfutbol-app/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )