import os
import streamlit as st
from config import change_situations, PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_player_shot_location_plot(df_goals, df_non_goals, team_name, league_display, season_display, max_round, player_name):
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
        f"{league_display} {season_display} Sezonu Oyuncu Şut Lokasyonları\n{player_name} ({team_name})",
        fontsize=16,
        y=1.05
    )

    fig.suptitle(
        "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com",
        y=0,
        x=0.5,
        fontsize=12,
        fontstyle="italic",
        color="gray"
    )

    ax.text(
        x=50,
        y=105,
        s=(
            f"Şut Dönüşüm Oranı: %{conversion_rate:.1f} (Penaltı Dahil), %{non_penalty_conversion_rate:.1f} (Penaltı Hariç)"
        ),
        size=12,
        va="center",
        ha="center"
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

    file_name = f"{league_display}_{season_display}_{player_name}_{team_name}_Şut Lokasyonları.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league=None, season=None, team=None, league_display=None, season_display=None, player=None):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league, season)

        matches_data = matches_data[["season", "round", "game_id", "home_team", "away_team"]]

        shot_maps_data = shot_maps_data[[
            "season", "round", "game_id", "player_name", "is_home", "shot_type", "situation",
            "goal_mouth_location", "player_coordinates_x", "player_coordinates_y"
        ]]

        shot_maps_data = shot_maps_data.merge(
            matches_data,
            on=["season", "round", "game_id"],
            how="left"
        )

        shot_maps_data["team_name"] = shot_maps_data.apply(
            lambda row: row["home_team"] if row["is_home"] else row["away_team"], axis=1
        )

        shot_maps_data["is_goal"] = shot_maps_data["shot_type"].apply(lambda x: 1 if x == "goal" else 0)
        shot_maps_data["player_coordinates_x"] = 100 - shot_maps_data["player_coordinates_x"]
        shot_maps_data["player_coordinates_y"] = 100 - shot_maps_data["player_coordinates_y"]

        shot_maps_data["situation"] = shot_maps_data["situation"].replace(change_situations)

        player_data = shot_maps_data[(shot_maps_data["team_name"] == team) & (shot_maps_data["player_name"] == player)]

        df_goals = player_data[player_data["is_goal"] == 1]
        df_non_goals = player_data[player_data["is_goal"] == 0]

        max_round = matches_data["round"].max()

        create_player_shot_location_plot(df_goals, df_non_goals, team, league_display, season_display, max_round, player)

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