import streamlit as st
from modules.homepage import display_homepage
from modules.team_based import display_team_based
from modules.team_comparison import display_team_comparison
from modules.player_based import display_player_based
from modules.match_comparison import display_match_comparison
from modules.analysis import display_eda_analysis, display_predictive_analytics
from config import team_list_by_season, change_situations, change_body_parts
from code.utils.helpers import load_styles
from st_social_media_links import SocialMediaIcons
from streamlit_option_menu import option_menu

def configure_app():
    st.set_page_config(
        page_title="Bu Analitik Futbol",
        page_icon=":soccer:",
        layout="wide"
    )
    load_styles()

def render_sidebar(social_media_links):
    with st.sidebar:
        st.image("./imgs/buanalitikfutbol.PNG", use_container_width=True)

        social_media_icons = SocialMediaIcons(
            [link["url"] for link in social_media_links.values()],
            colors=[link["color"] for link in social_media_links.values()]
        )
        social_media_icons.render(sidebar=True)

        coffee_button = """
        <div style="text-align: center; margin-top: 20px;">
            <a href="https://www.buymeacoffee.com/urazdev" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
                alt="Buy Me a Coffee"
                style="height: 50px; width: 217px;">
            </a>
        </div>
        """
        st.sidebar.markdown(coffee_button, unsafe_allow_html=True)
        st.sidebar.markdown("<br><br>", unsafe_allow_html=True)

def main_menu():
    if "current_section" not in st.session_state:
        st.session_state["current_section"] = "Ana Sayfa"

    return option_menu(
        menu_title=None,
        options=["Ana Sayfa", "Takım", "Oyuncu", "Maç", "Analiz", "Metaveri"],
        icons=["house", "shield", "person", "calendar", "bar-chart", "info-circle"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#262730"},
            "icon": {"color": "#BABCBE", "font-size": "18px"},
            "nav-link": {
                "font-size": "20px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#3E4042",
                "color": "#BABCBE",
            },
            "nav-link-selected": {
                "background-color": "#262730",
                "color": "#fff",
            },
        },
    )

def handle_team_section():
    selection = st.sidebar.radio(
        "Takım Bazlı Analiz Türü",
        ["Takım Bazlı", "Takımlar Arası"],
        index=None,
        label_visibility="hidden"
    )
    if selection == "Takım Bazlı":
        display_team_based(
            team_list_by_season,
            change_situations,
            change_body_parts,
            st.session_state.get("selected_league"),
            st.session_state.get("selected_season")
        )
    elif selection == "Takımlar Arası":
        display_team_comparison(
            team_list_by_season,
            change_situations,
            change_body_parts,
            st.session_state.get("selected_league"),
            st.session_state.get("selected_season")
        )

def handle_player_section():
    selection = st.sidebar.radio(
        "Oyuncu Bazlı Analiz Türü",
        ["Oyuncu Bazlı", "Oyuncular Arası"],
        index=None,
        label_visibility="hidden"
    )
    if selection == "Oyuncu Bazlı":
        display_player_based(
            team_list_by_season,
            change_situations,
            change_body_parts,
            st.session_state.get("selected_league"),
            st.session_state.get("selected_season")
        )
    elif selection == "Oyuncular Arası":
        st.info("Oyuncular arası bölümü yakında eklenecek.")

def handle_match_section():
    selection = st.sidebar.radio(
        "Maç Bazlı Analiz Türü",
        ["Takım Bazlı", "Takımlar Arası"],
        index=None,
        label_visibility="hidden"
    )
    if selection == "Takım Bazlı":
        st.info("Takım bazlı bölümü yakında eklenecek.")
    elif selection == "Takımlar Arası":
        display_match_comparison(
            team_list_by_season,
            change_situations,
            change_body_parts,
            st.session_state.get("selected_league"),
            st.session_state.get("selected_season")
        )

def handle_analysis_section():
    selection = st.sidebar.radio(
        "Analiz Türü",
        ["Keşifçi Veri Analizi", "Tahmin"],
        index=None,
        label_visibility="hidden"
    )
    if selection == "Keşifçi Veri Analizi":
        display_eda_analysis(
            team_list_by_season,
            change_situations,
            change_body_parts,
            st.session_state.get("selected_league"),
            st.session_state.get("selected_season")
        )
    elif selection == "Tahmin":
        display_predictive_analytics(
            team_list_by_season,
            change_situations,
            change_body_parts,
            st.session_state.get("selected_league"),
            st.session_state.get("selected_season")
        )

def run_app():
    configure_app()

    social_media_links = {
        "X": {"url": "https://www.x.com/urazdev", "color": "#fff"},
        "GitHub": {"url": "https://www.github.com/urazakgul", "color": "#fff"},
        "Reddit": {"url": "https://www.reddit.com/user/urazdev/", "color": "#fff"},
        "LinkedIn": {"url": "https://www.linkedin.com/in/uraz-akg%C3%BCl-439b36239/", "color": "#fff"},
    }
    render_sidebar(social_media_links)

    general_section = main_menu()
    st.session_state["current_section"] = general_section

    if general_section == "Ana Sayfa":
        display_homepage()
    elif general_section == "Takım":
        if st.session_state.get("league_season_confirmed", False):
            handle_team_section()
        else:
            st.warning("Lütfen önce ana sayfadan lig ve sezon seçimini yapınız.")
    elif general_section == "Oyuncu":
        if st.session_state.get("league_season_confirmed", False):
            handle_player_section()
        else:
            st.warning("Lütfen önce Ana Sayfa'dan lig ve sezon seçimini yapınız.")
    elif general_section == "Maç":
        if st.session_state.get("league_season_confirmed", False):
            handle_match_section()
        else:
            st.warning("Lütfen önce Ana Sayfa'dan lig ve sezon seçimini yapınız.")
    elif general_section == "Analiz":
        if st.session_state.get("league_season_confirmed", False):
            handle_analysis_section()
        else:
            st.warning("Lütfen önce Ana Sayfa'dan lig ve sezon seçimini yapınız.")
    elif general_section == "Metaveri":
        st.info("Metaveri bölümü yakında eklenecek.")

if __name__ == "__main__":
    run_app()