import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import date
import io

# ==========================================
# KONFIGURACJA STRONY
# ==========================================
st.set_page_config(page_title="Oferomat - System Wycen", page_icon="🏗️", layout="wide")

# ==========================================
# SYMULACJA BAZY DANYCH (CENNIK)
# ==========================================
@st.cache_data
def load_cennik():
    data = [
        {"Kategoria": "Prace wyburzeniowe", "Usługa": "Skuwanie płytek", "Jednostka": "m2", "Robocizna": 50.0, "Materiał": 5.0},
        {"Kategoria": "Prace wyburzeniowe", "Usługa": "Wyburzenie ściany z cegły", "Jednostka": "m2", "Robocizna": 120.0, "Materiał": 10.0},
        {"Kategoria": "Zabudowa G-K", "Usługa": "Ścianka działowa G-K", "Jednostka": "m2", "Robocizna": 90.0, "Materiał": 65.0},
        {"Kategoria": "Zabudowa G-K", "Usługa": "Sufit podwieszany", "Jednostka": "m2", "Robocizna": 110.0, "Materiał": 75.0},
        {"Kategoria": "Elektryka", "Usługa": "Punkt elektryczny", "Jednostka": "szt", "Robocizna": 70.0, "Materiał": 35.0},
        {"Kategoria": "Hydraulika", "Usługa": "Punkt wod-kan", "Jednostka": "szt", "Robocizna": 150.0, "Materiał": 60.0},
        {"Kategoria": "Malowanie", "Usługa": "Malowanie dwukrotne", "Jednostka": "m2", "Robocizna": 20.0, "Materiał": 8.0},
        {"Kategoria": "Płytki", "Usługa": "Układanie gresu", "Jednostka": "m2", "Robocizna": 130.0, "Materiał": 45.0},
    ]
    return pd.DataFrame(data)

cennik_df = load_cennik()

# ==========================================
# INICJALIZACJA STANU SESJI (STATE MANAGEMENT)
# ==========================================
if 'kosztorys' not in st.session_state:
    st.session_state.kosztorys = []
if 'klient' not in st.session_state:
    st.session_state.klient = {"imie": "", "adres": "", "termin": str(date.today())}

# ==========================================
# FUNKCJE POMOCNICZE
# ==========================================
def dodaj_pozycje(kategoria, usluga, ilosc):
    wiersz = cennik_df[(cennik_df["Kategoria"] == kategoria) & (cennik_df["Usługa"] == usluga)].iloc[0]
    koszt_robocizny = wiersz["Robocizna"] * ilosc
    koszt_materialu = wiersz["Materiał"] * ilosc
    
    st.session_state.kosztorys.append({
        "Kategoria": kategoria,
        "Usługa": usluga,
        "Ilość": ilosc,
        "Jednostka": wiersz["Jednostka"],
        "Robocizna (Suma)": koszt_robocizny,
        "Materiał (Suma)": koszt_materialu,
        "Suma Netto": koszt_robocizny + koszt_materialu
    })

def usun_pozycje(index):
    st.session_state.kosztorys.pop(index)

# Prosta funkcja usuwająca polskie znaki dla podstawowego PDF (bez zewnętrznych fontów TTF)
def usun_pl_znaki(text):
    pl_znaki = {'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z',
                'Ą':'A', 'Ć':'C', 'Ę':'E', 'Ł':'L', 'Ń':'N', 'Ó':'O', 'Ś':'S', 'Ź':'Z', 'Ż':'Z'}
    for pl, ang in pl_znaki.items():
        text = str(text).replace(pl, ang)
    return text

def generuj_pdf(dane_klienta, df_kosztorys, robocizna, materialy, marza_kwota, netto, brutto, vat_proc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    # Nagłówek
    pdf.set_font("helvetica", style="B", size=16)
    pdf.cell(200, 10, txt="OFERTA CENOWA", ln=True, align='C')
    pdf.set_font("helvetica", size=10)
    pdf.cell(200, 10, txt=f"Data wygenerowania: {date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # Dane klienta
    pdf.set_font("helvetica", style="B", size=12)
    pdf.cell(200, 10, txt="Dane Klienta i Inwestycji:", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(200, 8, txt=f"Klient: {usun_pl_znaki(dane_klienta['imie'])}", ln=True)
    pdf.cell(200, 8, txt=f"Adres: {usun_pl_znaki(dane_klienta['adres'])}", ln=True)
    pdf.cell(200, 8, txt=f"Proponowany termin: {dane_klienta['termin']}", ln=True)
    pdf.ln(10)
    
    # Podsumowanie finansowe
    pdf.set_font("helvetica", style="B", size=12)
    pdf.cell(200, 10, txt="Podsumowanie Kosztow (PLN):", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.cell(100, 8, txt=f"Koszty robocizny:", ln=False); pdf.cell(100, 8, txt=f"{robocizna:.2f}", ln=True)
    pdf.cell(100, 8, txt=f"Koszty materialow:", ln=False); pdf.cell(100, 8, txt=f"{materialy:.2f}", ln=True)
    pdf.cell(100, 8, txt=f"Marza/Narzut:", ln=False); pdf.cell(100, 8, txt=f"{marza_kwota:.2f}", ln=True)
    pdf.cell(100, 8, txt=f"Wartosc NETTO:", ln=False); pdf.cell(100, 8, txt=f"{netto:.2f}", ln=True)
    pdf.cell(100, 8, txt=f"Stawka VAT:", ln=False); pdf.cell(100, 8, txt=f"{vat_proc}%", ln=True)
    
    pdf.set_font("helvetica", style="B", size=14)
    pdf.cell(100, 12, txt=f"Wartosc BRUTTO:", ln=False); pdf.cell(100, 12, txt=f"{brutto:.2f} PLN", ln=True)
    pdf.ln(20)
    
    # Klauzula
    pdf.set_font("helvetica", style="I", size=9)
    pdf.multi_cell(0, 5, txt=usun_pl_znaki("Powyzsza oferta ma charakter informacyjny i nie stanowi oferty handlowej w rozumieniu art. 66 §1 Kodeksu Cywilnego. Waznosc oferty: 14 dni."))
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# INTERFEJS UŻYTKOWNIKA (UI)
# ==========================================
st.title("🏗️ Oferomat - System Ofertowania")

# Zakładki
tab1, tab2, tab3, tab4 = st.tabs(["👤 Dane Klienta", "🛠️ Kreator Wyceny", "💰 Kosztorys i Ustawienia", "📊 Dashboard"])

# --- ZAKŁADKA 1: DANE KLIENTA ---
with tab1:
    st.header("Dane Inwestora")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.klient["imie"] = st.text_input("Imię i Nazwisko / Nazwa firmy", value=st.session_state.klient["imie"])
    with col2:
        st.session_state.klient["adres"] = st.text_input("Adres inwestycji", value=st.session_state.klient["adres"])
    st.session_state.klient["termin"] = st.date_input("Proponowany termin realizacji")

# --- ZAKŁADKA 2: KREATOR WYCENY ---
with tab2:
    st.header("Dodaj pozycje do kosztorysu")
    
    # Formularz dodawania usług
    with st.expander("Wybierz i dodaj usługę", expanded=True):
        col_cat, col_srv, col_qty, col_btn = st.columns([2, 3, 1, 1])
        
        with col_cat:
            wybrana_kategoria = st.selectbox("Kategoria", cennik_df["Kategoria"].unique())
        
        with col_srv:
            dostepne_uslugi = cennik_df[cennik_df["Kategoria"] == wybrana_kategoria]
            wybrana_usluga = st.selectbox("Usługa", dostepne_uslugi["Usługa"].tolist())
            
        with col_qty:
            jednostka = dostepne_uslugi[dostepne_uslugi["Usługa"] == wybrana_usluga].iloc[0]["Jednostka"]
            ilosc = st.number_input(f"Ilość [{jednostka}]", min_value=0.1, value=1.0, step=1.0)
            
        with col_btn:
            st.write("") # Odstęp
            st.write("")
            if st.button("➕ Dodaj", use_container_width=True):
                dodaj_pozycje(wybrana_kategoria, wybrana_usluga, ilosc)
                st.success("Dodano!")

    # Wyświetlanie aktualnego kosztorysu
    st.subheader("Bieżące pozycje")
    if st.session_state.kosztorys:
        df_kosztorys = pd.DataFrame(st.session_state.kosztorys)
        st.dataframe(df_kosztorys, use_container_width=True)
        
        # Opcja usunięcia ostatniej pozycji
        if st.button("❌ Usuń ostatnią pozycję"):
            usun_pozycje(-1)
            st.rerun()
    else:
        st.info("Brak pozycji w kosztorysie. Dodaj pierwszą usługę.")

# --- ZAKŁADKA 3: KOSZTORYS I USTAWIENIA ---
with tab3:
    st.header("Ustawienia Finansowe i Podsumowanie")
    
    if st.session_state.kosztorys:
        df_k = pd.DataFrame(st.session_state.kosztorys)
        
        col_fin1, col_fin2, col_fin3 = st.columns(3)
        with col_fin1:
            marza = st.number_input("Globalna Marża (%)", min_value=-50.0, max_value=200.0, value=20.0, step=1.0)
        with col_fin2:
            vat = st.selectbox("Stawka VAT (%)", options=[8, 23], index=0, help="8% dla mieszkalnictwa, 23% dla firm")
        
        # Obliczenia
        suma_robocizna = df_k["Robocizna (Suma)"].sum()
        suma_material = df_k["Materiał (Suma)"].sum()
        koszt_bazowy = suma_robocizna + suma_material
        
        kwota_marzy = koszt_bazowy * (marza / 100)
        kwota_netto = koszt_bazowy + kwota_marzy
        kwota_vat = kwota_netto * (vat / 100)
        kwota_brutto = kwota_netto + kwota_vat

        st.markdown("### 📋 Podsumowanie końcowe")
        
        # Wyświetlanie w metrykach dla estetyki
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Koszty Bazowe", f"{koszt_bazowy:.2f} PLN")
        m2.metric(f"Marża ({marza}%)", f"{kwota_marzy:.2f} PLN")
        m3.metric("Wartość NETTO", f"{kwota_netto:.2f} PLN")
        m4.metric(f"Wartość BRUTTO (VAT {vat}%)", f"{kwota_brutto:.2f} PLN")
        
        st.divider()
        st.subheader("⬇️ Eksport dokumentów")
        
        col_exp1, col_exp2 = st.columns(2)
        
        # Eksport do Excel (CSV)
        with col_exp1:
            csv = df_k.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Pobierz kosztorys (CSV)",
                data=csv,
                file_name='kosztorys.csv',
                mime='text/csv',
                use_container_width=True
            )
            
        # Generowanie PDF
        with col_exp2:
            pdf_bytes = generuj_pdf(
                st.session_state.klient, df_k, 
                suma_robocizna, suma_material, kwota_marzy, kwota_netto, kwota_brutto, vat
            )
            st.download_button(
                label="📄 Pobierz Gotową Ofertę (PDF)",
                data=pdf_bytes,
                file_name="Oferta_Remontowa.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
    else:
        st.warning("Przejdź do zakładki 'Kreator Wyceny' i dodaj pozycje, aby zobaczyć podsumowanie.")

# --- ZAKŁADKA 4: DASHBOARD ANALITYCZNY ---
with tab4:
    st.header("Struktura Kosztów Oferty")
    
    if st.session_state.kosztorys:
        # Przygotowanie danych do wykresu kołowego
        dane_wykres = pd.DataFrame({
            "Kategoria": ["Robocizna", "Materiały", "Marża Firmy"],
            "Wartość": [suma_robocizna, suma_material, kwota_marzy]
        })
        
        fig = px.pie(
            dane_wykres, 
            values='Wartość', 
            names='Kategoria', 
            title='Rozkład Finansowy Projektu (wartości Netto)',
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'],
            hole=0.4 # Wykres pierścieniowy
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dodaj pozycje do kosztorysu, aby wygenerować wykresy analityczne.")
