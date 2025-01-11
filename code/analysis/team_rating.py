import os
import streamlit as st
from config import PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer, turkish_english_lower
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_rating_plot(rating_data, league, season, league_display, season_display, last_round, subcategory):

    if subcategory in ["Ortalama-Standart Sapma (Genel)", "Ortalama-Standart Sapma (İç Saha)", "Ortalama-Standart Sapma (Deplasman)"]:

        context = subcategory[subcategory.find('(')+1:subcategory.find(')')]

        fig, ax = plt.subplots(figsize=(12, 10))

        ax.scatter(
            rating_data["mean"],
            rating_data["std"],
            alpha=0
        )

        mean_avg_rating_data = rating_data["mean"].mean()
        mean_sd_rating_data = rating_data["std"].mean()

        ax.axvline(x=mean_avg_rating_data, color="darkblue", linestyle="--", linewidth=2, label="Ortalamanın Ortalaması")
        ax.axhline(y=mean_sd_rating_data, color="darkred", linestyle="--", linewidth=2, label="Ortalama Standart Sapma")

        def getImage(path):
            return OffsetImage(plt.imread(path), zoom=.3, alpha=1)

        for index, row in rating_data.iterrows():
            logo_path = f"./imgs/team_logo/{row['team_name']}.png"
            ab = AnnotationBbox(getImage(logo_path), (row["mean"], row["std"]), frameon=False)
            ax.add_artist(ab)

        ax.set_xlabel("Ortalama", labelpad=20, fontsize=12)
        ax.set_ylabel("Standart Sapma", labelpad=20, fontsize=12)
        ax.set_title(
            f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların {context} Reyting Ortalaması ve Standart Sapması",
            fontsize=14,
            fontweight="bold",
            pad=40
        )
        ax.grid(True, linestyle="--", alpha=0.7)

        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, 1.05),
            ncol=2,
            fontsize=8,
            frameon=False
        )

        add_footer(fig)

        file_name = f"{league_display}_{season_display}_{last_round}_Takımların {turkish_english_lower(context)} Reyting Ortalaması ve Standart Sapması.png"
        st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
        st.pyplot(fig)

def main(subcategory, league, season, league_display, season_display):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        games_data = load_filtered_json_files(directories, "games", league_display, season_display)
        lineups_data = load_filtered_json_files(directories, "lineups", league_display, season_display)
        lineups_data = lineups_data[lineups_data["stat_name"] == "rating"]

        lineups_games_data = lineups_data.merge(
            games_data,
            on=["tournament","season","round","game_id"],
            how="right"
        )

        lineups_games_data["team_name"] = lineups_games_data.apply(
            lambda row: row["home_team"] if row["team"] == "home" else row["away_team"], axis=1
        )

        last_round = games_data["round"].max()

        if subcategory == "Ortalama-Standart Sapma (Genel)":
            rating_data = lineups_games_data.groupby("team_name")["stat_value"].agg(["mean", "std"]).reset_index()
            create_rating_plot(rating_data, league, season, league_display, season_display, last_round, subcategory)
        elif subcategory == "Ortalama-Standart Sapma (İç Saha)":
            home_data = lineups_games_data[lineups_games_data["team"] == "home"]
            rating_data = home_data.groupby("team_name")["stat_value"].agg(["mean", "std"]).reset_index()
            create_rating_plot(rating_data, league, season, league_display, season_display, last_round, subcategory)
        elif subcategory == "Ortalama-Standart Sapma (Deplasman)":
            away_data = lineups_games_data[lineups_games_data["team"] == "away"]
            rating_data = away_data.groupby("team_name")["stat_value"].agg(["mean", "std"]).reset_index()
            create_rating_plot(rating_data, league, season, league_display, season_display, last_round, subcategory)

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