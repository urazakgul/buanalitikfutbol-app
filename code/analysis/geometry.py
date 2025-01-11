import os
import numpy as np
import pandas as pd
import streamlit as st
from config import change_situations, PLOT_STYLE
from code.utils.helpers import add_download_button, add_footer, load_filtered_json_files, turkish_upper, turkish_english_lower
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def calculate_mean_distance(player_positions):
    distances = []
    for i, player1 in player_positions.iterrows():
        for j, player2 in player_positions.iterrows():
            if i != j:
                distance = np.sqrt((player1["x"] - player2["x"])**2 + (player1["y"] - player2["y"])**2)
                distances.append(distance)
    return np.mean(distances) if distances else None

def calculate_horizontal_vertical_spread(player_positions):
    horizontal_spread = player_positions["x"].std()
    vertical_spread = player_positions["y"].std()
    return horizontal_spread, vertical_spread

def create_geometry_plot(overall_data, category, league, season, league_display, season_display, last_round):
    if category == "Kompaktlık":
        metric = "mean_distance"
        xlabel = "Kompaktlık (Ortalama)"
    elif category == "Yatay Yayılım":
        metric = "horizontal_spread"
        xlabel = "Yatay Yayılım (Standart Sapma)"
    elif category == "Dikey Yayılım":
        metric = "vertical_spread"
        xlabel = "Dikey Yayılım (Standart Sapma)"

    team_means = overall_data.groupby("team_name")[metric].mean().sort_values(ascending=False)
    sorted_teams = team_means.index.tolist()

    fig, ax = plt.subplots(figsize=(12, 12))
    for team in sorted_teams:
        team_data = overall_data[overall_data["team_name"] == team]

        team_min = team_data[metric].min()
        team_max = team_data[metric].max()
        team_mean = team_data[metric].mean()

        ax.scatter(
            team_data[metric], [team] * len(team_data), color='grey', edgecolors='black', alpha=0.7, s=50
        )

        ax.hlines(y=team, xmin=team_min, xmax=team_max, colors='black', linestyles='-', linewidth=0.5, alpha=0.7)

        ax.scatter(
            [team_min], [team], color='blue', edgecolors='black', alpha=0.7, s=100,
            label='Minimum' if team == sorted_teams[0] else "", zorder=3
        )
        ax.scatter(
            [team_mean], [team], color='orange', edgecolors='black', alpha=0.7, s=100,
            label='Ortalama' if team == sorted_teams[0] else "", zorder=3
        )
        ax.scatter(
            [team_max], [team], color='red', edgecolors='black', alpha=0.7, s=100,
            label='Maksimum' if team == sorted_teams[0] else "", zorder=3
        )

    ax.set_yticks(range(len(sorted_teams)))
    ax.set_yticklabels(sorted_teams, fontsize=9)
    ax.set_title(
        f'{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların {category}',
        fontsize=16,
        fontweight="bold",
        pad=30
    )
    ax.set_xlabel(xlabel, fontsize=12, labelpad=15)
    ax.set_ylabel("")
    ax.legend(
        loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=3, frameon=False, fontsize=8
    )
    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()

    add_footer(fig, y=-0.01)
    file_name = f"{league_display}_{season_display}_{last_round}_{turkish_english_lower(category)}.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(category, league, season, league_display, season_display):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        games_data = load_filtered_json_files(directories, "games", league_display, season_display)
        heat_maps_data = load_filtered_json_files(directories, "heat_maps", league_display, season_display)
        lineups_data = load_filtered_json_files(directories, "lineups", league_display, season_display)
        substitutions_data = load_filtered_json_files(directories, "substitutions", league_display, season_display)

        games_data = games_data[["tournament","season","round","game_id","home_team","away_team"]]
        heat_maps_data = heat_maps_data.groupby(["tournament","season","round","game_id","player_name", "player_id"]).agg({'x': 'mean', 'y': 'mean'}).reset_index()
        lineups_data = lineups_data[["tournament","season","round","game_id","team","player_name", "player_id"]].drop_duplicates()

        final_merged_data = pd.merge(
            pd.merge(
                heat_maps_data,
                lineups_data,
                on=["tournament", "season", "round", "game_id", "player_name", "player_id"]
            ),
            games_data,
            on=["tournament", "season", "round", "game_id"]
        )
        final_merged_data["team_name"] = final_merged_data.apply(lambda row: row["home_team"] if row["team"] == "home" else row["away_team"], axis=1)
        final_merged_data = final_merged_data.drop(columns=["team","home_team","away_team"])

        def check_player_status_and_time(row):
            player_in = substitutions_data[
                (substitutions_data["tournament"] == row["tournament"]) &
                (substitutions_data["season"] == row["season"]) &
                (substitutions_data["round"] == row["round"]) &
                (substitutions_data["game_id"] == row["game_id"]) &
                (substitutions_data["player_in"] == row["player_name"]) &
                (substitutions_data["player_in_id"] == row["player_id"])
            ]
            player_out = substitutions_data[
                (substitutions_data["tournament"] == row["tournament"]) &
                (substitutions_data["season"] == row["season"]) &
                (substitutions_data["round"] == row["round"]) &
                (substitutions_data["game_id"] == row["game_id"]) &
                (substitutions_data["player_out"] == row["player_name"]) &
                (substitutions_data["player_out_id"] == row["player_id"])
            ]

            status = "Starting 11"
            time = None
            if not player_in.empty:
                status = "Subbed in"
                time = player_in['time'].iloc[0]
            elif not player_out.empty:
                status = "Subbed out"
                time = player_out['time'].iloc[0]

            return status, time

        final_merged_data[['status', 'time']] = final_merged_data.apply(
            lambda row: pd.Series(check_player_status_and_time(row)), axis=1
        )

        if category in ["Kompaktlık","Dikey Yayılım","Yatay Yayılım"]:
            results = []
            for (tournament, season, round_, game_id), group in final_merged_data.groupby(["tournament", "season", "round", "game_id"]):
                team_groups = group.groupby("team_name")
                for team_name, team_data in team_groups:
                    time_points = team_data["time"].dropna().sort_values().unique().tolist()
                    max_time = max(time_points + [90])
                    time_points = [0] + time_points + [max_time]

                    active_players = team_data[(team_data["status"] == "Starting 11") | (team_data["status"] == "Subbed out")].copy()

                    if len(active_players) > 1:
                        initial_mean_distance = calculate_mean_distance(active_players)
                        initial_horizontal_spread, initial_vertical_spread = calculate_horizontal_vertical_spread(team_data)
                        results.append({
                            "tournament": tournament,
                            "season": season,
                            "round": round_,
                            "game_id": game_id,
                            "team_name": team_name,
                            "start_time": 0,
                            "end_time": time_points[1],
                            "mean_distance": initial_mean_distance,
                            "horizontal_spread": initial_horizontal_spread,
                            "vertical_spread": initial_vertical_spread,
                            "active_players": active_players["player_name"].tolist()
                        })

                    for start, end in zip(time_points[:-1], time_points[1:]):
                        for _, substitution in team_data[(team_data["time"] > start) & (team_data["time"] <= end)].iterrows():
                            if substitution["status"] == "Subbed in":
                                active_players = pd.concat([active_players, substitution.to_frame().T], ignore_index=True)
                            elif substitution["status"] == "Subbed out":
                                active_players = active_players[active_players["player_id"] != substitution["player_id"]]

                        if len(active_players) > 1:
                            mean_distance = calculate_mean_distance(active_players)
                            horizontal_spread, vertical_spread = calculate_horizontal_vertical_spread(team_data)
                            player_names = active_players["player_name"].tolist()
                            results.append({
                                "tournament": tournament,
                                "season": season,
                                "round": round_,
                                "game_id": game_id,
                                "team_name": team_name,
                                "start_time": start,
                                "end_time": end,
                                "mean_distance": mean_distance,
                                "horizontal_spread": horizontal_spread,
                                "vertical_spread": vertical_spread,
                                "active_players": player_names
                            })

            data = pd.DataFrame(results)
            overall_data = data.groupby(["tournament", "season", "round", "game_id", "team_name"]).agg({
                "mean_distance": "mean",
                "horizontal_spread": "mean",
                "vertical_spread": "mean"
            }).reset_index()

        last_round = games_data['round'].max()

        create_geometry_plot(overall_data, category, league, season, league_display, season_display, last_round)

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