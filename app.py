import streamlit as st
from modules.homepage import display_homepage
from modules.team_based import display_team_based
from modules.team_comparison import display_team_comparison
from modules.player_based import display_player_based
from modules.match_comparison import display_match_comparison
from config import team_list, change_situations, change_body_parts
from code.utils.helpers import load_styles
from st_social_media_links import SocialMediaIcons
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Bu Analitik Futbol",
    page_icon=":soccer:",
    layout="wide"
)

social_media_links = {
    "X": {"url": "https://www.x.com/urazdev", "color": "#fff"},
    "GitHub": {"url": "https://www.github.com/urazakgul", "color": "#fff"},
    "Reddit": {"url": "https://www.reddit.com/user/urazdev/", "color": "#fff"},
    "LinkedIn": {"url": "https://www.linkedin.com/in/uraz-akg%C3%BCl-439b36239/", "color": "#fff"}
}

load_styles()

def run_app():
    general_section = option_menu(
        menu_title=None,
        options=["Ana Sayfa", "Takım", "Oyuncu", "Maç", "Metaveri"],
        icons=["house", "shield", "person", "calendar", "info-circle"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#262730"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "20px", "text-align": "center", "margin": "0px", "--hover-color": "#444"},
            "nav-link-selected": {"background-color": "orange"},
        }
    )

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

    if general_section == "Ana Sayfa":
        display_homepage()
    elif general_section == "Takım":
        selection = st.sidebar.radio(
            "Takım Bazlı Analiz Türü",
            ["Spesifik", "Karşılaştırma"],
            index=None,
            label_visibility="hidden"
        )
        if selection == "Spesifik":
            display_team_based(team_list, change_situations, change_body_parts)
        elif selection == "Karşılaştırma":
            display_team_comparison(team_list, change_situations, change_body_parts)
    elif general_section == "Oyuncu":
        selection = st.sidebar.radio(
            "Oyuncu Bazlı Analiz Türü",
            ["Spesifik", "Karşılaştırma"],
            index=None,
            label_visibility="hidden"
        )
        if selection == "Spesifik":
            display_player_based(team_list, change_situations, change_body_parts)
        elif selection == "Karşılaştırma":
            pass
    elif general_section == "Maç":
        selection = st.sidebar.radio(
            "Maç Bazlı Analiz Türü",
            ["Spesifik", "Karşılaştırma"],
            index=None,
            label_visibility="hidden"
        )
        if selection == "Spesifik":
            pass
        elif selection == "Karşılaştırma":
            display_match_comparison(team_list, change_situations, change_body_parts)
if __name__ == "__main__":
    run_app()