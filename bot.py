import os
import time
import requests
import cloudscraper
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
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
    if not DISCORD_WEBHOOK_URL:
        print("[HATA] Discord Webhook Secret'ı eksik!")
        return

    posted_ads = load_posted_ads()
    is_first_run = len(posted_ads) == 0
    print(f"[INFO] Hafızadaki ilan sayısı: {len(posted_ads)}")
    print("[INFO] Cloudscraper ile Kleinanzeigen doğrudan taranıyor...")

    # Cloudflare engelini aşan tarayıcı simülasyonu
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:
        response = scraper.get(TARGET_URL, timeout=30)

        if response.status_code != 200:
            print(f"[HATA] Bağlantı Başarısız! HTTP Kodu: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Kleinanzeigen kapsayıcı tespiti
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
        if not articles:
            articles = soup.find_all('a', href=lambda h: h and '/s-anzeige/' in h)

        print(f"[INFO] Bulunan ilan sayısı: {len(articles)}")

        if len(articles) == 0:
            print("[UYARI] Sayfada ilan etiketleri çekilemedi.")
            return

        new_ads_count = 0

        for item in articles:
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

            ad_id = item.get('data-adid') if item.name != 'a' else None
            if not ad_id:
                ad_id = href.split('/')[-1]

            if ad_id in posted_ads:
                continue

            link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

            if is_first_run:
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
                continue

            print(f"[YENİ İLAN] {title} | {price} | {raw_date}")

            payload_discord = {
                "content": f"<@734134493039951964> 🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Sitedeki Yüklenme Saati:** 🕒 `{raw_date}`\n**Link:** {link}"
            }
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
            if res.status_code in [200, 204]:
                print(f"[BAŞARILI] Discord bildirimi gönderildi: {ad_id}")
                save_posted_ad(ad_id)
                posted_ads.add(ad_id)
                new_ads_count += 1
                time.sleep(1.5)
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")

        if is_first_run:
            print("[INFO] İlk tarama yapıldı! Mevcut eski ilanlar hafızaya kaydedildi.")
        elif new_ads_count == 0:
            print("[INFO] Yeni ilan bulunamadı.")

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
