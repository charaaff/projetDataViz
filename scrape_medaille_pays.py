import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://olympics-statistics.com"
NATIONS_URL = f"{BASE_URL}/nations"

# Nettoyage du texte brut
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<.*?>', '', text)  # Supprimer balises HTML
    text = re.sub(r'[^\w\s\-\'éèàçùûüäöëô]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_name(name):
    return ' '.join([w.capitalize() for w in name.split()])

def get_nations():
    res = requests.get(NATIONS_URL, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    nation_cards = soup.select("a.card.nation")

    nations = []
    for card in nation_cards:
        name_raw = card.select_one(".bez").text.strip()
        name = format_name(clean_text(name_raw))
        href = card.get("href")
        flag_img = card.find("img")
        flag_url = BASE_URL + flag_img["src"] if flag_img else ""
        url = BASE_URL + href
        nations.append({"nom": name, "url": url, "drapeau": flag_url})
    return nations

def scrape_medals(nation):
    try:
        res = requests.get(nation["url"], timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        blocks = soup.select("div.rnd.teaser > div")
        gold = silver = bronze = 0

        for block in blocks:
            medal = block.select_one("div.the-medal")
            value = block.select_one("span.mal")
            if medal and value:
                count = int(value.text.strip())
                code = medal.get("data-medal")
                if code == "1":
                    gold = count
                elif code == "2":
                    silver = count
                elif code == "3":
                    bronze = count

        return {
            "pays": nation["nom"],
            "url": nation["url"],
            "drapeau": nation["drapeau"],
            "or": gold,
            "argent": silver,
            "bronze": bronze,
            "total": gold + silver + bronze
        }

    except Exception as e:
        print(f"[ERREUR] {nation['nom']} ({nation['url']}) : {e}")
        return {
            "pays": nation["nom"],
            "url": nation["url"],
            "drapeau": nation["drapeau"],
            "or": 0,
            "argent": 0,
            "bronze": 0,
            "total": 0
        }

# --- MAIN ---
nations_list = get_nations()
results = []

for i, nation in enumerate(nations_list):
    print(f"[{i+1}/{len(nations_list)}] {nation['nom']}")
    results.append(scrape_medals(nation))
    time.sleep(1)

# Sauvegarde
with open("json/medaille_pays.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Fichier nettoyé et sauvegardé sous medaille_pays.json")
