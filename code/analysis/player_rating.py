import os
import streamlit as st
from config import PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer, turkish_english_lower
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_player_rating_plot(main_rating_df, league, season, league_display, season_display, team, last_round, player):

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.fill_between(
        main_rating_df["round"],
        main_rating_df["min"],
        main_rating_df["max"],
        color="gray",
        alpha=0.1,
        label=f"Takım Min-Maks Reyting Kanalı"
    )
    ax.plot(
        main_rating_df["round"],
        main_rating_df["min"],
        color="gray",
        alpha=0.2,
        linewidth=2,
        linestyle="-"
    )
    ax.plot(
        main_rating_df["round"],
        main_rating_df["max"],
        color="gray",
        alpha=0.2,
        linewidth=2,
        linestyle="-"
    )
    ax.plot(
        main_rating_df["round"],
        main_rating_df["mean"],
        label=f"Takım Reyting Ortalaması",
        marker="o",
        linestyle="--",
        linewidth=2,
        color="gray"
    )
    ax.plot(
        main_rating_df["round"],
        main_rating_df["stat_value"],
        label=f"Oyuncu Reytingi",
        marker="o",
        linestyle="-",
        color="red"
    )

    ax.set_xlabel("Hafta", labelpad=20, fontsize=12)
    ax.set_ylabel("Reyting", labelpad=20, fontsize=12)
    ax.set_title(
        f"{league} {season} Sezonu Geçmiş {last_round} Haftada Oyuncu Reytingleri\n\n{player} ({team})",
        fontsize=14,
        fontweight="bold",
        pad=40
    )

    ax.set_ylim(0, 10)

    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.05),
        ncol=3,
        fontsize=8,
        frameon=False
    )

    ax.grid(True, linestyle="--", alpha=0.7)

    add_footer(fig)
    file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(player)}_reytingleri.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, team, player):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        games_data = load_filtered_json_files(directories, "games", league_display, season_display)
        lineups_data = load_filtered_json_files(directories, "lineups", league_display, season_display)

        games_data = games_data[games_data["status"] == "Ended"]
        games_data = games_data[["tournament","season","round","game_id","home_team","home_team_id","away_team","away_team_id"]]

        player_rating_df = games_data.merge(
            lineups_data,
            on=["tournament","season","round","game_id"]
        )

        player_rating_df = player_rating_df[player_rating_df["stat_name"] == "rating"]
        player_rating_df["team_name"] = player_rating_df.apply(
            lambda row: row["home_team"] if row["team"] == "home" else row["away_team"], axis=1
        )
        player_rating_df = player_rating_df[player_rating_df['team_name'] == team]
        rating_df_filtered_player = player_rating_df[player_rating_df["player_name"] == player]

        team_min_max_rating_df = player_rating_df.groupby(["team_name", "round"])["stat_value"].agg(["min", "max", "mean"]).reset_index()

        main_rating_df = team_min_max_rating_df.merge(
            rating_df_filtered_player,
            on=["team_name","round"],
            how="left"
        )

        last_round = games_data["round"].max()

        create_player_rating_plot(main_rating_df, league, season, league_display, season_display, team, last_round, player)

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