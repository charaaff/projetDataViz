import json
import pandas as pd
import matplotlib.pyplot as plt

# Charger les données JSON
with open("json/medaille_athlete.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Combiner prénom + nom
athletes = pd.json_normalize(data)
athletes["name"] = athletes["firstname"].fillna('') + " " + athletes["lastname"].fillna('')

# Explosion des médailles
medals_expanded = athletes.explode("medals").dropna(subset=["medals"])
medals_details = pd.json_normalize(medals_expanded["medals"])
medals_details["athlete"] = medals_expanded["name"].values

# Top 50 athlètes
top_medalists = medals_details["athlete"].value_counts().head(50).sort_values()

# Graphique
plt.figure(figsize=(10, 8))
top_medalists.plot(kind="barh", color=["royalblue"] * 10 + ["tomato"] * 10)
plt.xlabel("Nombre de médailles")
plt.title("Top 50 des athlètes les plus médaillés (toutes médailles confondues)")
plt.grid(axis='x', linestyle='--', alpha=0.6)
plt.tight_layout()

# Enregistrement
plt.savefig("png/top_medaille_athletes.png", dpi=300)
plt.close()

