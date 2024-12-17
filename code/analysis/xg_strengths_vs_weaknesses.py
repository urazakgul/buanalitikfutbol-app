import os
import numpy as np
import streamlit as st
from code.utils.helpers import add_download_button, load_filtered_json_files, add_footer
from config import change_situations, change_body_parts, PLOT_STYLE
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_strength_vs_weakness_xg_plot(xg_xga_sw_teams, league_display, season_display, last_round, plot_type, category=None, situation_type=None, body_part_type=None):

    fig, ax = plt.subplots(figsize=(10, 14))

    if plot_type == "Üretilen xG ve Yenen xG (xGA)":
        x_col, xga_col = "xg", "xga"
        title_suffix = "Üretilen xG ve Yenen xG (xGA)"
        label_suffix_1 = "Üretilen xG"
        label_suffix_2 = "Yenen xG (xGA)"
    elif plot_type == "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)":
        x_col, xga_col = "xgDiff", "xgaDiff"
        title_suffix = "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)"
        label_suffix_1 = "Atılan Gol - Üretilen xG"
        label_suffix_2 = "Yenen Gol - Yenen xG (xGA)"

    additional_info = []
    if category:
        catergory_name = "Senaryo" if category == "situation" else "Vücut Parçası"
        additional_info.append(f"{catergory_name}")
    if situation_type:
        additional_info.append(f"{situation_type.capitalize()}")
    if body_part_type:
        additional_info.append(f"{body_part_type.capitalize()}")
    additional_info_text = " | ".join(additional_info)

    xg_xga_sw_teams = xg_xga_sw_teams.sort_values(x_col, ascending=True)

    teams = xg_xga_sw_teams["team_name"]
    xg_values = xg_xga_sw_teams[x_col]
    xga_values = xg_xga_sw_teams[xga_col]

    y = np.arange(len(teams))

    for i, (xg_val, xga_val) in enumerate(zip(xg_values, xga_values)):
        ax.plot([xg_val, xga_val], [y[i], y[i]], color="gray", alpha=0.5, linewidth=1.5)

    for i, val in enumerate(xg_values):
        ax.scatter(val, y[i], color="blue", s=100, label=label_suffix_1 if i == 0 else "")

    for i, val in enumerate(xga_values):
        ax.scatter(val, y[i], color="red", s=100, label=label_suffix_2 if i == 0 else "")

    ax.set_yticks(y)
    ax.set_yticklabels(teams, fontsize=10)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.3)

    ax.set_title(
        f"{league_display} {season_display} Sezonu Geçmiş {last_round} Haftada {title_suffix}\n{additional_info_text}",
        fontsize=14,
        fontweight="bold",
        pad=35
    )
    add_footer(fig)
    ax.set_xlabel("")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.03), ncol=2, frameon=False, fontsize=10)

    plt.tight_layout()

    file_name = f"{league_display}_{season_display}_{last_round}_{plot_type}_{additional_info_text}.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, situation_type=None, body_part_type=None, category=None, plot_type=None):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league, season)

        shot_maps_data = shot_maps_data.merge(matches_data, on=["tournament", "season", "round", "game_id"])
        shot_maps_data["team_name"] = shot_maps_data.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)

        shot_maps_data["situation"] = shot_maps_data["situation"].replace(change_situations)
        shot_maps_data["body_part"] = shot_maps_data["body_part"].replace(change_body_parts)

        if category == "situation" and situation_type is not None:
            filtered_data = shot_maps_data[shot_maps_data["situation"] == situation_type]
            grouping_columns = ["game_id", "team_name", "situation"]
        elif category == "body_part" and body_part_type is not None:
            filtered_data = shot_maps_data[shot_maps_data["body_part"] == body_part_type]
            grouping_columns = ["game_id", "team_name", "body_part"]
        elif category is None:
            filtered_data = shot_maps_data
            grouping_columns = ["game_id", "team_name"]

        xg_xga_df = filtered_data.groupby(grouping_columns)["xg"].sum().reset_index()

        goals_data = filtered_data[filtered_data["shot_type"] == "goal"]
        goals_df = goals_data.groupby(grouping_columns)["shot_type"].count().reset_index()
        goals_df = goals_df.rename(columns={"shot_type": "goals"})

        xg_xga_df = xg_xga_df.merge(goals_df, on=grouping_columns, how="left")
        xg_xga_df["goals"] = xg_xga_df["goals"].fillna(0)

        for game_id in xg_xga_df["game_id"].unique():
            game_data = xg_xga_df[xg_xga_df["game_id"] == game_id]
            match_info = matches_data[matches_data["game_id"] == game_id]

            if not match_info.empty:
                home_team = match_info["home_team"].values[0]
                away_team = match_info["away_team"].values[0]

                for index, row in game_data.iterrows():
                    opponent_xg = game_data.loc[game_data["team_name"] != row["team_name"], "xg"].values
                    opponent_goals = game_data.loc[game_data["team_name"] != row["team_name"], "goals"].values

                    if opponent_xg.size > 0:
                        xg_xga_df.at[index, "xga"] = opponent_xg[0]
                    else:
                        if row["team_name"] not in [home_team, away_team]:
                            xg_xga_df.at[index, "xga"] = 0

                    if opponent_goals.size > 0:
                        xg_xga_df.at[index, "conceded_goals"] = opponent_goals[0]
                    else:
                        if row["team_name"] not in [home_team, away_team]:
                            xg_xga_df.at[index, "conceded_goals"] = 0

        grouping_columns_without_game_id = [col for col in grouping_columns if col != "game_id"]
        team_totals_df = xg_xga_df.groupby(grouping_columns_without_game_id)[["xg", "xga", "goals", "conceded_goals"]].sum().reset_index()

        team_totals_df["xgDiff"] = team_totals_df["goals"] - team_totals_df["xg"]
        team_totals_df["xgaDiff"] = team_totals_df["conceded_goals"] - team_totals_df["xga"]

        last_round = matches_data["round"].max()

        if plot_type == "Üretilen xG ve Yenen xG (xGA)":
            create_strength_vs_weakness_xg_plot(
                team_totals_df,
                league_display,
                season_display,
                last_round,
                plot_type="Üretilen xG ve Yenen xG (xGA)",
                category=category,
                situation_type=situation_type,
                body_part_type=body_part_type
            )
        elif plot_type == "Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)":
            create_strength_vs_weakness_xg_plot(
                team_totals_df,
                league_display,
                season_display,
                last_round,
                plot_type="Üretilen xG ve Yenen xG (xGA) (Gerçekleşen ile Fark)",
                category=category,
                situation_type=situation_type,
                body_part_type=body_part_type
            )

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