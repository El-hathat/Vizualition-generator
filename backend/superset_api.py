import requests
import json

SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"


# 🔐 LOGIN
def get_token():
    res = requests.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={
            "username": USERNAME,
            "password": PASSWORD,
            "provider": "db",
            "refresh": True
        }
    )
    return res.json()["access_token"]


# 📊 GET DATASET
def get_dataset(token, table_name):
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(
        f"{SUPERSET_URL}/api/v1/dataset/?q=(filters:!((col:table_name,opr:eq,value:{table_name})))",
        headers=headers
    )

    return res.json()["result"][0]["id"]


# 📚 GET COLUMNS
def get_columns(token, dataset_id):
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(
        f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}",
        headers=headers
    )

    return [c["column_name"] for c in res.json()["result"]["columns"]]




# 🧠 metrics builder
def build_metrics(metrics):
    if not metrics:
        return ["count__*"]

    return [
        f"{m.get('type','sum')}__{m.get('column','')}"
        for m in metrics
    ]


# 🧠 fix viz type if no datetime
def fix_viz(viz_type, time_col):
    if viz_type in ["line", "area", "time-series"] and not time_col:
        return "histogram"
    return viz_type


def detect_time_column(columns):
    for c in columns:
        if any(x in c.lower() for x in ["date", "time", "created", "timestamp"]):
            return c
    return None


# -----------------------------
# 🔥 fix viz type safely
# -----------------------------
def fix_viz_type(viz_type, has_time):
    time_viz = ["line", "area", "time-series"]

    if viz_type in time_viz and not has_time:
        return "histogram"

    return viz_type


# -----------------------------
# 🔥 MAIN FUNCTION
# -----------------------------



def create_chart(token, dataset_id, result):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    viz_type       = result.get("viz_type", "bar")
    title          = result.get("title", "AI Chart")
    groupby        = result.get("groupby", ["region"])
    metric_column  = result.get("metric_column", "montant_vente")
    metric_agg     = result.get("metric_agg", "SUM")

    # Build the metric object
    metric = {
        "expressionType": "SIMPLE",
        "column": {"column_name": metric_column},
        "aggregate": metric_agg,
        "label": f"{metric_agg}({metric_column})"
    }

    # Map friendly viz_type → Superset internal name
    VIZ_MAP = {
        "bar":        "dist_bar",
        "pie":        "pie",
        "table":      "table",
        "big_number": "big_number_total",
        "scatter":    "scatter",
    }
    superset_viz = VIZ_MAP.get(viz_type, "dist_bar")

    # Base form_data shared by all types
    form_data = {
        "datasource":  f"{dataset_id}__table",
        "viz_type":    superset_viz,
        "time_range":  "No filter",
        "row_limit":   1000,
    }

    # Per-viz field mapping
    if viz_type == "bar":
        form_data.update({
            "groupby": groupby,
            "columns": [],
            "metrics": [metric],
        })

    elif viz_type == "pie":
        form_data.update({
            "groupby": groupby,
            "metrics": [metric],
            "donut":   False,
            "show_legend": True,
        })

    elif viz_type == "table":
        form_data.update({
            "groupby":      groupby,
            "metrics":      [metric] if groupby else [],
            "all_columns":  [] if groupby else [metric_column],
            "order_desc":   True,
        })

    elif viz_type == "big_number":
        form_data.update({
            "metric": metric,  # big_number uses singular "metric"
        })

    elif viz_type == "scatter":
        # scatter needs x and y — use quantite vs montant_vente
        x_col = "quantite" if metric_column == "montant_vente" else "montant_vente"
        form_data.update({
            "entity":  groupby[0] if groupby else "client",
            "x":       {
                "expressionType": "SIMPLE",
                "column": {"column_name": x_col},
                "aggregate": "SUM",
                "label": f"SUM({x_col})"
            },
            "y": metric,
        })

    payload = {
        "datasource_id":   dataset_id,
        "datasource_type": "table",
        "slice_name":      title,
        "viz_type":        superset_viz,
        "params":          json.dumps(form_data),
    }

    res = requests.post(
        f"{SUPERSET_URL}/api/v1/chart/",
        json=payload,
        headers=headers
    )

    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)

    if res.status_code >= 300:
        raise Exception(res.text)

    return res.json()