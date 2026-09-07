import os
import re
import requests
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")
TARGET_URL = "https://www.kleinanzeigen.de/s-grafikkarte-defekt/k0"
HISTORY_FILE = "posted_ads.txt"

def load_posted_ads():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_posted_ad(ad_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{ad_id}\n")

def main():
    if not DISCORD_WEBHOOK_URL or not SCRAPER_API_KEY:
        print("[HATA] Secret'lar eksik!")
        return

    posted_ads = load_posted_ads()
    print(f"[INFO] Hafızadaki ilan sayısı: {len(posted_ads)}")
    
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': TARGET_URL,
        'country_code': 'de'
    }
    
    try:
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"[HATA] ScraperAPI Istek Başarısız! HTTP: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)

        if not articles:
            print("[UYARI] Sayfada aditem sınıfı bulunamadı.")
            return

        print(f"[INFO] Toplam {len(articles)} ilan inceleniyor...")

        for article in articles:
            # İlan ID'si çekme
            ad_id = article.get('data-adid')
            if not ad_id:
                continue

            # Daha önce atıldıysa atla
            if ad_id in posted_ads:
                continue

            # Detayları çek
            title_elem = article.find('a', class_=lambda x: x and ('ellipsis' in x or 'badge' in x)) or article.find('h2')
            price_elem = article.find('p', class_=lambda x: x and 'price' in x)
            date_elem = article.find('div', class_=lambda x: x and 'aditem-main--top--right' in x)

            if not title_elem:
                continue

            title = title_elem.text.strip()
            price = price_elem.text.strip() if price_elem else "Fiyat Belirtilmedi"
            raw_date = " ".join(date_elem.text.split()) if date_elem else "Saat Belirtilmedi"
            href = title_elem.get('href') or title_elem.find_parent('a')['href']
            link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

            print(f"[YENİ İLAN] {title} | {price} | {raw_date}")

            payload_discord = {
                "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Sitedeki Yüklenme Saati:** 🕒 `{raw_date}`\n**Link:** {link}"
            }
            
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
            if res.status_code in [200, 204]:
                print(f"[BAŞARILI] Discord'a atıldı: {ad_id}")
                save_posted_ad(ad_id)
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
