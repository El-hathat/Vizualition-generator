# AI Superset Generator

Générateur automatique de visualisations Apache Superset à partir de requêtes en langage naturel, basé sur une approche **Agentic AI**.

---

## Aperçu

L'utilisateur pose une question en français → le système génère le SQL, choisit le meilleur type de chart et le crée directement dans Apache Superset via son API REST — sans aucune intervention manuelle.

```
Utilisateur → FastAPI → SQL Agent (LangChain) → PostgreSQL
                                ↓
                          Gemini LLM → viz_type + groupby + metric
                                ↓
                        Superset API → Chart créé (201)
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Backend API | FastAPI (Python) |
| LLM Agent | LangChain + Gemini (`gemini-1.5-flash`) |
| Base de données | PostgreSQL `:5433` |
| Visualisation | Apache Superset `:8088` |
| Connexion DB | SQLAlchemy + psycopg2 |
| Config | python-dotenv |

---

## Structure du projet

```
backend/
├── main.py            # FastAPI — endpoint POST /generate-viz
├── agent.py           # LangChain SQL Agent + sélection viz via LLM
├── superset_api.py    # Auth + création de charts Superset
├── .env               # Variables d'environnement (non versionné)
├── .env.example       # Template de configuration
└── requirements.txt   # Dépendances Python
```

---

## Dataset

Table PostgreSQL `sales_dummy` :

| Colonne | Type | Rôle |
|---|---|---|
| `date` | VARCHAR | Date de transaction |
| `region` | VARCHAR | Dimension géographique |
| `client` | VARCHAR | Dimension client |
| `categorie_produit` | VARCHAR | Dimension produit |
| `montant_vente` | NUMERIC | Métrique principale (€) |
| `quantite` | INTEGER | Métrique volume |

```sql
CREATE TABLE IF NOT EXISTS sales_dummy (
    date              VARCHAR(20),
    region            VARCHAR(100),
    client            VARCHAR(100),
    categorie_produit VARCHAR(100),
    montant_vente     NUMERIC(12, 2),
    quantite          INTEGER
);
```

---

## Installation

### 1. Cloner et installer les dépendances

```bash
pip install fastapi uvicorn langchain langchain-google-genai \
            langchain-community sqlalchemy psycopg2-binary python-dotenv
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

```env
# .env
GOOGLE_API_KEY=AIzaSy...votre_cle_gemini
```

### 3. Lancer Apache Superset

```bash
docker start <container_superset>
# Interface : http://localhost:8088  (admin / admin)
```

### 4. Lancer le backend

```bash
uvicorn main:app --reload --port 8000
# Docs auto : http://localhost:8000/docs
```

---

## Utilisation

### Endpoint

```
POST http://localhost:8000/generate-viz
Content-Type: application/json
```

### Corps de la requête

```json
{
  "query": "Montre-moi le chiffre d'affaires par région",
  "table_name": "sales_dummy"
}
```

### Réponse

```json
{
  "status": "success",
  "sql": "SELECT region, SUM(montant_vente) FROM sales_dummy GROUP BY region",
  "viz_type": "bar",
  "title": "Chiffre d'affaires par région",
  "chart_id": 1,
  "message": "Chart créé avec succès ! ID = 1"
}
```

---

## Exemples de requêtes

| Requête | Chart généré |
|---|---|
| "Chiffre d'affaires par région" | Bar chart |
| "Répartition des ventes par catégorie" | Pie chart |
| "Total des ventes" | Big number |
| "Liste détaillée des ventes par client" | Table |
| "Corrélation quantité / montant par client" | Scatter |

---

## Types de visualisations supportés

| viz_type | Nom Superset | Cas d'usage |
|---|---|---|
| `bar` | `dist_bar` | Comparaison entre catégories |
| `pie` | `pie` | Proportions / parts |
| `table` | `table` | Détail ligne par ligne |
| `big_number` | `big_number_total` | KPI unique agrégé |
| `scatter` | `scatter` | Corrélation entre métriques |

---

## Logique Agentic AI

### Étape 1 — Génération SQL

Le `SQL Agent` LangChain interprète la requête en langage naturel et génère une requête SQL adaptée au schéma de `sales_dummy`, sans LIMIT arbitraire.

### Étape 2 — Sélection de la visualisation

Un second appel Gemini analyse la requête + le SQL pour déterminer :
- `viz_type` — type de chart
- `groupby` — colonnes de regroupement
- `metric_column` — métrique à agréger
- `metric_agg` — agrégation (SUM / AVG / COUNT / MAX / MIN)
- `title` — titre professionnel

### Safety guards

Protections contre les sorties LLM mal formées :

```python
# metric_agg peut être une liste
if isinstance(metric_agg, list):
    metric_agg = metric_agg[0] if metric_agg else "SUM"
metric_agg = str(metric_agg).upper()

# groupby peut être une string
if isinstance(groupby, str):
    groupby = [groupby]

# allowlist validation
allowed_viz = ["bar", "pie", "table", "big_number", "scatter"]
if viz_type not in allowed_viz:
    viz_type = "bar"
```

---

## Bugs résolus

| Erreur | Cause | Correction |
|---|---|---|
| `form_data: Unknown field` | API Superset n'accepte pas `form_data` en top-level | `params: json.dumps(form_data)` |
| `'list' has no .upper()` | LLM retourne `metric_agg` comme liste | `isinstance` check + extraction `[0]` |
| `429 RESOURCE_EXHAUSTED` | Quota dépassé sur `gemini-2.5-flash-lite` (20/jour) | Migration vers `gemini-1.5-flash` (1500/jour) |
| Chart type `histogram` | `bar` mappé incorrectement | Mapping explicite `bar → dist_bar` |
| `COLUMNS` vide dans Superset | `groupby` mal configuré pour `dist_bar` | Ajout de `columns: []` en plus de `groupby` |

---

## Gestion des rate limits

| Modèle | Limite gratuite | Usage recommandé |
|---|---|---|
| `gemini-2.5-flash-lite` | 20 req/jour | Développement uniquement |
| `gemini-1.5-flash` | 1500 req/jour | Tests et démo |
| `claude-3-5-haiku` | Payant | Production |

---

## .gitignore

```gitignore
__pycache__/
*.py[cod]
.env
.env.*
!.env.example
venv/
.venv/
*.log
.langchain.db
*.db
.DS_Store
.idea/
.vscode/
```

---

## Auteur

**Mohamed El-hathat** — Ingénieur Data, ENSET Mohammedia  
Metaverse — Use Case Data Visualization