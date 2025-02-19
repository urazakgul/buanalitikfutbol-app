import os
import pandas as pd
import streamlit as st
from config import event_type_translations, event_colors, PLOT_STYLE, LEAGUE_COUNTRY_LOOKUP
from code.utils.helpers import add_download_button, load_filtered_json_files, turkish_upper, turkish_english_lower
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def fill_team_name(df):
    df["team_name"] = df.groupby("id")["team_name"].transform(lambda x: x.ffill().bfill())
    return df

def fill_opponent_team_name(df):
    df["opponent_team_name"] = df.groupby("id")["opponent_team_name"].transform(lambda x: x.ffill().bfill())
    return df

def merge_match_data(match_data_df, shots_data_df):
    filtered_shots = shots_data_df[shots_data_df["shot_type"] == "goal"][[
        "tournament", "season", "week", "game_id", "player_name", "is_home", "goal_type", "xg"
    ]]
    merged_df = match_data_df.merge(filtered_shots, on=["tournament", "season", "week", "game_id"])
    return merged_df[~merged_df["goal_type"].isin(["penalty", "own"])]

def create_goal_network_plot(side_data, league, season, league_display, season_display, team, last_round, plot_type, side):
    if plot_type == "Birleştir":
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

        kde_data = side_data[side_data["event_type"] != "Gol"]
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

        for _, row in side_data.iterrows():
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

        for _, group in side_data.groupby("id"):
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
            f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların Gol Ağları ve Etkin Olduğu Alanlar (Takımın {side})",
            fontsize=10,
            fontweight="bold",
            pad=40
        )
        ax.text(
            0.5, 1.02,
            turkish_upper(team),
            fontsize=10,
            fontweight="bold",
            ha="center",
            va="center",
            transform=ax.transAxes
        )
        fig.suptitle(
            "Veri: SofaScore, Hazırlayan: @urazdev",
            y=0,
            x=0.5,
            fontsize=10,
            fontstyle="italic",
            color="gray"
        )
        file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(team)}_gol_aglari_ve_etkin_oldugu_alanlar_{turkish_english_lower(side)}.png"
    elif plot_type == "Ayrıştır":
        all_rounds = list(range(1, last_round + 1))
        existing_rounds = sorted(side_data["week"].unique())
        missing_rounds = set(all_rounds) - set(existing_rounds)

        for missing_round in missing_rounds:
            empty_data = pd.DataFrame({
                "week": [missing_round],
                "player_x": [None],
                "player_y": [None],
                "event_type": ["Veri Yok"],
                "id": [None]
            })
            side_data = pd.concat([side_data, empty_data], ignore_index=True)

        rounds = sorted(side_data["week"].unique())

        n_cols = 5
        n_rows = -(-len(rounds) // n_cols)

        subplot_width = 4
        subplot_height = 5
        fig_width = n_cols * subplot_width
        fig_height = n_rows * subplot_height

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))
        axes = axes.flatten()

        for i, round_num in enumerate(rounds):
            round_data = side_data[side_data["week"] == round_num]
            ax = axes[i]
            pitch = VerticalPitch(
                pitch_type="opta",
                corner_arcs=True,
                half=False,
                label=False,
                tick=False
            )
            pitch.draw(ax=ax)

            if not round_data.empty and round_data["event_type"].iloc[0] != "Veri Yok":

                for _, row in round_data.iterrows():
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

                for _, group in round_data.groupby("id"):
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
            else:
                ax.text(
                    0.5, 0.5,
                    "Gol ağı bulunmamaktadır.",
                    fontsize=10,
                    ha="center",
                    va="center",
                    transform=ax.transAxes
                )

            ax.set_title(f"{round_num}. Hafta", fontsize=10, fontweight="bold", pad=20)

        for j in range(len(rounds), len(axes)):
            axes[j].axis("off")

        handles = [plt.Line2D([0], [0], marker="o", color=color, markersize=7, linestyle="None") for _, color in event_colors.items()]
        fig.legend(
            handles,
            event_colors.keys(),
            title="",
            loc="lower center",
            bbox_to_anchor=(0.5, 0.03),
            frameon=False,
            ncol=3,
            fontsize=12
        )

        fig.suptitle(
            f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların Gol Ağları (Takımın {side})",
            fontsize=16,
            fontweight="bold",
            y=0.96
        )

        fig.text(
            0.5, 0.93,
            turkish_upper(team),
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="center"
        )

        fig.text(
            0.5, 0.02,
            "Veri: SofaScore, Hazırlayan: @urazdev",
            ha="center",
            fontsize=14,
            fontstyle="italic",
            color="gray"
        )

        file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(team)}_gol_aglari_{turkish_english_lower(side)}.png"

    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, team=None, plot_type=None, side=None):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")

        match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        shots_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "shots_data")
        goal_networks_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "goal_networks_data")

        match_data_df = match_data_df[match_data_df["status"].isin(["Ended","Retired"])]
        match_data_df = match_data_df[["tournament", "season", "week", "game_id", "home_team", "away_team"]]
        match_shots_data_df = merge_match_data(match_data_df, shots_data_df)

        goal_networks_data_df["team_name"] = None
        goal_networks_data_df["opponent_team_name"] = None

        for game_id in match_shots_data_df["game_id"].unique():
            match_data = match_shots_data_df[match_shots_data_df["game_id"] == game_id]
            for _, row in match_data.iterrows():
                team_name = row["home_team"] if row["is_home"] else row["away_team"]
                opponent_team_name = row["away_team"] if row["is_home"] else row["home_team"]

                goal_networks_data_df.loc[
                    (goal_networks_data_df["game_id"] == game_id) &
                    (goal_networks_data_df["player_name"] == row["player_name"]) &
                    (goal_networks_data_df["event_type"] == "goal"), "team_name"
                ] = team_name

                goal_networks_data_df.loc[
                    (goal_networks_data_df["game_id"] == game_id) &
                    (goal_networks_data_df["player_name"] == row["player_name"]) &
                    (goal_networks_data_df["event_type"] == "goal"), "opponent_team_name"
                ] = opponent_team_name

        goal_networks_data_df = fill_team_name(goal_networks_data_df)
        goal_networks_data_df = fill_opponent_team_name(goal_networks_data_df)

        for _, group in goal_networks_data_df.groupby("id"):
            if (group["event_type"] == "goal").any() and group.loc[group["event_type"] == "goal", "goal_shot_x"].iloc[0] != 100:
                goal_networks_data_df.loc[group.index, ["player_x", "player_y"]] = 100 - group[["player_x", "player_y"]]

        goal_networks_data_df = goal_networks_data_df.merge(match_data_df, on=["tournament", "season", "week", "game_id"])
        goal_networks_data_df["event_type"] = goal_networks_data_df["event_type"].replace(event_type_translations)

        if side == "Attığı":
            side_data = goal_networks_data_df[goal_networks_data_df["team_name"] == team]
        elif side == "Yediği":
            side_data = goal_networks_data_df[goal_networks_data_df["opponent_team_name"] == team]

        last_round = match_data_df['week'].max()

        create_goal_network_plot(side_data, league, season, league_display, season_display, team, last_round, plot_type, side)

    except Exception as e:
        st.error(f"Uygun veri bulunamadı.{e}")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/datafc-web/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )