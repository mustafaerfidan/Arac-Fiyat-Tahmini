from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def araba_verisi_cek(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Sunucuya geçince bunu True yapacağız
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(6000)
        
        html_icerigi = page.content()
        browser.close()
        
        soup = BeautifulSoup(html_icerigi, "html.parser")
        araba_verisi = {}
        
        baslik_elem = soup.find("h1")
        araba_verisi["İlan Başlığı"] = baslik_elem.text.strip() if baslik_elem else "Bulunamadı"
        
        fiyat_elem = soup.find(class_=lambda x: x and 'price' in x)
        if fiyat_elem:
            fiyat_parcalari = list(fiyat_elem.stripped_strings)
            for parca in fiyat_parcalari:
                if "TL" in parca or parca.replace(".", "").isdigit():
                    araba_verisi["Fiyat"] = parca.strip()
                    break
        if "Fiyat" not in araba_verisi:
            araba_verisi["Fiyat"] = "Bulunamadı"
        
        ozellik_listesi = soup.find_all(["li", "div"])
        hedef_anahtarlar = [
            "Marka", "Seri", "Model", "Yıl", "Kilometre", 
            "Vites Tipi", "Yakıt Tipi", "Kasa Tipi", "Renk", 
            "Motor Hacmi", "Motor Gücü", "Ağır Hasarlı", 
            "Yakıt Deposu", "Çekiş", "Ortalama Yakıt Tüketimi", 
            "Ort. Yakıt Tüketimi", "Boya-değişen", "Boya/Değişen"
        ]
        
        for element in ozellik_listesi:
            parcalar = list(element.stripped_strings)
            if len(parcalar) == 2:
                anahtar = parcalar[0].replace(":", "").strip()
                deger = parcalar[1].strip()
                
                if anahtar in hedef_anahtarlar:
                    if anahtar not in araba_verisi:
                        araba_verisi[anahtar] = deger
                        
        if "Boya-değişen" not in araba_verisi and "Boya/Değişen" not in araba_verisi:
            araba_verisi["Boya/Değişen"] = "Belirtilmemiş veya Ekspertiz Şemasında"
            
        return araba_verisi