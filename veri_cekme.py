from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd  # Pandas eklendi

def araba_verisi_cek(url):
    print("Tarayıcı başlatılıyor...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("İlan sayfasına gidiliyor...")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(6000)
        
        html_icerigi = page.content()
        browser.close()
        
        soup = BeautifulSoup(html_icerigi, "html.parser")
        araba_verisi = {}
        
        # 1. İlan Başlığı
        baslik_elem = soup.find("h1")
        araba_verisi["İlan Başlığı"] = baslik_elem.text.strip() if baslik_elem else "Bulunamadı"
        
        # 2. Fiyat Bilgisi
        fiyat_elem = soup.find(class_=lambda x: x and 'price' in x)
        if fiyat_elem:
            fiyat_parcalari = list(fiyat_elem.stripped_strings)
            for parca in fiyat_parcalari:
                if "TL" in parca or parca.replace(".", "").isdigit():
                    araba_verisi["Fiyat"] = parca.strip()
                    break
        if "Fiyat" not in araba_verisi:
            araba_verisi["Fiyat"] = "Bulunamadı"
        
        # 3. Tüm Araç Bilgileri
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
                        
        print("\n--- Çekilen Yapılandırılmış Araç Verileri ---")
        for k, v in araba_verisi.items():
            print(f"{k}: {v}")
            
        return araba_verisi

# URL'mizi fonksiyona gönderiyoruz
hedef_url = "https://www.arabam.com/ilan/galeriden-satilik-hyundai-bayon-1-4-mpi-style/dogan-oto-galeriden-2024-otomtik-hyundai-bayon-1-4-mpi-style-sunroff-full-22-bin-km-hatasz/42577061"
elde_edilen_veri = araba_verisi_cek(hedef_url)

# Veriyi Pandas DataFrame'e çevirip CSV olarak kaydediyoruz
df = pd.DataFrame([elde_edilen_veri])
df.to_csv("araba_verileri.csv", index=False, encoding="utf-8-sig")
print("\nVeriler başarıyla 'araba_verileri.csv' dosyasına kaydedildi!")