import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json, copy, os, hashlib, base64, time
import requests

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
        "label": "Infractions racistes", "unit": "nb infractions",
        "inv": True, "cat": "devoir",
        "years": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [9185, 8637, 9267, 10842, 11312, 13064, 12618, 15000, 16335, 16485],
        "frozen_scores": {"2025": 21.6},
    },
    "participation": {
        "label": "Participation électorale", "unit": "%",
        "inv": False, "cat": "droit",
        "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [60.05875, 60, 56.5175, 56.5175, 56.5175, 52.02375, 47.415, 46.9275, 46.88375, 50.29125, 50.3],
        "frozen_scores": {"2025": 40.4},
    },
    "presse": {
        "label": "Liberté de la presse (rang RSF)", "unit": "rang",
        "inv": True, "cat": "droit",
        "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [38, 45, 39, 33, 32, 34, 34, 26, 24, 21, 25],
        "frozen_scores": {"2025": 76.5},
    },
    "delinquance": {
        "label": "Délinquance", "unit": "nb crimes et délits",
        "inv": True, "cat": "devoir",
        "years": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [3168570, 3190310, 3153413, 3219475, 2794838, 3020318, 3308943, 3382111, 3368566, 3442183],
        "frozen_scores": {"2025": 30.9},
    },
    "laicite": {
        "label": "Incidents laïcité", "unit": "nb incidents",
        "inv": True, "cat": "devoir",
        "years": [2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [935, 2226, 2167, 4710, 6554, 4230],
        "frozen_scores": {"2025": 19.8},
    },
    "salaires": {
        "label": "Écart salaires H/F", "unit": "%",
        "inv": True, "cat": "devoir",
        "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "vals": [19.1, 18.4, 17.9, 17.5, 16.6, 15.8, 15.5, 14.8, 14.2, 14],
        "frozen_scores": {"2025": 72.1},
    },
    "decrochage": {
        "label": "Décrochage scolaire", "unit": "%",
        "inv": True, "cat": "droit",
        "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [9.2, 8.8, 8.8, 8.7, 8.2, 8, 7.8, 7.6, 7.6, 7.9, 7.2],
        "frozen_scores": {"2025": 60.5},
    },
    "violences": {
        "label": "Violences faites aux femmes", "unit": "nb cas",
        "inv": True, "cat": "devoir",
        "years": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "vals": [16916, 16829, 17908, 20200, 22764, 33040, 35138, 37176, 38006],
        "frozen_scores": {"2025": 28.2},
    },
    "rsa": {
        "label": "Minima sociaux (RSA)", "unit": "%",
        "inv": False, "cat": "droit",
        "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
        "vals": [7.72368676771166, 7.586442401986661, 7.676919454692048, 7.678971531865303, 7.730308222546486, 8.020831649432282, 7.712203575595507, 7.697367765164609, 7.7],
        "frozen_scores": {"2025": 57.2},
    },
    "rcds": {
        "label": "Réservistes RCDS", "unit": "effectifs",
        "inv": False, "cat": "droit",
        "years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "vals": [4062, 4251, 5230, 5544, 5732, 5729, 5847, 6117, 6523, 6414, 6147],
        "frozen_scores": {"2025": 67.5},
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

# ── Session state : par défaut visiteur, auth admin persistée via URL ──────
# Streamlit réinitialise session_state à chaque rechargement complet (F5).
# On persiste donc l'état admin dans les query params de l'URL avec un token.

def _admin_token():
    """Token de session admin (hash d'un secret + marqueur)."""
    try:
        secret = st.secrets.get("admin_session_secret", "ledlr-icf-default-secret")
    except Exception:
        secret = "ledlr-icf-default-secret"
    return hashlib.sha256(f"admin::{secret}".encode()).hexdigest()[:24]

if "is_admin" not in st.session_state:
    # Restaure l'état admin depuis l'URL si le token est présent et valide
    qp = st.query_params
    st.session_state.is_admin = (qp.get("s") == _admin_token())
if "show_login_form" not in st.session_state:
    st.session_state.show_login_form = False

IS_ADMIN = st.session_state.is_admin

# ════════════════════════════════════════════════════════════════════════════
# PERSISTANCE
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
# PERSISTANCE DURABLE VIA GITHUB
# Le disque de Streamlit Cloud est effacé à chaque déploiement. Pour que
# "Sauvegarder pour toujours" survive aux push, le fichier de données est
# aussi stocké dans le dépôt GitHub, sur une branche dédiée ("data") qui ne
# déclenche PAS de redéploiement (Streamlit ne suit que la branche main).
# Configuration (Settings → Secrets de l'app Streamlit) :
#   github_token = "ghp_…"              (token avec le scope repo)
#   github_repo  = "utilisateur/repo"   (ex : "jerempazpers/icf")
#   github_data_branch = "data"         (optionnel, défaut "data")
# ════════════════════════════════════════════════════════════════════════════

def _gh_conf():
    try:
        tok    = st.secrets.get("github_token", "")
        repo   = st.secrets.get("github_repo", "")
        branch = st.secrets.get("github_data_branch", "data")
        if tok and repo:
            return tok, repo, branch
    except Exception:
        pass
    return None

def _gh_headers(tok):
    return {"Authorization": f"token {tok}",
            "Accept": "application/vnd.github+json"}

def gh_load():
    """Charge le JSON de données depuis la branche data du dépôt GitHub."""
    conf = _gh_conf()
    if not conf:
        return None
    tok, repo, branch = conf
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo}/contents/{SAVE_FILE}",
            params={"ref": branch}, headers=_gh_headers(tok), timeout=10)
        if r.status_code == 200:
            return json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))
    except Exception:
        pass
    return None

def _gh_ensure_branch(tok, repo, branch):
    """Crée la branche data si elle n'existe pas (à partir de main/master)."""
    h = _gh_headers(tok)
    r = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/{branch}",
                     headers=h, timeout=10)
    if r.status_code == 200:
        return True
    for base in ("main", "master"):
        rb = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/{base}",
                          headers=h, timeout=10)
        if rb.status_code == 200:
            sha = rb.json()["object"]["sha"]
            rc = requests.post(f"https://api.github.com/repos/{repo}/git/refs",
                               headers=h, timeout=10,
                               json={"ref": f"refs/heads/{branch}", "sha": sha})
            return rc.status_code in (200, 201)
    return False

def gh_save(data):
    """Écrit le JSON de données sur la branche data du dépôt. Best-effort."""
    conf = _gh_conf()
    if not conf:
        return False, "Persistance GitHub non configurée (voir Secrets)."
    tok, repo, branch = conf
    try:
        _gh_ensure_branch(tok, repo, branch)
        api = f"https://api.github.com/repos/{repo}/contents/{SAVE_FILE}"
        h   = _gh_headers(tok)
        r   = requests.get(api, params={"ref": branch}, headers=h, timeout=10)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {
            "message": time.strftime("Sauvegarde ICF %Y-%m-%d %H:%M:%S"),
            "content": base64.b64encode(
                json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            ).decode("ascii"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        r = requests.put(api, headers=h, json=payload, timeout=15)
        if r.status_code in (200, 201):
            return True, "OK"
        return False, str(r.json().get("message", r.status_code))
    except Exception as e:
        return False, str(e)

def load_saved():
    # 1. Fichier local (le plus frais pendant une session)
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 2. GitHub (survit aux redéploiements)
    gh = gh_load()
    if gh:
        try:  # re-crée le cache local
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(gh, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return gh
    # 3. Données par défaut gravées dans le code
    return copy.deepcopy(ORIGINAL_DATA)

def write_save(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    ok, msg = gh_save(data)
    st.session_state.gh_last_save = (ok, msg, time.strftime("%H:%M:%S"))

# ── Catégories Droits / Devoirs (cf. Excel EDLR colonne "Droit/Devoir") ─────
CATEGORY_MAP = {
    "participation": "droit",  "presse": "droit",   "decrochage": "droit",
    "rcds": "droit",           "rsa": "droit",      "pauvrete": "droit",
    "delinquance": "devoir",   "laicite": "devoir", "salaires": "devoir",
    "violences": "devoir",     "racisme": "devoir",
}

def ensure_categories(d):
    """Injecte la catégorie ('droit'/'devoir') sur chaque indicateur si absente
    (rétrocompatibilité avec les données sauvegardées avant cette version)."""
    for key, ind in d.items():
        if "cat" not in ind:
            ind["cat"] = CATEGORY_MAP.get(key, "droit")
    return d

if "saved_data" not in st.session_state:
    st.session_state.saved_data = ensure_categories(load_saved())
if "data" not in st.session_state:
    st.session_state.data = ensure_categories(copy.deepcopy(st.session_state.saved_data))

# ════════════════════════════════════════════════════════════════════════════
# CALCULS
# ════════════════════════════════════════════════════════════════════════════

def z_apply_fixed(arr, mu, sigma, inv):
    """Applique une normalisation Z-score avec mu/sigma fixes."""
    arr = np.array(arr, float)
    if sigma == 0: return np.full(len(arr), 50.0)
    zn = np.clip(((arr - mu) / sigma + 3) / 6, 0, 1) * 100
    return np.round(100 - zn if inv else zn, 1)

BASE_YEAR_0 = 2015   # première année de base de la méthode

def get_reference_period(icf_year):
    """
    Retourne (ref_start, ref_end) : période de référence (μ, σ) pour
    l'indice / ICF de l'année icf_year.

    MÉTHODE (cumulative avec rebasage décennal, inspirée de l'INSEE) :
      - ICF ≤ 2025       : référence FIXE 2015–2024
        (les ICF 2015–2024 affichés à titre indicatif utilisent cette même référence)
      - ICF 2026 → 2035  : référence CUMULATIVE 2015 → (ICF−1)
      - ICF 2036 → 2045  : REBASAGE → référence 2025 → (ICF−1)
      - puis rebasage tous les 10 ans (base 2035 pour ICF 2046-2055, etc.)
    """
    if icf_year <= BASE_YEAR_0 + 10:                 # ICF ≤ 2025
        return BASE_YEAR_0, BASE_YEAR_0 + 9          # (2015, 2024) fixe
    n_rebase = max(0, (icf_year - (BASE_YEAR_0 + 11)) // 10)  # 2026-35→0, 2036-45→1…
    base = BASE_YEAR_0 + 10 * n_rebase
    return base, icf_year - 1

def compute_score_for_year(ind, target_year):
    """
    Calcule l'indice d'un indicateur pour l'année de données target_year.
    L'indice/ICF correspondant est celui de l'année (target_year + 1).

    La référence (μ, σ) suit get_reference_period(target_year+1).
    Les années manquantes de la référence sont extrapolées par régression
    linéaire — cohérent avec la méthode MATLAB d'origine.
    """
    years = np.array(ind["years"]); vals = np.array(ind["vals"], float)
    a, b  = np.polyfit(years, vals, 1)
    rby   = dict(zip(ind["years"], ind["vals"]))

    icf_year = target_year + 1
    ref_start, ref_end = get_reference_period(icf_year)
    ref_years = list(range(ref_start, ref_end + 1))
    ref_vals  = np.array([rby.get(y, a*y+b) for y in ref_years])

    mu    = ref_vals.mean()
    sigma = ref_vals.std(ddof=1)
    if sigma == 0:
        return 50.0, mu, sigma

    val_target = rby.get(target_year, a*target_year + b)
    zn    = np.clip(((val_target - mu) / sigma + 3) / 6, 0, 1) * 100
    score = round(float(100 - zn if ind["inv"] else zn), 1)
    return score, round(float(mu), 4), round(float(sigma), 4)

def build_series(ind):
    """
    Construit la série des INDICES pour affichage.

    CONVENTION UNIFIÉE (identique au tableau ICF global) :
      Indice N = compute_score_for_year(ind, N-1)
               = valeur de l'année (N-1) normalisée sur la fenêtre [N-10, N-1]

    L'axe "année d'indice" va de (première_donnée+1) à 2030.
    - Indices dont l'année de données (N-1) est réelle → point plein
    - Indices dont l'année de données (N-1) est extrapolée → projection
    - frozen_scores[str(N)] écrase le calcul si présent (score figé définitif)
    """
    years  = np.array(ind["years"])
    rby    = dict(zip(ind["years"], ind["vals"]))
    frozen = ind.get("frozen_scores", {})   # {"2025": 21.6, ...}

    first_data = int(years.min())
    last_data  = int(years.max())

    # Axe des années d'INDICE : depuis 2015 (affichage indicatif inclus)
    indice_years = list(range(BASE_YEAR_0, 2031))

    scores      = np.full(len(indice_years), np.nan)  # indice réel (année données réelle)
    proj_scores = np.full(len(indice_years), np.nan)  # tous (réels + extrapolés)
    stale_frozen = []   # indices figés qui divergent du recalcul (données changées depuis)

    for i, iy in enumerate(indice_years):
        data_yr = iy - 1  # année de données correspondante
        str_iy  = str(iy)
        # Calcul "live" (données actuelles)
        sc_live, _, _ = compute_score_for_year(ind, data_yr)
        if str_iy in frozen:
            scores[i]      = frozen[str_iy]
            proj_scores[i] = frozen[str_iy]
            # Le figé diverge-t-il du recalcul actuel ? (données modifiées depuis le gel)
            if abs(frozen[str_iy] - sc_live) > 0.05:
                stale_frozen.append((iy, frozen[str_iy], sc_live))
        else:
            proj_scores[i] = sc_live
            if data_yr in rby:          # donnée réelle → indice "réel"
                scores[i] = sc_live

    # Régression sur les indices réels pour la tendance
    known_i = [indice_years[j] for j in range(len(indice_years)) if not np.isnan(scores[j])]
    known_s = [scores[j]        for j in range(len(indice_years)) if not np.isnan(scores[j])]
    if len(known_i) >= 2:
        as_, bs_ = np.polyfit(known_i, known_s, 1)
        slope = round(float(as_), 3)
    else:
        slope = 0.0

    # Dernière année d'indice réel
    real_idx = [j for j in range(len(indice_years)) if not np.isnan(scores[j])]
    li       = real_idx[-1] if real_idx else 0

    # Données brutes alignées sur l'axe standard 2015-2030 (pour le graphe brut)
    a, b   = np.polyfit(years, np.array(ind["vals"], float), 1)
    raw_all = np.array([rby.get(y, a*y+b) for y in YEARS_AXIS])
    raw_real = np.where(np.array([y in rby for y in YEARS_AXIS]), raw_all, np.nan)

    return {
        "indice_years": indice_years,        # axe X des indices
        "scores":       proj_scores,         # indices (réels + extrapolés)
        "real_scores":  scores,              # NaN sauf indices réels
        "raw_years":    YEARS_AXIS,          # axe X des données brutes
        "real_raw":     raw_real,
        "proj_raw":     raw_all,
        "slope":        slope,
        "last_score":   float(scores[li]) if real_idx else float("nan"),
        "prev_score":   float(scores[li-1]) if li > 0 and not np.isnan(scores[li-1]) else None,
        "proj_2030":    float(proj_scores[-1]),
        "last_indice_year": int(indice_years[li]) if real_idx else indice_years[0],
        "last_data_year":   last_data,
        "stale_frozen":     stale_frozen,   # [(annee, valeur_figée, valeur_recalculée)]
    }

def get_indice(ind, icf_year):
    """
    Indice OFFICIEL d'un indicateur pour une année d'ICF donnée.
    PRIORITÉ ABSOLUE au score figé : frozen_scores[str(icf_year)] s'il existe
    (un indice figé ne bouge plus JAMAIS, même si les données changent).
    Sinon, calcul à la volée : compute_score_for_year(ind, icf_year - 1).
    C'est LA fonction de référence — courbe, tableau, métrique l'utilisent tous.
    """
    frozen = ind.get("frozen_scores", {})
    if str(icf_year) in frozen:
        return float(frozen[str(icf_year)])
    sc, _, _ = compute_score_for_year(ind, icf_year - 1)
    return float(sc)

def compute_global(data, start_year=None, cat=None):
    """
    ICF par année : moyenne des indices officiels (get_indice) — les scores
    figés sont respectés en priorité.
    cat : None = tous les indicateurs (ICF global) ;
          "droit"/"devoir" = sous-ICF de la catégorie.
    Retourne (icf_years, icf_values) alignés, depuis 2015 par défaut.
    """
    axis_start = start_year if start_year is not None else BASE_YEAR_0
    inds = [ind for ind in data.values() if cat is None or ind.get("cat") == cat]
    icf_years = list(range(axis_start, 2031))
    if not inds:
        return icf_years, np.full(len(icf_years), np.nan)
    icf_vals = []
    for iy in icf_years:
        scores = [get_indice(ind, iy) for ind in inds]
        icf_vals.append(round(float(np.mean(scores)), 2))
    return icf_years, np.array(icf_vals)

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
    ICF d'une année = moyenne des indices officiels (figés prioritaires,
    sinon calculés à la volée).
    """
    scores = [get_indice(ind, icf_year) for ind in data.values()]
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
    # Axe X = années d'indice (fourni par build_series)
    indice_axis = s["indice_years"]
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
        x=s["raw_years"], y=s["proj_raw"], mode="lines",
        name="Projection linéaire (2015–2030)",
        line=dict(color=RED, dash="dash", width=1.5),
        hovertemplate="%{x}: %{y:,.2f}<extra>Projection</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=s["raw_years"], y=s["real_raw"], mode="lines+markers",
        name="Données réelles",
        line=dict(color=BLUE, width=2), marker=dict(size=7, color=BLUE),
        connectgaps=False,
        hovertemplate=f"%{{x}}: %{{y:,.2f}} {unit}<extra>Réel</extra>",
    ))
    fig.update_layout(
        title=f"Données brutes — {label}", height=400,
        xaxis=dict(tickvals=s["raw_years"], tickangle=45, title="Année"),
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

def add_next_year_data(year, values_by_key):
    """
    Ajoute les données de l'année `year` pour chaque indicateur.
    values_by_key : {key: valeur ou None}. Si None/vide → l'indicateur
    n'est pas mis à jour (pas de donnée pour cette année-là).
    Sauvegarde permanente immédiate.
    """
    for key, val in values_by_key.items():
        if val is None:
            continue
        ind = st.session_state.data[key]
        if year in ind["years"]:
            # Écrase la valeur existante pour cette année
            idx = ind["years"].index(year)
            ind["vals"][idx] = float(val)
        else:
            ind["years"].append(int(year))
            ind["vals"].append(float(val))
            # Garde les listes triées par année
            pairs = sorted(zip(ind["years"], ind["vals"]))
            ind["years"] = [p[0] for p in pairs]
            ind["vals"]  = [p[1] for p in pairs]
    st.session_state.saved_data = copy.deepcopy(st.session_state.data)
    write_save(st.session_state.saved_data)

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
               "cat": st.session_state.get("new_ind_cat", "droit"),
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
            st.radio(
                "Catégorie",
                options=["droit", "devoir"],
                format_func=lambda c: "⚖️ Droits" if c == "droit" else "📜 Devoirs",
                key="new_ind_cat",
                horizontal=True,
                help="Rattache l'indicateur au sous-score ICF Droits ou ICF Devoirs."
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
        # ── État de la persistance durable ───────────────────────────────────
        if _gh_conf() is None:
            st.warning("⚠️ Persistance GitHub non configurée : les sauvegardes "
                       "seront perdues au prochain déploiement. Ajoutez "
                       "`github_token` et `github_repo` dans les Secrets de l'app.")
        elif "gh_last_save" in st.session_state:
            ok, msg, hhmm = st.session_state.gh_last_save
            if ok:
                st.caption(f"☁️ Sauvegardé sur GitHub à {hhmm}")
            else:
                st.error(f"☁️ Échec sauvegarde GitHub ({hhmm}) : {msg}")
        else:
            st.caption("☁️ Persistance GitHub active")

        with st.expander("🛠 Maintenance"):
            st.caption("Réinitialise TOUTES les données aux valeurs officielles "
                       "gravées dans le code (Excel v4 + gels 2025), et remplace "
                       "la sauvegarde locale ET GitHub.")
            confirm_reset = st.checkbox("Je confirme la réinitialisation totale",
                                        key="confirm_full_reset")
            if st.button("♻️ Réinitialiser aux données officielles",
                         disabled=not confirm_reset, use_container_width=True):
                st.session_state.data       = ensure_categories(copy.deepcopy(ORIGINAL_DATA))
                st.session_state.saved_data = copy.deepcopy(st.session_state.data)
                write_save(st.session_state.saved_data)
                st.success("Données officielles restaurées et sauvegardées.")
                st.rerun()

        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.is_admin         = False
            st.session_state.show_login_form  = False
            st.session_state.show_create_form = False
            st.session_state.data = copy.deepcopy(st.session_state.saved_data)
            # Retire le token de l'URL
            if "s" in st.query_params:
                del st.query_params["s"]
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
                    # Persiste l'auth dans l'URL pour survivre aux rafraîchissements
                    st.query_params["s"] = _admin_token()
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
        # Série ICF unique (référence cumulative) — démarre à 2015
        icf_years_axis, gs = compute_global(data)
        ag, bg = np.polyfit(icf_years_axis, gs, 1)
        # Sous-séries Droits / Devoirs (mêmes règles : get_indice, gels respectés)
        _, gs_droits  = compute_global(data, cat="droit")
        _, gs_devoirs = compute_global(data, cat="devoir")
        n_droits  = sum(1 for ind in data.values() if ind.get("cat") == "droit")
        n_devoirs = sum(1 for ind in data.values() if ind.get("cat") == "devoir")

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

        # ── ICF affiché : automatique = le plus récent calculable ────────────
        # (dès qu'au moins un indicateur a une donnée pour l'année N-1,
        #  l'ICF N devient l'ICF courant)
        icf_year       = int(min(icf_max_calculable, CURRENT_YEAR + 1))
        target_data_yr = icf_year - 1        # dernière année de données utilisée
        win_start, win_end = get_reference_period(icf_year)   # période de référence

        st.caption(
            f"**ICF {icf_year}** — indices calculés sur les valeurs {target_data_yr}, "
            f"référence **{win_start}–{win_end}** (méthode cumulative, rebasage décennal)"
        )

        # Indicateurs sans données réelles pour target_data_yr
        late_inds  = {key: data[key]["label"]
                      for key, yr in last_years.items() if yr < target_data_yr}
        ahead_inds = {key: data[key]["label"]
                      for key, yr in last_years.items() if yr > target_data_yr}

        # ── Bouton : ajouter les données de l'année suivante (admin) ──────────
        if IS_ADMIN:
            next_year = max_last + 1  # année à ajouter = juste après le max actuel
            if "show_add_year_form" not in st.session_state:
                st.session_state.show_add_year_form = False

            if not st.session_state.show_add_year_form:
                if st.button(f"➕ Ajouter les données de l'année {next_year}",
                             type="primary", use_container_width=True):
                    st.session_state.show_add_year_form = True
                    st.rerun()
            else:
                with st.container(border=True):
                    st.markdown(f"### ➕ Saisie des données {next_year}")
                    st.caption("Renseignez la valeur brute de chaque indicateur pour "
                               f"{next_year}. Laissez vide si la donnée n'est pas "
                               "disponible — l'indicateur sera alors extrapolé.")

                    entered = {}
                    for key, ind in data.items():
                        last_val = ind["vals"][-1] if ind["vals"] else 0
                        col_lbl, col_inp = st.columns([3, 2])
                        col_lbl.markdown(
                            f"**{ind['label']}**  \n"
                            f"<span style='color:#888;font-size:12px;'>"
                            f"{ind['unit']} · dernière valeur ({max(ind['years'])}) : "
                            f"{last_val:g}</span>",
                            unsafe_allow_html=True
                        )
                        val = col_inp.number_input(
                            f"Valeur {next_year}",
                            value=None, format="%.10g",
                            key=f"addyear_{key}",
                            label_visibility="collapsed",
                            placeholder="(vide = pas de donnée)"
                        )
                        entered[key] = val

                    st.markdown("")
                    col_ok, col_cancel = st.columns(2)
                    with col_ok:
                        if st.button("✓ Valider et calculer", type="primary",
                                     use_container_width=True):
                            add_next_year_data(next_year, entered)
                            st.session_state.show_add_year_form = False
                            # Nettoie les inputs
                            for key in data:
                                st.session_state.pop(f"addyear_{key}", None)
                            st.success(f"✅ Données {next_year} ajoutées !")
                            st.rerun()
                    with col_cancel:
                        if st.button("✕ Annuler", use_container_width=True):
                            st.session_state.show_add_year_form = False
                            for key in data:
                                st.session_state.pop(f"addyear_{key}", None)
                            st.rerun()

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
            # ICF officiel = moyenne des indices officiels (get_indice) :
            # score FIGÉ prioritaire, sinon calcul à la volée.
            # → strictement identique à la courbe et à la ligne ICF du tableau.
            icf_scores_direct = {}
            for key, ind in data.items():
                icf_scores_direct[key] = get_indice(ind, icf_year)
            icf_last = round(float(np.mean(list(icf_scores_direct.values()))), 1)

            c1.metric(f"ICF {icf_year}", f"{icf_last:.1f} / 100",
                      help=f"Référence : {win_start}–{win_end} "
                           f"({win_end - win_start + 1} ans, méthode cumulative)")
            c2.metric("Tendance",           f"{ag:+.2f} pts/an")
            c3.metric("Projection 2030",    f"{gs[-1]:.1f} / 100")
            c4.metric("Indicateurs actifs", len(data))

            # ── Sous-scores Droits / Devoirs ─────────────────────────────────
            _iy_idx = icf_years_axis.index(icf_year)
            d1, d2, _sp = st.columns([1, 1, 2])
            d1.metric(f"⚖️ ICF Droits {icf_year}",
                      f"{gs_droits[_iy_idx]:.1f} / 100",
                      help=f"Moyenne des {n_droits} indicateurs de la catégorie Droits")
            d2.metric(f"📜 ICF Devoirs {icf_year}",
                      f"{gs_devoirs[_iy_idx]:.1f} / 100",
                      help=f"Moyenne des {n_devoirs} indicateurs de la catégorie Devoirs")

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
                    _frs, _fre = get_reference_period(freeze_year_input)
                    col_yr.caption(f"Référence : {_frs}–{_fre}")

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

                    st.markdown("**Supprimer / recalculer une année gelée :**")
                    cols_del = st.columns(min(len(frozen_summary), 4))
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
                            if st.button(f"♻ Recalc {yr}", key=f"recalc_frozen_{yr}",
                                         help=f"Recalcule ICF {yr} avec la formule actuelle"):
                                freeze_year_all(int(yr))
                                st.rerun()

                    st.markdown("---")
                    if st.button("🧹 Supprimer TOUS les gels (repartir de zéro)",
                                 key="clear_all_frozen"):
                        for k2 in list(data.keys()):
                            st.session_state.data[k2]["frozen_scores"] = {}
                        st.session_state.saved_data = copy.deepcopy(st.session_state.data)
                        write_save(st.session_state.saved_data)
                        st.rerun()

        # ── Graphique ICF ─────────────────────────────────────────────────────
        frozen_icf      = get_frozen_icf_series(data)
        current_icf_val = compute_icf_for_year(data, icf_year)

        # Série d'AFFICHAGE (démarre à 2015, fenêtres incomplètes incluses).
        # N'affecte AUCUN calcul officiel — uniquement le tracé de la courbe.
        last_data_global = max(max(ind["years"]) for ind in data.values())

        real_icf_years, real_icf_vals = [], []
        proj_icf_years, proj_icf_vals = [], []
        for iy, val in zip(icf_years_axis, gs):
            if iy <= icf_year:
                real_icf_years.append(iy); real_icf_vals.append(round(float(val),1))
            else:
                proj_icf_years.append(iy); proj_icf_vals.append(round(float(val),1))

        # Régression sur ICF figés (sinon sur ICF réels) pour la tendance
        if len(frozen_icf) >= 2:
            ref_x, ref_y = list(frozen_icf.keys()), list(frozen_icf.values())
        else:
            ref_x, ref_y = real_icf_years, real_icf_vals
        if len(ref_x) >= 2:
            fa, fb     = np.polyfit(ref_x, ref_y, 1)
            proj_start = min(real_icf_years) if real_icf_years else icf_year
            proj_line_years = list(range(proj_start, 2031))
            proj_line_vals  = [fa*y+fb for y in proj_line_years]
        else:
            proj_line_years, proj_line_vals = [], []

        fig_g = go.Figure()

        # Tendance (pointillés rouges)
        if proj_line_years:
            fig_g.add_trace(go.Scatter(
                x=proj_line_years, y=proj_line_vals,
                mode="lines", name="Tendance (projection)",
                line=dict(color=RED, dash="dash", width=1.5),
            ))

        # ICF calculés (bleu) — pour toutes les années d'indice réelles
        # On distingue les figés (marqueur plein) des non-figés (via texte)
        if real_icf_years:
            marker_colors = [BLUE if y in frozen_icf else "#7FA8D8"
                             for y in real_icf_years]
            fig_g.add_trace(go.Scatter(
                x=real_icf_years, y=real_icf_vals,
                mode="lines+markers+text", name="ICF",
                line=dict(color=BLUE, width=2.5),
                marker=dict(size=8, color=marker_colors),
                text=[f"{v:.1f}" for v in real_icf_vals],
                textposition="top center", textfont=dict(size=10),
            ))

        # ICF sélectionné mis en évidence (orange si non figé, vert si figé)
        sel_val = frozen_icf.get(icf_year, current_icf_val)
        sel_color = "#2ECC71" if icf_year in frozen_icf else "#F5A623"
        sel_name  = f"ICF {icf_year} (figé)" if icf_year in frozen_icf else f"ICF {icf_year} (provisoire)"
        fig_g.add_trace(go.Scatter(
            x=[icf_year], y=[sel_val],
            mode="markers", name=sel_name,
            marker=dict(size=13, color=sel_color,
                        symbol="circle", line=dict(width=2, color="white")),
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

        # ── Graphes séparés : ICF Droits / ICF Devoirs ───────────────────────
        def _cat_fig(title, series, color, n_count):
            sub_years = [iy for iy in icf_years_axis if iy <= icf_year]
            n = len(sub_years)
            vals = [float(v) for v in series[:n]]
            fig = go.Figure()
            # Tendance : régression sur la sous-série, projetée jusqu'à 2030
            valid = [(y, v) for y, v in zip(sub_years, vals) if not np.isnan(v)]
            if len(valid) >= 2:
                vx, vy = zip(*valid)
                ca, cb = np.polyfit(vx, vy, 1)
                proj_x = list(range(sub_years[0], 2031))
                fig.add_trace(go.Scatter(
                    x=proj_x, y=[ca*y+cb for y in proj_x],
                    mode="lines", name="Tendance (projection)",
                    line=dict(color=RED, dash="dash", width=1.5),
                ))
            fig.add_trace(go.Scatter(
                x=sub_years, y=vals,
                mode="lines+markers+text", name=title,
                line=dict(color=color, width=2.2),
                marker=dict(size=7, color=color),
                text=[f"{v:.1f}" for v in vals],
                textposition="top center", textfont=dict(size=9, color=color),
            ))
            fig.update_layout(
                title=f"{title} ({n_count} indicateurs)",
                height=340,
                xaxis=dict(tickvals=list(range(2015, 2031)), tickangle=45,
                           title="Année ICF"),
                yaxis=dict(range=[0, 100], title="Score (0–100)"),
                legend=dict(orientation="h", y=-0.35),
                margin=dict(l=45, r=15, t=45, b=85),
            )
            return fig

        col_dr, col_dv = st.columns(2)
        with col_dr:
            st.plotly_chart(_cat_fig("⚖️ ICF Droits", gs_droits, "#26C6DA", n_droits),
                            use_container_width=True)
        with col_dv:
            st.plotly_chart(_cat_fig("📜 ICF Devoirs", gs_devoirs, "#EC407A", n_devoirs),
                            use_container_width=True)

        # ── Tableau des indices par indicateur + ligne ICF ───────────────────
        # Terminologie : "indice" = score d'un indicateur ; "ICF" = moyenne globale
        st.subheader(f"Indices par indicateur — référence {win_start}–{win_end}")

        # Légende
        st.markdown(
            "<div style='display:flex;gap:20px;font-size:13px;margin-bottom:8px;'>"
            "<span><span style='display:inline-block;width:14px;height:14px;"
            "background:#1E4A8C;border-radius:3px;vertical-align:middle;margin-right:5px;'>"
            "</span>Données réelles</span>"
            "<span><span style='display:inline-block;width:14px;height:14px;"
            "background:#5A3E7A;border-radius:3px;vertical-align:middle;margin-right:5px;'>"
            "</span>Extrapolé (régression)</span>"
            "<span><span style='display:inline-block;width:14px;height:14px;"
            "background:#2E7D32;border-radius:3px;vertical-align:middle;margin-right:5px;'>"
            "</span>Figé (définitif)</span>"
            "</div>",
            unsafe_allow_html=True
        )

        # Colonnes = années d'indice, de 2015 à icf_year
        # (2015–2024 affichés à titre indicatif : même référence 2015-2024)
        icf_cols = list(range(BASE_YEAR_0, icf_year + 1))

        ind_labels = ([ind["label"] for ind in data.values()]
                      + ["⚖️ ICF Droits", "📜 ICF Devoirs", "🏆 ICF"])

        cell_vals   = []  # une liste par colonne
        cell_colors = []  # couleur par cellule

        for icf_col_yr in icf_cols:
            data_yr = icf_col_yr - 1
            col_vals, col_colors = [], []
            col_scores = []   # pour la ligne ICF
            for key, ind in data.items():
                frozen = ind.get("frozen_scores", {})
                if str(icf_col_yr) in frozen:
                    sc = frozen[str(icf_col_yr)]
                    col_vals.append(f"{sc:.1f}")
                    col_colors.append("#2E7D32")  # vert = figé
                else:
                    sc, _, _ = compute_score_for_year(ind, data_yr)
                    is_real  = data_yr in ind["years"]
                    col_vals.append(f"{sc:.1f}")
                    col_colors.append("#1E4A8C" if is_real else "#5A3E7A")
                col_scores.append(float(sc))
            # Lignes ICF Droits / Devoirs / global (moyennes de la colonne)
            cats = [ind.get("cat") for ind in data.values()]
            droits_sc  = [s for s, c in zip(col_scores, cats) if c == "droit"]
            devoirs_sc = [s for s, c in zip(col_scores, cats) if c == "devoir"]
            for subset, color in ((droits_sc, "#00838F"), (devoirs_sc, "#AD1457")):
                if subset:
                    col_vals.append(f"<b>{np.mean(subset):.1f}</b>")
                else:
                    col_vals.append("—")
                col_colors.append(color)
            icf_cell = round(float(np.mean(col_scores)), 1)
            col_vals.append(f"<b>{icf_cell:.1f}</b>")
            col_colors.append("#B8860B")   # doré = ligne ICF
            cell_vals.append(col_vals)
            cell_colors.append(col_colors)

        fig_table = go.Figure(data=[go.Table(
            header=dict(
                values=["<b>Indicateur</b>"] + [f"<b>{y}</b>" for y in icf_cols],
                fill_color="#0D1B2A",
                font=dict(color="white", size=12),
                align="center",
                height=32,
            ),
            cells=dict(
                values=[ind_labels] + cell_vals,
                fill_color=[
                    ["#0D1B2A"] * len(ind_labels)
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
        # ── Badge de catégorie Droits / Devoirs ──────────────────────────────
        _cat = ind.get("cat", "droit")
        _badge, _bcolor = (("⚖️ Catégorie : Droits", "#26C6DA") if _cat == "droit"
                           else ("📜 Catégorie : Devoirs", "#EC407A"))
        st.markdown(
            f"<span style='background:{_bcolor}22;border:1px solid {_bcolor};"
            f"color:{_bcolor};padding:3px 12px;border-radius:12px;"
            f"font-size:13px;font-weight:600;'>{_badge}</span>",
            unsafe_allow_html=True
        )

        s = build_series(ind)

        last_yr      = s["last_data_year"]           # dernière année de données brutes
        indice_yr    = last_yr + 1                    # indice correspondant (ex: 2024→2025)
        indice_score, _, _ = compute_score_for_year(ind, last_yr)
        prev_score_val = None
        if last_yr - 1 in ind["years"]:
            prev_sc, _, _ = compute_score_for_year(ind, last_yr - 1)
            prev_score_val = prev_sc

        c1, c2, c3, c4 = st.columns(4)
        _irs, _ire = get_reference_period(indice_yr)
        c1.metric(f"Indice {indice_yr}",
                  f"{indice_score:.1f} / 100",
                  help=f"Valeur {last_yr} normalisée sur la référence {_irs}–{_ire}")
        c2.metric("Tendance",        f"{s['slope']:+.2f} pts/an")
        c3.metric("Projection 2030", f"{s['proj_2030']:.1f} / 100")
        if prev_score_val is not None:
            c4.metric("Variation",
                      f"{indice_score - prev_score_val:+.1f} pts",
                      help=f"vs Indice {last_yr}")

        # ── Avertissement : scores figés périmés (données changées depuis le gel) ──
        if s.get("stale_frozen") and IS_ADMIN:
            stale_list = ", ".join(
                f"Indice {yr} (figé {fv:.1f} → recalculé {lv:.1f})"
                for yr, fv, lv in s["stale_frozen"]
            )
            st.warning(
                f"⚠️ Des scores figés ne correspondent plus aux données actuelles : "
                f"{stale_list}. Le graphique affiche les valeurs **figées**, pas le recalcul."
            )
            if st.button("♻ Recalculer ces scores figés", key=f"recalc_stale_{key}"):
                for yr, _, _ in s["stale_frozen"]:
                    new_sc, _, _ = compute_score_for_year(ind, yr - 1)
                    st.session_state.data[key]["frozen_scores"][str(yr)] = new_sc
                st.session_state.saved_data = copy.deepcopy(st.session_state.data)
                write_save(st.session_state.saved_data)
                st.rerun()

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

            st.caption("Vous pouvez modifier les valeurs existantes. Pour ajouter "
                       "une nouvelle année, utilisez le bouton dédié dans l'onglet "
                       "**ICF Global**.")

            # La clé inclut le nombre d'années : si une année est ajoutée via
            # le formulaire global, la clé change et le tableau se rafraîchit
            editor_key = f"editor_{key}_{len(ind['years'])}_{max(ind['years'])}"
            edited = st.data_editor(
                pd.DataFrame({"Année": ind["years"], ind["unit"]: ind["vals"]}),
                num_rows="fixed",
                disabled=["Année"],
                column_config={
                    "Année":     st.column_config.NumberColumn(
                                     "Année", format="%d"),
                    ind["unit"]: st.column_config.NumberColumn(ind["unit"], format="%.10g"),
                },
                key=editor_key,
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
                        f"(référence {get_reference_period(int(fy))[0]}–{get_reference_period(int(fy))[1]}, μ={mu:.2f}, σ={sigma:.2f})"
                    )
                    st.rerun()

                if frozen:
                    st.markdown("**ICF figés pour cet indicateur :**")
                    for yr in sorted(frozen):
                        win_s, win_e = get_reference_period(int(yr))
                        st.caption(f"• Indice {yr} = **{frozen[yr]}** "
                                   f"(référence {win_s}–{win_e})")
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
