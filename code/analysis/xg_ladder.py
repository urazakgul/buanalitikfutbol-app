import os
import pandas as pd
import numpy as np
import streamlit as st
from code.utils.helpers import add_download_button, load_filtered_json_files
from config import PLOT_STYLE
from adjustText import adjust_text
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_xg_ladder_plot(filtered_matches, shot_maps_data, season, league_display, season_display, home_team, away_team, selected_round):

    formatted_season = f"{season[:2]}/{season[2:]}"

    goal_counts = shot_maps_data[
        (shot_maps_data["home_team"] == home_team) &
        (shot_maps_data["away_team"] == away_team) &
        (shot_maps_data["season"] == formatted_season) &
        (shot_maps_data["round"] == selected_round)
    ]

    home_team_goals = goal_counts[(goal_counts["team_name"] == home_team) & (goal_counts["shot_type"] == "goal")].shape[0]
    away_team_goals = goal_counts[(goal_counts["team_name"] == away_team) & (goal_counts["shot_type"] == "goal")].shape[0]
    match_score = f"{home_team_goals} - {away_team_goals}"

    filtered_shotmaps_data = shot_maps_data[
        (shot_maps_data["home_team"] == home_team) &
        (shot_maps_data["away_team"] == away_team) &
        (shot_maps_data["season"] == formatted_season) &
        (shot_maps_data["round"] == selected_round)
    ].reset_index(drop=True)

    injury_time_1 = filtered_matches[
        (filtered_matches["home_team"] == home_team) &
        (filtered_matches["away_team"] == away_team) &
        (filtered_matches["season"] == formatted_season) &
        (filtered_matches["round"] == selected_round)
    ]["injury_time_1"].iloc[0]
    injury_time_2 = filtered_matches[
        (filtered_matches["home_team"] == home_team) &
        (filtered_matches["away_team"] == away_team) &
        (filtered_matches["season"] == formatted_season) &
        (filtered_matches["round"] == selected_round)
    ]["injury_time_2"].iloc[0]

    xg_max_time_firsthalf = filtered_shotmaps_data[filtered_shotmaps_data["period"] == "First Half"]["net_time"].iloc[0]
    xg_max_time_secondhalf = filtered_shotmaps_data[filtered_shotmaps_data["period"] == "Second Half"]["net_time"].iloc[0]

    xg_max_time_firsthalf = int(max(xg_max_time_firsthalf, (45 + injury_time_1)))
    xg_time_series_firsthalf = pd.DataFrame({"net_full_time": list(range(1, xg_max_time_firsthalf + 1))})

    xg_max_time_secondhalf = int(max(xg_max_time_secondhalf, (90 + injury_time_2)))
    xg_time_series_secondhalf = pd.DataFrame({"net_full_time": list(range(45, xg_max_time_secondhalf + 1))})

    cum_xg_home_team = filtered_shotmaps_data[filtered_shotmaps_data["team_name"] == home_team]
    cum_xg_home_team_first = cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]
    cum_xg_home_team_first = cum_xg_home_team_first.merge(
        xg_time_series_firsthalf,
        how="right",
        left_on="net_time",
        right_on="net_full_time"
    )
    cum_xg_home_team_first["period"] = cum_xg_home_team_first["period"].fillna("First Half")
    cum_xg_home_team_second = cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]
    cum_xg_home_team_second = cum_xg_home_team_second.merge(
        xg_time_series_secondhalf,
        how="right",
        left_on="net_time",
        right_on="net_full_time"
    )
    cum_xg_home_team_second["period"] = cum_xg_home_team_second["period"].fillna("Second Half")
    cum_xg_home_team = pd.concat([cum_xg_home_team_first,cum_xg_home_team_second], ignore_index=True)
    cum_xg_home_team["xg"] = cum_xg_home_team["xg"].fillna(0)
    cum_xg_home_team["xg_cum"] = cum_xg_home_team["xg"].cumsum()
    cum_xg_home_team["team_name"] = home_team

    cum_xg_away_team = filtered_shotmaps_data[filtered_shotmaps_data["team_name"] == away_team]
    cum_xg_away_team_first = cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]
    cum_xg_away_team_first = cum_xg_away_team_first.merge(
        xg_time_series_firsthalf,
        how="right",
        left_on="net_time",
        right_on="net_full_time"
    )
    cum_xg_away_team_first["period"] = cum_xg_away_team_first["period"].fillna("First Half")
    cum_xg_away_team_second = cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]
    cum_xg_away_team_second = cum_xg_away_team_second.merge(
        xg_time_series_secondhalf,
        how="right",
        left_on="net_time",
        right_on="net_full_time"
    )
    cum_xg_away_team_second["period"] = cum_xg_away_team_second["period"].fillna("Second Half")
    cum_xg_away_team = pd.concat([cum_xg_away_team_first,cum_xg_away_team_second], ignore_index=True)
    cum_xg_away_team["xg"] = cum_xg_away_team["xg"].fillna(0)
    cum_xg_away_team["xg_cum"] = cum_xg_away_team["xg"].cumsum()
    cum_xg_away_team["team_name"] = away_team

    home_team_score_str, away_team_score_str = match_score.split("-")
    home_team_score = int(home_team_score_str.strip())
    away_team_score = int(away_team_score_str.strip())

    fig, axs = plt.subplots(1, 2, figsize=(14, 8), sharey=True)

    axs[0].step(
        cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["net_full_time"],
        cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["xg_cum"],
        label=f"{home_team}",
        color="darkred",
        linewidth=3,
        where="post"
    )
    axs[0].step(
        cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["net_full_time"],
        cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["xg_cum"],
        label=f"{away_team}",
        color="darkblue",
        linewidth=3,
        where="post"
    )

    axs[0].set_xticks([15, 30, 45])
    axs[0].set_xticklabels([15, 30, 45])

    min_time_firsthalf = min(
        cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["net_full_time"].min(),
        cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["net_full_time"].min()
    )
    max_time_firsthalf = max(
        cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["net_full_time"].max(),
        cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["net_full_time"].max()
    )
    all_times_firsthalf = np.arange(min_time_firsthalf, max_time_firsthalf + 1)

    home_xg_interp_firsthalf = np.interp(
        all_times_firsthalf,
        cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["net_full_time"],
        cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["xg_cum"],
        left=0,
        right=cum_xg_home_team[cum_xg_home_team["period"] == "First Half"]["xg_cum"].iloc[-1]
    )
    away_xg_interp_firsthalf = np.interp(
        all_times_firsthalf,
        cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["net_full_time"],
        cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["xg_cum"],
        left=0,
        right=cum_xg_away_team[cum_xg_away_team["period"] == "First Half"]["xg_cum"].iloc[-1]
    )

    all_times_firsthalf_repeated = np.repeat(all_times_firsthalf, 2)[1:]
    home_xg_interp_firsthalf_repeated = np.repeat(home_xg_interp_firsthalf, 2)[:-1]
    away_xg_interp_firsthalf_repeated = np.repeat(away_xg_interp_firsthalf, 2)[:-1]

    axs[0].fill_between(
        all_times_firsthalf_repeated,
        home_xg_interp_firsthalf_repeated,
        away_xg_interp_firsthalf_repeated,
        where=(home_xg_interp_firsthalf_repeated > away_xg_interp_firsthalf_repeated),
        color="darkred",
        alpha=0.3
    )
    axs[0].fill_between(
        all_times_firsthalf_repeated,
        home_xg_interp_firsthalf_repeated,
        away_xg_interp_firsthalf_repeated,
        where=(away_xg_interp_firsthalf_repeated > home_xg_interp_firsthalf_repeated),
        color="darkblue",
        alpha=0.3
    )

    axs[0].axvline(x=xg_max_time_firsthalf, color="black", linestyle="--", linewidth=1.5)
    axs[0].set_title("İlk Yarı", fontsize=16)
    axs[0].set_ylabel("Kümülatif xG", fontsize=16, labelpad=20)
    axs[0].set_xlim(left=1)
    axs[0].grid(True)

    axs[1].step(
        cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["net_full_time"],
        cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["xg_cum"],
        color="darkred",
        linewidth=3,
        where="post"
    )
    axs[1].step(
        cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["net_full_time"],
        cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["xg_cum"],
        color="darkblue",
        linewidth=3,
        where="post"
    )

    axs[1].set_xticks([45, 60, 75, 90])
    axs[1].set_xticklabels([45, 60, 75, 90])

    min_time_secondhalf = min(
        cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["net_full_time"].min(),
        cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["net_full_time"].min()
    )
    max_time_secondhalf = max(
        cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["net_full_time"].max(),
        cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["net_full_time"].max()
    )
    all_times_secondhalf = np.arange(min_time_secondhalf, max_time_secondhalf + 1)

    home_xg_interp_secondhalf = np.interp(
        all_times_secondhalf,
        cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["net_full_time"],
        cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["xg_cum"],
        left=0,
        right=cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["xg_cum"].iloc[-1]
    )
    away_xg_interp_secondhalf = np.interp(
        all_times_secondhalf,
        cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["net_full_time"],
        cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["xg_cum"],
        left=0,
        right=cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["xg_cum"].iloc[-1]
    )

    all_times_secondhalf_repeated = np.repeat(all_times_secondhalf, 2)[1:]
    home_xg_interp_secondhalf_repeated = np.repeat(home_xg_interp_secondhalf, 2)[:-1]
    away_xg_interp_secondhalf_repeated = np.repeat(away_xg_interp_secondhalf, 2)[:-1]

    axs[1].fill_between(
        all_times_secondhalf_repeated,
        home_xg_interp_secondhalf_repeated,
        away_xg_interp_secondhalf_repeated,
        where=(home_xg_interp_secondhalf_repeated > away_xg_interp_secondhalf_repeated),
        color="darkred",
        alpha=0.3
    )
    axs[1].fill_between(
        all_times_secondhalf_repeated,
        home_xg_interp_secondhalf_repeated,
        away_xg_interp_secondhalf_repeated,
        where=(away_xg_interp_secondhalf_repeated > home_xg_interp_secondhalf_repeated),
        color="darkblue",
        alpha=0.3
    )

    axs[1].axvline(x=45, color="black", linestyle="--", linewidth=1.5)
    axs[1].set_title("İkinci Yarı", fontsize=16)
    axs[1].set_xlim(left=44)
    axs[1].grid(True)

    home_final_xg_secondhalf = cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"]["xg_cum"].iloc[-1]
    away_final_xg_secondhalf = cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"]["xg_cum"].iloc[-1]

    axs[1].text(
        max_time_secondhalf + 1,
        home_final_xg_secondhalf + 0,
        f"{home_final_xg_secondhalf:.2f}",
        color="darkred",
        fontsize=16,
        va="center"
    )
    axs[1].text(
        max_time_secondhalf + 1,
        away_final_xg_secondhalf + 0,
        f"{away_final_xg_secondhalf:.2f}",
        color="darkblue",
        fontsize=16,
        va="center"
    )

    texts_firsthalf = []
    for team_data, team_color, team_label, ax in [
        (cum_xg_home_team[cum_xg_home_team["period"] == "First Half"], "darkred", home_team, axs[0]),
        (cum_xg_away_team[cum_xg_away_team["period"] == "First Half"], "darkblue", away_team, axs[0])
    ]:
        goals = team_data[team_data["shot_type"] == "goal"]
        ax.scatter(
            goals["net_full_time"],
            goals["xg_cum"],
            color=team_color,
            marker="o",
            edgecolor=team_color,
            linewidths=4,
            alpha=0.7,
            s=200
        )
        for _, row in goals.iterrows():
            player_name = row["player_name"]
            if row["goal_type"] == "own":
                player_name += " (KK)"
            text = ax.text(
                row["net_full_time"] - 9,
                row["xg_cum"] + 0.12,
                player_name,
                fontsize=12
            )
            texts_firsthalf.append(text)

    adjust_text(texts_firsthalf, arrowprops=dict(arrowstyle="-", color="gray", lw=1), ax=axs[0])

    texts_secondhalf = []
    for team_data, team_color, team_label, ax in [
        (cum_xg_home_team[cum_xg_home_team["period"] == "Second Half"], "darkred", home_team, axs[1]),
        (cum_xg_away_team[cum_xg_away_team["period"] == "Second Half"], "darkblue", away_team, axs[1])
    ]:
        goals = team_data[team_data["shot_type"] == "goal"]
        ax.scatter(
            goals["net_full_time"],
            goals["xg_cum"],
            color=team_color,
            marker="o",
            edgecolor=team_color,
            linewidths=4,
            alpha=0.7,
            s=200
        )
        for _, row in goals.iterrows():
            player_name = row["player_name"]
            if row["goal_type"] == "own":
                player_name += " (KK)"
            text = ax.text(
                row["net_full_time"] -9,
                row["xg_cum"] + 0.12,
                player_name,
                fontsize=12
            )
            texts_secondhalf.append(text)

    adjust_text(texts_secondhalf, arrowprops=dict(arrowstyle="-", color="gray", lw=1), ax=axs[1])

    fig.subplots_adjust(wspace=0.05)
    fig.suptitle(
        f"{league_display} {season_display} Sezonu {selected_round}. Hafta xG Merdiveni",
        fontsize=22
    )
    fig.supxlabel("Dakika", fontsize=16, x=0.5, y=-0.005)

    fig.text(
        0.99, -0.07,
        "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com",
        horizontalalignment="right",
        verticalalignment="bottom",
        fontsize=12,
        fontstyle="italic",
        color="gray"
    )

    fig.legend(
        loc="lower center",
        ncol=2,
        fontsize="large",
        bbox_to_anchor=(0.5, -0.09)
    )

    match_score = f"{home_team} {home_team_score} - {away_team_score} {away_team}"
    fig.text(0.5, 0.9, match_score, ha="center", va="center", fontsize=16)

    axs[0].grid(True, alpha=0.3)
    axs[1].grid(True, alpha=0.3)

    file_name = f"{league_display}_{season_display}_{selected_round}_{home_team}-{away_team}.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, selected_round, home_team, away_team):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league, season)

        filtered_matches = matches_data[
            (matches_data["round"] == selected_round) &
            (matches_data["home_team"] == home_team) &
            (matches_data["away_team"] == away_team)
        ]

        shot_maps_data = shot_maps_data.merge(
            filtered_matches,
            on=["tournament","season","round","game_id"]
        )
        shot_maps_data["team_name"] = shot_maps_data.apply(
            lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1
        )
        shot_maps_data["period"] = shot_maps_data["time"].apply(lambda x: "First Half" if x <= 45 else "Second Half")
        shot_maps_data["injury_time_1"] = shot_maps_data["injury_time_1"].fillna(0)
        shot_maps_data["injury_time_2"] = shot_maps_data["injury_time_2"].fillna(0)
        shot_maps_data["added_time"] = shot_maps_data["added_time"].fillna(0)
        shot_maps_data["net_time"] = shot_maps_data["time"] + shot_maps_data["added_time"]

        create_xg_ladder_plot(filtered_matches, shot_maps_data, season, league_display, season_display, home_team, away_team, selected_round)

    except Exception as e:
        st.error(f"Uygun veri bulunamadı. {e}")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/buanalitikfutbol-app/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )