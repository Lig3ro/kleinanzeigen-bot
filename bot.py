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
        
        # Farklı ilan kapsayıcılarını tara
        articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
        if not articles:
            articles = soup.find_all('a', href=lambda h: h and '/s-anzeige/' in h)

        print(f"[INFO] Bulunan ilan sayısı: {len(articles)}")

        if len(articles) == 0:
            print("[UYARI] Sayfada ilan etiketleri çekilemedi.")
            return

        for item in articles[:5]:
            # Eğer doğrudan 'a' etiketi yakalandıysa
            if item.name == 'a':
                href = item.get('href')
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

            link = "https://www.kleinanzeigen.de" + href if href.startswith('/') else href

            print(f"[INFO] İlan bulundu: {title} | {price} | {raw_date}")

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
