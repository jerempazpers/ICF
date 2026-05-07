import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json, copy, os

st.set_page_config(page_title="ICF — Indice de Citoyenneté Française", layout="wide")

SAVE_FILE = "icf_saved_data.json"

# ─── Données initiales (fichier MATLAB) ────────────────────────────────────
ORIGINAL_DATA = {
    "racisme": {
        "label": "Infractions racistes", "unit": "nb infractions", "inv": True,
        "years": [2016,2017,2018,2019,2020,2021,2022,2023,2024],
        "vals":  [9185,8637,9267,10842,11312,13064,12618,15000,16335],
    },
    "participation": {
        "label": "Participation électorale", "unit": "%", "inv": False,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024],
        "vals":  [60.1,60.0,56.5,56.5,56.5,52.0,47.4,46.9,46.9,50.3],
    },
    "presse": {
        "label": "Liberté de la presse (rang RSF)", "unit": "rang", "inv": True,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025],
        "vals":  [38,45,39,33,32,34,34,26,24,21,25],
    },
    "delinquance": {
        "label": "Délinquance", "unit": "nb atteintes", "inv": True,
        "years": [2016,2017,2018,2019,2020,2021,2022,2023,2024],
        "vals":  [269770,280910,306213,330675,333438,379518,430843,454685,464685],
    },
    "laicite": {
        "label": "Incidents laïcité", "unit": "nb incidents", "inv": True,
        "years": [2020,2021,2022,2023,2024],
        "vals":  [935,2226,2167,4710,6554],
    },
    "salaires": {
        "label": "Écart salaires H/F", "unit": "%", "inv": True,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024],
        "vals":  [19.1,18.4,17.9,17.5,16.6,15.8,15.5,14.8,14.2,13.9],
    },
    "decrochage": {
        "label": "Décrochage scolaire", "unit": "%", "inv": True,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022,2023],
        "vals":  [9.2,8.8,8.8,8.7,8.2,8.0,7.8,7.6,7.6],
    },
    "pauvrete": {
        "label": "Taux de pauvreté", "unit": "%", "inv": True,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022],
        "vals":  [13.9,13.7,13.8,14.5,14.3,13.6,14.5,14.4],
    },
    "violences": {
        "label": "Violences faites aux femmes", "unit": "nb cas", "inv": True,
        "years": [2016,2017,2018,2019,2020,2021,2022,2023],
        "vals":  [16916,17559,18591,18591,22764,33040,35138,37176],
    },
    "rsa": {
        "label": "Non-recours RSA", "unit": "%", "inv": False,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022],
        "vals":  [7.7,7.6,7.7,7.7,7.7,8.0,7.7,7.7],
    },
    "rcds": {
        "label": "Réservistes RCDS", "unit": "effectifs", "inv": False,
        "years": [2015,2016,2017,2018,2019,2020,2021,2022,2023],
        "vals":  [4062,4251,5230,5544,5732,5729,5980,6800,7110],
    },
}

YEARS_AXIS = list(range(2015, 2031))
BLUE, RED  = "#378ADD", "#E24B4A"

# ─── Persistance fichier JSON ────────────────────────────────────────────────
def load_saved():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return copy.deepcopy(ORIGINAL_DATA)

def write_save(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── Calculs ─────────────────────────────────────────────────────────────────
def z_norm_100(arr, inv):
    arr = np.array(arr, float)
    mu, sigma = arr.mean(), arr.std()
    if sigma == 0:
        return np.full(len(arr), 50.0)
    z  = (arr - mu) / sigma
    zn = np.clip((z + 3) / 6, 0, 1) * 100
    return np.round(100 - zn if inv else zn, 1)

def build_series(ind):
    years = np.array(ind["years"])
    vals  = np.array(ind["vals"], float)
    a, b  = np.polyfit(years, vals, 1)

    real_by_year = dict(zip(ind["years"], ind["vals"]))
    all_vals = np.array([real_by_year.get(y, a*y+b) for y in YEARS_AXIS])
    is_real  = np.array([y in real_by_year for y in YEARS_AXIS])

    scores   = z_norm_100(all_vals, ind["inv"])
    proj_raw = np.array([a*y+b for y in YEARS_AXIS])
    as_, _   = np.polyfit(YEARS_AXIS, scores, 1)

    last_idx   = int(np.where(is_real)[0][-1])
    last_score = float(scores[last_idx])
    prev_score = float(scores[last_idx-1]) if last_idx > 0 else None

    return {
        "scores":       scores,
        "real_scores":  np.where(is_real, scores, np.nan),
        "real_raw":     np.where(is_real, all_vals, np.nan),
        "proj_raw":     proj_raw,
        "slope":        round(float(as_), 3),
        "last_score":   last_score,
        "prev_score":   prev_score,
        "proj_2030":    float(scores[-1]),
    }

def compute_global(data):
    matrix = np.vstack([build_series(ind)["scores"] for ind in data.values()])
    return np.round(np.nanmean(matrix, axis=0), 2)

# ─── Graphiques ───────────────────────────────────────────────────────────────
def score_fig(s, label):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=YEARS_AXIS, y=s["scores"], mode="lines",
        name="Projection linéaire (2015–2030)",
        line=dict(color=RED, dash="dash", width=1.5),
        hovertemplate="%{x}: %{y:.1f}<extra>Projection</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=YEARS_AXIS, y=s["real_scores"], mode="lines+markers",
        name="Score réel",
        line=dict(color=BLUE, width=2), marker=dict(size=7, color=BLUE),
        connectgaps=False,
        hovertemplate="%{x}: %{y:.1f}<extra>Score réel</extra>",
    ))
    fig.update_layout(
        title=f"Score normalisé — {label}", height=400,
        xaxis=dict(tickvals=YEARS_AXIS, tickangle=45, title="Année"),
        yaxis=dict(range=[0, 100], title="Score (0–100)"),
        legend=dict(orientation="h", y=-0.3),
        margin=dict(l=55, r=20, t=50, b=90),
    )
    return fig

def raw_fig(s, label, unit):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=YEARS_AXIS, y=s["proj_raw"], mode="lines",
        name="Projection linéaire (2015–2030)",
        line=dict(color=RED, dash="dash", width=1.5),
        hovertemplate="%{x}: %{y:,.2f}<extra>Projection</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=YEARS_AXIS, y=s["real_raw"], mode="lines+markers",
        name="Données réelles",
        line=dict(color=BLUE, width=2), marker=dict(size=7, color=BLUE),
        connectgaps=False,
        hovertemplate=f"%{{x}}: %{{y:,.2f}} {unit}<extra>Réel</extra>",
    ))
    fig.update_layout(
        title=f"Données brutes — {label}", height=400,
        xaxis=dict(tickvals=YEARS_AXIS, tickangle=45, title="Année"),
        yaxis=dict(title=unit),
        legend=dict(orientation="h", y=-0.3),
        margin=dict(l=60, r=20, t=50, b=90),
    )
    return fig

# ─── Session state ────────────────────────────────────────────────────────────
# saved_data  → dernière sauvegarde permanente (référence pour "Réinitialiser")
# data        → état courant affiché (peut diverger de saved_data)

if "saved_data" not in st.session_state:
    st.session_state.saved_data = load_saved()
if "data" not in st.session_state:
    st.session_state.data = copy.deepcopy(st.session_state.saved_data)

# ─── Actions ──────────────────────────────────────────────────────────────────
def _parse_edited(key, edited_df):
    unit = st.session_state.data[key]["unit"]
    clean = edited_df.dropna(subset=["Année", unit])
    return (
        list(clean["Année"].astype(int)),
        list(clean[unit].astype(float)),
    )

def do_apply(key, edited_df):
    yrs, vals = _parse_edited(key, edited_df)
    st.session_state.data[key]["years"] = yrs
    st.session_state.data[key]["vals"]  = vals

def do_save_permanent(key, edited_df):
    do_apply(key, edited_df)
    st.session_state.saved_data = copy.deepcopy(st.session_state.data)
    write_save(st.session_state.saved_data)

def do_reset(key):
    ref = st.session_state.saved_data
    st.session_state.data[key] = copy.deepcopy(
        ref[key] if key in ref else ORIGINAL_DATA[key]
    )

def do_delete(key):
    del st.session_state.data[key]
    if key in st.session_state.saved_data:
        del st.session_state.saved_data[key]
    write_save(st.session_state.saved_data)

# ─── Titre ────────────────────────────────────────────────────────────────────
st.title("🇫🇷 Indice de Citoyenneté Française (ICF)")
st.caption("Tableau de bord · Données 2015–2024 · Projection linéaire jusqu'en 2030")

data = st.session_state.data
tab_names = ["ICF Global"] + [ind["label"] for ind in data.values()]
tabs = st.tabs(tab_names)

# ══════════════════════════════════════════════════════════════════════════════
# ONGLET GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    if not data:
        st.warning("Aucun indicateur disponible.")
    else:
        gs   = compute_global(data)
        ag, bg = np.polyfit(YEARS_AXIS, gs, 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score 2024", f"{gs[YEARS_AXIS.index(2024)]:.1f} / 100")
        c2.metric("Tendance",   f"{ag:+.2f} pts/an")
        c3.metric("Projection 2030", f"{gs[-1]:.1f} / 100")
        c4.metric("Indicateurs actifs", len(data))

        fig_g = go.Figure()
        fig_g.add_trace(go.Scatter(
            x=YEARS_AXIS, y=[ag*y+bg for y in YEARS_AXIS],
            mode="lines", name="Projection linéaire",
            line=dict(color=RED, dash="dash", width=1.5),
        ))
        fig_g.add_trace(go.Scatter(
            x=YEARS_AXIS, y=gs, mode="lines+markers+text",
            name="ICF Global",
            line=dict(color=BLUE, width=2.5), marker=dict(size=7),
            text=[f"{v:.1f}" for v in gs],
            textposition="top center", textfont=dict(size=10),
        ))
        fig_g.update_layout(
            title="Évolution ICF Global — moyenne des indices normalisés",
            height=460,
            xaxis=dict(tickvals=YEARS_AXIS, tickangle=45),
            yaxis=dict(range=[0, 100], title="Score moyen (0–100)"),
            legend=dict(orientation="h", y=-0.25),
            margin=dict(l=50, r=20, t=55, b=90),
        )
        st.plotly_chart(fig_g, use_container_width=True)

        st.subheader("Scores par indicateur (2015–2024)")
        rows = {
            ind["label"]: {
                str(y): f"{build_series(ind)['scores'][i]:.1f}"
                for i, y in enumerate(YEARS_AXIS) if y <= 2024
            }
            for ind in data.values()
        }
        st.dataframe(pd.DataFrame(rows).T, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ONGLETS INDIVIDUELS
# ══════════════════════════════════════════════════════════════════════════════
for tab_idx, (key, ind) in enumerate(list(data.items()), start=1):
    with tabs[tab_idx]:
        s = build_series(ind)

        # Métriques
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dernier score réel", f"{s['last_score']:.1f} / 100")
        c2.metric("Tendance", f"{s['slope']:+.2f} pts/an")
        c3.metric("Projection 2030", f"{s['proj_2030']:.1f} / 100")
        if s["prev_score"] is not None:
            c4.metric("Variation", f"{s['last_score']-s['prev_score']:+.1f} pts")

        # Courbes
        col_l, col_r = st.columns(2)
        with col_l:
            st.plotly_chart(score_fig(s, ind["label"]), use_container_width=True)
        with col_r:
            st.plotly_chart(raw_fig(s, ind["label"], ind["unit"]), use_container_width=True)

        st.divider()

        # ── Éditeur ──────────────────────────────────────────────────────────
        st.subheader("Modifier les données")

        # Bandeau d'état : modif non sauvegardée ?
        saved_ref = st.session_state.saved_data.get(key)
        has_unsaved = saved_ref is not None and (
            saved_ref["years"] != ind["years"] or saved_ref["vals"] != ind["vals"]
        )
        if has_unsaved:
            st.warning("⚠️ Modifications en cours — pas encore sauvegardées définitivement.")

        edited = st.data_editor(
            pd.DataFrame({"Année": ind["years"], ind["unit"]: ind["vals"]}),
            num_rows="dynamic",
            column_config={
                "Année": st.column_config.NumberColumn(
                    "Année", min_value=2000, max_value=2040, step=1, format="%d"),
                ind["unit"]: st.column_config.NumberColumn(ind["unit"], format="%.4g"),
            },
            key=f"editor_{key}",
            use_container_width=True,
        )

        # ── 3 boutons ─────────────────────────────────────────────────────────
        st.markdown("")
        col_a, col_p, col_r, _ = st.columns([2.2, 2.8, 1.8, 2])

        with col_a:
            if st.button(
                "▶ Appliquer la modif", key=f"apply_{key}", use_container_width=True,
                help="Met à jour les courbes — ne sauvegarde pas sur disque"
            ):
                do_apply(key, edited)
                st.rerun()

        with col_p:
            if st.button(
                "💾 Sauvegarder pour toujours", key=f"perm_{key}",
                use_container_width=True, type="primary",
                help="Sauvegarde sur disque — devient la nouvelle référence du bouton Réinitialiser"
            ):
                do_save_permanent(key, edited)
                st.success("✅ Sauvegarde permanente effectuée !")
                st.rerun()

        with col_r:
            if st.button(
                "↺ Réinitialiser", key=f"reset_{key}", use_container_width=True,
                help="Revient à la dernière sauvegarde permanente"
            ):
                do_reset(key)
                st.rerun()

        # ── Supprimer l'indicateur ────────────────────────────────────────────
        st.markdown("")
        with st.expander("⚠️ Supprimer cet indicateur"):
            st.warning(
                f"Supprimer **{ind['label']}** le retirera de l'ICF global et de tous les onglets. "
                "Cette action est permanente (écrase la sauvegarde sur disque)."
            )
            confirmed = st.checkbox(
                f"Je confirme la suppression de « {ind['label']} »",
                key=f"confirm_del_{key}"
            )
            if st.button(
                "🗑 Supprimer définitivement", key=f"del_{key}",
                disabled=not confirmed, type="primary"
            ):
                do_delete(key)
                st.rerun()

        # ── Export JSON ───────────────────────────────────────────────────────
        with st.expander("Exporter les données (JSON)"):
            json_str = json.dumps(
                {"label": ind["label"], "unit": ind["unit"],
                 "years": ind["years"], "vals":  ind["vals"]},
                indent=2, ensure_ascii=False,
            )
            st.code(json_str, language="json")
            st.download_button(
                f"⬇ Télécharger icf_{key}.json", data=json_str,
                file_name=f"icf_{key}.json", mime="application/json",
                key=f"dl_{key}",
            )
