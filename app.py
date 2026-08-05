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

def z_apply_fixed(arr, mu, sigma, inv):
    """Applique une normalisation Z-score avec mu/sigma fixes."""
    arr = np.array(arr, float)
    if sigma == 0: return np.full(len(arr), 50.0)
    zn = np.clip(((arr - mu) / sigma + 3) / 6, 0, 1) * 100
    return np.round(100 - zn if inv else zn, 1)

def compute_score_for_year(ind, target_year):
    """
    Calcule le score d'un indicateur pour une année cible donnée.
    Fenêtre glissante : [target_year-9, target_year] (10 ans).
    Si les données ne couvrent pas encore target_year, extrapole par régression.
    """
    years = np.array(ind["years"]); vals = np.array(ind["vals"], float)
    a, b  = np.polyfit(years, vals, 1)
    rby   = dict(zip(ind["years"], ind["vals"]))

    win_start = target_year - 9
    win_years = list(range(win_start, target_year + 1))   # 10 ans glissants
    win_vals  = np.array([rby.get(y, a*y+b) for y in win_years])

    mu    = win_vals.mean()
    sigma = win_vals.std(ddof=1)
    if sigma == 0:
        return 50.0, mu, sigma

    val_target = rby.get(target_year, a*target_year + b)
    zn    = np.clip(((val_target - mu) / sigma + 3) / 6, 0, 1) * 100
    score = round(float(100 - zn if ind["inv"] else zn), 1)
    return score, round(float(mu), 4), round(float(sigma), 4)

def build_series(ind):
    """
    Construit la série complète 2015-2030 pour affichage.
    - Années avec frozen_scores : utilise le score figé
    - Autres années réelles     : calcule avec fenêtre glissante [Y-9, Y]
    - Années projetées          : régression sur les scores figés
    """
    years = np.array(ind["years"]); vals = np.array(ind["vals"], float)
    a, b  = np.polyfit(years, vals, 1)
    rby   = dict(zip(ind["years"], ind["vals"]))
    frozen = ind.get("frozen_scores", {})   # {"2024": 21.6, ...}

    # ── Calcul score pour chaque année réelle ─────────────────────────────
    all_v  = np.array([rby.get(y, a*y+b) for y in YEARS_AXIS])
    is_r   = np.array([y in rby for y in YEARS_AXIS])

    scores = np.full(len(YEARS_AXIS), np.nan)
    for i, y in enumerate(YEARS_AXIS):
        str_y = str(y)
        if str_y in frozen:
            # Score définitivement figé
            scores[i] = frozen[str_y]
        elif is_r[i]:
            # Année réelle non encore figée : calcul fenêtre glissante
            score, _, _ = compute_score_for_year(ind, y)
            scores[i] = score
        else:
            # Année projetée : on laisse NaN, sera interpolé pour le graphique

            scores[i] = np.nan

    # ── Régression sur les scores connus pour projeter 2025-2030 ─────────
    known_y = [YEARS_AXIS[i] for i in range(len(YEARS_AXIS)) if not np.isnan(scores[i])]
    known_s = [scores[i]     for i in range(len(YEARS_AXIS)) if not np.isnan(scores[i])]

    proj_scores = scores.copy()
    if len(known_y) >= 2:
        as_, bs_ = np.polyfit(known_y, known_s, 1)
        for i, y in enumerate(YEARS_AXIS):
            if np.isnan(scores[i]):
                proj_scores[i] = round(float(as_*y + bs_), 1)
        slope = round(float(as_), 3)
    else:
        slope = 0.0

    # ── Indices utiles ────────────────────────────────────────────────────
    real_idx  = [i for i in range(len(YEARS_AXIS)) if is_r[i]]
    li        = real_idx[-1] if real_idx else 0

    real_scores_arr = np.where(is_r, proj_scores, np.nan)
    # Pour les années réelles, on veut le vrai score (pas la projection)
    for i in range(len(YEARS_AXIS)):
        if is_r[i]:
            real_scores_arr[i] = scores[i] if not np.isnan(scores[i]) else proj_scores[i]

    return {
        "scores":      proj_scores,          # toute la plage 2015-2030 (proj incluses)
        "real_scores": real_scores_arr,      # NaN sur années non réelles
        "real_raw":    np.where(is_r, all_v, np.nan),
        "proj_raw":    np.array([a*y+b for y in YEARS_AXIS]),
        "slope":       slope,
        "last_score":  float(proj_scores[li]),
        "prev_score":  float(proj_scores[li-1]) if li > 0 else None,
        "proj_2030":   float(proj_scores[-1]),
        "last_real_year": int(YEARS_AXIS[li]),
    }

def compute_global(data):
    """Moyenne des scores par année sur tous les indicateurs (pour la courbe de projection)."""
    all_scores = []
    for ind in data.values():
        s = build_series(ind)
        all_scores.append(s["scores"])
    return np.round(np.nanmean(np.vstack(all_scores), axis=0), 2)

def get_frozen_icf_series(data):
    """
    Retourne la série des ICF gelés (definitifs) par année ICF.
    ICF année X = moyenne des frozen_scores[str(X)] de tous les indicateurs.
    Si un indicateur n'a pas de frozen_score pour X, on l'exclut de la moyenne.
    Retourne un dict {annee_icf: icf_moyen}.
    """
    # Collecte tous les frozen_scores de tous les indicateurs
    all_frozen = {}  # {str_year: [scores...]}
    for ind in data.values():
        for yr_str, sc in ind.get("frozen_scores", {}).items():
            all_frozen.setdefault(yr_str, []).append(sc)
    # Moyenne par année
    return {int(yr): round(float(np.mean(scs)), 1)
            for yr, scs in sorted(all_frozen.items())}

def compute_icf_for_year(data, icf_year):
    """
    Calcule l'ICF d'une année donnée à la volée (non figé).
    ICF année X = moyenne de compute_score_for_year(ind, X-1) pour tous les indicateurs.
    Fenêtre : [X-10, X-1] (10 ans de données).
    """
    target = icf_year - 1
    scores = []
    for ind in data.values():
        sc, _, _ = compute_score_for_year(ind, target)
        scores.append(sc)
    return round(float(np.mean(scores)), 1)

def freeze_year(key, target_year):
    """
    Fige définitivement l'ICF d'une année pour un indicateur.
    ICF année X = compute_score_for_year(ind, X-1) — fenêtre [X-10, X-1].
    Stocké sous frozen_scores[str(X)].
    """
    ind   = st.session_state.data[key]
    # On score sur X-1 (dernière année de données), pas sur X
    score, mu, sigma = compute_score_for_year(ind, target_year - 1)
    if "frozen_scores" not in st.session_state.data[key]:
        st.session_state.data[key]["frozen_scores"] = {}
    st.session_state.data[key]["frozen_scores"][str(target_year)] = score
    st.session_state.saved_data = copy.deepcopy(st.session_state.data)
    write_save(st.session_state.saved_data)
    return score, mu, sigma

def freeze_year_all(target_year):
    """Fige l'ICF de target_year pour TOUS les indicateurs en une fois."""
    results = {}
    for key in list(st.session_state.data.keys()):
        score, mu, sigma = freeze_year(key, target_year)
        results[key] = score
    return results

# ════════════════════════════════════════════════════════════════════════════
# GRAPHIQUES
# ════════════════════════════════════════════════════════════════════════════

def score_fig(s, label):
    # L'axe X = années d'indice = années de données + 1
    # Ex : données 2024 → indice 2025
    indice_axis = [y + 1 for y in YEARS_AXIS]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=indice_axis, y=s["scores"], mode="lines",
        name="Projection linéaire",
        line=dict(color=RED, dash="dash", width=1.5),
        hovertemplate="Indice %{x}: %{y:.1f}<extra>Projection</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=indice_axis, y=s["real_scores"], mode="lines+markers",
        name="Indice réel",
        line=dict(color=BLUE, width=2), marker=dict(size=7, color=BLUE),
        connectgaps=False,
        hovertemplate="Indice %{x}: %{y:.1f}<extra>Indice réel</extra>",
    ))
    fig.update_layout(
        title=f"Indice normalisé — {label}", height=400,
        xaxis=dict(tickvals=indice_axis, tickangle=45, title="Année de l'indice"),
        yaxis=dict(range=[0, 100], title="Indice (0–100)"),
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

def do_create(label, unit, inv, rows_df):
    """Crée un nouvel indicateur à partir du formulaire admin."""
    # Clé interne : slug sans accents ni espaces
    import re, unicodedata
    slug = unicodedata.normalize("NFD", label.lower())
    slug = "".join(c for c in slug if unicodedata.category(c) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")[:30]
    # Éviter les doublons de clé
    base, n = slug, 1
    while slug in st.session_state.data:
        slug = f"{base}_{n}"; n += 1

    clean = rows_df.dropna(subset=["Année", "Valeur"])
    if clean.empty:
        return None, "Aucune donnée valide saisie."
    years = list(clean["Année"].astype(int))
    vals  = list(clean["Valeur"].astype(float))
    if len(years) < 2:
        return None, "Il faut au moins 2 points de données."

    new_ind = {"label": label.strip(), "unit": unit.strip() or "valeur",
               "inv": inv, "years": years, "vals": vals}
    st.session_state.data[slug]       = new_ind
    st.session_state.saved_data[slug] = copy.deepcopy(new_ind)
    write_save(st.session_state.saved_data)
    return slug, None

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════

# Init états sidebar
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False

with st.sidebar:
    st.title("🇫🇷 ICF")
    st.caption("Les Enfants de la République\nIndice de Citoyenneté Française")
    st.divider()

    if IS_ADMIN:
        # ── Connecté en admin ────────────────────────────────────────────────
        st.success("👑 Connecté en tant qu'admin")

        # Bouton créer un indicateur
        if not st.session_state.show_create_form:
            if st.button("➕ Créer un indicateur", use_container_width=True, type="primary"):
                st.session_state.show_create_form = True
                st.rerun()
        else:
            st.markdown("### Nouvel indicateur")

            new_label = st.text_input("Nom de l'indicateur *",
                                      placeholder="ex : Taux de chômage")
            new_unit  = st.text_input("Unité de mesure",
                                      placeholder="ex : %, nb, score…")
            new_inv   = st.radio(
                "Sens de l'indicateur",
                options=[False, True],
                format_func=lambda x: (
                    "↑ Hausse = bon (ex : participation)"   if not x
                    else "↑ Hausse = mauvais (ex : chômage)"
                ),
                help="Détermine si une valeur qui monte améliore ou dégrade le score."
            )

            st.caption("Saisir les données année par année :")

            # Tableau de saisie dynamique — démarre avec 3 lignes vides
            if "new_ind_rows" not in st.session_state:
                st.session_state.new_ind_rows = pd.DataFrame(
                    {"Année": [2022, 2023, 2024], "Valeur": [None, None, None]}
                )

            new_rows = st.data_editor(
                st.session_state.new_ind_rows,
                num_rows="dynamic",
                column_config={
                    "Année":  st.column_config.NumberColumn(
                                  "Année", min_value=2000, max_value=2040,
                                  step=1, format="%d"),
                    "Valeur": st.column_config.NumberColumn("Valeur", format="%.10g"),
                },
                key="new_ind_editor",
                use_container_width=True,
            )

            col_ok, col_cancel = st.columns(2)
            with col_ok:
                create_clicked = st.button("✓ Créer", use_container_width=True,
                                           type="primary")
            with col_cancel:
                if st.button("✕ Annuler", use_container_width=True):
                    st.session_state.show_create_form = False
                    if "new_ind_rows" in st.session_state:
                        del st.session_state["new_ind_rows"]
                    st.rerun()

            if create_clicked:
                if not new_label.strip():
                    st.error("Le nom de l'indicateur est obligatoire.")
                else:
                    slug, err = do_create(new_label, new_unit, new_inv, new_rows)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.show_create_form = False
                        if "new_ind_rows" in st.session_state:
                            del st.session_state["new_ind_rows"]
                        st.success(f"✅ « {new_label.strip()} » créé !")
                        st.rerun()

        st.divider()
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.is_admin         = False
            st.session_state.show_login_form  = False
            st.session_state.show_create_form = False
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
st.caption("Les Enfants de la République · Indice de Citoyenneté Française · Projection linéaire jusqu'en 2030")

data           = st.session_state.data
max_year_global = max(max(ind["years"]) for ind in data.values()) if data else 2024
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

        # ── Sélecteur d'année ICF (admin) ou calcul automatique ─────────────
        import datetime
        CURRENT_YEAR = datetime.datetime.now().year

        last_years    = {key: min(max(ind["years"]), CURRENT_YEAR)
                         for key, ind in data.items()}
        first_years   = {key: min(ind["years"]) for key, ind in data.items()}
        first_data_yr = min(first_years.values())
        max_last      = max(last_years.values())
        min_last      = min(last_years.values())

        # Années ICF calculables : première_donnée+10 → max_last+1
        icf_min_calculable = first_data_yr + 10   # ex: 2015+10=2025
        icf_max_calculable = max_last + 1          # ex: 2025+1=2026

        # Sélecteur d'année ICF pour l'admin (stocké en session)
        if "selected_icf_year" not in st.session_state:
            st.session_state.selected_icf_year = min(icf_max_calculable,
                                                      CURRENT_YEAR + 1)

        # Re-clamp : si les données ont changé (ajout/suppression), l'année
        # sélectionnée peut être hors des bornes calculables → on la corrige
        st.session_state.selected_icf_year = max(
            icf_min_calculable,
            min(int(st.session_state.selected_icf_year), icf_max_calculable)
        )
        # Si le widget garde une valeur hors bornes, on le réinitialise
        if "icf_year_selector" in st.session_state:
            if (st.session_state.icf_year_selector > icf_max_calculable or
                st.session_state.icf_year_selector < icf_min_calculable):
                del st.session_state["icf_year_selector"]

        if IS_ADMIN:
            sel_col1, sel_col2 = st.columns([2, 6])
            with sel_col1:
                chosen = st.number_input(
                    "📅 Afficher l'ICF de l'année",
                    min_value=icf_min_calculable,
                    max_value=icf_max_calculable,
                    value=int(st.session_state.selected_icf_year),
                    step=1, key="icf_year_selector",
                    help=f"Années disponibles : {icf_min_calculable}–{icf_max_calculable}"
                )
                st.session_state.selected_icf_year = int(chosen)
            with sel_col2:
                st.caption(
                    f"ICF {chosen} = scores calculés sur les données "
                    f"**{int(chosen)-10}–{int(chosen)-1}** (fenêtre 10 ans)"
                )
        else:
            chosen = min(icf_max_calculable, CURRENT_YEAR + 1)

        icf_year       = int(chosen)
        target_data_yr = icf_year - 1        # dernière année de données utilisée
        win_start      = target_data_yr - 9  # 2025-1-9=2015
        win_end        = target_data_yr      # 2024

        # Indicateurs sans données réelles pour target_data_yr
        late_inds  = {key: data[key]["label"]
                      for key, yr in last_years.items() if yr < target_data_yr}
        ahead_inds = {key: data[key]["label"]
                      for key, yr in last_years.items() if yr > target_data_yr}

        c1, c2, c3, c4 = st.columns(4)

        # ── Garde : pas assez d'historique ───────────────────────────────────
        if win_start < first_data_yr:
            nb_years_avail = target_data_yr - first_data_yr + 1
            c1.metric(f"ICF {icf_year}", "— / 100")
            c2.metric("Tendance", f"{ag:+.2f} pts/an")
            c3.metric("Projection 2030", f"{gs[-1]:.1f} / 100")
            c4.metric("Indicateurs actifs", len(data))
            st.error(
                f"❌ **Impossible de calculer l'ICF {icf_year}.** "
                f"Il faut 10 années de données ({win_start}–{win_end}), "
                f"mais les premières données remontent à {first_data_yr} "
                f"({nb_years_avail} an{'s' if nb_years_avail > 1 else ''} "
                f"disponible{'s' if nb_years_avail > 1 else ''} au lieu de 10)."
            )

        # ── Cas normal : calcul ICF ─────────────────────────────────────────
        else:
            # ICF 2025 = pour chaque indicateur, score sur fenêtre [2015, 2024]
            # = compute_score_for_year(ind, target_data_yr=2024)
            # On calcule DIRECTEMENT, sans passer par gs (qui utilise build_series
            # avec des fenêtres variables selon les données de chaque indicateur).
            # Cela garantit que tous les indicateurs sont comparés sur la MÊME fenêtre.
            icf_scores_direct = {}
            for key, ind in data.items():
                sc, _, _ = compute_score_for_year(ind, target_data_yr)
                icf_scores_direct[key] = sc
            icf_last = round(float(np.mean(list(icf_scores_direct.values()))), 1)

            c1.metric(f"ICF {icf_year}", f"{icf_last:.1f} / 100",
                      help=f"Données : {win_start}–{win_end} (fenêtre 10 ans)")
            c2.metric("Tendance",           f"{ag:+.2f} pts/an")
            c3.metric("Projection 2030",    f"{gs[-1]:.1f} / 100")
            c4.metric("Indicateurs actifs", len(data))

            if late_inds:
                st.info(
                    f"ℹ️ Ces indicateurs n'ont pas de données pour {win_end} "
                    f"— extrapolés par régression : {', '.join(late_inds.values())}."
                )
            if ahead_inds:
                all_at_max = all(yr >= max_last for yr in last_years.values())
                if all_at_max:
                    st.success(f"✅ Tous les indicateurs ont des données jusqu'en {max_last}. "
                               f"**ICF {max_last + 1}** peut être calculé !")
                else:
                    st.warning(
                        f"⚠️ {', '.join(ahead_inds.values())} ont des données jusqu'en {max_last}. "
                        f"Mettez les autres à jour pour calculer **ICF {max_last + 1}**."
                    )

        # ── Panneau admin : geler les scores d'une année ─────────────────────
        if IS_ADMIN:
            with st.expander("🔒 Geler les scores d'une année (admin)"):
                # Années gelables :
                #   min = first_data_yr + 10  (10 ans de données disponibles)
                #   max = icf_year            (pas d'années sans données réelles)
                freeze_min = first_data_yr + 10
                freeze_max = icf_year

                if freeze_min > freeze_max:
                    st.warning(
                        f"Pas encore assez de données pour geler un ICF. "
                        f"Il faut des données jusqu'en {freeze_min - 1} minimum."
                    )
                else:
                    st.markdown(
                        f"Années gelables : **{freeze_min}** à **{freeze_max}** "
                        f"(10 ans de données réelles requis)."
                    )
                    col_yr, col_btn = st.columns([1, 2])
                    freeze_year_input = int(col_yr.number_input(
                        "Année à geler",
                        min_value=freeze_min, max_value=freeze_max,
                        value=min(int(icf_year), freeze_max),
                        step=1, key="freeze_year_global"
                    ))
                    fy_win = f"{freeze_year_input - 10}–{freeze_year_input - 1}"
                    col_yr.caption(f"Fenêtre : {fy_win}")

                    if col_btn.button(
                        f"🔒 Geler ICF {freeze_year_input} pour tous les indicateurs",
                        key="freeze_all", type="primary"
                    ):
                        results    = freeze_year_all(freeze_year_input)
                        icf_frozen = round(float(np.mean(list(results.values()))), 1)
                        st.success(f"✅ ICF {freeze_year_input} figé = **{icf_frozen}**")
                        st.rerun()

                # ── Tableau des ICF gelés ─────────────────────────────────────
                frozen_summary = {}
                for k, ind2 in data.items():
                    for yr, sc in ind2.get("frozen_scores", {}).items():
                        frozen_summary.setdefault(yr, {})[k] = (ind2["label"], sc)

                if frozen_summary:
                    st.markdown("---")
                    st.markdown("**📋 ICF gelés — historique définitif**")
                    frozen_rows = {}
                    for yr in sorted(frozen_summary):
                        row = {}
                        scores_yr = []
                        for k in data:
                            fs = data[k].get("frozen_scores", {})
                            if yr in fs:
                                row[data[k]["label"]] = fs[yr]
                                scores_yr.append(fs[yr])
                            else:
                                row[data[k]["label"]] = "—"
                        row["🏆 ICF moyen"] = round(float(np.mean(scores_yr)), 1)
                        frozen_rows[f"ICF {yr}"] = row
                    df_frozen = pd.DataFrame(frozen_rows).T
                    st.dataframe(df_frozen, use_container_width=True)

                    st.markdown("**Supprimer une année gelée :**")
                    cols_del = st.columns(min(len(frozen_summary), 6))
                    for i, yr in enumerate(sorted(frozen_summary)):
                        with cols_del[i % len(cols_del)]:
                            if st.button(f"🗑 ICF {yr}", key=f"del_frozen_global_{yr}"):
                                for k2 in list(data.keys()):
                                    fs2 = st.session_state.data[k2].get("frozen_scores", {})
                                    if yr in fs2:
                                        del st.session_state.data[k2]["frozen_scores"][yr]
                                st.session_state.saved_data = copy.deepcopy(st.session_state.data)
                                write_save(st.session_state.saved_data)
                                st.rerun()

        # ── Graphique ICF ─────────────────────────────────────────────────────
        frozen_icf      = get_frozen_icf_series(data)
        current_icf_val = compute_icf_for_year(data, icf_year)

        # ── Série historique 2015–2024 ────────────────────────────────────────
        # ICF calculé sur les données disponibles à l'époque, fenêtre incomplète
        # Affiché en gris pour signaler qu'ils sont indicatifs, pas méthodologiquement stricts
        HIST_START = 2015
        HIST_END   = 2024  # inclus — avant la fenêtre complète de 10 ans
        hist_years, hist_vals = [], []
        for yr in range(HIST_START, HIST_END + 1):
            target_yr = yr - 1   # données jusqu'à yr-1
            # Prend toutes les données disponibles jusqu'à target_yr
            scores_yr = []
            for ind2 in data.values():
                avail_years = [y for y in ind2["years"] if y <= target_yr]
                if not avail_years:
                    continue
                # Fenêtre : max 10 ans, ou moins si pas assez d'historique
                win_end2   = max(avail_years)
                win_start2 = max(min(avail_years), win_end2 - 9)
                win_yrs    = list(range(win_start2, win_end2 + 1))
                a2, b2     = np.polyfit(ind2["years"], ind2["vals"], 1)
                rby2       = dict(zip(ind2["years"], ind2["vals"]))
                wv         = np.array([rby2.get(y, a2*y+b2) for y in win_yrs])
                mu2, sg2   = wv.mean(), wv.std(ddof=1) if len(wv)>1 else 1.0
                if sg2 == 0: sg2 = 1.0
                val2  = rby2.get(win_end2, a2*win_end2+b2)
                zn2   = float(np.clip(((val2-mu2)/sg2+3)/6, 0, 1)*100)
                sc2   = round(100 - zn2 if ind2["inv"] else zn2, 1)
                scores_yr.append(sc2)
            if scores_yr:
                hist_years.append(yr)
                hist_vals.append(round(float(np.mean(scores_yr)), 1))

        # Régression sur ICF figés pour projection (ou sur historique si pas encore de gel)
        ref_x = list(frozen_icf.keys()) if len(frozen_icf) >= 2 else hist_years
        ref_y = list(frozen_icf.values()) if len(frozen_icf) >= 2 else hist_vals
        if len(ref_x) >= 2:
            fa, fb     = np.polyfit(ref_x, ref_y, 1)
            proj_start = min(ref_x + ([icf_year] if icf_year not in frozen_icf else []))
            proj_years = list(range(proj_start, 2031))
            proj_vals  = [fa*y+fb for y in proj_years]
        else:
            proj_years, proj_vals = [], []

        fig_g = go.Figure()

        # Pointillés de projection
        if proj_years:
            fig_g.add_trace(go.Scatter(
                x=proj_years, y=proj_vals,
                mode="lines", name="Tendance (projection)",
                line=dict(color=RED, dash="dash", width=1.5),
            ))

        # Série historique 2015–2024 en gris (fenêtre incomplète, indicatif)
        if hist_years:
            fig_g.add_trace(go.Scatter(
                x=hist_years, y=hist_vals,
                mode="lines+markers+text",
                name="ICF historique (fenêtre incomplète)",
                line=dict(color="#6B7280", width=1.5, dash="dot"),
                marker=dict(size=6, color="#6B7280"),
                text=[f"{v:.1f}" for v in hist_vals],
                textposition="top center",
                textfont=dict(size=9, color="#6B7280"),
            ))

        # ICF figés (points bleus pleins — définitifs)
        frozen_x = sorted(frozen_icf.keys())
        frozen_y = [frozen_icf[y] for y in frozen_x]
        if frozen_x:
            fig_g.add_trace(go.Scatter(
                x=frozen_x, y=frozen_y,
                mode="lines+markers+text", name="ICF figé (définitif)",
                line=dict(color=BLUE, width=2.5),
                marker=dict(size=9, color=BLUE),
                text=[f"{v:.1f}" for v in frozen_y],
                textposition="top center", textfont=dict(size=10),
            ))

        # ICF courant non figé (point orange creux — provisoire)
        if icf_year not in frozen_icf:
            fig_g.add_trace(go.Scatter(
                x=[icf_year], y=[current_icf_val],
                mode="markers+text", name=f"ICF {icf_year} (provisoire)",
                marker=dict(size=11, color="#F5A623",
                            symbol="circle-open", line=dict(width=2.5, color="#F5A623")),
                text=[f"{current_icf_val:.1f}"],
                textposition="top center", textfont=dict(size=10, color="#F5A623"),
            ))

        fig_g.update_layout(
            title="Évolution ICF Global",
            height=460,
            xaxis=dict(tickvals=list(range(2015, 2031)), tickangle=45, title="Année ICF"),
            yaxis=dict(range=[0, 100], title="Score ICF (0–100)"),
            legend=dict(orientation="h", y=-0.28),
            margin=dict(l=50, r=20, t=55, b=100),
        )
        st.plotly_chart(fig_g, use_container_width=True)

        # ── Tableau récap indices par indicateur avec code couleur ───────────
        all_real_years = sorted(set(
            y for ind in data.values() for y in ind["years"]
            if y <= CURRENT_YEAR
        ))
        st.subheader(f"Scores par indicateur (fenêtre {win_start}–{win_end} → ICF {icf_year})")

        # Légende
        st.markdown(
            "<div style='display:flex;gap:20px;font-size:13px;margin-bottom:8px;'>"
            "<span><span style='display:inline-block;width:14px;height:14px;"
            "background:#1E4A8C;border-radius:3px;vertical-align:middle;margin-right:5px;'>"
            "</span>Données réelles</span>"
            "<span><span style='display:inline-block;width:14px;height:14px;"
            "background:#5A3E7A;border-radius:3px;vertical-align:middle;margin-right:5px;'>"
            "</span>Extrapolé (régression)</span>"
            "</div>",
            unsafe_allow_html=True
        )

        # Colonnes = années ICF (y+1)
        # Règle : n'afficher ICF X que si AU MOINS UN indicateur a une donnée
        # réelle pour l'année X-1 (sinon toute la colonne serait extrapolée)
        icf_cols = []
        for y in all_real_years:
            icf_col = y + 1
            if icf_col > icf_year:
                continue
            data_yr = icf_col - 1  # = y
            # Au moins un indicateur a-t-il une vraie donnée pour data_yr ?
            has_real = any(data_yr in ind["years"] for ind in data.values())
            if has_real:
                icf_cols.append(icf_col)

        ind_labels = [ind["label"] for ind in data.values()]

        # Construit les valeurs et les couleurs cellule par cellule
        cell_vals   = []  # une liste par colonne ICF
        cell_colors = []  # couleur par cellule

        for icf_col_yr in icf_cols:
            data_yr = icf_col_yr - 1  # année de données correspondante
            col_vals   = []
            col_colors = []
            for key, ind in data.items():
                sc, _, _ = compute_score_for_year(ind, data_yr)
                is_real  = data_yr in ind["years"]
                col_vals.append(f"{sc:.1f}")
                col_colors.append("#1E4A8C" if is_real else "#5A3E7A")
            cell_vals.append(col_vals)
            cell_colors.append(col_colors)

        fig_table = go.Figure(data=[go.Table(
            header=dict(
                values=["<b>Indicateur</b>"] + [f"<b>ICF {y}</b>" for y in icf_cols],
                fill_color="#0D1B2A",
                font=dict(color="white", size=12),
                align="center",
                height=32,
            ),
            cells=dict(
                values=[ind_labels] + cell_vals,
                fill_color=[
                    ["#0D1B2A"] * len(ind_labels)   # colonne indicateurs
                ] + cell_colors,
                font=dict(color="white", size=12),
                align="center",
                height=28,
            )
        )])
        fig_table.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=max(200, 40 + len(ind_labels) * 28 + 32),
        )
        st.plotly_chart(fig_table, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# ONGLETS INDIVIDUELS
# ════════════════════════════════════════════════════════════════════════════

for tab_idx, (key, ind) in enumerate(list(data.items()), start=1):
    with tabs[tab_idx]:
        s = build_series(ind)

        last_yr      = s["last_real_year"]          # dernière année de données brutes
        indice_yr    = last_yr + 1                   # indice correspondant (ex: 2024→2025)
        # Score de l'indice = compute sur last_yr (fenêtre [last_yr-9, last_yr])
        indice_score, _, _ = compute_score_for_year(ind, last_yr)
        prev_score_val = None
        if last_yr - 1 in ind["years"]:
            prev_sc, _, _ = compute_score_for_year(ind, last_yr - 1)
            prev_score_val = prev_sc

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Indice {indice_yr}",
                  f"{indice_score:.1f} / 100",
                  help=f"Calculé sur les données {last_yr-9}–{last_yr}")
        c2.metric("Tendance",        f"{s['slope']:+.2f} pts/an")
        c3.metric("Projection 2030", f"{s['proj_2030']:.1f} / 100")
        if prev_score_val is not None:
            c4.metric("Variation",
                      f"{indice_score - prev_score_val:+.1f} pts",
                      help=f"vs Indice {last_yr}")

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
                    ind["unit"]: st.column_config.NumberColumn(ind["unit"], format="%.10g"),
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

            # ── Geler le score d'une année spécifique ────────────────────
            st.markdown("")
            with st.expander(f"🔒 Geler / recalculer le score d'une année"):
                st.markdown(
                    "Geler = score permanent calculé sur la fenêtre **[année−9, année]**. "
                    "Recalculer = force un nouveau calcul (écrase le score figé existant)."
                )
                frozen = ind.get("frozen_scores", {})

                col_fy, col_fbtn = st.columns([1,2])
                fy = col_fy.number_input("Année", min_value=2015, max_value=2040,
                                         value=last_yr, step=1, key=f"fy_{key}")
                if col_fbtn.button(f"🔒 Geler / recalculer {fy}",
                                   key=f"freeze_{key}", type="primary"):
                    score, mu, sigma = freeze_year(key, int(fy))
                    st.success(
                        f"✅ ICF {fy} figé : **{score}** "
                        f"(fenêtre {fy-10}–{fy-1}, μ={mu:.2f}, σ={sigma:.2f})"
                    )
                    st.rerun()

                if frozen:
                    st.markdown("**ICF figés pour cet indicateur :**")
                    for yr in sorted(frozen):
                        win_s = int(yr) - 10
                        win_e = int(yr) - 1
                        st.caption(f"• ICF {yr} = **{frozen[yr]}** "
                                   f"(fenêtre {win_s}–{win_e})")
                    # Option dégel
                    unfreeze_yr = st.selectbox(
                        "Dégeler une année (supprime le score figé)",
                        options=["—"] + sorted(frozen.keys()),
                        key=f"unfreeze_{key}"
                    )
                    if unfreeze_yr != "—":
                        if st.button(f"🔓 Dégeler {unfreeze_yr}", key=f"uf_{key}_{unfreeze_yr}"):
                            del st.session_state.data[key]["frozen_scores"][unfreeze_yr]
                            st.session_state.saved_data = copy.deepcopy(st.session_state.data)
                            write_save(st.session_state.saved_data)
                            st.rerun()

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
