import base64
import io
import os
import glob
import gzip
import pandas as pd
import re
from unidecode import unidecode
import streamlit as st

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

def add_footer(fig, data_source="SofaScore", prepared_by="@urazdev", extra_text=None, x=0.99, y=-0.05, fontsize=10, ha="right"):
    footer_text = f"Veri: {data_source}\nHazırlayan: {prepared_by}"
    if extra_text:
        footer_text += f"\n{extra_text}"

    fig.text(
        x, y,
        footer_text,
        ha=ha,
        va="bottom",
        fontsize=fontsize,
        fontstyle="italic",
        color="gray"
    )

@st.cache_data(show_spinner=False)
def load_filtered_json_files(directory: str, country: str, league: str, season: str, subdirectory: str) -> pd.DataFrame:
    path = os.path.join(directory, subdirectory, f"sofascore_{country}_{league}_{season}_{subdirectory}.json*")
    files = glob.glob(path)

    dataframes = []
    for file in files:
        if file.endswith(".gz"):
            with gzip.open(file, 'rt', encoding='utf-8') as f:
                dataframes.append(pd.read_json(f))
        else:
            dataframes.append(pd.read_json(file))

    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

def get_user_selection(team_list_by_season, change_situations, change_body_parts, include_situation_type=True, include_team=True, include_body_part=True, key_prefix=""):

    st.session_state["league_display"] = re.sub(r"\s+", "_", unidecode(st.session_state["selected_league"].lower()))
    st.session_state["season_display"] = st.session_state["selected_season"].split('/')[0][2:] + st.session_state["selected_season"].split('/')[1]

    team = None
    if include_team:
        team_list = team_list_by_season.get(st.session_state["season_display"], [])
        team = st.sidebar.selectbox(
            "Takımlar",
            team_list,
            index=None,
            label_visibility="hidden",
            placeholder="Takımlar",
            key=f"{key_prefix}_selectbox_team"
        )

    situation_type = None
    if include_situation_type:
        situation_type_display = st.sidebar.selectbox(
            "Senaryo Tipi:",
            ["Hepsi"] + list(change_situations.values()),
            index=None,
            label_visibility="hidden",
            placeholder="Senaryo Tipleri",
            key=f"{key_prefix}_selectbox_situation"
        )
        situation_type = situation_type_display

    body_part_type = None
    if include_body_part:
        body_part_display = st.sidebar.selectbox(
            "Vücut Parçası Tipi:",
            ["Hepsi"] + list(change_body_parts.values()),
            index=None,
            label_visibility="hidden",
            placeholder="Vücut Parçaları",
            key=f"{key_prefix}_selectbox_body_part"
        )
        body_part_type = body_part_display

    return (
        st.session_state["selected_league"],
        st.session_state["selected_season"],
        st.session_state["league_display"],
        st.session_state["season_display"],
        team,
        situation_type,
        body_part_type
    )

def turkish_upper(text):
    replacements = {"i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ç": "Ç", "ö": "Ö", "ü": "Ü"}
    return ''.join(replacements.get(char, char.upper()) for char in text)

def turkish_english_lower(text):
    replacements = {
        "İ": "i", "I": "i", "Ş": "s", "Ğ": "g", "Ç": "c", "Ö": "o", "Ü": "u",
        "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u", "ı": "i"
    }
    text = text.replace(' ', '-')
    return ''.join(replacements.get(char, char.lower()) for char in text)

def turkish_sort_key():
    turkish_alphabet = "AaBbCcÇçDdEeFfGgĞğHhIıİiJjKkLlMmNnOoÖöPpRrSsŞşTtUuÜüVvYyZz"
    turkish_sort_order = {char: idx for idx, char in enumerate(turkish_alphabet)}

    def sort_function(text):
        return [turkish_sort_order.get(char, -1) for char in text]

    return sort_function

def sort_turkish(df, column):
    sort_key = turkish_sort_key()
    return df.sort_values(by=column, key=lambda col: col.map(sort_key))