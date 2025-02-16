import os
import numpy as np
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from config import PLOT_STYLE, LEAGUE_COUNTRY_LOOKUP
from code.utils.helpers import load_filtered_json_files, add_footer, add_download_button, turkish_english_lower
from code.models.dixon_coles import solve_parameters_cached, dixon_coles_simulate_match_cached
from code.models.bradley_terry import solve_bt_ratings_cached, bt_forecast_match_cached

plt.style.use(PLOT_STYLE)

def create_predictive_analytics_plot(
        model_df,
        selected_model,
        home_team,
        away_team,
        league,
        season,
        league_display,
        season_display,
        last_round,
        max_round_next_day,
        plot_type,
        first_n_goals,
        bt_prob,
        params=None
):

    if selected_model == "Dixon-Coles":
        home_win_prob = np.sum(np.tril(model_df, -1)) * 100
        draw_prob = np.sum(np.diag(model_df)) * 100
        away_win_prob = np.sum(np.triu(model_df, 1)) * 100

        percentage_matrix = model_df * 100

        if plot_type == "Matris":
            fig, ax = plt.subplots(figsize=(10, 8))

            sns.heatmap(
                percentage_matrix,
                annot=True,
                fmt=".1f",
                cmap="Reds",
                cbar=False,
                ax=ax
            )

            ax.set_xlabel(f"{away_team} (Deplasman) Gol Sayısı", labelpad=20, fontsize=12)
            ax.xaxis.set_label_position("top")
            ax.xaxis.tick_top()

            ax.set_ylabel(f"{home_team} (Ev Sahibi) Gol Sayısı", fontsize=12)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

            ax.set_title(
                f"{league} {season} Sezonu {max_round_next_day}. Hafta Maç Sonu Olasılıkları",
                fontsize=16,
                fontweight="bold",
                pad=45
            )

            plt.suptitle(
                f"{home_team} Galibiyeti: %{home_win_prob:.1f} | Beraberlik: %{draw_prob:.1f} | {away_team} Galibiyeti: %{away_win_prob:.1f}",
                fontsize=10,
                y=0.89
            )

            add_footer(fig, x=0.98, y=-0.05, fontsize=8, extra_text=f"{selected_model} sonuçlarıdır.\nGeçmiş {last_round} haftanın verileri kullanılmıştır.")
            plt.tight_layout()

        elif plot_type == "Sıralı":
            bar_data = []
            for i in range(percentage_matrix.shape[0]):
                for j in range(percentage_matrix.shape[1]):
                    bar_data.append({
                        "Home Goals": int(i),
                        "Away Goals": int(j),
                        "Probability": percentage_matrix[i, j]
                    })

            bar_data = pd.DataFrame(bar_data)
            bar_data = bar_data.sort_values("Probability", ascending=False).head(20)

            norm = mcolors.Normalize(vmin=bar_data["Probability"].min(), vmax=bar_data["Probability"].max())
            cmap = plt.get_cmap("Reds")
            colors = [cmap(norm(prob)) for prob in bar_data["Probability"]]

            fig, ax = plt.subplots(figsize=(12, 12))
            ax.barh(
                bar_data.apply(lambda x: f"{int(x['Home Goals'])} - {int(x['Away Goals'])}", axis=1),
                bar_data["Probability"],
                color=colors,
                edgecolor="black"
            )

            ax.set_title(
                f"{league} {season} Sezonu {max_round_next_day}. Hafta Maç Sonu Olasılıkları (Sıralı, İlk 20)",
                fontsize=16,
                fontweight="bold",
                pad=50
            )
            plt.suptitle(
                f"{home_team} - {away_team}",
                fontsize=16,
                fontweight="bold",
                y=0.91
            )
            ax.set_xlabel("Olasılık (%)", labelpad=20, fontsize=12)
            ax.set_ylabel("Gol Kombinasyonları", labelpad=20, fontsize=12)
            ax.invert_yaxis()

            ax.grid(True, linestyle="--", alpha=0.7)

            add_footer(fig, x=0.98, y=-0.02, fontsize=8, extra_text=f"{selected_model} sonuçlarıdır.\nGeçmiş {last_round} haftanın verileri kullanılmıştır.")
            plt.tight_layout()

        elif plot_type == "Özet":
            bar_data = []
            for i in range(percentage_matrix.shape[0]):
                for j in range(percentage_matrix.shape[1]):
                    bar_data.append({
                        "Home Goals": int(i),
                        "Away Goals": int(j),
                        "Probability": percentage_matrix[i, j]
                    })

            bar_data = pd.DataFrame(bar_data)
            top_combinations = bar_data.sort_values("Probability", ascending=False).head(first_n_goals)

            summary = {
                "Ev Sahibi Önde": sum(top_combinations["Home Goals"] > top_combinations["Away Goals"]),
                "Deplasman Önde": sum(top_combinations["Home Goals"] < top_combinations["Away Goals"]),
                "Beraberlik": sum(top_combinations["Home Goals"] == top_combinations["Away Goals"]),
                "Ortalama Ev Sahibi Golü": top_combinations["Home Goals"].mean(),
                "Ortalama Deplasman Golü": top_combinations["Away Goals"].mean(),
                "Karşılıklı Gol Var": sum((top_combinations["Home Goals"] > 0) & (top_combinations["Away Goals"] > 0)),
                "Karşılıklı Gol Yok": sum((top_combinations["Home Goals"] == 0) | (top_combinations["Away Goals"] == 0)),
                "0.5 Üst": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) > 0.5),
                "1.5 Üst": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) > 1.5),
                "2.5 Üst": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) > 2.5),
                "3.5 Üst": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) > 3.5),
                "4.5 Üst": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) > 4.5),
                "0.5 Alt": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) <= 0.5),
                "1.5 Alt": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) <= 1.5),
                "2.5 Alt": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) <= 2.5),
                "3.5 Alt": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) <= 3.5),
                "4.5 Alt": sum((top_combinations["Home Goals"] + top_combinations["Away Goals"]) <= 4.5),
            }

            group_1 = {k: summary[k] for k in ["Ev Sahibi Önde", "Beraberlik", "Deplasman Önde"]}
            group_2 = {k: summary[k] for k in ["Ortalama Ev Sahibi Golü", "Ortalama Deplasman Golü"]}
            group_3 = {k: summary[k] for k in ["Karşılıklı Gol Var", "Karşılıklı Gol Yok"]}
            group_4 = {k: summary[k] for k in ["0.5 Üst", "1.5 Üst", "2.5 Üst", "3.5 Üst", "4.5 Üst"]}
            group_5 = {k: summary[k] for k in ["0.5 Alt", "1.5 Alt", "2.5 Alt", "3.5 Alt", "4.5 Alt"]}

            groups = [group_1, group_2, group_3, group_4, group_5]
            group_titles = ["Sonuç", "Ortalama Goller", "Karşılıklı Goller", "Üst Oynama", "Alt Oynama"]

            fig, axes = plt.subplots(5, 1, figsize=(12, 20))

            fig.suptitle(
                f"{league} {season} Sezonu {max_round_next_day}. Haftada İlk {first_n_goals} Gol Kombinasyonuna Göre Sonuçlar",
                fontsize=16,
                fontweight="bold",
                y=1.04
            )
            fig.text(
                0.5, 1.00,
                f"{home_team} - {away_team}",
                ha="center",
                fontsize=14,
                fontweight="bold"
            )

            for ax, group, title in zip(axes, groups, group_titles):
                ax.bar(group.keys(), group.values(), color="indianred", edgecolor="black")
                ax.set_title(title, fontsize=14, fontweight="bold")
                ax.set_ylabel("")
                ax.grid(axis="y", linestyle="--", alpha=0.7)
                ax.set_xticklabels(group.keys(), rotation=0, ha="center")

            add_footer(fig, x=0.98, y=-0.02, fontsize=8, extra_text=f"{selected_model} sonuçlarıdır.\nGeçmiş {last_round} haftanın verileri kullanılmıştır.")
            plt.tight_layout()

        elif plot_type == "Takım Gücü":

            teams = list(set(
                k.split("_")[1] for k in params.keys() if "_" in k and (k.startswith("attack_") or k.startswith("defence_"))
            ))
            attack_strength = np.array([params.get(f"attack_{team}", 0) for team in teams])
            defense_strength = np.array([params.get(f"defence_{team}", 0) for team in teams])

            fig, ax = plt.subplots(figsize=(12, 8))

            mean_attack = np.mean(attack_strength)
            mean_defense = np.mean(defense_strength)

            ax.axvline(mean_attack, color="red", linestyle="dashed", linewidth=1, label="Ortalama Hücum Gücü")
            ax.axhline(mean_defense, color="blue", linestyle="dashed", linewidth=1, label="Ortalama Savunma Gücü")

            ax.scatter(attack_strength, defense_strength, color="red", s=100, edgecolor="black", alpha=0.7)

            def getImage(path, zoom):
                return OffsetImage(plt.imread(path), zoom=zoom, alpha=1)

            for team, x, y in zip(teams, attack_strength, defense_strength):
                logo_path = f"./imgs/team_logo/{team}.png"
                zoom = 0.3 if team in [home_team, away_team] else 0.15
                ab = AnnotationBbox(getImage(logo_path, zoom), (x, y), frameon=False)
                ax.add_artist(ab)

            ax.set_xlabel("Hücum Gücü (daha büyük daha iyi)", labelpad=20, fontsize=12)
            ax.set_ylabel("Savunma Gücü (daha küçük daha iyi)", labelpad=20, fontsize=12)
            ax.set_title(
                f"{league} {season} Sezonu Geçmiş {last_round} Haftada Takımların Hücum ve Savunma Gücü",
                fontsize=16,
                fontweight="bold",
                pad=70
            )

            home_adv_value = params.get("home_adv", 0) * 100
            if home_adv_value > 0:
                home_adv_text = f"Ev sahibi takımın gol beklentisi yaklaşık %{home_adv_value:.1f} oranında artmaktadır."
            elif home_adv_value < 0:
                home_adv_text = f"Ev sahibi takımın gol beklentisi yaklaşık %{abs(home_adv_value):.1f} oranında azalmaktadır."
            else:
                home_adv_text = ""

            if home_adv_text:
                ax.text(0.5, 1.12, home_adv_text, ha="center", va="center", fontsize=10, fontstyle="italic", color="gray", transform=ax.transAxes)

            ax.invert_yaxis()
            ax.grid(True, linestyle="--", alpha=0.7)
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False, fontsize=10)
            add_footer(fig, x=0.96, y=-0.04, fontsize=8, extra_text=f"{selected_model} sonuçlarıdır.\nGeçmiş {last_round} haftanın verileri kullanılmıştır.")

    elif selected_model == "Bradley-Terry":
        fig, ax = plt.subplots(figsize=(12, 10))

        colors = ["red" if team == home_team else "blue" if team == away_team else "gray" for team in model_df["Team"]]
        ax.barh(
            model_df["Team"],
            model_df["Rating"],
            color=colors,
            edgecolor=colors
        )

        fig.suptitle(
            f"{league} {season} Sezonu {max_round_next_day}. Hafta\nTakımların Güç Sıralaması ve Ev Sahibi Kazanma Olasılığı",
            fontsize=18,
            fontweight="bold",
            y=1.00
        )

        ax.set_title(
            f"{home_team} - {away_team} Maçında Ev Sahibinin Kazanma Olasılığı: %{bt_prob * 100:.1f}",
            fontsize=14,
            fontweight="bold",
            pad=20
        )
        ax.set_xlabel("Reyting", labelpad=20, fontsize=12)
        ax.set_ylabel("")
        ax.grid(axis="x", linestyle="--", alpha=0.7)

        ax.invert_yaxis()
        add_footer(fig, x=0.98, y=-0.05, fontsize=8, extra_text=f"{selected_model} sonuçlarıdır.\nGeçmiş {last_round} haftanın verileri kullanılmıştır.")
        plt.tight_layout()

    file_name = f"{league_display}_{season_display}_{max_round_next_day}_{turkish_english_lower(home_team)}_{turkish_english_lower(away_team)}_{turkish_english_lower(selected_model)}_mac_sonu_olasiliklari.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, selected_model, selected_game, max_round_next_day, plot_type, first_n_goals):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        country_display = LEAGUE_COUNTRY_LOOKUP.get(league_display, "unknown")

        match_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "match_data")
        shots_data_df = load_filtered_json_files(directories, country_display, league_display, season_display, "shots_data")

        shots_data_df = shots_data_df.merge(match_data_df, on=["tournament", "season", "week", "game_id"])
        shots_data_df["team_name"] = shots_data_df.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)

        goal_counts = (
            shots_data_df[shots_data_df["shot_type"] == "goal"]
            .groupby(["game_id", "team_name"])
            .size()
            .reset_index(name="goals")
        )
        merged = shots_data_df[["game_id", "home_team", "away_team"]].drop_duplicates()
        merged = merged.merge(
            goal_counts, left_on=["game_id", "home_team"], right_on=["game_id", "team_name"], how="left"
        ).rename(columns={"goals": "home_team_goals"}).drop(columns=["team_name"])

        merged = merged.merge(
            goal_counts, left_on=["game_id", "away_team"], right_on=["game_id", "team_name"], how="left"
        ).rename(columns={"goals": "away_team_goals"}).drop(columns=["team_name"])
        merged["home_team_goals"] = merged["home_team_goals"].fillna(0).astype(int)
        merged["away_team_goals"] = merged["away_team_goals"].fillna(0).astype(int)
        merged = merged[["game_id", "home_team", "home_team_goals", "away_team", "away_team_goals"]]

        home_team = selected_game.split("-")[0].strip()
        away_team = selected_game.split("-")[1].strip()

        if selected_model == "Dixon-Coles":
            params = solve_parameters_cached(merged)
            model_df = dixon_coles_simulate_match_cached(params, home_team, away_team, max_goals=10)
            bt_prob = None
        elif selected_model == "Bradley-Terry":
            teams = np.sort(list(set(merged["home_team"].unique()) | set(merged["away_team"].unique())))
            bt_ratings, team_indices = solve_bt_ratings_cached(merged, teams)
            bt_prob = bt_forecast_match_cached(bt_ratings, home_team, away_team, team_indices)
            model_df = pd.DataFrame({
                "Team": list(team_indices.keys()),
                "Rating": bt_ratings
            }).sort_values("Rating", ascending=False)
            model_df["Team"] = model_df["Team"].replace("home_field_advantage", "Ev Sahibi Avantajı")

        last_round = match_data_df[match_data_df["status"] == "Ended"]["week"].max()

        create_predictive_analytics_plot(
            model_df,
            selected_model,
            home_team,
            away_team,
            league,
            season,
            league_display,
            season_display,
            last_round,
            max_round_next_day,
            plot_type,
            first_n_goals,
            bt_prob,
            params if selected_model == "Dixon-Coles" and plot_type == "Takım Gücü" else None
        )

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