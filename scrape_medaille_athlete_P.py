import json
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from random import sample

BASE_URL     = "https://olympics-statistics.com"
START_PAGE   = "/olympic-athletes"
PROXIES_FILE = "proxies.txt"
OUTPUT_FILE  = "json/medaille_athlete.json"
COUNTRY_CODE_FILE = "json/country_codes.json"

MAX_RETRIES  = 5
MAX_WORKERS  = 30

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

def load_proxies(path):
    proxies = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 4:
                host, port, user, pwd = parts
                proxies.append(f"http://{user}:{pwd}@{host}:{port}")
    if not proxies:
        raise RuntimeError(f"No valid proxies in {path}")
    return proxies

def get_letter_urls():
    resp = requests.get(urljoin(BASE_URL, START_PAGE))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [
        urljoin(BASE_URL, a["href"])
        for a in soup.select('div.alpha a[href^="/olympic-athletes/"]')
    ]

def fetch_athlete_detail(card, proxies):
    first = format_name(clean_text(card.select_one(".vn").get_text(strip=True)))
    last  = format_name(clean_text(card.select_one(".nn").get_text(strip=True)))
    raw_url = urljoin(BASE_URL, card["href"])
    parsed = urlparse(raw_url)
    encoded_path = quote(parsed.path)
    detail_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"
    last_error = None

    for proxy in sample(proxies, k=min(MAX_RETRIES, len(proxies))):
        sess = requests.Session()
        sess.proxies.update({"http": proxy, "https": proxy})
        try:
            r = sess.get(detail_url, timeout=10)
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
            last_error = e

    return {
        "firstname": first,
        "lastname": last,
        "country": None,
        "medals": [],
        "error": str(last_error)
    }

def scrape_all_athletes():
    proxies = load_proxies(PROXIES_FILE)
    letter_urls = get_letter_urls()

    cards = []
    for url in letter_urls:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cards.extend(soup.select("a.card.athlet.visible"))

    total = len(cards)
    print(f"Total athletes to fetch: {total}")

    results = []
    count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_athlete_detail, c, proxies) for c in cards]
        for fut in as_completed(futures):
            athlete = fut.result()
            count += 1
            print(f"{count}/{total} - {athlete['firstname']} {athlete['lastname']}")
            results.append(athlete)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"{len(results)} athlètes sauvegardés dans '{OUTPUT_FILE}'")

if __name__ == "__main__":
    scrape_all_athletes()
