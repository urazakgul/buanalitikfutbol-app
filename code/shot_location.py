from config import event_type_translations, event_colors, change_situations
import os
import glob
import pandas as pd
import streamlit as st
from mplsoccer import VerticalPitch
from io import BytesIO
import base64
import matplotlib.pyplot as plt

plt.style.use('fivethirtyeight')

def load_filtered_json_files(directory: str, subdirectory: str, league: str, season: str) -> pd.DataFrame:
    path = os.path.join(directory, subdirectory, f'{league}_{subdirectory}_{season}.json')
    files = glob.glob(path)

    if not files:
        st.error("Uygun dosya bulunamadı.")
        return pd.DataFrame()
    else:
        return pd.concat((pd.read_json(file, orient='records', lines=True) for file in files), ignore_index=True)

def create_shot_location_plot(df_goals, df_non_goals, team_name, league_display, season_display, max_round, situation_type=None):
    pitch = VerticalPitch(
        pitch_type='opta',
        corner_arcs=True,
        half=False,
        label=False,
        tick=False
    )

    fig, ax = pitch.draw(figsize=(16, 16))

    pitch.scatter(
        df_non_goals['player_coordinates_x'],
        df_non_goals['player_coordinates_y'],
        edgecolors='black',
        c='gray',
        marker='h',
        alpha=0.1,
        s=150,
        label='Gol Değil',
        ax=ax
    )

    pitch.scatter(
        df_goals['player_coordinates_x'],
        df_goals['player_coordinates_y'],
        edgecolors='black',
        c='red',
        marker='h',
        alpha=0.5,
        s=150,
        label='Gol',
        ax=ax
    )

    title_suffix = f"({situation_type})" if situation_type else ""
    ax.text(
        x=50,
        y=30,
        s=f'{league_display} {season_display} Sezonu İlk {max_round} Hafta:\n{team_name} Takımının Şut Lokasyonları\n{title_suffix}',
        size=28,
        color=pitch.line_color,
        va='center',
        ha='center'
    )

    y_axis_direction = 22 if situation_type else 24
    ax.text(
        x=50,
        y=y_axis_direction,
        s='Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com',
        size=16,
        color=pitch.line_color,
        fontstyle='italic',
        va='center',
        ha='center'
    )

    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.02),
        ncol=2,
        fontsize=16,
        frameon=True,
        facecolor='white',
        edgecolor='black'
    )

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    img_html = f'<img src="data:image/png;base64,{img_str}" style="display: block; margin-left: auto; margin-right: auto; width: 750px;"/>'
    st.markdown(img_html, unsafe_allow_html=True)

def main(league=None, season=None, team=None, league_display=None, season_display=None, situation_type=None):
    if team == "Takım seçin":
        st.warning("Henüz bir takım seçmediniz.")
        return

    directories = os.path.join(os.path.dirname(__file__), '../data/sofascore/')

    matches_data = load_filtered_json_files(directories, 'matches', league, season)
    shotmaps_data = load_filtered_json_files(directories, 'shot_maps', league, season)

    if matches_data.empty or shotmaps_data.empty:
        st.error("Seçilen takım için uygun veri bulunamadı.")
        return

    shotmaps_data = shotmaps_data[[
        'season', 'round', 'game_id', 'is_home', 'shot_type', 'situation',
        'goal_mouth_location', 'player_coordinates_x', 'player_coordinates_y'
    ]]

    shotmaps_data = shotmaps_data.merge(
        matches_data[['season', 'round', 'game_id', 'home_team', 'away_team']],
        on=['season', 'round', 'game_id'],
        how='left'
    )

    shotmaps_data['team_name'] = shotmaps_data.apply(
        lambda row: row['home_team'] if row['is_home'] else row['away_team'], axis=1
    )

    shotmaps_data['is_goal'] = shotmaps_data['shot_type'].apply(lambda x: 1 if x == 'goal' else 0)
    shotmaps_data['player_coordinates_x'] = 100 - shotmaps_data['player_coordinates_x']
    shotmaps_data['player_coordinates_y'] = 100 - shotmaps_data['player_coordinates_y']

    shotmaps_data['situation'] = shotmaps_data['situation'].replace(change_situations)

    if situation_type is not None:
        team_data = shotmaps_data[(shotmaps_data['team_name'] == team) & (shotmaps_data['situation'] == situation_type)]
    else:
        team_data = shotmaps_data[shotmaps_data['team_name'] == team]

    df_goals = team_data[team_data['is_goal'] == 1]
    df_non_goals = team_data[team_data['is_goal'] == 0]

    if not team_data.empty:
        max_round = matches_data['round'].max()
        create_shot_location_plot(df_goals, df_non_goals, team, league_display, season_display, max_round, situation_type)
    else:
        st.error("Seçilen takım için uygun veri bulunamadı.")