import streamlit as st
import numpy as np
from scipy.optimize import minimize

def bt_home_forecast(home_rating, away_rating, home_field_advantage):
    return 1 / (1 + np.exp(-(home_field_advantage + home_rating - away_rating)))

def bt_log_likelihood(bt_ratings, dataset, team_indices):
    log_likelihood = 0
    for _, row in dataset.iterrows():
        home = row["home_team"]
        visitor = row["away_team"]
        h_win = row["home_team_goals"] > row["away_team_goals"]

        home_rating = bt_ratings[team_indices[home]]
        away_rating = bt_ratings[team_indices[visitor]]
        home_field_advantage = bt_ratings[team_indices["home_field_advantage"]]

        forecast = bt_home_forecast(home_rating, away_rating, home_field_advantage)
        result = forecast if h_win else (1 - forecast)

        log_likelihood += np.log(max(result, 1e-10))
    return -log_likelihood

@st.cache_data(show_spinner=False)
def solve_bt_ratings_cached(dataset, teams):
    n_teams = len(teams)
    initial_ratings = np.ones(n_teams + 1)
    team_indices = {team: i for i, team in enumerate(teams)}
    team_indices["home_field_advantage"] = n_teams

    result = minimize(
        bt_log_likelihood,
        initial_ratings,
        args=(dataset, team_indices),
        method="BFGS"
    )

    bt_ratings = result.x
    return bt_ratings, team_indices

@st.cache_data(show_spinner=False)
def bt_forecast_match_cached(bt_ratings, home_team, away_team, team_indices):
    home_rating = bt_ratings[team_indices[home_team]]
    away_rating = bt_ratings[team_indices[away_team]]
    home_field_advantage = bt_ratings[team_indices["home_field_advantage"]]
    return bt_home_forecast(home_rating, away_rating, home_field_advantage)