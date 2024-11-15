import streamlit as st
from config import team_list
from code.goal_path import main as goal_path_main

st.set_page_config(page_title="Bu Analitik Futbol", layout="wide")

st.markdown("""
    <style>
    .big-font {
        font-size: 48px !important;
    }
    .medium-font {
        font-size: 24px !important;
    }
    .small-font {
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def run_app():
    st.sidebar.title("Bu Analitik Futbol | Türkiye")
    section = st.sidebar.radio(
        "Kategori seçin:",
        options=["Ana Sayfa", "Gol Ağı"],
        index=0
    )

    if section == "Gol Ağı":
        league_display = st.sidebar.selectbox("Lig seçin:", ["Süper Lig"], disabled=True)
        league = "super_lig" if league_display == "Süper Lig" else league_display
        season_display = st.sidebar.selectbox("Sezon seçin:", ["2024/25"], disabled=True)
        season = "2425" if season_display == "2024/25" else season_display
        team = st.sidebar.selectbox("Takım seçin:", ["Takım seçin"] + team_list)

        goal_path_main(league=league, season=season, team=team, league_display=league_display, season_display=season_display)
    else:
        st.markdown('<h1 class="big-font">Bu Analitik Futbol\'a Hoş Geldiniz</h1>', unsafe_allow_html=True)
        st.markdown("""
            <p class="medium-font">
            Bu uygulama, futbol analitiği üzerine çeşitli görselleştirmeler ve analizler sunar.
            </p>
        """, unsafe_allow_html=True)
        st.image("imgs/buanalitikfutbol.PNG", use_column_width=True)

        st.markdown("""
            <hr>
            <p class="small-font">
            <strong>İletişim:</strong><br>
            E-posta: <a href="mailto:urazdev@gmail.com">urazdev@gmail.com</a><br>
            X (Twitter): <a href="https://twitter.com/urazdev" target="_blank">@urazdev</a><br>
            Web: <a href="https://www.buanalitikfutbol.com/" target="_blank">https://www.buanalitikfutbol.com/</a>
            </p>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    run_app()