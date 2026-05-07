import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json, copy, os, hashlib

st.set_page_config(
    page_title="ICF — Les Enfants de la République",
    page_icon="🇫🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

SAVE_FILE = "icf_saved_data.json"
BLUE, RED = "#378ADD", "#E24B4A"

# ════════════════════════════════════════════════════════════════════════════
# DONNÉES
# ════════════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ════════════════════════════════════════════════════════════════════════════

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def load_users():
    """Charge les comptes admin depuis st.secrets ou users.json."""
    try:
        users = dict(st.secrets["users"])
        roles = dict(st.secrets["roles"])
        return {u: {"hash": h, "role": roles.get(u, "visitor")}
                for u, h in users.items()}
    except Exception:
        pass
    if os.path.exists("users.json"):
        try:
            with open("users.json") as f: return json.load(f)
        except Exception:
            pass
    # Fallback : seul compte admin par défaut
    return {"admin": {"hash": hash_pw("admin1234"), "role": "admin"}}

def check_login(username, password):
    user = load_users().get(username.strip().lower())
    if user and user["hash"] == hash_pw(password):
        return user["role"]
    return None

# ── Session state : par défaut visiteur anonyme, pas de connexion requise ──
if "is_admin" not in st.session_state:
    st.session_state.is_admin       = False
if "show_login_form" not in st.session_state:
    st.session_state.show_login_form = False

IS_ADMIN = st.session_state.is_admin

# ════════════════════════════════════════════════════════════════════════════
# PERSISTANCE
# ════════════════════════════════════════════════════════════════════════════

def load_saved():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return copy.deepcopy(ORIGINAL_DATA)

def write_save(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "saved_data" not in st.session_state:
    st.session_state.saved_data = load_saved()
if "data" not in st.session_state:
    st.session_state.data = copy.deepcopy(st.session_state.saved_data)

# ════════════════════════════════════════════════════════════════════════════
# CALCULS
# ════════════════════════════════════════════════════════════════════════════

def z_norm_100(arr, inv):
    arr = np.array(arr, float)
    mu, sigma = arr.mean(), arr.std()
    if sigma == 0: return np.full(len(arr), 50.0)
    zn = np.clip(((arr - mu) / sigma + 3) / 6, 0, 1) * 100
    return np.round(100 - zn if inv else zn, 1)

def build_series(ind):
    years = np.array(ind["years"]); vals = np.array(ind["vals"], float)
    a, b  = np.polyfit(years, vals, 1)
    rby   = dict(zip(ind["years"], ind["vals"]))
    all_v = np.array([rby.get(y, a*y+b) for y in YEARS_AXIS])
    is_r  = np.array([y in rby for y in YEARS_AXIS])
    scores = z_norm_100(all_v, ind["inv"])
    as_, _ = np.polyfit(YEARS_AXIS, scores, 1)
    li = int(np.where(is_r)[0][-1])
    return {
        "scores":      scores,
        "real_scores": np.where(is_r, scores, np.nan),
        "real_raw":    np.where(is_r, all_v, np.nan),
        "proj_raw":    np.array([a*y+b for y in YEARS_AXIS]),
        "slope":       round(float(as_), 3),
        "last_score":  float(scores[li]),
        "prev_score":  float(scores[li-1]) if li > 0 else None,
        "proj_2030":   float(scores[-1]),
    }

def compute_global(data):
    return np.round(np.nanmean(
        np.vstack([build_series(ind)["scores"] for ind in data.values()]), axis=0), 2)

# ════════════════════════════════════════════════════════════════════════════
# GRAPHIQUES
# ════════════════════════════════════════════════════════════════════════════

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

# ════════════════════════════════════════════════════════════════════════════
# ACTIONS ADMIN
# ════════════════════════════════════════════════════════════════════════════

def _parse(key, df):
    unit  = st.session_state.data[key]["unit"]
    clean = df.dropna(subset=["Année", unit])
    return list(clean["Année"].astype(int)), list(clean[unit].astype(float))

def do_apply(key, df):
    y, v = _parse(key, df)
    st.session_state.data[key]["years"] = y
    st.session_state.data[key]["vals"]  = v

def do_save_permanent(key, df):
    do_apply(key, df)
    st.session_state.saved_data = copy.deepcopy(st.session_state.data)
    write_save(st.session_state.saved_data)

def do_reset(key):
    ref = st.session_state.saved_data
    st.session_state.data[key] = copy.deepcopy(
        ref[key] if key in ref else ORIGINAL_DATA[key])

def do_delete(key):
    del st.session_state.data[key]
    if key in st.session_state.saved_data:
        del st.session_state.saved_data[key]
    write_save(st.session_state.saved_data)

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🇫🇷 ICF")
    st.caption("Les Enfants de la République\nIndice de Citoyenneté Française")
    st.divider()

    if IS_ADMIN:
        # ── Connecté en admin ────────────────────────────────────────────────
        st.success("👑 Connecté en tant qu'admin")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.is_admin        = False
            st.session_state.show_login_form = False
            # On recharge les données depuis la sauvegarde propre
            st.session_state.data = copy.deepcopy(st.session_state.saved_data)
            st.rerun()
    else:
        # ── Visiteur anonyme ─────────────────────────────────────────────────
        st.info("👁 Mode visiteur\nConsultation libre, sans connexion.")

        if not st.session_state.show_login_form:
            if st.button("🔑 Connexion admin", use_container_width=True):
                st.session_state.show_login_form = True
                st.rerun()
        else:
            # Formulaire de connexion dans la sidebar
            st.markdown("**Connexion administrateur**")
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Identifiant")
                password = st.text_input("Mot de passe", type="password")
                col_ok, col_cancel = st.columns(2)
                submitted = col_ok.form_submit_button("→ Entrer", use_container_width=True,
                                                       type="primary")
                cancelled = col_cancel.form_submit_button("Annuler", use_container_width=True)

            if submitted:
                role = check_login(username, password)
                if role == "admin":
                    st.session_state.is_admin        = True
                    st.session_state.show_login_form = False
                    st.success("Connecté !")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

            if cancelled:
                st.session_state.show_login_form = False
                st.rerun()

    st.divider()
    st.markdown(
        "<a href='https://ledlr.org' style='font-size:11px;color:gray;'>"
        "ledlr.org</a>",
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ════════════════════════════════════════════════════════════════════════════

st.title("🇫🇷 Indice de Citoyenneté Française (ICF)")
st.caption("Les Enfants de la République · Données 2015–2024 · Projection linéaire jusqu'en 2030")

data      = st.session_state.data
tab_names = ["ICF Global"] + [ind["label"] for ind in data.values()]
tabs      = st.tabs(tab_names)

# ════════════════════════════════════════════════════════════════════════════
# ONGLET GLOBAL
# ════════════════════════════════════════════════════════════════════════════

with tabs[0]:
    if not data:
        st.warning("Aucun indicateur disponible.")
    else:
        gs     = compute_global(data)
        ag, bg = np.polyfit(YEARS_AXIS, gs, 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score 2024",         f"{gs[YEARS_AXIS.index(2024)]:.1f} / 100")
        c2.metric("Tendance",           f"{ag:+.2f} pts/an")
        c3.metric("Projection 2030",    f"{gs[-1]:.1f} / 100")
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

# ════════════════════════════════════════════════════════════════════════════
# ONGLETS INDIVIDUELS
# ════════════════════════════════════════════════════════════════════════════

for tab_idx, (key, ind) in enumerate(list(data.items()), start=1):
    with tabs[tab_idx]:
        s = build_series(ind)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dernier score réel", f"{s['last_score']:.1f} / 100")
        c2.metric("Tendance",           f"{s['slope']:+.2f} pts/an")
        c3.metric("Projection 2030",    f"{s['proj_2030']:.1f} / 100")
        if s["prev_score"] is not None:
            c4.metric("Variation",      f"{s['last_score']-s['prev_score']:+.1f} pts")

        col_l, col_r = st.columns(2)
        with col_l:
            st.plotly_chart(score_fig(s, ind["label"]), use_container_width=True)
        with col_r:
            st.plotly_chart(raw_fig(s, ind["label"], ind["unit"]), use_container_width=True)

        # ── Section édition (admin uniquement) ───────────────────────────────
        if IS_ADMIN:
            st.divider()
            st.subheader("Modifier les données")

            saved_ref   = st.session_state.saved_data.get(key)
            has_unsaved = saved_ref is not None and (
                saved_ref["years"] != ind["years"] or saved_ref["vals"] != ind["vals"])
            if has_unsaved:
                st.warning("⚠️ Modifications en cours — pas encore sauvegardées définitivement.")

            edited = st.data_editor(
                pd.DataFrame({"Année": ind["years"], ind["unit"]: ind["vals"]}),
                num_rows="dynamic",
                column_config={
                    "Année":     st.column_config.NumberColumn(
                                     "Année", min_value=2000, max_value=2040,
                                     step=1, format="%d"),
                    ind["unit"]: st.column_config.NumberColumn(ind["unit"], format="%.4g"),
                },
                key=f"editor_{key}",
                use_container_width=True,
            )

            col_a, col_p, col_r2, _ = st.columns([2.2, 2.8, 1.8, 2])
            with col_a:
                if st.button("▶ Appliquer la modif", key=f"apply_{key}",
                             use_container_width=True,
                             help="Met à jour les courbes sans sauvegarder sur disque"):
                    do_apply(key, edited); st.rerun()
            with col_p:
                if st.button("💾 Sauvegarder pour toujours", key=f"perm_{key}",
                             use_container_width=True, type="primary",
                             help="Sauvegarde permanente sur disque"):
                    do_save_permanent(key, edited)
                    st.success("✅ Sauvegarde permanente effectuée !")
                    st.rerun()
            with col_r2:
                if st.button("↺ Réinitialiser", key=f"reset_{key}",
                             use_container_width=True,
                             help="Revient à la dernière sauvegarde permanente"):
                    do_reset(key); st.rerun()

            st.markdown("")
            with st.expander("⚠️ Supprimer cet indicateur"):
                st.warning(
                    f"Supprimer **{ind['label']}** le retirera définitivement "
                    "de l'ICF global et de tous les onglets.")
                confirmed = st.checkbox(
                    f"Je confirme la suppression de « {ind['label']} »",
                    key=f"confirm_del_{key}")
                if st.button("🗑 Supprimer définitivement", key=f"del_{key}",
                             disabled=not confirmed, type="primary"):
                    do_delete(key); st.rerun()

        else:
            # Visiteur : invitation discrète à se connecter pour modifier
            st.caption("🔒 Connectez-vous en admin (sidebar) pour modifier les données.")

        # ── Export JSON (tout le monde) ──────────────────────────────────────
        with st.expander("Exporter les données (JSON)"):
            json_str = json.dumps(
                {"label": ind["label"], "unit": ind["unit"],
                 "years": ind["years"], "vals": ind["vals"]},
                indent=2, ensure_ascii=False)
            st.code(json_str, language="json")
            st.download_button(
                f"⬇ Télécharger icf_{key}.json", data=json_str,
                file_name=f"icf_{key}.json", mime="application/json",
                key=f"dl_{key}")
