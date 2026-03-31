import streamlit as st
import pandas as pd
from db_service import get_data_as_df, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Gabinet Medycyny Pracy", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# --- URUCHOMIENIE STYLU PRO ---
apply_pro_style()

# --- FUNKCJA GENERUJĄCA KARTY PREMIUM (HTML/CSS INJECTION) ---
def premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    """Generuje nowoczesną kartę statystyk wyglądającą jak z drogiego SaaS-a."""
    html = f"""
    <div style="
        background: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 10px 15px -3px rgba(0, 0, 0, 0.1)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px -1px rgba(0, 0, 0, 0.05)'">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span style="color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
            <span style="font-size: 1.2rem; background: #f8fafc; padding: 10px; border-radius: 12px; border: 1px solid #f1f5f9;">{icon}</span>
        </div>
        <div style="color: #0f172a; font-size: 2.2rem; font-weight: 700; line-height: 1;">{value}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {badge_color}; background: {badge_bg}; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">{badge_text}</span>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 500;">Aktualny stan bazy</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- POBRANIE DANYCH DO DASHBOARDU ---
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

# --- GŁÓWNY NAGŁÓWEK (Custom HTML dla lepszego fontu) ---
st.markdown("<h2 style='font-weight: 800; color: #0f172a; margin-bottom: 0; letter-spacing: -0.5px;'>System Obsługi Gabinetu</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;'>Witaj w nowoczesnym panelu dowodzenia.</p>", unsafe_allow_html=True)

# --- WYŚWIETLANIE KART PREMIUM ---
c1, c2, c3 = st.columns(3)
with c1:
    premium_card("Zarejestrowani Pacjenci", str(len(df_pacjenci)), "👥", "+ Aktywni", "#059669", "#d1fae5")
with c2:
    premium_card("Obsługiwane Firmy", str(len(df_firmy)), "🏢", "+ Kontrakty", "#2563eb", "#dbeafe")
with c3:
    dzisiejsze = len(df_wizyty[df_wizyty['DataWizyty'] == str(pd.Timestamp.today().date())]) if not df_wizyty.empty else 0
    kolor_tla = "#ffedd5" if dzisiejsze > 0 else "#f1f5f9"
    kolor_tekstu = "#ea580c" if dzisiejsze > 0 else "#64748b"
    premium_card("Dzisiejsze Wizyty", str(dzisiejsze), "📅", "W poczekalni", kolor_tekstu, kolor_tla)

st.markdown("<br>", unsafe_allow_html=True)

# --- NOWOCZESNA TABELA ---
st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1rem;'>Ostatnie aktywności</h4>", unsafe_allow_html=True)

if not df_wizyty.empty:
    df_display = df_wizyty[['DataWizyty', 'TypBadania', 'Status']].tail(5).sort_values('DataWizyty', ascending=False)
    
    # Wykorzystanie Column Config do upiększenia standardowej tabeli
    st.dataframe(
        df_display,
        column_config={
            "DataWizyty": st.column_config.TextColumn("🗓️ Data Wizyty"),
            "TypBadania": st.column_config.TextColumn("🩺 Rodzaj Badań"),
            "Status": st.column_config.TextColumn("📌 Status")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Brak zaplanowanych wizyt.")
