import os
import requests
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")
TARGET_URL = "https://www.kleinanzeigen.de/s-grafikkarte-defekt/k0"

def main():
    if not DISCORD_WEBHOOK_URL or not SCRAPER_API_KEY:
        print("[HATA] Secret'lar eksik!")
        return

    print("[INFO] ScraperAPI üzerinden Kleinanzeigen taranıyor...")
    
    # ScraperAPI konfigürasyonu - render ve keep_headers
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
        
        # Sayfa başlığını yazdırarak engeli doğrula
        page_title = soup.title.string.strip() if soup.title else "Başlık Yok"
        print(f"[DEBUG] Sayfa Başlığı: {page_title}")

        # Tüm 'a' etiketlerinden ilan linklerini filtrele
        ad_links = soup.find_all('a', href=lambda h: h and '/s-anzeige/' in h)
        print(f"[DEBUG] Bulunan ilan linki sayısı: {len(ad_links)}")

        if len(ad_links) == 0:
            print("[UYARI] Sayfada hiç ilan linki bulunamadı.")
            return

        # İlk geçerli ilanı al
        first_ad = ad_links[0]
        title = first_ad.text.strip() or "Arızalı Ekran Kartı İlanı"
        href = first_ad.get('href')
        link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

        print(f"[INFO] İlan bulundu: {title} -> {link}")

        payload_discord = {
            "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Link:** {link}"
        }
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
        if res.status_code in [200, 204]:
            print("[BAŞARILI] Discord bildirimi gönderildi!")
        else:
            print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
