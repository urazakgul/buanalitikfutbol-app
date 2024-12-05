import os
import streamlit as st
from config import change_situations, PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_shot_location_plot(df_goals, df_non_goals, team_name, league_display, season_display, max_round, situation_type=None):
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

    title_suffix = f" ({situation_type})" if situation_type else ""
    ax.text(
        x=50,
        y=110,
        s=(
            f"{league_display} {season_display} Sezonu İlk {max_round} Hafta:\n"
            f"{team_name} Takımının Şut Lokasyonları{title_suffix}"
        ),
        size=18,
        va="center",
        ha="center"
    )

    if situation_type is None:
        ax.text(
            x=50,
            y=105,
            s=(
                f"Şut Dönüşüm Oranı: %{conversion_rate:.1f} (Penaltı Dahil), {non_penalty_conversion_rate:.1f}% (Penaltı Hariç)"
            ),
            size=12,
            va="center",
            ha="center"
        )
    else:
        ax.text(
            x=50,
            y=105,
            s=(
                f"Şut Dönüşüm Oranı: %{conversion_rate:.1f}"
            ),
            size=12,
            va="center",
            ha="center"
        )

    y_axis_direction = 22 if situation_type else 24
    ax.text(
        x=50,
        y=y_axis_direction,
        s="Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com",
        size=16,
        color=pitch.line_color,
        fontstyle="italic",
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

    situation_filename = f"_{situation_type}" if situation_type else ""
    file_name = f"{league_display}_{season_display}_{max_round}_{team_name}_Şut Lokasyonu{situation_filename}.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league=None, season=None, team=None, league_display=None, season_display=None, situation_type=None):
    try:
        if team == "Takım seçin":
            st.warning("Lütfen bir takım seçin.")
            return

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        shotmaps_data = load_filtered_json_files(directories, "shot_maps", league, season)

        shotmaps_data = shotmaps_data[[
            "season", "round", "game_id", "is_home", "shot_type", "situation",
            "goal_mouth_location", "player_coordinates_x", "player_coordinates_y"
        ]]

        shotmaps_data = shotmaps_data.merge(
            matches_data[["season", "round", "game_id", "home_team", "away_team"]],
            on=["season", "round", "game_id"],
            how="left"
        )

        shotmaps_data["team_name"] = shotmaps_data.apply(
            lambda row: row["home_team"] if row["is_home"] else row["away_team"], axis=1
        )

        shotmaps_data["is_goal"] = shotmaps_data["shot_type"].apply(lambda x: 1 if x == "goal" else 0)
        shotmaps_data["player_coordinates_x"] = 100 - shotmaps_data["player_coordinates_x"]
        shotmaps_data["player_coordinates_y"] = 100 - shotmaps_data["player_coordinates_y"]

        shotmaps_data["situation"] = shotmaps_data["situation"].replace(change_situations)

        if situation_type is not None:
            team_data = shotmaps_data[(shotmaps_data["team_name"] == team) & (shotmaps_data["situation"] == situation_type)]
        else:
            team_data = shotmaps_data[shotmaps_data["team_name"] == team]

        df_goals = team_data[team_data["is_goal"] == 1]
        df_non_goals = team_data[team_data["is_goal"] == 0]

        max_round = matches_data["round"].max()

        create_shot_location_plot(df_goals, df_non_goals, team, league_display, season_display, max_round, situation_type)

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