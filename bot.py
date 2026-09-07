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
    print("[INFO] ScraperAPI üzerinden Kleinanzeigen taranıyor...")
    
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': TARGET_URL,
        'country_code': 'de'
    }
    
    try:
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"[HATA] ScraperAPI Istek Başarısız! HTTP Kodu: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Senin çalışan yapıdaki kapsayıcılar
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
        if not articles:
            articles = soup.find_all('a', href=lambda h: h and '/s-anzeige/' in h)

        print(f"[INFO] Bulunan ilan sayısı: {len(articles)}")

        if len(articles) == 0:
            print("[UYARI] Sayfada ilan etiketleri çekilemedi.")
            return

        new_ads_count = 0

        for item in articles:
            # 1. Veri Ayıklama
            if item.name == 'a':
                href = item.get('href') or ''
                title = item.text.strip() or "Arızalı Ekran Kartı İlanı"
                price = "Detay için linke tıklayın"
                raw_date = "Bugün / Yeni"
            else:
                title_elem = item.find('a', class_=lambda x: x and ('ellipsis' in x or 'badge' in x)) or item.find('h2')
                price_elem = item.find('p', class_=lambda x: x and 'price' in x)
                date_elem = item.find('div', class_=lambda x: x and 'aditem-main--top--right' in x)
                
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                price = price_elem.text.strip() if price_elem else "Fiyat Belirtilmedi"
                raw_date = " ".join(date_elem.text.split()) if date_elem else "Saat Bilgisi Yok"
                href = title_elem.get('href') or title_elem.find_parent('a')['href']

            if not href or '/s-anzeige/' not in href:
                continue

            # Benzersiz ilan ID'si al
            ad_id = item.get('data-adid') if item.name != 'a' else None
            if not ad_id:
                ad_id = href.split('/')[-1]

            # 2. Hafıza Filtresi (Daha önce atıldıysa atla)
            if ad_id in posted_ads:
                continue

            link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

            # 3. İlk Çalıştırma Koruması (Eski ilanları atma, sadece hafızaya kaydet)
            if is_first_run:
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
                continue

            # 4. Gerçek Yeni İlanı Discord'a Gönder
            print(f"[YENİ İLAN] {title} | {price} | {raw_date}")

            payload_discord = {
                "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Sitedeki Yüklenme Saati:** 🕒 `{raw_date}`\n**Link:** {link}"
            }
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
            if res.status_code in [200, 204]:
                print(f"[BAŞARILI] Discord bildirimi gönderildi: {ad_id}")
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
                new_ads_count += 1
                time.sleep(1.5)  # Discord spam engeli (429) koruması
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")

        if is_first_run:
            print("[INFO] İlk tarama yapıldı! Mevcut eski ilanlar hafızaya kaydedildi. Bundan sonraki turlarda sadece SIFIR YENİ ilanlar atılacak.")
        elif new_ads_count == 0:
            print("[INFO] Yeni ilan bulunamadı.")

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
