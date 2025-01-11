import os
import pandas as pd
import streamlit as st
from config import team_list_by_season, PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer, turkish_english_lower
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_xg_cum_actual_plot(xg_goal_teams, league, season, league_display, season_display, teams, last_round, plot_type):

    global_x_min = xg_goal_teams["round"].min()
    global_x_max = xg_goal_teams["round"].max()

    if plot_type == "Kümülatif xG ve Gol (Haftalık Seri)":
        global_y_min = min(xg_goal_teams["cumulative_goal_count"].min(), xg_goal_teams["cumulative_total_xg"].min())
        global_y_max = max(xg_goal_teams["cumulative_goal_count"].max(), xg_goal_teams["cumulative_total_xg"].max())
    elif plot_type == "Kümülatif xG ve Gol Farkı (Haftalık Seri)":
        global_y_min = xg_goal_teams["cum_goal_xg_diff"].min()
        global_y_max = xg_goal_teams["cum_goal_xg_diff"].max()

    fig, axes = plt.subplots(
        nrows=(len(teams) + 3) // 4,
        ncols=4,
        figsize=(20, 5 * ((len(teams) + 3) // 4))
    )
    axes = axes.flatten()

    for i, team in enumerate(teams):
        team_data = xg_goal_teams[xg_goal_teams["team_name"] == team].copy()

        ax = axes[i]

        if plot_type == "Kümülatif xG ve Gol (Haftalık Seri)":
            ax.plot(team_data["round"], team_data["cumulative_goal_count"], label="Kümülatif Gol", color="blue")
            ax.plot(team_data["round"], team_data["cumulative_total_xg"], label="Kümülatif xG", color="red")
            ax.fill_between(
                team_data["round"],
                team_data["cumulative_goal_count"],
                team_data["cumulative_total_xg"],
                where=(team_data["cumulative_goal_count"] >= team_data["cumulative_total_xg"]),
                color="blue",
                alpha=0.3,
                interpolate=True
            )
            ax.fill_between(
                team_data["round"],
                team_data["cumulative_goal_count"],
                team_data["cumulative_total_xg"],
                where=(team_data["cumulative_goal_count"] < team_data["cumulative_total_xg"]),
                color="red",
                alpha=0.3,
                interpolate=True
            )
            fig.legend(
                ["Kümülatif Gol", "Kümülatif xG"],
                loc="upper center",
                bbox_to_anchor=(0.5, 1.00),
                frameon=False,
                ncol=2,
                fontsize="large"
            )
            fig.suptitle(
                f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımlara Göre Kümülatif xG ve Gol",
                fontsize=24,
                fontweight="bold",
                y=1.02
            )
            ax.grid(True, linestyle="--", alpha=0.7)
        elif plot_type == "Kümülatif xG ve Gol Farkı (Haftalık Seri)":
            diff = team_data["cumulative_goal_count"] - team_data["cumulative_total_xg"]
            team_data["diff"] = diff.round(5)
            for i in range(len(team_data) - 1):
                x = team_data["round"].iloc[i:i+2]
                y = team_data["diff"].iloc[i:i+2]

                if y.mean() >= 0:
                    ax.plot(x, y, color="darkblue", linewidth=3)
                else:
                    ax.plot(x, y, color="darkred", linewidth=3)

            ax.fill_between(
                team_data["round"],
                0,
                team_data["diff"],
                where=(team_data["diff"] >= 0),
                color="blue",
                alpha=0.3,
                interpolate=True
            )
            ax.fill_between(
                team_data["round"],
                0,
                team_data["diff"],
                where=(team_data["diff"] < 0),
                color="red",
                alpha=0.3,
                interpolate=True
            )

            positive_patch = mpatches.Patch(color="darkblue", label="Gol Sayısı xG'nin Üstünde")
            negative_patch = mpatches.Patch(color="darkred", label="Gol Sayısı xG'nin Altında")

            fig.legend(
                handles=[positive_patch, negative_patch],
                loc="upper center",
                bbox_to_anchor=(0.5, 1.00),
                frameon=False,
                ncol=2,
                fontsize="large"
            )

            fig.suptitle(
                f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımlara Göre Kümülatif xG ile Gol Farkı",
                fontsize=24,
                fontweight="bold",
                y=1.02
            )
            ax.grid(True, linestyle="--", alpha=0.7)

        ax.set_title(team)

        ax.xaxis.set_major_locator(MultipleLocator(3))
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}"))

        ax.set_xlim(global_x_min, global_x_max)
        ax.set_ylim(global_y_min, global_y_max)
        ax.set_title(team)

    for j in range(len(teams), len(axes)):
        fig.delaxes(axes[j])

    fig.text(0.5, 0.04, "Hafta", ha="center", va="center", fontsize="large")
    add_footer(fig, y=0.02, fontsize=12)
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(plot_type)}.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, plot_type):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        games_data = load_filtered_json_files(directories, "games", league_display, season_display)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league_display, season_display)
        points_table_data = load_filtered_json_files(directories, "points_table", league_display, season_display)

        points_table_data = points_table_data[points_table_data["category"] == "Total"][["team_name", "scores_for", "scores_against"]]

        shot_maps_data = shot_maps_data.merge(games_data, on=["tournament", "season", "round", "game_id"])
        shot_maps_data["team_name"] = shot_maps_data.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)

        xg_by_team = shot_maps_data.groupby(["team_name", "round"])["xg"].sum().reset_index(name="total_xg")
        xg_by_team_pivot = xg_by_team.pivot(index="team_name", columns="round", values="total_xg").fillna(0)
        xg_by_team_long = xg_by_team_pivot.reset_index().melt(id_vars="team_name", var_name="round", value_name="total_xg")

        goal_shots = shot_maps_data[shot_maps_data["shot_type"] == "goal"]
        goal_shots_by_team = goal_shots.groupby(["team_name", "round"]).size().reset_index(name="goal_count")
        goal_shots_by_team_pivot = goal_shots_by_team.pivot(index="team_name", columns="round", values="goal_count").fillna(0)
        goal_shots_by_team_long = goal_shots_by_team_pivot.reset_index().melt(id_vars="team_name", var_name="round", value_name="goal_count")

        xg_goal_teams = pd.merge(xg_by_team_long, goal_shots_by_team_long, on=["team_name", "round"])
        xg_goal_teams = xg_goal_teams.sort_values(by=["team_name", "round"])
        xg_goal_teams["cumulative_total_xg"] = xg_goal_teams.groupby("team_name")["total_xg"].cumsum()
        xg_goal_teams["cumulative_goal_count"] = xg_goal_teams.groupby("team_name")["goal_count"].cumsum()
        xg_goal_teams["cum_goal_xg_diff"] = xg_goal_teams["cumulative_goal_count"] - xg_goal_teams["cumulative_total_xg"]

        xg_goal_teams["cumulative_goal_count"] = pd.to_numeric(xg_goal_teams["cumulative_goal_count"], errors="coerce")
        xg_goal_teams["cumulative_total_xg"] = pd.to_numeric(xg_goal_teams["cumulative_total_xg"], errors="coerce")
        xg_goal_teams["round"] = pd.to_numeric(xg_goal_teams["round"], errors="coerce")

        xg_goal_teams = xg_goal_teams.dropna(subset=["cumulative_goal_count", "cumulative_total_xg", "round"])

        teams = [team for team in team_list_by_season[season_display] if team in xg_goal_teams["team_name"].unique()]

        last_round = games_data["round"].max()

        if plot_type == "Kümülatif xG ve Gol (Haftalık Seri)":
            create_xg_cum_actual_plot(xg_goal_teams, league, season, league_display, season_display, teams, last_round, plot_type="Kümülatif xG ve Gol (Haftalık Seri)")
        elif plot_type == "Kümülatif xG ve Gol Farkı (Haftalık Seri)":
            create_xg_cum_actual_plot(xg_goal_teams, league, season, league_display, season_display, teams, last_round, plot_type="Kümülatif xG ve Gol Farkı (Haftalık Seri)")

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