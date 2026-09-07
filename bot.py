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
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    # Korumaya takılmamak için kısa bir es
    time.sleep(2)
    
    response = scraper.get(SEARCH_URL, headers=headers)
    if response.status_code != 200:
        print(f"[HATA] Bağlantı başarısız! HTTP Kodu: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Farklı ilan kapsayıcı etiketlerini dene
    articles = soup.find_all('article', class_=lambda x: x and 'aditem' in x)
    if not articles:
        articles = soup.select('ul#srchrslt-adresults > li article')
    if not articles:
        articles = soup.select('.ad-listitem')

    print(f"[INFO] Toplam {len(articles)} adet ilan tarandı.")

    if len(articles) == 0:
        print("[UYARI] Sayfa çekildi ancak ilan etiketi bulunamadı (Anti-bot engelinde olabilir).")
        return

    for article in articles[:5]:
        title_elem = article.find('a', class_=lambda x: x and ('ellipsis' in x or 'badge' in x)) or article.find('h2')
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
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")
            
            break

if __name__ == "__main__":
    main()
