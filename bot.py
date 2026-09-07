import os
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
    
    scraper = cloudscraper.create_scraper()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = scraper.get(SEARCH_URL, headers=headers)
    if response.status_code != 200:
        print(f"[HATA] Bağlantı başarısız! HTTP Kodu: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article', class_='aditem')
    print(f"[INFO] Toplam {len(articles)} adet ilan tarandı.")

    for article in articles[:5]:  # En son yüklenen ilk 5 ilana bak
        title_elem = article.find('a', class_='ellipsis')
        price_elem = article.find('p', class_='aditem-main--middle--price-shipping--price')
        
        if title_elem and price_elem:
            title = title_elem.text.strip()
            price = price_elem.text.strip()
            link = "https://www.kleinanzeigen.de" + title_elem['href']

            print(f"[INFO] Son ilan bulundu: {title} - {price}")

            # Discord'a Bildirim Gönder
            payload = {
                "content": f"🚨 **Yeni Arızalı Ekran Kartı İlanı!**\n**Başlık:** {title}\n**Fiyat:** {price}\n**Link:** {link}"
            }
            res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if res.status_code in [200, 204]:
                print("[BAŞARILI] Discord bildirimi gönderildi!")
            else:
                print(f"[HATA] Discord bildirimi atılamadı. HTTP: {res.status_code}")
            
            break # Sadece en son ilanı atar

if __name__ == "__main__":
    main()
