import json
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote

BASE_URL     = "https://olympics-statistics.com"
START_PAGE   = "/olympic-athletes"
OUTPUT_FILE  = "json/medaille_athlete.json"
COUNTRY_CODE_FILE = "json/country_codes.json"

MEDAL_MAP = {'1': 'gold', '2': 'silver', '3': 'bronze'}

# Chargement des codes pays
with open(COUNTRY_CODE_FILE, "r", encoding="utf-8") as f:
    country_codes = json.load(f)

# Fonctions utilitaires
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^\w\s\-\'éèàçùûüäöëô]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_name(name):
    return ' '.join([part.capitalize() for part in name.split()])

def get_country_from_img_src(img_tag):
    if img_tag and img_tag.get("src"):
        src = img_tag["src"]
        if "flagge/" in src:
            code = src.split("flagge/")[-1].split(".")[0]
            return country_codes.get(code.lower(), "")
    return ""

def get_letter_urls():
    resp = requests.get(urljoin(BASE_URL, START_PAGE))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [
        urljoin(BASE_URL, a["href"])
        for a in soup.select('div.alpha a[href^="/olympic-athletes/"]')
    ]

def fetch_athlete_detail(card):
    try:
        first = format_name(clean_text(card.select_one(".vn").get_text(strip=True)))
        last  = format_name(clean_text(card.select_one(".nn").get_text(strip=True)))
        raw_url = urljoin(BASE_URL, card["href"])
        parsed = urlparse(raw_url)
        encoded_path = quote(parsed.path)
        detail_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"

        r = requests.get(detail_url, timeout=10)
        r.raise_for_status()
        dsoup = BeautifulSoup(r.text, "html.parser")

        flag = dsoup.select_one(".legende img")
        country = get_country_from_img_src(flag)

        medals = []
        for med in dsoup.select(".deck .medaille.visible"):
            medal_type = med.select_one(".the-medal")
            code_med = medal_type["data-medal"] if medal_type else "?"
            medal = MEDAL_MAP.get(code_med, "unknown")

            sport = clean_text(med.select_one(".m-sport").get_text(strip=True)) if med.select_one(".m-sport") else ""
            date_elem = med.select_one(".m-event-am")
            year = None
            if date_elem:
                try:
                    year = date_elem.text.strip().split()[-1]
                    if not year.isdigit():
                        year = None
                except:
                    year = None

            medals.append({
                "sport": sport,
                "medal": medal,
                "year": int(year) if year and year.isdigit() else None
            })

        return {
            "firstname": first,
            "lastname": last,
            "country": country,
            "medals": medals
        }

    except Exception as e:
        print(f"[Erreur] {card['href']} : {e}")
        return None

def scrape_all_athletes():
    letter_urls = get_letter_urls()

    cards = []
    for url in letter_urls:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cards.extend(soup.select("a.card.athlet.visible")) 


    total = len(cards)
    print(f"Total athlètes à récupérer : {total}")
    results = []
    for i, card in enumerate(cards, 1):
        athlete = fetch_athlete_detail(card)
        if athlete:
            print(f"[{i}/{total}] {athlete['firstname']} {athlete['lastname']}")
            results.append(athlete)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"{len(results)} athlètes sauvegardés dans '{OUTPUT_FILE}'")

if __name__ == "__main__":
    scrape_all_athletes()
