from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="L'électricité dans 12 quartiers", page_icon="⚡", layout="wide")

st.title("L'électricité dans 12 quartiers")
st.caption("Relevés mensuels de janvier 2024 à décembre 2025. Données fictives.")

# Etape 2
@st.cache_data
def charger():
    return pd.read_csv(DOSSIER / "consommation_propre.csv")
 
 
df = charger()
 
st.write(
    "Une compagnie d'électricité a relevé la consommation de 12 quartiers de "
    "Port-au-Prince, Delmas, Pétion-Ville et Cap-Haïtien pendant deux ans."
)
st.write(
    "La question du directeur : la consommation suit-elle la chaleur, "
    "ou les heures de courant ?"
)


# Etape 3
communes = sorted(df["commune"].unique())
choix = st.sidebar.multiselect("Communes", communes, default=communes)
 
annees = sorted(df["annee"].unique(), reverse=True) 
annee = st.sidebar.selectbox("Année", annees)
 
if not choix:
    st.warning("Choisissez au moins une commune dans la barre latérale.")
    st.stop()
 
df_c = df[df["commune"].isin(choix)]           
filtre = df_c[df_c["annee"] == annee]           
 
# Etape 4
col1, col2, col3 = st.columns(3)
col1.metric(f"Consommation totale {annee}", f"{filtre['kwh'].sum() / 1e6:.2f} millions de kWh")
col2.metric("Consommation par abonné", f"{filtre['kwh_par_abonne'].mean():.1f} kWh")
col3.metric("Heures de courant par jour", f"{filtre['heures_courant'].mean():.1f} h")
 
# Etape 5
onglets = st.tabs([
    "Quartiers",
    "Évolution",
    "Chaleur ou courant ?",
    "Coupures",
    "Relevés hors norme",
])
 
with onglets[0]:
    st.subheader("Quels quartiers consomment le plus par abonné ?")
    classement = (
        df_c.groupby("quartier")["kwh_par_abonne"].mean().round(1).sort_values(ascending=False)
    )
    st.bar_chart(classement)
    par_type = df_c.groupby("type")["kwh_par_abonne"].mean().round(1)
    if {"Commercial", "Résidentiel"} <= set(par_type.index):
        st.write(
            f"Un abonné commercial consomme en moyenne {par_type['Commercial']} kWh par mois, "
            f"contre {par_type['Résidentiel']} pour un abonné résidentiel. "
            f"En tête : {classement.index[0]} ({classement.iloc[0]})."
        )
    else:
        st.write(f"En tête : {classement.index[0]} ({classement.iloc[0]} kWh par abonné).")
 
with onglets[1]:
    st.subheader("Comment la consommation évolue-t-elle ?")
    courbes = df_c.pivot_table(
        index="mois", columns="commune", values="kwh_par_abonne", aggfunc="mean"
    )
    st.line_chart(courbes)
    totaux = df_c.pivot_table(index="commune", columns="annee", values="kwh", aggfunc="sum")
    hausse = ((totaux[2025] / totaux[2024] - 1) * 100).sort_values(ascending=False)
    st.write(
        f"{hausse.index[0]} progresse le plus entre 2024 et 2025 (+{hausse.iloc[0]:.1f} %), "
        f"{hausse.index[-1]} le moins (+{hausse.iloc[-1]:.1f} %)."
    )
 
with onglets[2]:
    st.subheader("La consommation suit-elle la chaleur, ou les heures de courant ?")
    residentiel = df_c[df_c["type"] == "Résidentiel"]
    st.scatter_chart(residentiel, x="heures_courant", y="kwh_par_abonne")
    corr_courant = residentiel["kwh_par_abonne"].corr(residentiel["heures_courant"])
    corr_temp = residentiel["kwh_par_abonne"].corr(residentiel["temperature_c"])
    st.write(
        f"Quartiers résidentiels : la corrélation de la consommation par abonné est de "
        f"{corr_courant:.2f} avec les heures de courant et de {corr_temp:.2f} avec la température."
    )
 
with onglets[3]:
    st.subheader("Où les coupures sont-elles les plus longues ?")
    mediane = df_c.groupby("commune")["heures_courant"].median().round(1)
    st.bar_chart(mediane)
    faibles = df_c[(df_c["annee"] == 2025) & (df_c["heures_courant"] < 8)]
    st.write(
        f"{mediane.idxmin()} a la médiane la plus basse ({mediane.min()} heures par jour). "
        f"En 2025, {len(faibles)} relevé(s) passent sous 8 heures de courant par jour."
    )
 
with onglets[4]:
    st.subheader("Quels relevés sortent du lot ?")
    top3 = df_c.nlargest(3, "kwh")[["mois", "quartier", "type", "kwh"]]
    st.dataframe(top3, hide_index=True)
    st.write(
        f"La plus grosse consommation est celle de {top3.iloc[0]['quartier']} "
        f"en {top3.iloc[0]['mois']} ({top3.iloc[0]['kwh']:,.0f} kWh)."
    )
 
# Etape 6
st.markdown("---")
st.markdown(
    """
### Conclusion
 
Dans les quartiers résidentiels, la consommation par abonné suit les **heures de courant**
(corrélation de 0.76) et non la chaleur (-0.15 avec la température).
Les coupures sont les plus longues à Cap-Haïtien (médiane de 10.0 heures contre 11.6 à 11.9 ailleurs),
où la consommation a aussi le plus augmenté (+22.4 %).
Une corrélation ne prouve pas une cause : elle montre que deux séries varient ensemble,
pas que l'une provoque l'autre.
"""
)
 
with st.expander("Voir les données filtrées"):
    st.dataframe(filtre, hide_index=True)
 