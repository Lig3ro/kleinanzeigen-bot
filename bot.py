import os
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
        'country_code': 'de',
        'keep_headers': 'true'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        response = requests.get('http://api.scraperapi.com', params=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            print(f"[HATA] ScraperAPI Istek Başarısız! HTTP: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Kleinanzeigen ilan kapsayıcıları
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
        
        if not articles:
            # Alternatif liste kapsayıcısı
            articles = soup.find_all('li', class_=lambda x: x and 'ad-listitem' in x)

        print(f"[INFO] Incelenecek toplam ilan sayısı: {len(articles)}")

        if not articles:
            print("[UYARI] Sayfada ilan kapsayıcısı bulunamadı.")
            return

        for article in articles:
            ad_id = article.get('data-adid')
            
            # ID yoksa linkten çek
            title_elem = article.find('a', class_=lambda x: x and ('ellipsis' in x or 'badge' in x)) or article.find('h2') or article.find('a')
            if not title_elem:
                continue

            href = title_elem.get('href') or ''
            if not ad_id and href:
                ad_id = href.split('/')[-1]

            if not ad_id or ad_id in posted_ads:
                continue

            price_elem = article.find('p', class_=lambda x: x and 'price' in x)
            date_elem = article.find('div', class_=lambda x: x and 'aditem-main--top--right' in x)

            title = title_elem.text.strip() or "Arızalı Ekran Kartı İlanı"
            price = price_elem.text.strip() if price_elem else "Fiyat Belirtilmedi"
            raw_date = " ".join(date_elem.text.split()) if date_elem else "Bugün / Yeni"
            link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

            print(f"[YENİ İLAN] {title} | {price} | {raw_date}")

            payload_discord = {
                "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Sitedeki Yüklenme Saati:** 🕒 `{raw_date}`\n**Link:** {link}"
            }
            
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
            if res.status_code in [200, 204]:
                print(f"[BAŞARILI] Discord'a atıldı: {ad_id}")
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
