import os, json, time, zipfile, logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://www.indiacode.nic.in"
CENTRAL_URL = f"{BASE_URL}/handle/123456789/1362/browse?type=actyear&order=ASC&rpp=100&offset=100"
STATE_URL   = f"{BASE_URL}/handle/123456789/1363/browse?type=actyear"
OUT_DIR     = "All_Acts_PDFs"
ZIP_FILE    = "All_Acts_India.zip"
MANIFEST    = "manifest.json"

os.makedirs(OUT_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
})`1`

def get_soup(url):
    for _ in range(3):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            logging.warning(f"Retrying {url}: {e}")
            time.sleep(3)
    return None

def find_year_links(base):
    soup = get_soup(base)
    if not soup:
        return []
    year_links = []
    for a in soup.select("a[href*='type=actyear']"):
        link = urljoin(BASE_URL, a["href"])
        if link not in year_links:
            year_links.append(link)
    return year_links

def find_act_links(year_url):
    soup = get_soup(year_url)
    if not soup:
        return []
    acts = []
    for a in soup.select("table.panel a[href*='/handle/123456789/']"):
        acts.append(urljoin(BASE_URL, a["href"]))
    return acts

def find_pdf_link(act_url):
    soup = get_soup(act_url)
    if not soup:
        return None
    for a in soup.select("a[href*='bitstream']"):
        href = a.get("href", "")
        if href.endswith(".pdf"):
            return urljoin(BASE_URL, href)
    return None

def download_pdf(url, out_path):
    try:
        with session.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        logging.warning(f"Failed to download {url}: {e}")
        return False

def scrape(base_url, label="central"):
    logging.info(f"📘 Fetching {label} acts from {base_url}")
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    year_links = find_year_links(base_url)
    logging.info(f"✅ Found {len(year_links)} year pages.")

    all_acts = []
    for y in tqdm(year_links, desc=f"{label}-years"):
        acts = find_act_links(y)
        all_acts.extend(acts)

    logging.info(f"📜 Found {len(all_acts)} act pages in {label} category.")
    downloaded = 0

    for act_url in tqdm(sorted(set(all_acts)), desc=f"{label}-acts"):
        if act_url in manifest and manifest[act_url].get("downloaded"):
            continue
        pdf_url = find_pdf_link(act_url)
        if not pdf_url:
            continue

        fname = os.path.basename(pdf_url.split("/")[-1])
        out = os.path.join(OUT_DIR, fname)
        if os.path.exists(out):
            manifest[act_url] = {"downloaded": out, "pdf": pdf_url}
            continue

        if download_pdf(pdf_url, out):
            manifest[act_url] = {"downloaded": out, "pdf": pdf_url}
            downloaded += 1
            with open(MANIFEST, "w") as f:
                json.dump(manifest, f, indent=2)
            time.sleep(1)

    logging.info(f"✅ Downloaded {downloaded} new {label} acts.")

def main():
    scrape(CENTRAL_URL, "central")
    scrape(STATE_URL, "state")
    with zipfile.ZipFile(ZIP_FILE, "w", zipfile.ZIP_DEFLATED) as z:
        for f in os.listdir(OUT_DIR):
            if f.endswith(".pdf"):
                z.write(os.path.join(OUT_DIR, f), f)
    logging.info(f"📦 All acts zipped → {ZIP_FILE}")

if __name__ == "__main__":
    main()
