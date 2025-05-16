import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    # 1. Charger le fichier JSON
    with open('json/medaille_sport.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Normaliser en DataFrame
    df = pd.json_normalize(data)

    # 3. Trier par nombre total de médailles et garder le top 10
    df_top10 = df.sort_values('total_medaille', ascending=False).head(10)

    # 4. Générer une palette dégradée depuis 'viridis'
    cmap = plt.get_cmap('viridis')
    colors = cmap(np.linspace(0.2, 0.8, len(df_top10)))

    # 5. Créer le diagramme en barres avec style
    plt.figure(figsize=(10, 6))
    bars = plt.bar(
        df_top10['sport'],
        df_top10['total_medaille'],
        color=colors,
        edgecolor='black',
        linewidth=1
    )
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Sport')
    plt.ylabel('Total Médailles')
    plt.title('Top 10 des sports olympiques par nombre total de médailles')
    plt.tight_layout()

    # 6. Annoter chaque barre avec sa valeur
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2,
            height + 5,
            f'{int(height)}',
            ha='center',
            va='bottom',
            fontsize=9
        )

    # 7. Sauvegarder le graphique en PNG haute résolution
    output_path = 'png/top_medaille_sport.png'
    plt.savefig(output_path, format='png', dpi=300)
    plt.close()

    print(f"Graphique coloré sauvegardé sous : {output_path}")

if __name__ == '__main__':
    main()
