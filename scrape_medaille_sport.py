import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://olympics-statistics.com"

# --- Fonctions de nettoyage ---
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^\w\s\-\'éèàçùûüäöëô]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_name(name):
    return ' '.join([w.capitalize() for w in name.split()])

# --- Scraper principal ---
def get_all_sports():
    url = f"{BASE_URL}/olympic-sports"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    sports = []

    for link in soup.select("a.card"):
        sport_name = format_name(clean_text(link.text.strip()))
        sport_url = BASE_URL + link['href']
        sports.append((sport_name, sport_url))
    return sports

def scrape_sport_medals(sport_name, url):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")

        summary_block = soup.select_one("div.statistik")
        nb_medals = int(summary_block.select_one("h2 span").text.strip())
        nb_games = int(summary_block.select("h2")[0].text.split("in")[1].split("Games")[0].strip())
        years = summary_block.select_one("h3").text.strip()

        boxes = summary_block.select("div.teaser div span.mal")
        nb_gold = int(boxes[1].text.strip())
        nb_silver = int(boxes[2].text.strip())
        nb_bronze = int(boxes[3].text.strip())

        last_box = summary_block.select("div.teaser div")[-1].text.strip()
        sport_type = "Summer" if "Summer" in last_box else "Winter" if "Winter" in last_box else ""

        nations_data = []
        for card in soup.select('div.card.nation'):
            country_raw = card['data-bez']
            country = format_name(clean_text(country_raw))
            medals = card.select('div.medals > div')
            gold = int(medals[0].text.strip())
            silver = int(medals[1].text.strip())
            bronze = int(medals[2].text.strip())

            nations_data.append({
                "pays": country,
                "or": gold,
                "argent": silver,
                "bronze": bronze,
                "total": gold + silver + bronze
            })

        return {
            "sport": sport_name,
            "periode": years,
            "nombre_jeux": nb_games,
            "total_medaille": nb_medals,

            "or": nb_gold,
            "argent": nb_silver,
            "bronze": nb_bronze,
            "nations": nations_data
        }

    except Exception as e:
        print(f"[ERREUR] {sport_name} ({url}) : {e}")
        return None

def main():
    all_data = []
    sports = get_all_sports()
    print(f"🔍 {len(sports)} sports trouvés")

    for i, (sport_name, sport_url) in enumerate(sports, 1):
        print(f"[{i}/{len(sports)}] {sport_name}")
        data = scrape_sport_medals(sport_name, sport_url)
        if data:
            all_data.append(data)
        time.sleep(0.5)

    with open("json/medaille_sport.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("Fichier nettoyé et sauvegardé sous 'medaille_sport.json'")

if __name__ == "__main__":
    main()
