import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)
dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(365)]
regions = ["Casablanca", "Rabat", "Marrakech", "Tanger", "Agadir"]
clients = [f"Client_{i:04d}" for i in range(200)]

data = {
    "date": np.random.choice(dates, 5000),
    "region": np.random.choice(regions, 5000),
    "client": np.random.choice(clients, 5000),
    "categorie_produit": np.random.choice(["Électronique", "Mode", "Alimentaire", "Maison"], 5000),
    "montant_vente": np.random.uniform(50, 1500, 5000).round(2),
    "quantite": np.random.randint(1, 20, 5000),
}

df = pd.DataFrame(data)
df.to_csv("sales_dummy.csv", index=False)
print("✅ Dataset créé : sales_dummy.csv (5000 lignes)")