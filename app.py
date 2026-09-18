import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

st.set_page_config(page_title="Д'Онтов систем - Симулација", layout="wide")

st.title("📊 Интерактивна симулација Д'Онтовог система")
st.markdown("Унесите податке о изборима да бисте видели тачну расподелу мандата и тестирали **Шта ако?** сценарије.")

# --- ПОМОЋНА ФУНКЦИЈА ЗА РАЧУНАЊЕ МАНДАТА ---
def racunaj_mandate(stranke_glasovi, ukupno_mandata, cenzus_glasovi):
    mandati = {ime: 0 for ime, gl in stranke_glasovi.items() if gl >= cenzus_glasovi}
    if not mandati: 
        return {}, []
    
    istorija = []
    for i in range(1, ukupno_mandata + 1):
        najveci_kolicnik = -1
        dobitnik = ""
        for ime in mandati.keys():
            kolicnik = stranke_glasovi[ime] / (mandati[ime] + 1)
            if kolicnik > najveci_kolicnik:
                najveci_kolicnik = kolicnik
                dobitnik = ime
        mandati[dobitnik] += 1
        istorija.append({"Мандат": i, "Странка": dobitnik, "Количник": f"{najveci_kolicnik:,.2f}"})
    return mandati, istorija

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

if 'stranke_df' not in st.session_state:
    st.session_state.stranke_df = pd.DataFrame([
        {"Име странке": "Странка А", "Број гласова": 1600000},
        {"Име странке": "Странка Б", "Број гласова": 900000},
        {"Име странке": "Странка В (испод цензуса)", "Број гласова": 105000}
    ])

edited_df = st.data_editor(st.session_state.stranke_df, num_rows="dynamic", use_container_width=True)
stranke = {row["Име странке"]: row["Број гласова"] for idx, row in edited_df.iterrows() if pd.notna(row["Име странке"]) and pd.notna(row["Број гласова"])}

if not stranke:
    st.warning("Морате унети барем једну странку!")
    st.stop()

# --- КРЕИРАЊЕ ТАБОВА ЗА ПРИКАЗ ---
tab1, tab2 = st.tabs(["📊 Главни резултати", "🔮 Шта ако? (Симулација промене цензуса)"])

# ==========================================
# ТАБ 1: ГЛАВНИ РЕЗУЛТАТИ
# ==========================================
with tab1:
    glasovi_ispod = sum(gl for gl in stranke.values() if gl < cenzus_glasovi)
    procenat_ispod = (glasovi_ispod / vazeci_glasovi) * 100 if vazeci_glasovi > 0 else 0

    if procenat_ispod > 0:
        st.error(f"⚠️ **ГЛАСОВИ ИСПОД ЦЕНЗУСА: {glasovi_ispod:,} ({procenat_ispod:.1f}%)**\n\nОви гласови су избрисани из формуле. Највећа странка математички преузима највећи део ових расутих гласова.")
    else:
        st.success("Све унете странке су прешле цензус. Нема расутих гласова.")

    mandati, istorija = racunaj_mandate(stranke, ukupno_mandata, cenzus_glasovi)
    
    if not mandati:
        st.error("Ниједна странка није прешла цензус!")
    else:
        sortirani_rezultati = sorted(mandati.items(), key=lambda x: x[1], reverse=True)
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

        ax.set_title("Утицај расутих гласова на расподелу мандата", fontweight='bold')
        ax.set_ylabel("Проценат (%)")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(imena_bar, rotation=45, ha='right')
        ax.legend()

        for i, m in enumerate(mandati_bar):
            ax.text(x_pos[i] + width/2, procenat_mandata[i] + 0.5, f"{m} м.", ha='center', fontweight='bold')

        st.pyplot(fig)

        st.subheader("📜 Редослед доделе мандата")
        st.dataframe(pd.DataFrame(istorija), use_container_width=True)


# ==========================================
# ТАБ 2: ШТА АКО СЦЕНАРИО (What-If)
# ==========================================
with tab2:
    st.subheader("Анализа: Шта се дешава ако неко пређе/падне испод цензуса?")
    st.markdown("""
    Означите или одзначите странке испод. 
    - Ако означите странку која је била испод црте, програм јој додељује **тачно онолико гласова колико је цензус**.
    - Ако одзначите странку која је прешла, програм јој скида гласове на **1 глас испод цензуса**.
    Графикон ће аутоматски показати коме се одузимају, а коме додају мандати.
    """)

    col_box1, col_box2 = st.columns(2)
    nove_stranke_glasovi = {}
    
    # Интерактивни Checkbox-ови
    for idx, (ime, gl) in enumerate(stranke.items()):
        presla_orig = gl >= cenzus_glasovi
        
        with col_box1 if idx % 2 == 0 else col_box2:
            status_txt = "🟢 ПРЕШЛА" if presla_orig else "🔴 ИСПОД ЦРТЕ"
            nova_vrednost = st.checkbox(f"{ime} (Стварно: {status_txt})", value=presla_orig, key=f"chk_{ime}")
            
            if nova_vrednost and not presla_orig:
                nove_stranke_glasovi[ime] = cenzus_glasovi
            elif not nova_vrednost and presla_orig:
                nove_stranke_glasovi[ime] = cenzus_glasovi - 1
            else:
                nove_stranke_glasovi[ime] = gl

    # Рачунање нових мандата у реалном времену
    orig_mandati, _ = racunaj_mandate(stranke, ukupno_mandata, cenzus_glasovi)
    novi_mandati, _ = racunaj_mandate(nove_stranke_glasovi, ukupno_mandata, cenzus_glasovi)

    sve_stranke = set(orig_mandati.keys()).union(set(novi_mandati.keys()))
    razlike = {s: novi_mandati.get(s, 0) - orig_mandati.get(s, 0) for s in sve_stranke}
    
    aktivne_stranke = [s for s in razlike.keys() if orig_mandati.get(s, 0) > 0 or novi_mandati.get(s, 0) > 0]
    aktivne_stranke.sort(key=lambda x: razlike[x], reverse=True)

    if not aktivne_stranke:
        st.info("Промените стање неке странке да бисте видели промене у мандатима.")
    else:
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        
        vrijednosti_razlike = [razlike[s] for s in aktivne_stranke]
        boje = ['#4CAF50' if val > 0 else '#F44336' if val < 0 else 'gray' for val in vrijednosti_razlike]

        bars = ax2.bar(aktivne_stranke, vrijednosti_razlike, color=boje, edgecolor='black')
        ax2.axhline(0, color='black', linewidth=1)

        ax2.set_title("Ефекат промене цензуса на мандате", fontsize=14, fontweight='bold')
        ax2.set_ylabel("Изгубљени / Добијени мандати")
        ax2.set_xticklabels(aktivne_stranke, rotation=45, ha='right')
        
        # Исписивање бројева изнад/испод стубића
        for s, bar, val in zip(aktivne_stranke, bars, vrijednosti_razlike):
            stari_broj = orig_mandati.get(s, 0)
            novi_broj = novi_mandati.get(s, 0)
            tekst = f"{val:+d}\n({stari_broj} -> {novi_broj})"
            
            y_pos = bar.get_height() + 0.5 if val >= 0 else bar.get_height() - 2.5
            ax2.text(bar.get_x() + bar.get_width()/2, y_pos, tekst, ha='center', va='bottom' if val>=0 else 'top', fontweight='bold', fontsize=10)

        y_min, y_max = ax2.get_ylim()
        ax2.set_ylim(y_min - max(3, abs(y_min)*0.2), y_max + max(3, abs(y_max)*0.2))

        st.pyplot(fig2)

        st.info("💡 **ЗАКЉУЧАК:** Када странка која је била испод цензуса пређе праг, њени нови мандати се директно одузимају од других странака. Највише мандата губи највећа странка, јер је она претходно присвојила највећи део тих 'расутих' гласова.")
