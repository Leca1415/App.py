import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

st.set_page_config(page_title="Д'Онтов систем - Симулација", layout="wide")

st.title("📊 Интерактивна симулација Д'Онтовог система")
st.markdown("Унесите податке о изборима да бисте видели тачну расподелу мандата и утицај расутих гласова.")

# --- УНОС ОПШТИХ ПОДАТАКА ---
col1, col2, col3, col4 = st.columns(4)
ukupno_mandata = col1.number_input("Укупан број мандата:", min_value=1, value=250)
ukupno_glasaca = col2.number_input("Укупан број гласача:", min_value=1, value=3800000)
nevazeci_listici = col3.number_input("Неважећи листићи:", min_value=0, value=100000)
cenzus_procenat = col4.number_input("Цензус (%):", min_value=0.0, value=3.0, step=0.1)

vazeci_glasovi = ukupno_glasaca - nevazeci_listici
cenzus_glasovi = int(vazeci_glasovi * (cenzus_procenat / 100)) if vazeci_glasovi > 0 else 0

st.info(f"🟢 **Потребно гласова за цензус: {cenzus_glasovi:,}** (од {vazeci_glasovi:,} важећих гласова)")

# --- УНОС СТРАНАКА (Интерактивна табела) ---
st.subheader("📝 Унос странака")
st.write("Додајте странке у табелу испод. Можете директно мењати имена, бројеве гласова или додавати нове редове.")

if 'stranke_df' not in st.session_state:
    st.session_state.stranke_df = pd.DataFrame([
        {"Име странке": "Странка А", "Број гласова": 1600000},
        {"Име странке": "Странка Б", "Број гласова": 900000},
        {"Име странке": "Странка В (испод цензуса)", "Број гласова": 105000}
    ])

# Табела коју корисник може да мења уживо на вебу
edited_df = st.data_editor(st.session_state.stranke_df, num_rows="dynamic", use_container_width=True)

# Конвертовање табеле у речник
stranke = {row["Име странке"]: row["Број гласова"] for idx, row in edited_df.iterrows() if pd.notna(row["Име странке"]) and pd.notna(row["Број гласова"])}

# --- СИМУЛАЦИЈА ---
if st.button("🚀 ПОКРЕНИ СИМУЛАЦИЈУ", type="primary"):
    if not stranke:
        st.warning("Морате унети барем једну странку!")
        st.stop()

    stranke_cenzus = {}
    glasovi_ispod = 0

    for ime, gl in stranke.items():
        if gl >= cenzus_glasovi:
            stranke_cenzus[ime] = gl
        else:
            glasovi_ispod += gl

    procenat_ispod = (glasovi_ispod / vazeci_glasovi) * 100 if vazeci_glasovi > 0 else 0

    if procenat_ispod > 0:
        st.error(f"⚠️ **ГЛАСОВИ ИСПОД ЦЕНЗУСА: {glasovi_ispod:,} ({procenat_ispod:.1f}%)**\n\nОви гласови су избрисани из формуле. Због тога странке изнад цензуса добијају већи проценат мандата него што имају проценат гласова.")
    else:
        st.success("Све унете странке су прешле цензус.")

    if not stranke_cenzus:
        st.error("Ниједна странка није прешла цензус!")
        st.stop()

    # Д'Онтова логика
    mandati = {ime: 0 for ime in stranke_cenzus}
    istorija_dodele = []

    for i in range(1, ukupno_mandata + 1):
        najveci_kolicnik = 0
        dobitnik = ""
        for ime, glasovi in stranke_cenzus.items():
            kolicnik = glasovi / (mandati[ime] + 1)
            if kolicnik > najveci_kolicnik:
                najveci_kolicnik = kolicnik
                dobitnik = ime

        mandati[dobitnik] += 1
        istorija_dodele.append({"Мандат": i, "Странка": dobitnik, "Количник": f"{najveci_kolicnik:,.2f}"})

    sortirani_rezultati = sorted(mandati.items(), key=lambda x: x[1], reverse=True)

    # --- ПРИКАЗ РЕЗУЛТАТА (Графикони) ---
    st.subheader("📊 Резултати симулације")
    
    imena_bar = [x[0] for x in sortirani_rezultati if x[1] > 0]
    mandati_bar = [x[1] for x in sortirani_rezultati if x[1] > 0]
    
    procenat_glasova = [(stranke[ime] / vazeci_glasovi) * 100 for ime in imena_bar]
    procenat_mandata = [(m / ukupno_mandata) * 100 for m in mandati_bar]

    cmap = plt.get_cmap('tab10')
    boje_bar = [cmap(i % 10) for i in range(len(imena_bar))]

    fig, ax = plt.subplots(figsize=(10, 6))
    x_pos = np.arange(len(imena_bar))
    width = 0.4

    ax.bar(x_pos - width/2, procenat_glasova, width, label='% Стварних гласова', color='lightgray', edgecolor='black')
    ax.bar(x_pos + width/2, procenat_mandata, width, label='% Мандата у парламенту', color=boje_bar, edgecolor='black')

    ax.set_title("Утицај расутих гласова (Разлика између % гласова и % мандата)", fontweight='bold')
    ax.set_ylabel("Проценат (%)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(imena_bar, rotation=45, ha='right')
    ax.legend()

    for i, m in enumerate(mandati_bar):
        ax.text(x_pos[i] + width/2, procenat_mandata[i] + 0.5, f"{m} м.", ha='center', fontweight='bold')

    # Streamlit метода за приказ matplotlib графикона
    st.pyplot(fig)

    # Приказ табеле корак-по-корак
    st.subheader("📜 Редослед доделе мандата")
    st.dataframe(pd.DataFrame(istorija_dodele), use_container_width=True)