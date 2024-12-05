import base64
import io
import os
import glob
import pandas as pd
import streamlit as st
from matplotlib.axes import Axes

def load_styles():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def add_download_button(fig, file_name: str = "grafik.png") -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    buf.seek(0)

    file_data = buf.getvalue()
    b64 = base64.b64encode(file_data).decode()

    download_button = f"""
    <a href="data:image/png;base64,{b64}" download="{file_name}" class="download-button">
        PNG Olarak İndir
    </a>
    """
    return download_button

def add_footer_text(ax: Axes, footer_text: str = "Veri: SofaScore\nHesaplamalar ve Grafik: buanalitikfutbol.com") -> None:
    ax.text(
        1, -0.15, footer_text,
        transform=ax.transAxes,
        fontsize=10,
        fontstyle="italic",
        color="gray",
        ha="right"
    )

@st.cache_data(show_spinner=False)
def load_filtered_json_files(directory: str, subdirectory: str, league: str, season: str) -> pd.DataFrame:
    path = os.path.join(directory, subdirectory, f"{league}_{subdirectory}_{season}.json")
    files = glob.glob(path)

    return pd.concat((pd.read_json(file, orient="records", lines=True) for file in files), ignore_index=True)

def get_user_selection(team_list, change_situations, change_body_parts, include_situation_type=True, include_team=True, include_body_part=True, key_prefix=""):
    league_display = st.sidebar.selectbox(
        "Lig:", ["Süper Lig"], disabled=True, key=f"{key_prefix}_selectbox_league"
    )
    league = "super_lig" if league_display == "Süper Lig" else league_display

    season_display = st.sidebar.selectbox(
        "Sezon:", ["2024/25"], disabled=True, key=f"{key_prefix}_selectbox_season"
    )
    season = "2425" if season_display == "2024/25" else season_display

    team = None
    if include_team:
        team = st.sidebar.selectbox(
            "Takım:", ["Takım seçin"] + team_list, key=f"{key_prefix}_selectbox_team"
        )

    situation_type = None
    if include_situation_type:
        situation_type_display = st.sidebar.selectbox(
            "Şut Tipi:", ["Hepsi"] + list(change_situations.values()), key=f"{key_prefix}_selectbox_situation"
        )
        situation_type = situation_type_display if situation_type_display != "Hepsi" else None

    body_part_type = None
    if include_body_part:
        body_part_display = st.sidebar.selectbox(
            "Vücut Parçası Tipi:", ["Hepsi"] + list(change_body_parts.values()), key=f"{key_prefix}_selectbox_body_part"
        )
        body_part_type = body_part_display if body_part_display != "Hepsi" else None

    return league, season, team, league_display, season_display, situation_type, body_part_type