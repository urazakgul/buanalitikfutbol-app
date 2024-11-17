from config import team_list
import os
import glob
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import warnings

plt.style.use('fivethirtyeight')
warnings.filterwarnings('ignore')

def load_filtered_json_files(directory: str, subdirectory: str, league: str, season: str) -> pd.DataFrame:
    path = os.path.join(directory, subdirectory, f'{league}_{subdirectory}_{season}.json')
    files = glob.glob(path)

    if not files:
        st.error("Uygun dosya bulunamadı.")
        return pd.DataFrame()
    else:
        return pd.concat((pd.read_json(file, orient='records', lines=True) for file in files), ignore_index=True)

def create_xg_cum_actual_plot(xg_goal_teams, league_display, season_display):
    teams = [team for team in team_list if team in xg_goal_teams['team_name'].unique()]

    fig, axes = plt.subplots(nrows=len(teams) // 4 + (len(teams) % 4 > 0), ncols=4, figsize=(20, 20))
    axes = axes.flatten()

    for i, team in enumerate(teams):
        team_data = xg_goal_teams[xg_goal_teams['team_name'] == team].copy()

        ax = axes[i]
        ax.plot(team_data['round'], team_data['cumulative_goal_count'], label='Kümülatif Gol', color='blue')
        ax.plot(team_data['round'], team_data['cumulative_total_xg'], label='Kümülatif xG', color='red')
        ax.fill_between(
            team_data['round'],
            team_data['cumulative_goal_count'],
            team_data['cumulative_total_xg'],
            where=(team_data['cumulative_goal_count'] >= team_data['cumulative_total_xg']),
            color='blue', alpha=0.3
        )
        ax.fill_between(
            team_data['round'],
            team_data['cumulative_goal_count'],
            team_data['cumulative_total_xg'],
            where=(team_data['cumulative_goal_count'] < team_data['cumulative_total_xg']),
            color='red', alpha=0.3
        )

        ax.set_title(team)
        ax.grid(True)
        ax.set_xticks(range(int(xg_goal_teams['round'].min()), int(xg_goal_teams['round'].max()) + 1))
        ax.set_xticklabels(range(int(xg_goal_teams['round'].min()), int(xg_goal_teams['round'].max()) + 1))

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(
        f'{league_display} {season_display} Sezonu Takımlara Göre Haftalık Bazda Kümülatif Gol ve xG Değerleri', fontsize=20, y=1.02
    )
    fig.legend(
        ['Kümülatif Gol', 'Kümülatif xG'],
        loc='upper center',
        bbox_to_anchor=(0.5, 1.00),
        ncol=2,
        fontsize='large'
    )
    fig.text(0.5, 0.04, 'Hafta', ha='center', va='center', fontsize='large')
    fig.text(-0.02, 0.5, 'Kümülatif Değer', ha='center', va='center', rotation='vertical', fontsize='large')
    fig.text(
        0.99, 0.01,
        'Veri: SofaScore\nHesaplamalar ve grafik: buanalitikfutbol.com',
        ha='right',
        va='bottom',
        fontsize='medium',
        fontstyle='italic',
        color='gray'
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    st.pyplot(fig)

def main(league, season, league_display, season_display):
    directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/')

    matches_data = load_filtered_json_files(directories, 'matches', league, season)
    shot_maps_data = load_filtered_json_files(directories, 'shot_maps', league, season)
    points_table_data = load_filtered_json_files(directories, 'points_table', league, season)

    if matches_data.empty or shot_maps_data.empty or points_table_data.empty:
        st.error("Uygun veri bulunamadı.")
        return

    points_table_data = points_table_data[points_table_data['category'] == 'Total'][['team_name', 'scores_for', 'scores_against']]

    shot_maps_data = shot_maps_data.merge(matches_data, on=['tournament', 'season', 'round', 'game_id'])
    shot_maps_data['team_name'] = shot_maps_data.apply(lambda x: x['home_team'] if x['is_home'] else x['away_team'], axis=1)

    xg_by_team = shot_maps_data.groupby(['team_name', 'round'])['xg'].sum().reset_index(name='total_xg')
    xg_by_team_pivot = xg_by_team.pivot(index='team_name', columns='round', values='total_xg').fillna(0)
    xg_by_team_long = xg_by_team_pivot.reset_index().melt(id_vars='team_name', var_name='round', value_name='total_xg')

    goal_shots = shot_maps_data[shot_maps_data['shot_type'] == 'goal']
    goal_shots_by_team = goal_shots.groupby(['team_name', 'round']).size().reset_index(name='goal_count')
    goal_shots_by_team_pivot = goal_shots_by_team.pivot(index='team_name', columns='round', values='goal_count').fillna(0)
    goal_shots_by_team_long = goal_shots_by_team_pivot.reset_index().melt(id_vars='team_name', var_name='round', value_name='goal_count')

    xg_goal_teams = pd.merge(xg_by_team_long, goal_shots_by_team_long, on=['team_name', 'round'])
    xg_goal_teams = xg_goal_teams.sort_values(by=['team_name', 'round'])
    xg_goal_teams['cumulative_total_xg'] = xg_goal_teams.groupby('team_name')['total_xg'].cumsum()
    xg_goal_teams['cumulative_goal_count'] = xg_goal_teams.groupby('team_name')['goal_count'].cumsum()
    xg_goal_teams['cum_goal_xg_diff'] = xg_goal_teams['cumulative_goal_count'] - xg_goal_teams['cumulative_total_xg']

    xg_goal_teams['cumulative_goal_count'] = pd.to_numeric(xg_goal_teams['cumulative_goal_count'], errors='coerce')
    xg_goal_teams['cumulative_total_xg'] = pd.to_numeric(xg_goal_teams['cumulative_total_xg'], errors='coerce')
    xg_goal_teams['round'] = pd.to_numeric(xg_goal_teams['round'], errors='coerce')

    xg_goal_teams = xg_goal_teams.dropna(subset=['cumulative_goal_count', 'cumulative_total_xg', 'round'])

    create_xg_cum_actual_plot(xg_goal_teams, league_display, season_display)