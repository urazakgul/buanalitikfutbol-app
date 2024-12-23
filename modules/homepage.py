import streamlit as st

def display_homepage():
    st.markdown('<h1 class="big-font">BAF - SÜPER LİG\'e Hoş Geldiniz</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div>
            <p>
            Bu uygulama, Süper Lig özelinde detaylı analizler ve etkileyici görselleştirmeler sunarak, <mark>veri odaklı bakış açısını</mark> güçlendirmeyi, futbol tutkunlarına <mark>yeni bir perspektif</mark> kazandırmayı ve profesyonellerin <mark>stratejik karar alma</mark> süreçlerinde rol oynamayı hedeflemektedir.
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    display_homepage()