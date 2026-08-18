import pandas as pd
from playwright.sync_api import sync_playwright
import os
import csv  # Anlık kayıt için

# Kendi yazdığımız modülleri çağırıyoruz
from link_toplayici import ilan_linklerini_topla 
from veri_ayiklayici import araba_verisi_cek 

def linkleri_dosyadan_oku(dosya_adi="linkler.txt"):
    """linkler.txt dosyasını okuyup bir sözlük döndürür."""
    kategoriler = {}
    if not os.path.exists(dosya_adi):
        print(f"HATA: '{dosya_adi}' bulunamadı! Lütfen dosyayı oluşturun.")
        return kategoriler

    with open(dosya_adi, "r", encoding="utf-8") as dosya:
        for satir in dosya:
            satir = satir.strip()
            if satir and "," in satir: 
                kategori_adi, link = satir.split(",", 1)
                kategoriler[kategori_adi.strip()] = link.strip()
    return kategoriler

def linki_dosyadan_sil(hedef_kategori, dosya_adi="linkler.txt"):
    """İşlemine başlanan linki txt dosyasından siler (Vur-Kaç mantığı)."""
    if not os.path.exists(dosya_adi): return
    
    with open(dosya_adi, "r", encoding="utf-8") as dosya:
        satirlar = dosya.readlines()
        
    with open(dosya_adi, "w", encoding="utf-8") as dosya:
        for satir in satirlar:
            # Hedef kategori adını içermeyen satırları geri yaz (Hedefi sil)
            if not satir.startswith(f"{hedef_kategori},"):
                dosya.write(satir)

def main():
    kategoriler = linkleri_dosyadan_oku("linkler.txt")
    
    if not kategoriler:
        print("İşlenecek link bulunamadı veya linkler.txt boş. Program sonlandırılıyor.")
        return

    print(f"Toplam {len(kategoriler)} adet kategori işlenmek üzere yüklendi.\n")

    with sync_playwright() as p:
        tarayici = p.chromium.launch(headless=False) 
        
        # Metin dosyasından okunan her bir kategori için döngü başlıyor
        for kategori_adi, kategori_linki in kategoriler.items():
            print(f"\n>>> '{kategori_adi}' işlemleri başlıyor...")
            dosya_ismi = f"{kategori_adi}_veriseti.csv"
            
            # 1. KURAL: Kategoriye başladığımız an txt'den siliyoruz
            linki_dosyadan_sil(kategori_adi)
            print("🗑️ Kategori 'linkler.txt' dosyasından silindi (Kuyruk güncellendi).")

            # YENİ KURAL: Her kategori için YEPYENİ bir tarayıcı geçmişi açıyoruz (Çerezleri sıfırlamak için)
            context = tarayici.new_context()
            sayfa = context.new_page()
            
            # HIZLANDIRMA: Resim, CSS vb. kapat, maksimum hız
            sayfa.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
            
            try:
                ilan_linkleri = ilan_linklerini_topla(sayfa, kategori_linki)
                print(f"Toplam {len(ilan_linkleri)} adet ilan linki bulundu. TURBO kazıma başlıyor...")

                dosya_olusturuldu_mu = False

                for index, link in enumerate(ilan_linkleri):
                    print(f"[{index + 1}/{len(ilan_linkleri)}] İşleniyor: {link}")
                    
                    try:
                        araba_verisi = araba_verisi_cek(sayfa, link)
                        sayfa_icerik = sayfa.content().lower()
                        sayfa_basligi = sayfa.title().lower()

                        # VUR-KAÇ TAKTİĞİ: Yakalanırsak bekleme, direkt döngüyü kır!
                        if "bir dakika" in sayfa_basligi or "doğrulama" in sayfa_basligi or "just a moment" in sayfa_basligi or "cloudflare" in sayfa_basligi or "güvenlik doğrulaması" in sayfa_icerik:
                            print("\n🚨 YAKALANDIK! (Cloudflare duvarı).")
                            print(f"🏃 Vur-Kaç taktiği devrede: {index} adet ilan kurtarıldı. Bu kategori kapatılıp sıradakine geçiliyor...\n")
                            break # İlan döngüsünü kırar, sonraki kategoriye geçer

                        # İlan boşsa atlama (Pas geçme)
                        if not araba_verisi or not any(araba_verisi.values()):
                            print("⏭️ İlan okunamadı (yayından kalkmış olabilir), atlanıyor...")
                            continue # Bunu direkt atlattık (Vur-Kaç için hızlı geçiş)

                        # CSV'ye Hızlı Yazma
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

                    except Exception as e:
                        print(f"HATA: İlan sayfasında atlanabilir sorun: {e}")
                        continue 

                print(f"✅ '{kategori_adi}' işlemleri tamamlandı veya sonlandırıldı. Veriler: {dosya_ismi}")

            except Exception as e:
                print(f"HATA: Kategori işlenirken sorun oluştu: {e}")
            finally:
                # KRİTİK KURAL: Kategori bittiğinde (veya yakalandığında) sekmeyi kapat ve çerezleri KESİNLİKLE yok et
                context.close()
        
        tarayici.close()
        print("\n🎉 BÜTÜN KULLANILABİLİR LİNKLER TÜKENDİ! İŞLEM BİTTİ.")

if __name__ == "__main__":
    main()