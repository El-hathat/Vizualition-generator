import os
import json
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

load_dotenv()

# LLM Gemini — temperature=0 pour des réponses déterministes
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.0
)

# Connexion à PostgreSQL
db = SQLDatabase.from_uri("postgresql+psycopg2://superset:superset@localhost:5433/superset")

# Prompt système : interdit les LIMIT arbitraires, liste les colonnes disponibles
custom_prefix = """
Tu es un expert SQL et visualisation pour Apache Superset.
Règles strictes :
- Ne jamais ajouter LIMIT sauf si l'utilisateur demande "top N", "meilleurs", "les plus", etc.
- Pour les GROUP BY, retourne toutes les lignes.
- Utilise uniquement les colonnes qui existent dans la table.
- Les colonnes disponibles sont : date, region, client, categorie_produit, montant_vente, quantite
"""

# SQL Agent LangChain — génère et exécute du SQL sur le dataset
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    prefix=custom_prefix,
    verbose=False,
    handle_parsing_errors=True
)


def clean_json(text: str) -> dict:
    # Supprime les balises ```json et extrait le JSON brut
    text = re.sub(r'```json|```', '', text).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text


def run_agentic_query(user_query: str) -> dict:
    try:
        # Étape 1 — SQL Agent génère la requête SQL
        sql_result = sql_agent.invoke({
            "input": f"{user_query}. Retourne uniquement la requête SQL finale sans LIMIT inutile."
        })
        sql = sql_result.get("output", "").strip()

        # Étape 2 — Gemini choisit viz_type, groupby, metric, agg et title
        viz_prompt = f"""
Tu es un expert en visualisation de données pour Apache Superset.

Requête utilisateur : "{user_query}"
SQL généré : {sql}

Colonnes disponibles dans la table sales_dummy :
- date (texte/date)
- region (texte, catégoriel)
- client (texte, catégoriel)
- categorie_produit (texte, catégoriel)
- montant_vente (numérique, euros)
- quantite (numérique, entier)

Choisis le meilleur type de visualisation selon ces règles :
- "bar"        → comparaison entre catégories (ex: ventes par région)
- "pie"        → proportions/parts (ex: % par catégorie)
- "table"      → plusieurs colonnes, détail ligne par ligne
- "big_number" → une seule valeur agrégée (ex: total ventes)
- "scatter"    → corrélation entre deux colonnes numériques

Réponds UNIQUEMENT avec ce JSON, sans texte avant ou après :
{{
  "viz_type": "bar",
  "title": "Titre professionnel en français",
  "groupby": ["region"],
  "metric_column": "montant_vente",
  "metric_agg": "SUM"
}}

Règles pour les champs :
- viz_type    : uniquement bar / pie / table / big_number / scatter
- groupby     : liste de colonnes catégorielles pour regrouper
- metric_column : colonne numérique à agréger (montant_vente ou quantite)
- metric_agg  : SUM / AVG / COUNT / MAX / MIN selon le sens de la question
"""

        response = llm.invoke(viz_prompt)
        config = json.loads(clean_json(response.content))

        viz_type      = config.get("viz_type", "bar")
        title         = config.get("title", "Analyse par AI")
        groupby       = config.get("groupby", ["region"])
        metric_column = config.get("metric_column", "montant_vente")
        metric_agg    = config.get("metric_agg", "SUM")

        # Safety guards — protection contre les réponses LLM mal formées
        if isinstance(metric_agg, list):
            metric_agg = metric_agg[0] if metric_agg else "SUM"
        metric_agg = str(metric_agg).upper()

        if isinstance(metric_column, list):
            metric_column = metric_column[0] if metric_column else "montant_vente"
        metric_column = str(metric_column)

        if isinstance(groupby, str):
            groupby = [groupby]
        if not isinstance(groupby, list):
            groupby = ["region"]

        allowed_viz = ["bar", "pie", "table", "big_number", "scatter"]
        if viz_type not in allowed_viz:
            viz_type = "bar"

        allowed_agg = ["SUM", "AVG", "COUNT", "MAX", "MIN"]
        if metric_agg not in allowed_agg:
            metric_agg = "SUM"

        allowed_columns = ["montant_vente", "quantite", "date", "region", "client", "categorie_produit"]
        if metric_column not in allowed_columns:
            metric_column = "montant_vente"

        groupby = [c for c in groupby if c in allowed_columns]
        if not groupby and viz_type not in ["big_number", "table"]:
            groupby = ["region"]

        return {
            "sql":           sql,
            "viz_type":      viz_type,
            "title":         title,
            "groupby":       groupby,
            "metric_column": metric_column,
            "metric_agg":    metric_agg,
        }

    except Exception as e:
        # Fallback en cas d'erreur
        return {
            "error":         str(e),
            "sql":           "",
            "viz_type":      "bar",
            "title":         "Erreur lors de la génération",
            "groupby":       ["region"],
            "metric_column": "montant_vente",
            "metric_agg":    "SUM",
        }