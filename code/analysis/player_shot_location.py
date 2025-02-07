import os
import streamlit as st
from config import change_situations, PLOT_STYLE, LEAGUE_COUNTRY_LOOKUP
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer, turkish_upper, turkish_english_lower
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_player_shot_location_plot(df_goals, df_non_goals, league, season, league_display, season_display, team, last_round, player_name):
    pitch = VerticalPitch(
        pitch_type="opta",
        corner_arcs=True,
        half=False,
        label=False,
        tick=False
    )

    fig, ax = pitch.draw(figsize=(16, 16))

    pitch.scatter(
        df_non_goals["player_coordinates_x"],
        df_non_goals["player_coordinates_y"],
        edgecolors="black",
        c="gray",
        marker="h",
        alpha=0.3,
        s=150,
        label="Gol Değil",
        ax=ax
    )

    pitch.scatter(
        df_goals["player_coordinates_x"],
        df_goals["player_coordinates_y"],
        edgecolors="black",
        c="red",
        marker="h",
        alpha=0.7,
        s=150,
        label="Gol",
        ax=ax
    )

    total_shots = len(df_goals) + len(df_non_goals)
    conversion_rate = len(df_goals) / total_shots * 100 if total_shots > 0 else 0

    non_penalty_goals = df_goals[df_goals["situation"] != "Penaltıdan"]
    non_penalty_shots = total_shots - len(df_goals[df_goals["situation"] == "Penaltıdan"])
    non_penalty_conversion_rate = len(non_penalty_goals) / non_penalty_shots * 100 if non_penalty_shots > 0 else 0

    ax.set_title(
        f"{league} {season} Sezonu Geçmiş {last_round} Haftada Oyuncu Şut Lokasyonları",
        fontsize=16,
        fontweight="bold",
        y=1.05
    )
    ax.text(
        0.5, 1.04,
        f"{turkish_upper(player_name)} ({turkish_upper(team)})",
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        transform=ax.transAxes
    )

    add_footer(fig, x=0.5, y=0, ha="center")

    ax.text(
        0.5, 1.02,
        s=(
            f"Şut Dönüşüm Oranı: %{conversion_rate:.1f} (Penaltı Dahil), %{non_penalty_conversion_rate:.1f} (Penaltı Hariç)"
        ),
        size=12,
        va="center",
        ha="center",
        transform=ax.transAxes
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=2,
        fontsize=12,
        frameon=False,
        facecolor="white",
        edgecolor="black"
    )

    file_name = f"{league_display}_{season_display}_{turkish_english_lower(player_name)}_{turkish_english_lower(team)}_sut_lokasyonlari.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, team, player):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")

        match_data = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        shots_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "shots_data")

        match_data = match_data[match_data["status"] == "Ended"]
        match_data = match_data[["season", "week", "game_id", "home_team", "away_team"]]

        shots_data_df = shots_data_df[[
            "season", "week", "game_id", "player_name", "is_home", "shot_type", "situation",
            "goal_mouth_location", "player_coordinates_x", "player_coordinates_y"
        ]]

        shots_data_df = shots_data_df.merge(
            match_data,
            on=["season", "week", "game_id"],
            how="left"
        )

        shots_data_df["team_name"] = shots_data_df.apply(
            lambda row: row["home_team"] if row["is_home"] else row["away_team"], axis=1
        )

        shots_data_df["is_goal"] = shots_data_df["shot_type"].apply(lambda x: 1 if x == "goal" else 0)
        shots_data_df["player_coordinates_x"] = 100 - shots_data_df["player_coordinates_x"]
        shots_data_df["player_coordinates_y"] = 100 - shots_data_df["player_coordinates_y"]

        shots_data_df["situation"] = shots_data_df["situation"].replace(change_situations)

        player_data = shots_data_df[(shots_data_df["team_name"] == team) & (shots_data_df["player_name"] == player)]

        df_goals = player_data[player_data["is_goal"] == 1]
        df_non_goals = player_data[player_data["is_goal"] == 0]

        last_round = match_data['week'].max()

        create_player_shot_location_plot(df_goals, df_non_goals, league, season, league_display, season_display, team, last_round, player)

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