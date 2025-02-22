import os
import streamlit as st
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer
from config import PLOT_STYLE, LEAGUE_COUNTRY_LOOKUP
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_xg_defence_efficiency_plot(team_opponent_df, league, season, league_display, season_display, last_round):

    fig, ax = plt.subplots(figsize=(12, 10))

    ax.scatter(
        team_opponent_df["non_penalty_xg_per_shot_against"],
        team_opponent_df["non_penalty_shot_conversion_against"],
        alpha=0
    )

    mean_non_penalty_xg_per_shot_against = team_opponent_df["non_penalty_xg_per_shot_against"].mean()
    mean_non_penalty_shot_conversion_against = team_opponent_df["non_penalty_shot_conversion_against"].mean()

    ax.axvline(x=mean_non_penalty_xg_per_shot_against, color="darkblue", linestyle="--", linewidth=2, label="Rakip Şut Başına Beklenen Gol (xG) (Ortalama)")
    ax.axhline(y=mean_non_penalty_shot_conversion_against, color="darkred", linestyle="--", linewidth=2, label="Rakip Şut Dönüşüm Oranı (%) (Ortalama)")

    def getImage(path):
        return OffsetImage(plt.imread(path), zoom=.3, alpha=1)

    for index, row in team_opponent_df.iterrows():
        logo_path = f"./imgs/team_logo/{row['team_name']}.png"
        ab = AnnotationBbox(getImage(logo_path), (row["non_penalty_xg_per_shot_against"], row["non_penalty_shot_conversion_against"]), frameon=False)
        ax.add_artist(ab)

    ax.set_xlabel("Rakip Şut Başına Beklenen Gol (xG) (Penaltı Hariç) (Daha küçük daha iyi)", labelpad=20, fontsize=12)
    ax.set_ylabel("Rakip Şut Dönüşüm Oranı (%) (Penaltı Hariç) (Daha küçük daha iyi)", labelpad=20, fontsize=12)
    ax.set_title(
        f"{league} {season} Sezonu Geçmiş {last_round} Haftada Rakip Şut Kalitesi ve Şut Dönüşüm Oranı",
        fontsize=16,
        fontweight="bold",
        pad=40
    )
    ax.grid(True, linestyle="--", alpha=0.7)

    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.05),
        ncol=2,
        fontsize=8,
        frameon=False
    )

    add_footer(fig)

    file_name = f"{league_display}_{season_display}_{last_round}_rakip_sut_kalitesi_ve_sut_donusum_orani.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")

        match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        shots_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "shots_data")

        match_data_df = match_data_df[match_data_df["status"].isin(["Ended","Retired"])]

        shots_data_df = shots_data_df.merge(match_data_df, on=["tournament", "season", "week", "game_id"])
        shots_data_df["team_name"] = shots_data_df.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)
        shots_data_df = shots_data_df[shots_data_df["goal_type"] != "penalty"]
        shots_data_df["is_goal"] = shots_data_df["shot_type"].apply(lambda x: 1 if x == "goal" else 0)

        xg_xga_df = shots_data_df.groupby(["game_id", "team_name"]).agg(
            xg=("xg", "sum"),
            shots=("xg", "count"),
            goals=("is_goal", "sum")
        ).reset_index()

        for game_id in xg_xga_df["game_id"].unique():
            game_data = xg_xga_df[xg_xga_df["game_id"] == game_id]
            match_info = match_data_df[match_data_df["game_id"] == game_id]

            if not match_info.empty:
                home_team = match_info["home_team"].values[0]
                away_team = match_info["away_team"].values[0]

                for index, row in game_data.iterrows():
                    opponent_data = game_data[game_data["team_name"] != row["team_name"]]

                    if not opponent_data.empty:
                        opponent_xg = opponent_data["xg"].values[0]
                        opponent_shots = opponent_data["shots"].values[0]
                        opponent_goals = opponent_data["goals"].values[0]

                        xg_xga_df.at[index, "xga"] = opponent_xg
                        xg_xga_df.at[index, "opponent_shots"] = opponent_shots
                        xg_xga_df.at[index, "opponent_goals"] = opponent_goals
                    else:
                        if row["team_name"] not in [home_team, away_team]:
                            xg_xga_df.at[index, "xga"] = 0
                            xg_xga_df.at[index, "opponent_shots"] = 0
                            xg_xga_df.at[index, "opponent_goals"] = 0

        team_opponent_df = xg_xga_df.groupby("team_name").agg(
            xg=("xg", "sum"),
            xgConceded=("xga", "sum"),
            shots=("shots", "sum"),
            goals=("goals", "sum"),
            opponent_shots=("opponent_shots", "sum"),
            opponent_goals=("opponent_goals", "sum")
        ).reset_index()

        team_opponent_df['non_penalty_xg_per_shot_against'] = team_opponent_df['xgConceded'] / team_opponent_df['opponent_shots']
        team_opponent_df['non_penalty_shot_conversion_against'] = (team_opponent_df['opponent_goals'] / team_opponent_df['opponent_shots']) * 100

        last_round = match_data_df["week"].max()

        create_xg_defence_efficiency_plot(team_opponent_df, league, season, league_display, season_display, last_round)

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