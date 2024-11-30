import os
import streamlit as st
from config import event_type_translations, event_colors, PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def fill_team_name(df):
    df["team_name"] = df.groupby("id")["team_name"].transform(lambda x: x.ffill().bfill())
    return df

def merge_match_data(matches_data, shot_maps_data):
    filtered_shot_maps = shot_maps_data[shot_maps_data["shot_type"] == "goal"][[
        "tournament", "season", "round", "game_id", "player_name", "is_home", "goal_type", "xg"
    ]]
    merged_df = matches_data.merge(filtered_shot_maps, on=["tournament", "season", "round", "game_id"])
    return merged_df[~merged_df["goal_type"].isin(["penalty", "own"])]

def create_goal_network_plot(team_data, team_name, league_display, season_display, max_round):
    pitch = VerticalPitch(
        pitch_type="opta",
        corner_arcs=True,
        half=False,
        label=False,
        tick=False
    )
    fig, ax = pitch.draw(figsize=(12, 8))

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
        bbox_to_anchor=(0.5, -0.15),
        frameon=False,
        ncol=3,
        fontsize=8
    )

    ax.set_title(
        f"{league_display} {season_display} Sezonu İlk {max_round} Hafta:\n{team_name} Takımının Gol Ağları ve Etkin Olduğu Alanlar",
        fontsize=12
    )
    fig.suptitle(
        "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com",
        y=0.13,
        x=0.5,
        fontsize=6,
        fontstyle="italic",
        color="gray"
    )
    file_name = f"{league_display}_{season_display}_{max_round}_{team_name}_Gol Ağı.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league=None, season=None, team=None, league_display=None, season_display=None):
    try:
        if team == "Takım seçin":
            st.warning("Lütfen bir takım seçin.")
            return

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        dataframes = {
            "matches": load_filtered_json_files(directories, "matches", league, season),
            "shot_maps": load_filtered_json_files(directories, "shot_maps", league, season),
            "passing_networks": load_filtered_json_files(directories, "passing_networks", league, season)
        }

        matches_data = dataframes["matches"][["tournament", "season", "round", "game_id", "home_team", "away_team"]]
        matches_shot_maps_df = merge_match_data(matches_data, dataframes["shot_maps"])
        dataframes["passing_networks"]["team_name"] = None

        for game_id in matches_shot_maps_df["game_id"].unique():
            match_data = matches_shot_maps_df[matches_shot_maps_df["game_id"] == game_id]
            for _, row in match_data.iterrows():
                team_name = row["home_team"] if row["is_home"] else row["away_team"]
                dataframes["passing_networks"].loc[
                    (dataframes["passing_networks"]["game_id"] == game_id) &
                    (dataframes["passing_networks"]["player_name"] == row["player_name"]) &
                    (dataframes["passing_networks"]["event_type"] == "goal"), "team_name"
                ] = team_name

        passing_networks_data = fill_team_name(dataframes["passing_networks"])
        for _, group in passing_networks_data.groupby("id"):
            if (group["event_type"] == "goal").any() and group.loc[group["event_type"] == "goal", "goal_shot_x"].iloc[0] != 100:
                passing_networks_data.loc[group.index, ["player_x", "player_y"]] = 100 - group[["player_x", "player_y"]]

        passing_networks_data = passing_networks_data.merge(matches_data, on=["tournament", "season", "round", "game_id"])
        passing_networks_data["event_type"] = passing_networks_data["event_type"].replace(event_type_translations)

        team_data = passing_networks_data[passing_networks_data["team_name"] == team]

        max_round = matches_data["round"].max()

        create_goal_network_plot(team_data, team, league_display, season_display, max_round)

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