import os
import numpy as np
import streamlit as st
from code.utils.helpers import add_download_button, load_filtered_json_files
from config import PLOT_STYLE
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_xg_defence_efficiency_plot(team_opponent_df, league_display, season_display, last_round):

    fig, ax = plt.subplots(figsize=(12, 10))

    ax.scatter(
        team_opponent_df["non_penalty_xg_per_shot_against"],
        team_opponent_df["non_penalty_shot_conversion_against"],
        alpha=0
    )

    mean_non_penalty_xg_per_shot_against = team_opponent_df["non_penalty_xg_per_shot_against"].mean()
    mean_non_penalty_shot_conversion_against = team_opponent_df["non_penalty_shot_conversion_against"].mean()

    ax.axvline(x=mean_non_penalty_xg_per_shot_against, color="darkblue", linestyle="--", linewidth=2, label="Rakip Şut Başına Beklenen Gol (xG) (Ortalama)")
    ax.axhline(y=mean_non_penalty_shot_conversion_against, color="darkred", linestyle="--", linewidth=2, label="Rakip Şut Dönüşüm Oranı (%) (Ortalama)")

    def getImage(path):
        return OffsetImage(plt.imread(path), zoom=.4, alpha=1)

    for index, row in team_opponent_df.iterrows():
        logo_path = f"./imgs/team_logo/{row['team_name']}.png"
        ab = AnnotationBbox(getImage(logo_path), (row["non_penalty_xg_per_shot_against"], row["non_penalty_shot_conversion_against"]), frameon=False)
        ax.add_artist(ab)

    ax.set_xlabel("Rakip Şut Başına Beklenen Gol (xG) (Penaltı Hariç)", labelpad=20, fontsize=12)
    ax.set_ylabel("Rakip Şut Dönüşüm Oranı (%) (Penaltı Hariç)", labelpad=20, fontsize=12)
    ax.set_title(
        f"{league_display} {season_display} Sezonu Geçmiş {last_round} Hafta Rakip Şut Kalitesi ve Şut Dönüşüm Oranı",
        fontsize=16,
        pad=75
    )
    ax.grid(True, linestyle="--", alpha=0.7)

    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.05),
        ncol=2,
        fontsize=8,
        frameon=False
    )

    fig.text(
        0.99, -0.1,
        "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com\nKümülatif değerlerdir.",
        horizontalalignment="right",
        verticalalignment="bottom",
        fontsize=10,
        fontstyle="italic",
        color="gray"
    )

    offset = 1.5
    annotations = [
        ("Yüksek Şut Kalitesi\nDüşük Şut Dönüşüm",
         team_opponent_df["non_penalty_xg_per_shot_against"].max(),
         team_opponent_df["non_penalty_shot_conversion_against"].min() - offset),
        ("Düşük Şut Kalitesi\nDüşük Şut Dönüşüm",
         team_opponent_df["non_penalty_xg_per_shot_against"].min(),
         team_opponent_df["non_penalty_shot_conversion_against"].min() - offset),
        ("Yüksek Şut Kalitesi\nYüksek Şut Dönüşüm",
         team_opponent_df["non_penalty_xg_per_shot_against"].max(),
         team_opponent_df["non_penalty_shot_conversion_against"].max() + offset),
        ("Düşük Şut Kalitesi\nYüksek Şut Dönüşüm",
         team_opponent_df["non_penalty_xg_per_shot_against"].min(),
         team_opponent_df["non_penalty_shot_conversion_against"].max() + offset)
    ]

    for text, x, y in annotations:
        ax.text(
            x, y, text,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=12,
            bbox=dict(facecolor="none", edgecolor="none")
        )

    file_name = f"{league_display}_{season_display}_{last_round}_Rakip Şut Kalitesi ve Şut Dönüşüm Oranı.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display):

    try:
        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league, season)

        shot_maps_data = shot_maps_data.merge(matches_data, on=["tournament", "season", "round", "game_id"])
        shot_maps_data["team_name"] = shot_maps_data.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)
        shot_maps_data = shot_maps_data[shot_maps_data["goal_type"] != "penalty"]
        shot_maps_data["is_goal"] = shot_maps_data["shot_type"].apply(lambda x: 1 if x == "goal" else 0)

        xg_xga_df = shot_maps_data.groupby(["game_id", "team_name"]).agg(
            xg=("xg", "sum"),
            shots=("xg", "count"),
            goals=("is_goal", "sum")
        ).reset_index()

        for game_id in xg_xga_df["game_id"].unique():
            game_data = xg_xga_df[xg_xga_df["game_id"] == game_id]
            match_info = matches_data[matches_data["game_id"] == game_id]

            if not match_info.empty:
                home_team = match_info["home_team"].values[0]
                away_team = match_info["away_team"].values[0]

                for index, row in game_data.iterrows():
                    opponent_data = game_data[game_data["team_name"] != row["team_name"]]

                    if not opponent_data.empty:
                        opponent_xg = opponent_data["xg"].values[0]
                        opponent_shots = opponent_data["shots"].values[0]
                        opponent_goals = opponent_data["goals"].values[0]

                        xg_xga_df.at[index, "xga"] = opponent_xg
                        xg_xga_df.at[index, "opponent_shots"] = opponent_shots
                        xg_xga_df.at[index, "opponent_goals"] = opponent_goals
                    else:
                        if row["team_name"] not in [home_team, away_team]:
                            xg_xga_df.at[index, "xga"] = 0
                            xg_xga_df.at[index, "opponent_shots"] = 0
                            xg_xga_df.at[index, "opponent_goals"] = 0

        team_opponent_df = xg_xga_df.groupby("team_name").agg(
            xg=("xg", "sum"),
            xgConceded=("xga", "sum"),
            shots=("shots", "sum"),
            goals=("goals", "sum"),
            opponent_shots=("opponent_shots", "sum"),
            opponent_goals=("opponent_goals", "sum")
        ).reset_index()

        team_opponent_df['non_penalty_xg_per_shot_against'] = team_opponent_df['xgConceded'] / team_opponent_df['opponent_shots']
        team_opponent_df['non_penalty_shot_conversion_against'] = (team_opponent_df['opponent_goals'] / team_opponent_df['opponent_shots']) * 100

        last_round = matches_data["round"].max()

        create_xg_defence_efficiency_plot(team_opponent_df, league_display, season_display, last_round)

    except Exception as e:
        st.error(f"Uygun veri bulunamadı. {e}")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/buanalitikfutbol-app/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )