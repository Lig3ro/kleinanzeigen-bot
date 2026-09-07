import os
import time
import requests
from bs4 import BeautifulSoup
import cloudscraper

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
SEARCH_URL = "https://www.kleinanzeigen.de/s-grafikkarte-defekt/k0"

def main():
    if not DISCORD_WEBHOOK_URL:
        print("[HATA] DISCORD_WEBHOOK Secret bulunamadi!")
        return

    print("[INFO] Kleinanzeigen taranıyor...")
    
    # Anti-bot korumasını aşmak için gelişmiş scraper konfigürasyonu
    scraper = cloudscraper.create_scraper(
        delay=10,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    time.sleep(2)
    response = scraper.get(SEARCH_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"[HATA] Bağlantı engellendi! HTTP Kodu: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Kleinanzeigen ilan kartları
    articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
    
    print(f"[INFO] Toplam {len(articles)} adet ilan tarandı.")

    if len(articles) == 0:
        print("[UYARI] Sayfa korumaya takıldı. Engel aşma servisi (Proxy/Scraper API) gerekiyor.")
        return

    for article in articles[:5]:
        title_elem = article.find('a', class_=lambda x: x and 'ellipsis' in x) or article.find('h2')
        price_elem = article.find('p', class_=lambda x: x and 'price' in x)
        
        if title_elem and price_elem:
            title = title_elem.text.strip()
            price = price_elem.text.strip()
            href = title_elem.get('href') or title_elem.find_parent('a')['href']
            link = "https://www.kleinanzeigen.de" + href

            print(f"[INFO] Son ilan bulundu: {title} - {price}")

            payload = {
                "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Link:** {link}"
            }
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if res.status_code in [200, 204]:
                print("[BAŞARILI] Discord bildirimi gönderildi!")
            break

if __name__ == "__main__":
    main()
