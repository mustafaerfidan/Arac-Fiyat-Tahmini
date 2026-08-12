import requests
from bs4 import BeautifulSoup

# Hedef siteye istek atarken bot olduğumuzun hemen anlaşılmaması için bir başlık (User-Agent) ekliyoruz
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Test amaçlı örnek bir arama URL'si veya basit bir sayfa kullanalım
# (Şimdilik bağlantının çalışıp çalışmadığını test ediyoruz)
url = "https://httpbin.org/headers" 

print("Web sitesine istek gönderiliyor...")
response = requests.get(url, headers=headers)

# İstek başarılı mı diye kontrol ediyoruz (200 başarılı demek)
if response.status_code == 200:
    print("Bağlantı başarılı! Site bize veri gönderdi.")
    print(response.text[:300]) # Gelen verinin ilk 300 karakterini ekrana bastıralım
else:
    print(f"Bir hata oluştu, hata kodu: {response.status_code}")