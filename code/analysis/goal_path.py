import os
import streamlit as st
from config import event_type_translations, event_colors, PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files, turkish_upper, turkish_english_lower
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def fill_team_name(df):
    df["team_name"] = df.groupby("id")["team_name"].transform(lambda x: x.ffill().bfill())
    return df

def merge_match_data(games_data, shot_maps_data):
    filtered_shot_maps = shot_maps_data[shot_maps_data["shot_type"] == "goal"][[
        "tournament", "season", "round", "game_id", "player_name", "is_home", "goal_type", "xg"
    ]]
    merged_df = games_data.merge(filtered_shot_maps, on=["tournament", "season", "round", "game_id"])
    return merged_df[~merged_df["goal_type"].isin(["penalty", "own"])]

def create_goal_network_plot(team_data, league, season, league_display, season_display, team, last_round):
    pitch = VerticalPitch(
        pitch_type="opta",
        corner_arcs=True,
        half=False,
        label=False,
        tick=False
    )
    fig, ax = pitch.draw(figsize=(16, 16))

    for x in [21, 37, 63, 79]:
        ax.axvline(x=x, color="black", linestyle="--", lw=1, alpha=0.5)

    for y in [33, 66]:
        ax.hlines(y=y, xmin=0, xmax=100, color="black", linestyle="-", lw=1, alpha=0.5)

    kde_data = team_data[team_data["event_type"] != "Gol"]
    pitch.kdeplot(
        kde_data["player_x"],
        kde_data["player_y"],
        ax=ax,
        fill=True,
        cmap="Reds",
        levels=100,
        alpha=0.6,
        zorder=0
    )

    for _, row in team_data.iterrows():
        color = event_colors.get(row["event_type"], "black")
        pitch.scatter(
            row["player_x"],
            row["player_y"],
            ax=ax,
            color=color,
            s=50,
            alpha=0.6,
            edgecolors="black",
            zorder=2
        )

    for _, group in team_data.groupby("id"):
        pitch.lines(
            group["player_x"][:-1],
            group["player_y"][:-1],
            group["player_x"][1:],
            group["player_y"][1:],
            ax=ax,
            lw=1,
            color="blue",
            alpha=0.2,
            zorder=1
        )

    handles = [plt.Line2D([0], [0], marker="o", color=color, markersize=7, linestyle="None") for _, color in event_colors.items()]
    ax.legend(
        handles,
        event_colors.keys(),
        title="",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        frameon=False,
        ncol=3,
        fontsize=8
    )

    ax.set_title(
        f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların Gol Ağları ve Etkin Olduğu Alanlar",
        fontsize=12,
        fontweight="bold"
    )
    ax.text(
        0.5, 0.99,
        turkish_upper(team),
        fontsize=10,
        fontweight="bold",
        ha="center",
        va="center",
        transform=ax.transAxes
    )
    fig.suptitle(
        "Veri: SofaScore\nHazırlayan: @urazdev",
        y=0,
        x=0.5,
        fontsize=12,
        fontstyle="italic",
        color="gray"
    )
    file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(team)}_gol_aglari_ve_etkin_oldugu_alanlar.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, team=None):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        dataframes = {
            "games": load_filtered_json_files(directories, "games", league_display, season_display),
            "shot_maps": load_filtered_json_files(directories, "shot_maps", league_display, season_display),
            "goal_paths": load_filtered_json_files(directories, "goal_paths", league_display, season_display)
        }

        games_data = dataframes["games"][["tournament", "season", "round", "game_id", "home_team", "away_team"]]
        games_shot_maps_df = merge_match_data(games_data, dataframes["shot_maps"])
        dataframes["goal_paths"]["team_name"] = None

        for game_id in games_shot_maps_df["game_id"].unique():
            match_data = games_shot_maps_df[games_shot_maps_df["game_id"] == game_id]
            for _, row in match_data.iterrows():
                team_name = row["home_team"] if row["is_home"] else row["away_team"]
                dataframes["goal_paths"].loc[
                    (dataframes["goal_paths"]["game_id"] == game_id) &
                    (dataframes["goal_paths"]["player_name"] == row["player_name"]) &
                    (dataframes["goal_paths"]["event_type"] == "goal"), "team_name"
                ] = team_name

        goal_paths_data = fill_team_name(dataframes["goal_paths"])
        for _, group in goal_paths_data.groupby("id"):
            if (group["event_type"] == "goal").any() and group.loc[group["event_type"] == "goal", "goal_shot_x"].iloc[0] != 100:
                goal_paths_data.loc[group.index, ["player_x", "player_y"]] = 100 - group[["player_x", "player_y"]]

        goal_paths_data = goal_paths_data.merge(games_data, on=["tournament", "season", "round", "game_id"])
        goal_paths_data["event_type"] = goal_paths_data["event_type"].replace(event_type_translations)

        team_data = goal_paths_data[goal_paths_data["team_name"] == team]

        last_round = games_data['round'].max()

        create_goal_network_plot(team_data, league, season, league_display, season_display, team, last_round)

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