import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    # 1. Charger le fichier JSON des médailles par pays
    with open('json/medaille_pays.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Normaliser et trier
    df = pd.json_normalize(data)
    df_top15 = df.sort_values('total', ascending=False).head(15)

    # 3. Générer une palette dégradée depuis 'viridis'
    cmap = plt.get_cmap('viridis')
    colors = cmap(np.linspace(0.2, 0.8, len(df_top15)))

    # 4. Créer le graphique
    plt.figure(figsize=(12, 7))
    bars = plt.bar(
        df_top15['pays'], 
        df_top15['total'], 
        color=colors, 
        edgecolor='black', 
        linewidth=1
    )
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Pays')
    plt.ylabel('Total Médailles')
    plt.title('Top 15 des pays olympiques par nombre total de médailles')
    plt.tight_layout()

    # 5. Annoter chaque barre avec sa valeur
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2, 
            height + 10, 
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=9
        )

    # 6. Sauvegarder le graphique en PNG haute résolution
    output_path = 'png/top_medaille_pays.png'
    plt.savefig(output_path, format='png', dpi=300)
    plt.close()

    print(f"Graphique coloré sauvegardé sous : {output_path}")

if __name__ == '__main__':
    main()
