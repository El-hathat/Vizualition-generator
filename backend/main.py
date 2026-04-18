from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import run_agentic_query
from superset_api import get_token, get_dataset, create_chart

app = FastAPI(title="AI Superset Generator")


class QueryRequest(BaseModel):
    query: str
    table_name: str = "sales_dummy"


@app.post("/generate-viz")
async def generate_viz(request: QueryRequest):
    try:
        result = run_agentic_query(request.query)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        token = get_token()
        dataset_id = get_dataset(token, "sales_dummy")  # ou le nom réel de ta table

        chart = create_chart(token, dataset_id, result)

        return {
            "status": "success",
            "sql": result["sql"],
            "viz_type": result["viz_type"],
            "title": result["title"],
            "chart_id": chart.get("id"),
            "message": f"Chart créé avec succès ! ID = {chart.get('id')}"
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))