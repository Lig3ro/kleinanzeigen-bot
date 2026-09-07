import os
import time
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
    is_first_run = len(posted_ads) == 0
    print(f"[INFO] Hafızadaki ilan sayısı: {len(posted_ads)}")
    
    # JS render aktif edildi
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': TARGET_URL,
        'country_code': 'de',
        'render': 'true'
    }
    
    try:
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=90)
        
        if response.status_code != 200:
            print(f"[HATA] ScraperAPI Istek Başarısız! HTTP: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Standart ilan kartları
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
        
        # 2. Alternatif liste kapsayıcıları
        if not articles:
            articles = soup.select('ul#srchrslt-adresults > li')

        if not articles:
            print("[UYARI] Sayfada ilan kartı bulunamadı.")
            return

        print(f"[INFO] Incelenecek toplam ilan sayısı: {len(articles)}")

        new_ads_found = 0

        for article in articles:
            # İlan ID'si çekme
            ad_id = article.get('data-adid')
            
            title_elem = article.find('a', class_=lambda x: x and ('ellipsis' in x or 'badge' in x)) or article.find('h2') or article.find('a')
            if not title_elem:
                continue

            href = title_elem.get('href') or ''
            if not href or '/s-anzeige/' not in href:
                continue

            if not ad_id:
                ad_id = href.split('/')[-1]

            # Zaten hafızadaysa atla
            if ad_id in posted_ads:
                continue

            price_elem = article.find('p', class_=lambda x: x and 'price' in x)
            date_elem = article.find('div', class_=lambda x: x and 'aditem-main--top--right' in x)

            title = title_elem.text.strip() or "Arızalı Ekran Kartı İlanı"
            price = price_elem.text.strip() if price_elem else "Fiyat Belirtilmedi"
            raw_date = " ".join(date_elem.text.split()) if date_elem else "Bugün / Yeni"
            link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

            # İlk çalıştırmada mevcut eski ilanları hafızaya alıp Discord'u spamlamıyoruz
            if is_first_run:
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
                continue

            print(f"[YENİ İLAN DETAYI] {title} | {price} | {raw_date}")

            payload_discord = {
                "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Sitedeki Yüklenme Saati:** 🕒 `{raw_date}`\n**Link:** {link}"
            }
            
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
            if res.status_code in [200, 204]:
                print(f"[BAŞARILI] Discord'a gönderildi: {title}")
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
                new_ads_found += 1
                time.sleep(1.5)
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")

        if is_first_run:
            print("[INFO] İlk çalıştırma tamamlandı. Sayfadaki mevcut ilanlar hafızaya kaydedildi. Artık sadece SIFIR YENİ ilanlar Discord'a atılacak!")
        elif new_ads_found == 0:
            print("[INFO] Yeni ilan yok.")

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
