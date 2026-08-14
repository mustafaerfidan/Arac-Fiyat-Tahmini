import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

# Kendi yazdığımız modülleri çağırıyoruz
from link_toplayici import linkleri_topla 
from veri_ayiklayici import araba_verisi_cek 

def linkleri_dosyadan_oku(dosya_adi="linkler.txt"):
    """linkler.txt dosyasını okuyup bir sözlük (dictionary) döndürür."""
    kategoriler = {}
    if not os.path.exists(dosya_adi):
        print(f"HATA: '{dosya_adi}' bulunamadı! Lütfen dosyayı oluşturun.")
        return kategoriler

    with open(dosya_adi, "r", encoding="utf-8") as dosya:
        for satir in dosya:
            satir = satir.strip()
            # Boş satırları ve hatalı formatları atla
            if satir and "," in satir: 
                kategori_adi, link = satir.split(",", 1)
                kategoriler[kategori_adi.strip()] = link.strip()
                
    return kategoriler

def main():
    # Linkleri txt dosyasından çekiyoruz
    kategoriler = linkleri_dosyadan_oku("linkler.txt")
    
    if not kategoriler:
        print("İşlenecek link bulunamadı. Program sonlandırılıyor.")
        return

    print(f"Toplam {len(kategoriler)} adet kategori işlenmek üzere yüklendi.\n")

    with sync_playwright() as p:
        # Sunucuda çalıştıracağımız zaman burayı True yapacağız. 
        tarayici = p.chromium.launch(headless=False) 
        sayfa = tarayici.new_page()

        # Metin dosyasından okunan her bir kategori için döngü başlıyor
        for kategori_adi, kategori_linki in kategoriler.items():
            print(f"\n>>> '{kategori_adi}' kategorisi için işlemler başlıyor...")
            
            try:
                # 1. Aşama: İlan linklerini topla
                ilan_linkleri = linkleri_topla(sayfa, kategori_linki)
                print(f"Toplam {len(ilan_linkleri)} adet ilan linki bulundu.")

                # 2. Aşama: Linklerin içine girip veri çek
                tum_araba_verileri = []
                for index, link in enumerate(ilan_linkleri):
                    print(f"[{index + 1}/{len(ilan_linkleri)}] İşleniyor: {link}")
                    
                    araba_verisi = araba_verisi_cek(sayfa, link)
                    if araba_verisi:
                        tum_araba_verileri.append(araba_verisi)
                    
                    time.sleep(2) 

                # 3. Aşama: Verileri CSV'ye çevir ve kaydet
                if tum_araba_verileri:
                    df = pd.DataFrame(tum_araba_verileri)
                    dosya_ismi = f"{kategori_adi}_veriseti.csv"
                    df.to_csv(dosya_ismi, index=False, encoding="utf-8-sig")
                    print(f"BAŞARILI: Veriler '{dosya_ismi}' olarak kaydedildi!")
                else:
                    print(f"UYARI: '{kategori_adi}' için çekilebilen bir veri bulunamadı.")

            except Exception as e:
                print(f"HATA: '{kategori_adi}' çekilirken sorun oluştu. Hata detayı: {e}")
                continue 
        
        tarayici.close()
        print("\nBÜTÜN KATEGORİLER BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    main()