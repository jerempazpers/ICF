# Méthodologie de l'Indice de Citoyenneté Française (ICF)

*Les Enfants de la République — document méthodologique de référence*

---

## 1. Terminologie

- **Indice** : score normalisé (0–100) d'un **indicateur** individuel (infractions racistes, participation électorale, etc.) pour une année donnée.
- **ICF** : moyenne arithmétique des indices de tous les indicateurs pour une année donnée. C'est le score global publié.

**Convention temporelle** : l'indice de l'année N est calculé à partir de la **valeur de l'année N−1**. Les données observées jusqu'en 2024 produisent donc l'ICF 2025 — l'indice publié une année reflète l'état mesuré l'année précédente, à la manière d'un bilan.

---

## 2. Normalisation d'un indice

Pour chaque indicateur, la valeur brute de l'année N−1 est transformée en indice via une normalisation **Z-score** :

1. **Z = (valeur − μ) / σ**, où μ (moyenne) et σ (écart-type, estimateur non biaisé N−1) sont calculés sur la **période de référence** (voir §3).
2. Le Z est ramené sur [0, 1] par **(Z + 3) / 6**, borné (clamp), puis multiplié par 100. Le choix de ±3 s'appuie sur la loi normale : 99,7 % des valeurs d'une distribution normale tombent dans ±3 écarts-types.
3. Pour les indicateurs où une hausse est défavorable (infractions, chômage…), l'indice est inversé : **indice = 100 − score**. Un indice élevé signifie toujours une situation favorable.

Les années manquantes de la période de référence (avant les premières données d'un indicateur, ou années non encore renseignées) sont **extrapolées par régression linéaire** sur les données réelles disponibles.

---

## 3. Période de référence : cumulative avec rebasage décennal

C'est le cœur de la méthode, inspirée de la pratique de l'INSEE pour ses indices de prix (année de base fixe, rebasée périodiquement — règlement européen : rebasage tous les 10 ans).

| Année d'ICF | Période de référence (μ, σ) | Régime |
|---|---|---|
| 2015 → 2025 | **2015–2024** (fixe) | Base initiale |
| 2026 | 2015–2025 | Cumulatif |
| 2027 | 2015–2026 | Cumulatif |
| … | … | … |
| 2035 | 2015–2034 | Cumulatif |
| **2036** | **2025–2035** | **Rebasage n°1** |
| 2037 → 2045 | 2025 → (ICF−1) | Cumulatif sur base 2025 |
| **2046** | **2035–2045** | **Rebasage n°2** |

**Cas particulier des ICF 2015–2024** : ils sont affichés avec la même référence que l'ICF 2025 (2015–2024). Leur fenêtre de référence « n'existait pas encore » à l'époque — ils sont donc **indicatifs**, publiés pour donner une lecture continue de la trajectoire, et non comme des mesures officielles. Seuls les ICF à partir de 2025 sont méthodologiquement complets.

---

## 4. Justification du choix

**Pourquoi cumulatif plutôt que fenêtre glissante de 10 ans ?**

La fenêtre glissante (référence = 10 dernières années) crée le paradoxe du *shifting baseline* : quand une dégradation devient continue, elle intègre progressivement la référence, et l'indice « s'améliore » alors que la situation empire en valeur absolue. Exemple observé sur les infractions racistes : la valeur passe de 16 335 à 16 485 (+150) mais l'indice remonte de 21,6 à 26, car la fenêtre a perdu l'année basse 2015 et gagné l'année haute 2025 — la moyenne de référence montait plus vite que la valeur. La référence cumulative amortit fortement ce paradoxe : ajouter une année à une base de 10, 15 ou 20 ans déplace peu la moyenne, et le point d'ancrage 2015 reste dans la référence.

**Pourquoi rebaser tous les 10 ans plutôt que cumuler indéfiniment ?**

Une référence qui s'allonge sans fin devient inerte (voir §6) et ancre définitivement le point de départ 2015 comme étalon, même si la société a changé structurellement. Le rebasage décennal renouvelle la référence de manière **explicite, prévisible et documentée** — exactement comme l'INSEE, qui a rebasé son IPC de la base 2015 à la base 2025 en 2026. Le rebasage est un acte méthodologique assumé, annoncé, et non un glissement silencieux.

**Pourquoi la moyenne arithmétique simple pour l'ICF ?**

La pondération égale est le choix par défaut recommandé par l'OCDE pour les indices composites : elle est neutre, reproductible, et ne nécessite aucun arbitrage normatif sur l'importance relative des dimensions de la citoyenneté — arbitrage qui relèverait d'un débat politique, non statistique.

---

## 5. Forces de la méthode

- **Stabilité des indices publiés** : ajouter l'année 2025 ne modifie pas l'indice 2025 (calculé sur 2015–2024). Les valeurs publiées ne « bougent » pas rétroactivement à chaque mise à jour.
- **Robustesse statistique croissante** : μ et σ sont estimés sur un nombre de points qui augmente chaque année — l'estimation devient plus fiable avec le temps.
- **Comparabilité intra-décennie forte** : entre deux rebasages, tous les indices partagent une base commune ancrée en 2015 (puis 2025, etc.).
- **Résistance au shifting baseline** : le paradoxe de la fenêtre glissante est fortement atténué.
- **Conformité aux standards** : Z-score et pondération égale (OCDE/PNUD), base fixe rebasée décennale (INSEE/Eurostat).
- **Transparence** : la période de référence de chaque indice est déterministe et affichée dans l'interface.

## 6. Faiblesses et limites assumées

- **Inertie croissante en fin de décennie** : plus la référence s'allonge, moins une variation annuelle pèse dans μ et σ (voir §7). C'est précisément ce que le rebasage décennal corrige.
- **Discontinuité au rebasage** : l'ICF 2036 (base 2025) n'est pas strictement comparable à l'ICF 2035 (base 2015). Comme pour l'INSEE, la transition doit être documentée publiquement ; on peut publier les deux valeurs l'année charnière.
- **ICF 2015–2024 indicatifs** : calculés avec une référence postérieure à leur année, ils décrivent la trajectoire mais ne sont pas des mesures « officielles ».
- **Extrapolations linéaires** : les indicateurs sans donnée pour une année sont extrapolés par régression, ce qui suppose la poursuite des tendances passées. L'interface signale ces cas (code couleur violet).
- **Hypothèse de normalité approximative** : la lecture probabiliste des bornes ±3 suppose des distributions proches de la normale, non vérifiable rigoureusement sur des séries courtes (les tests type Shapiro-Wilk manquent de puissance sous 10–20 points). Les bornes ±3 sont une convention robuste, pas une garantie.

---

## 7. La question de la sensibilité en fin de décennie (« les indices de 2034 seront-ils trop faibles ? »)

**Le phénomène est réel mais il ne rend pas les indices "plus faibles" — il les rend moins *réactifs*.** Deux effets opposés se combinent :

1. **σ augmente** avec la longueur de la référence si l'indicateur a une tendance (la dispersion incorpore la tendance de long terme). Une variation annuelle donnée produit donc un déplacement de Z plus petit → l'indice bouge moins d'une année sur l'autre.
2. **μ retarde sur la tendance** : la moyenne d'une référence de 19 ans est tirée vers le passé. Une année récente dans le prolongement de la tendance s'éloigne donc de plus en plus de μ → son Z est grand et l'indice peut dériver vers les bords de l'échelle (proche de 0 ou 100), où le clamp à ±3 finit par saturer.

Le résultat net en 2034 : des indices dont le **niveau** reflète surtout l'écart cumulé depuis 2015 (information pertinente pour un indice de trajectoire), mais dont les **variations annuelles** sont amorties d'environ 30–40 % par rapport au début de décennie (ordre de grandeur : σ estimé sur 19 points vs 10 points sur une série tendancielle typique).

**Peut-on y pallier ?** Trois options, par ordre de recommandation :

- **Le rebasage décennal (déjà prévu) est la parade principale** : en 2036, la référence redevient courte (2025–2035) et la sensibilité est restaurée. C'est exactement la fonction du rebasage chez l'INSEE.
- **Publier en complément la variation annuelle brute** de chaque indicateur (+x % vs année précédente) à côté de l'indice : l'indice porte la trajectoire de fond, la variation brute porte l'actualité. Coût nul, lisibilité maximale.
- *(Non recommandé)* pondérer la référence en donnant plus de poids aux années récentes (moyenne mobile exponentielle) : techniquement possible mais complexifie la méthode et affaiblit son ancrage dans les standards.

**Peut-on considérer l'effet comme négligeable ?** Sur l'horizon d'une décennie, oui, à condition de le savoir : l'amortissement est progressif, il ne fausse pas le sens des évolutions (un indice qui baisse traduit bien une dégradation relative), et il est borné dans le temps par le rebasage. C'est un compromis classique des indices de long terme : on échange un peu de réactivité contre beaucoup de stabilité et de comparabilité — le bon compromis pour un indice destiné au débat public, qui mesure une trajectoire de société et non une conjoncture.

---

## 8. Cycle de vie d'un indice dans la plateforme

1. **Saisie** : les données brutes de l'année N−1 sont saisies via le formulaire « Ajouter les données de l'année suivante » (onglet ICF Global). Un indicateur peut être laissé vide → extrapolé, signalé en violet.
2. **Vérification** : l'indice N apparaît en provisoire (orange). Les données restent modifiables (valeurs des années existantes éditables dans chaque onglet, y compris les années nouvellement ajoutées).
3. **Publication** : l'administrateur **fige** l'indice N (panneau « Geler les scores »). Il devient définitif (vert) et n'est plus jamais recalculé, même si les données brutes changent ensuite. Un mécanisme détecte et signale les scores figés divergents (données modifiées après gel) et permet de les recalculer ou de les dégeler explicitement.
