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
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)

        if len(articles) == 0:
            print("[UYARI] İlan bulunamadı.")
            return

        for article in articles[:5]:
            title_elem = article.find('a', class_=lambda x: x and ('ellipsis' in x or 'badge' in x)) or article.find('h2')
            price_elem = article.find('p', class_=lambda x: x and 'price' in x)
            
            # İlanın sitedeki gerçek yüklenme saati/tarihi
            date_elem = article.find('div', class_=lambda x: x and 'aditem-main--top--right' in x)
            
            if date_elem:
                # Satır sonlarını ve fazla boşlukları temizle
                raw_date = " ".join(date_elem.text.split())
            else:
                raw_date = "Saat bilgisi alınamadı"

            if title_elem and price_elem:
                title = title_elem.text.strip()
                price = price_elem.text.strip()
                href = title_elem.get('href') or title_elem.find_parent('a')['href']
                link = "https://www.kleinanzeigen.de" + href

                print(f"[INFO] İlan: {title} | Fiyat: {price} | Yüklenme Saati: {raw_date}")

                payload_discord = {
                    "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Sitedeki Yüklenme Saati:** 🕒 `{raw_date}`\n**Link:** {link}"
                }
                res = requests.post(DISCORD_WEBHOOK_URL, json=payload_discord)
                if res.status_code in [200, 204]:
                    print("[BAŞARILI] Discord bildirimi gönderildi!")
                else:
                    print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")
                
                break

    except Exception as e:
        print(f"[HATA] Bir sorun oluştu: {str(e)}")

if __name__ == "__main__":
    main()
