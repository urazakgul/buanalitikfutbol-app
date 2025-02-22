import os
import pandas as pd
import streamlit as st
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer, turkish_upper, sort_turkish
from config import PLOT_STYLE, LEAGUE_COUNTRY_LOOKUP
from matplotlib.ticker import MultipleLocator
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_win_rate_plot(ts_df_with_location, league, season, league_display, season_display, last_round):

    global_x_min = ts_df_with_location["week"].min()
    global_x_max = ts_df_with_location["week"].max()
    global_y_min = 0
    global_y_max = 100

    sorted_teams = sort_turkish(pd.DataFrame({'team': ts_df_with_location['team'].unique()}), column="team")["team"].tolist()

    fig, axes = plt.subplots(
        nrows=(len(sorted_teams) + 3) // 4,
        ncols=4,
        figsize=(20, 5 * ((len(sorted_teams) + 3) // 4))
    )
    axes = axes.flatten()

    for i, team in enumerate(sorted_teams):
        team_data = ts_df_with_location[ts_df_with_location["team"] == team].copy()
        ax = axes[i]

        home_data = team_data[team_data["location"] == "home"]
        away_data = team_data[team_data["location"] == "away"]

        ax.plot(home_data["week"], home_data["win_rate"], label="Home Win Rate", color="blue", marker="o")
        ax.plot(away_data["week"], away_data["win_rate"], label="Away Win Rate", color="darkred", marker="o")

        ax.set_title(turkish_upper(team), pad=35)
        ax.grid(True)

        latest_home_rate = home_data["win_rate"].iloc[-1] if not home_data.empty else 0
        latest_away_rate = away_data["win_rate"].iloc[-1] if not away_data.empty else 0
        ax.text(
            x=0.5,
            y=1.05,
            s=f"İç Saha: %{latest_home_rate:.1f}, Deplasman: %{latest_away_rate:.1f}",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=14
        )

        ax.xaxis.set_major_locator(MultipleLocator(3))
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}"))

        ax.set_xlim(global_x_min - 0.5, global_x_max + 0.5)
        ax.set_ylim(global_y_min - 5, global_y_max + 5)

        ax.grid(True, linestyle="--", alpha=0.7)

    for j in range(len(sorted_teams), len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(
        f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların Kümülatif Kazanma Oranı",
        fontsize=24,
        fontweight="bold",
        y=1.00
    )

    fig.text(0.5, 0.04, "Hafta", ha="center", va="center", fontsize=16)
    fig.text(-0.04, 0.5, "Kümülatif Kazanma Oranı", ha="center", va="center", rotation="vertical", fontsize=16)

    fig.legend(
        ["İç Saha", "Deplasman"],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.97),
        frameon=False,
        ncol=2,
        fontsize=16
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    add_footer(fig, y=0.01, fontsize=14, extra_text="Kazanma oranı: (Galibiyet Sayısı + Beraberlik Sayısı / 2) / Toplam Maç Sayısı × 100")

    file_name = f"{league_display}_{season_display}_kumulatif_kazanma_orani.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")

        match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        shots_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "shots_data")

        match_data_df = match_data_df[match_data_df["status"].isin(["Ended","Retired"])]
        match_data_df = match_data_df[["tournament", "season", "week", "game_id", "home_team", "away_team"]]

        shots_data_df = shots_data_df.merge(
            match_data_df,
            on=["tournament", "season", "week", "game_id"],
            how="left"
        )
        shots_data_df["team_name"] = shots_data_df.apply(
            lambda row: row["home_team"] if row["is_home"] else row["away_team"], axis=1
        )
        shots_data_df["is_goal"] = shots_data_df["shot_type"].apply(lambda x: 1 if x == "goal" else 0)
        shot_maps_data_goal = shots_data_df[shots_data_df['is_goal'] == 1]
        shot_maps_data_goal = shot_maps_data_goal[["tournament", "season", "week", "game_id", "team_name"]]

        match_data_df["home_score"] = 0
        match_data_df["away_score"] = 0

        match_data_df = match_data_df.sort_values(by=["week"], ascending=[True])

        for i, row in match_data_df.iterrows():
            home_team_shots = len(shot_maps_data_goal[(shot_maps_data_goal["game_id"] == row["game_id"]) & (shot_maps_data_goal["team_name"] == row["home_team"])])
            away_team_shots = len(shot_maps_data_goal[(shot_maps_data_goal["game_id"] == row["game_id"]) & (shot_maps_data_goal["team_name"] == row["away_team"])])
            match_data_df.at[i, "home_score"] = home_team_shots
            match_data_df.at[i, "away_score"] = away_team_shots

        team_stats = {}
        time_series_data_with_location = []

        for _, row in match_data_df.iterrows():
            for team, location in zip([row['home_team'], row['away_team']], ['home', 'away']):
                if team not in team_stats:
                    team_stats[team] = {
                        'home_wins': 0, 'home_draws': 0, 'home_losses': 0, 'home_games': 0,
                        'away_wins': 0, 'away_draws': 0, 'away_losses': 0, 'away_games': 0,
                    }

                if location == 'home':
                    team_stats[team]['home_games'] += 1
                    if row['home_score'] > row['away_score']:
                        team_stats[team]['home_wins'] += 1
                    elif row['home_score'] < row['away_score']:
                        team_stats[team]['home_losses'] += 1
                    else:
                        team_stats[team]['home_draws'] += 1
                elif location == 'away':
                    team_stats[team]['away_games'] += 1
                    if row['away_score'] > row['home_score']:
                        team_stats[team]['away_wins'] += 1
                    elif row['away_score'] < row['home_score']:
                        team_stats[team]['away_losses'] += 1
                    else:
                        team_stats[team]['away_draws'] += 1

                if location == 'home':
                    home_games = team_stats[team]['home_games']
                    home_wins = team_stats[team]['home_wins']
                    home_draws = team_stats[team]['home_draws']
                    home_win_rate = (home_wins + 0.5 * home_draws) / home_games * 100 if home_games > 0 else 0
                    time_series_data_with_location.append({
                        'team': team,
                        'week': row['week'],
                        'location': location,
                        'win_rate': home_win_rate
                    })
                elif location == 'away':
                    away_games = team_stats[team]['away_games']
                    away_wins = team_stats[team]['away_wins']
                    away_draws = team_stats[team]['away_draws']
                    away_win_rate = (away_wins + 0.5 * away_draws) / away_games * 100 if away_games > 0 else 0
                    time_series_data_with_location.append({
                        'team': team,
                        'week': row['week'],
                        'location': location,
                        'win_rate': away_win_rate
                    })

        ts_df_with_location = pd.DataFrame(time_series_data_with_location)

        last_round = match_data_df["week"].max()

        create_win_rate_plot(ts_df_with_location, league, season, league_display, season_display, last_round)

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