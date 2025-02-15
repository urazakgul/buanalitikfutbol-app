import os
import streamlit as st
from config import change_situations, PLOT_STYLE, LEAGUE_COUNTRY_LOOKUP
from code.utils.helpers import add_download_button, load_filtered_json_files, turkish_upper, turkish_english_lower
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_shot_location_plot(df_goals, df_non_goals, league, season, league_display, season_display, team, last_round, situation_type=None):
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
        0.5, 1.07,
        s=(
            f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takım Şut Lokasyonları"
        ),
        size=16,
        fontweight="bold",
        va="center",
        ha="center",
        transform=ax.transAxes
    )

    ax.text(
        0.5, 1.045,
        f"{turkish_upper(team)}",
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        transform=ax.transAxes
    )

    if situation_type is None:
        ax.text(
            0.5, 1.02,
            s=(
                f"Şut Dönüşüm Oranı{title_suffix}: %{conversion_rate:.1f} (Penaltı Dahil), %{non_penalty_conversion_rate:.1f} (Penaltı Hariç)"
            ),
            size=12,
            va="center",
            ha="center",
            transform=ax.transAxes
        )
    else:
        ax.text(
            0.5, 1.02,
            s=(
                f"Şut Dönüşüm Oranı{title_suffix}: %{conversion_rate:.1f}"
            ),
            size=12,
            va="center",
            ha="center",
            transform=ax.transAxes
        )

    ax.text(
        0.5, 0.24,
        s="Veri: SofaScore\nHazırlayan: @urazdev",
        size=16,
        color=pitch.line_color,
        fontstyle="italic",
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

    situation_filename = f"_{situation_type}" if situation_type else ""
    file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(team)}_sut_lokasyonlari{turkish_english_lower(situation_filename)}.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, team=None, situation_type=None):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")

        match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        shots_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "shots_data")

        match_data_df = match_data_df[match_data_df["status"] == "Ended"]

        shots_data_df = shots_data_df[[
            "season", "week", "game_id", "is_home", "shot_type", "situation",
            "goal_mouth_location", "player_coordinates_x", "player_coordinates_y"
        ]]

        shots_data_df = shots_data_df.merge(
            match_data_df[["season", "week", "game_id", "home_team", "away_team"]],
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

        if situation_type == "Hepsi":
            team_data = shots_data_df[shots_data_df["team_name"] == team]
        else:
            team_data = shots_data_df[(shots_data_df["team_name"] == team) & (shots_data_df["situation"] == situation_type)]

        df_goals = team_data[team_data["is_goal"] == 1]
        df_non_goals = team_data[team_data["is_goal"] == 0]

        last_round = match_data_df['week'].max()

        create_shot_location_plot(df_goals, df_non_goals, league, season, league_display, season_display, team, last_round, situation_type)

    except Exception as e:
        st.error("Uygun veri bulunamadı.")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/datafc-web/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )