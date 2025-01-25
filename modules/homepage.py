import streamlit as st

def initialize_session_state():
    if "league_season_confirmed" not in st.session_state:
        st.session_state["league_season_confirmed"] = False
        st.session_state["selected_league"] = None
        st.session_state["selected_season"] = None

def render_welcome_message():
    st.markdown('<h1 class="big-font">BAF - SÜPER LİG\'e Hoş Geldiniz</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div>
            <p>
            BAF (Bu Analitik Futbol) Süper Lig uygulaması, Süper Lig özelinde etkileyici görselleştirmeler ve detaylı analizler sunarak, <mark>veri odaklı bakış açısını</mark> güçlendirmeyi, futbol tutkunlarına <mark>yeni bir perspektif</mark> kazandırmayı ve profesyonellerin <mark>stratejik karar alma</mark> süreçlerinde rol oynamayı hedeflemektedir.
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

def render_league_season_selection():
    st.markdown("<h3>Lig ve Sezon Seçimi</h3>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-style: italic; color: gray;">
            Lütfen analiz yapmak istediğiniz lig ve sezonu seçiniz. Seçiminizi kaydettikten sonra analizler bu bilgilere göre gerçekleştirilecektir. Seçiminizi değiştirmek isterseniz bu sayfaya tekrar dönebilirsiniz.
        </div>
    """, unsafe_allow_html=True)

    selected_league = st.selectbox(
        "Lig:",
        ["Süper Lig"],
        index=None,
        key="league_select",
        placeholder="Ligler"
    )
    selected_season = st.selectbox(
        "Sezon:",
        ["2024/25", "2023/24"],
        index=None,
        key="season_select",
        placeholder="Sezonlar"
    )

    if st.button("Kaydet"):
        st.session_state["selected_league"] = selected_league
        st.session_state["selected_season"] = selected_season
        st.session_state["league_season_confirmed"] = True
        st.success(f"{st.session_state['selected_league']} {st.session_state['selected_season']} sezonu seçiminiz kaydedildi.")

def display_homepage():
    initialize_session_state()
    render_welcome_message()
    render_league_season_selection()

if __name__ == "__main__":
    display_homepage()