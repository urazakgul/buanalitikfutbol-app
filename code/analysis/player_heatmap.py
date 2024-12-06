import os
import streamlit as st
from config import PLOT_STYLE
from code.utils.helpers import add_download_button, load_filtered_json_files
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt

plt.style.use(PLOT_STYLE)

def create_player_heatmap_plot(filtered_hmap_data_df, team_name, league_display, season_display, last_round, player_name):

    pitch = VerticalPitch(
        pitch_type='opta',
        corner_arcs=True,
        half=False,
        label=False,
        tick=False
    )
    fig, ax = pitch.draw(figsize=(16, 16))

    pitch.kdeplot(
        filtered_hmap_data_df["x"],
        filtered_hmap_data_df["y"],
        ax=ax,
        fill=True,
        cmap="Reds",
        levels=100,
        alpha=0.6,
        zorder=0
    )

    ax.set_title(
        f"{league_display} {season_display} Sezonu Geçmiş {last_round} Hafta Oyuncu Isı Haritası\n{player_name} ({team_name})",
        fontsize=16
    )

    fig.suptitle(
        "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com",
        y=0,
        x=0.5,
        fontsize=12,
        fontstyle="italic",
        color="gray"
    )

    file_name = f"{league_display}_{season_display}_{last_round}_{player_name}_{team_name}_Isı Haritası.png"
    st.markdown(add_download_button(fig, file_name=file_name), unsafe_allow_html=True)
    st.pyplot(fig)

def main(league=None, season=None, team=None, league_display=None, season_display=None, player=None):
    try:

        directories = os.path.join(os.path.dirname(__file__), "../../data/sofascore/raw/")

        matches_data = load_filtered_json_files(directories, "matches", league, season)
        heatmaps_data = load_filtered_json_files(directories, "heatmaps", league, season)

        matches_data = matches_data[['game_id', 'tournament', 'season', 'round', 'home_team', 'away_team']]

        hmap_data_df = heatmaps_data.merge(
            matches_data,
            on=['game_id', 'tournament', 'season', 'round'],
            how='left'
        )

        hmap_data_df['team_name'] = hmap_data_df.apply(
            lambda row: row['home_team'] if row['team'] == 'home' else row['away_team'],
            axis=1
        )

        filtered_hmap_data_df = hmap_data_df[
            (hmap_data_df['team_name'] == team) &
            (hmap_data_df['player_name'] == player)
        ]

        last_round = matches_data['round'].max()

        create_player_heatmap_plot(filtered_hmap_data_df, team, league_display, season_display, last_round, player)

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