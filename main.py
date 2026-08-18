import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os
import csv  # Anlık kayıt için

# Kendi yazdığımız modülleri çağırıyoruz
from link_toplayici import ilan_linklerini_topla 
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

    # YENİ EKLENDİ: GİZLİ KRONOMETRE BAŞLIYOR
    baslangic_zamani = time.time()

    with sync_playwright() as p:
        # HIZLANDIRMA VE MANUEL MÜDAHALE: headless=False (Tarayıcıyı görebilmen için açık tutuyoruz)
        tarayici = p.chromium.launch(headless=False) 
        
        # Context oluşturuyoruz ki içine özel kurallar yazabilelim
        context = tarayici.new_context()
        sayfa = context.new_page()
        
        # HIZLANDIRMA: Resim, CSS, Video, Font ve Script indirmesini tamamen engelliyoruz!
        sayfa.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
        
        print("🚀 Turbo mod aktif! Resimler/Reklamlar engelleniyor...\n")

        # Metin dosyasından okunan her bir kategori için döngü başlıyor
        for kategori_adi, kategori_linki in kategoriler.items():
            print(f"\n>>> '{kategori_adi}' kategorisi için işlemler başlıyor...")
            dosya_ismi = f"{kategori_adi}_veriseti.csv"
            
            try:
                # 1. Aşama: İlan linklerini topla 
                ilan_linkleri = ilan_linklerini_topla(sayfa, kategori_linki)
                print(f"Toplam {len(ilan_linkleri)} adet ilan linki bulundu.")

                # Dosyanın ilk satırını (başlıkları) yazıp yazmadığımızı takip etmek için
                dosya_olusturuldu_mu = False

                # 2. Aşama: Linklerin içine girip veri çek (ANLIK KAYIT MODU)
                for index, link in enumerate(ilan_linkleri):
                    
                    # YENİ EKLENDİ: TAKTİKSEL MOLA KONTROLÜ (GÜVENLİK SİSTEMİ BOZULMADAN)
                    gecen_sure = time.time() - baslangic_zamani
                    if gecen_sure >= 600:  # 600 saniye = Tam 10 dakika (Yakalama süresinden 55 saniye önce)
                        print("\n☕ TAKTİKSEL MOLA: Cloudflare güvenlik duvarını sıfırlamak için 60 saniye dinleniliyor...")
                        time.sleep(60) # 60 saniye sistemi uyut
                        baslangic_zamani = time.time() # Kronometreyi sıfırla ve yeniden saymaya başla
                        print("🚀 Mola bitti! Aynı hızda veri çekmeye tam gaz devam ediyoruz...\n")

                    # Hata anında aynı ilanı tekrar deneyebilmesi için sonsuz döngü (DOKUNULMADI)
                    while True:
                        print(f"[{index + 1}/{len(ilan_linkleri)}] İşleniyor: {link}")
                        
                        try:
                            araba_verisi = araba_verisi_cek(sayfa, link)
                            sayfa_icerik = sayfa.content().lower()
                            sayfa_basligi = sayfa.title().lower()

                            # 1. GERÇEK CAPTCHA KONTROLÜ (DOKUNULMADI - AYNEN KORUNDU)
                            if "bir dakika" in sayfa_basligi or "doğrulama" in sayfa_basligi or "just a moment" in sayfa_basligi or "cloudflare" in sayfa_basligi or "güvenlik doğrulaması" in sayfa_icerik:
                                print("\n🚨 DİKKAT: Güvenlik Duvarı (Captcha/Cloudflare) algılandı!")
                                input("👉 Lütfen tarayıcıdan engeli çözün. Çözdükten sonra devam etmek için ENTER'a basın...")
                                print("🔄 Aynı ilan tekrar deneniyor...\n")
                                continue

                            # 2. VERİ ÇEKİLEMEDİ KONTROLÜ (DOKUNULMADI - AYNEN KORUNDU)
                            if not araba_verisi or not any(araba_verisi.values()):
                                print("\n⚠️ UYARI: Sayfa açıldı ancak ilan verileri okunamadı! (İlan yayından kalkmış veya HTML değişmiş olabilir)")
                                secim = input("👉 Tekrar denemek için ENTER'a basın (Veya ilanı atlamak için 'P' yazıp ENTER'a basın): ").strip().lower()
                                if secim == 'p':
                                    print("⏭️ Bu ilan atlanıyor, veritabanına yazılmadı...")
                                    break 
                                else:
                                    print("🔄 Aynı ilan tekrar deneniyor...\n")
                                    continue

                            # ANINDA CSV'YE YAZMA (DOKUNULMADI - AYNEN KORUNDU)
                            if araba_verisi:
                                if not dosya_olusturuldu_mu:
                                    with open(dosya_ismi, "w", encoding="utf-8-sig", newline="") as f:
                                        writer = csv.DictWriter(f, fieldnames=araba_verisi.keys())
                                        writer.writeheader()
                                        writer.writerow(araba_verisi)
                                    dosya_olusturuldu_mu = True
                                else:
                                    with open(dosya_ismi, "a", encoding="utf-8-sig", newline="") as f:
                                        writer = csv.DictWriter(f, fieldnames=araba_verisi.keys())
                                        writer.writerow(araba_verisi)
                                
                                break # Veri başarıyla kaydedildi, döngüden çıkıp bir sonraki linke geç

                        except Exception as e:
                            print(f"\n🚨 İLAN SAYFASINDA BEKLENMEYEN HATA: {e}")
                            input("👉 Lütfen tarayıcıyı kontrol edin. Devam etmek için ENTER'a basın...")
                            continue 

                print(f"✅ BİTTİ: '{kategori_adi}' işlemleri tamamlandı. Dosya hazır: {dosya_ismi}")

            except Exception as e:
                print(f"HATA: '{kategori_adi}' çekilirken genel sorun oluştu. Hata detayı: {e}")
                print(f"MERAK ETME: Çekilen son veriye kadar her şey '{dosya_ismi}' dosyasına anlık kaydedildi!")
                continue 
        
        tarayici.close()
        print("\n🎉 BÜTÜN KATEGORİLER BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    main()