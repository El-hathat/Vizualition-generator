from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import run_agentic_query
from superset_api import get_token, get_dataset, create_chart

app = FastAPI(title="AI Superset Generator")

# Schéma de la requête entrante
class QueryRequest(BaseModel):
    query: str
    table_name: str = "sales_dummy"  # valeur par défaut


# Endpoint principal — génère un chart Superset depuis une requête en langage naturel
@app.post("/generate-viz")
async def generate_viz(request: QueryRequest):
    try:
        # 1. Génération SQL + sélection viz via le pipeline Agentic AI
        result = run_agentic_query(request.query)

        # Remonte l'erreur LLM/SQL si le pipeline a échoué
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # 2. Authentification Superset
        token = get_token()

        # 3. Récupération du dataset_id à partir du nom de la table
        dataset_id = get_dataset(token, request.table_name)

        # 4. Création du chart via l'API Superset
        chart = create_chart(token, dataset_id, result)

        return {
            "status":   "success",
            "sql":      result["sql"],
            "viz_type": result["viz_type"],
            "title":    result["title"],
            "chart_id": chart.get("id"),
            "message":  f"Chart créé avec succès ! ID = {chart.get('id')}"
        }

    except Exception as e:
        # Log complet de la stacktrace côté serveur
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))