from config import PLOT_STYLE
from code.utils.helpers import load_filtered_json_files, add_footer, add_download_button, turkish_english_lower
import os
import numpy as np
import pandas as pd
from scipy.stats import poisson
from scipy.optimize import minimize
import streamlit as st
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def rho_correction(x, y, lambda_x, mu_y, rho):
    if x == 0 and y == 0:
        return 1 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1:
        return 1 + (lambda_x * rho)
    elif x == 1 and y == 0:
        return 1 + (mu_y * rho)
    elif x == 1 and y == 1:
        return 1 - rho
    else:
        return 1.0

def dc_log_like(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma):
    lambda_x = np.exp(alpha_x + beta_y + gamma)
    mu_y = np.exp(alpha_y + beta_x)
    log_lambda_x = np.log(max(poisson.pmf(x, lambda_x), 1e-10))
    log_mu_y = np.log(max(poisson.pmf(y, mu_y), 1e-10))
    return (
        np.log(rho_correction(x, y, lambda_x, mu_y, rho)) + log_lambda_x + log_mu_y
    )

def solve_parameters(dataset, init_vals=None, options={"disp": True, "maxiter": 100}, **kwargs):
    teams = np.sort(
        list(
            set(dataset["home_team"].unique()) | set(dataset["away_team"].unique())
        )
    )
    n_teams = len(teams)

    if init_vals is None:
        avg_attack = dataset.groupby("home_team")["home_team_goals"].mean().reindex(teams).fillna(1.0).values
        avg_defence = -dataset.groupby("away_team")["away_team_goals"].mean().reindex(teams).fillna(1.0).values
        init_vals = np.concatenate([
            avg_attack,
            avg_defence,
            np.array([0, 1.0])
        ])

    def estimate_parameters(params):
        attack_coeffs = dict(zip(teams, params[:n_teams]))
        defence_coeffs = dict(zip(teams, params[n_teams:2 * n_teams]))
        rho, gamma = params[-2:]

        log_likelihoods = [
            dc_log_like(
                row.home_team_goals,
                row.away_team_goals,
                attack_coeffs[row.home_team],
                defence_coeffs[row.home_team],
                attack_coeffs[row.away_team],
                defence_coeffs[row.away_team],
                rho, gamma
            )
            for row in dataset.itertuples()
        ]
        return -np.sum(log_likelihoods)

    constraints = [{"type": "eq", "fun": lambda x, n=n_teams: sum(x[:n]) - n}]
    opt_output = minimize(estimate_parameters, init_vals, options=options, constraints=constraints, **kwargs)

    return dict(
        zip(
            ["attack_" + team for team in teams] +
            ["defence_" + team for team in teams] +
            ["rho", "home_adv"],
            opt_output.x
        )
    )

def dixon_coles_simulate_match(params_dict, home_team, away_team, max_goals=10):
    def calc_means(param_dict, home_team, away_team):
        return [
            np.exp(param_dict["attack_" + home_team] + param_dict["defence_" + away_team] + param_dict["home_adv"]),
            np.exp(param_dict["defence_" + home_team] + param_dict["attack_" + away_team])
        ]

    team_avgs = calc_means(params_dict, home_team, away_team)
    team_pred = [[poisson.pmf(i, team_avg) for i in range(max_goals + 1)] for team_avg in team_avgs]

    output_matrix = np.outer(np.array(team_pred[0]), np.array(team_pred[1]))

    correction_matrix = np.array([
        [rho_correction(h, a, team_avgs[0], team_avgs[1], params_dict["rho"]) for a in range(2)]
        for h in range(2)
    ])
    output_matrix[:2, :2] *= correction_matrix
    return output_matrix

@st.cache_data(show_spinner=False)
def solve_parameters_cached(dataset):
    return solve_parameters(dataset)

@st.cache_data(show_spinner=False)
def dixon_coles_simulate_match_cached(params_dict, home_team, away_team, max_goals=10):
    return dixon_coles_simulate_match(params_dict, home_team, away_team, max_goals)

def create_predictive_analytics_plot(home_away_teams_dc, selected_model, home_team, away_team, league, season, league_display, season_display, last_round, max_round_next_day, plot_type, first_n_goals):

    home_win_prob = np.sum(np.tril(home_away_teams_dc, -1)) * 100
    draw_prob = np.sum(np.diag(home_away_teams_dc)) * 100
    away_win_prob = np.sum(np.triu(home_away_teams_dc, 1)) * 100

    percentage_matrix = home_away_teams_dc * 100

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

    file_name = f"{league_display}_{season_display}_{max_round_next_day}_{turkish_english_lower(home_team)}_{turkish_english_lower(away_team)}_{turkish_english_lower(selected_model)}_mac_sonu_olasiliklari.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league, season, league_display, season_display, selected_model, selected_game, max_round_next_day, plot_type, first_n_goals):

    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        games_data = load_filtered_json_files(directories, "games", league_display, season_display)
        shot_maps_data = load_filtered_json_files(directories, "shot_maps", league_display, season_display)

        shot_maps_data = shot_maps_data.merge(games_data, on=["tournament", "season", "round", "game_id"])
        shot_maps_data["team_name"] = shot_maps_data.apply(lambda x: x["home_team"] if x["is_home"] else x["away_team"], axis=1)

        goal_counts = (
            shot_maps_data[shot_maps_data["shot_type"] == "goal"]
            .groupby(["game_id", "team_name"])
            .size()
            .reset_index(name="goals")
        )
        merged = shot_maps_data[["game_id", "home_team", "away_team"]].drop_duplicates()
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

        params = solve_parameters_cached(merged)
        home_away_teams_dc = dixon_coles_simulate_match_cached(params, home_team, away_team, max_goals=10)

        last_round = games_data[games_data["status"] == "Ended"]["round"].max()

        create_predictive_analytics_plot(
            home_away_teams_dc,
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
            first_n_goals
        )

    except Exception as e:
        st.error(f"Uygun veri bulunamadı.{e}")
        st.markdown(
            """
            <a href="https://github.com/urazakgul/buanalitikfutbol-app/issues" target="_blank" class="error-button">
                🛠️ Hata bildir
            </a>
            """,
            unsafe_allow_html=True
        )