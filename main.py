import time
import pandas as pd

# Kendi yazdığımız modülleri içeri aktarıyoruz
from link_toplayici import ilan_linklerini_topla
from veri_ayiklayici import araba_verisi_cek

if __name__ == "__main__":
    ana_url = "https://www.arabam.com/ikinci-el/otomobil/bmw-1-serisi"
    
    # Gerçek veri çekimi için sayfa sayısını artırıyoruz
    kac_sayfa_taranacak = 50 
    tum_ilan_linkleri = []

    print("\n--- 1. AŞAMA: LİNKLER TOPLANIYOR ---")
    for sayfa in range(1, kac_sayfa_taranacak + 1):
        print(f"\n>>> Sayfa {sayfa} taranıyor...")
        sayfa_url = f"{ana_url}?page={sayfa}" if sayfa > 1 else ana_url
        
        yeni_linkler = ilan_linklerini_topla(sayfa_url)
        
        # Eğer sayfada hiç link bulunamazsa (son sayfaya gelinmişse) döngüyü kır
        if not yeni_linkler:
            print("Sayfada ilan bulunamadı, link toplama işlemi tamamlandı.")
            break
            
        tum_ilan_linkleri.extend(yeni_linkler)
        time.sleep(5) 

    tum_ilan_linkleri = list(set(tum_ilan_linkleri))
    print(f"\nTOPLAM {len(tum_ilan_linkleri)} BENZERSİZ İLAN LİNKİ BULUNDU!")

    print("\n--- 2. AŞAMA: İLAN DETAYLARI ÇEKİLİYOR VE KAYDEDİLİYOR ---")
    tum_araba_verileri = []

    # Bütün linkleri gez (Artık [:3] limiti yok)
    for index, link in enumerate(tum_ilan_linkleri, 1):
        print(f"\n[{index}/{len(tum_ilan_linkleri)}] Veri çekiliyor: {link}")
        try:
            veri = araba_verisi_cek(link)
            tum_araba_verileri.append(veri)
            time.sleep(3) 
        except Exception as e:
            print(f"Hata oluştu, bu ilan atlanıyor: {e}")

    # 3. AŞAMA: CSV'ye Kaydet
    if tum_araba_verileri:
        df = pd.DataFrame(tum_araba_verileri)
        dosya_adi = "arabam_bmw1_tam_veriseti.csv"
        df.to_csv(dosya_adi, index=False, encoding="utf-8-sig")
        print(f"\nMÜKEMMEL! Tüm veriler başarıyla '{dosya_adi}' dosyasına kaydedildi!")
    else:
        print("\nHiç veri çekilemedi.")