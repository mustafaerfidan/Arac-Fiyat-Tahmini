import pandas as pd
import numpy as np
import joblib
import os
import re
import difflib
import warnings
warnings.filterwarnings('ignore')

def dosya_adi_yap(metin):
    metin = str(metin).replace('İ', 'I').replace('ı', 'i').replace('Ş', 'S').replace('ş', 's')
    metin = metin.replace('Ğ', 'G').replace('ğ', 'g').replace('Ü', 'U').replace('ü', 'u')
    metin = metin.replace('Ö', 'O').replace('ö', 'o').replace('Ç', 'C').replace('ç', 'c')
    return re.sub(r'[^a-zA-Z0-9]', '_', metin.strip().upper())

def sistemdeki_markalari_ogren():
    mevcut_markalar = set()
    if os.path.exists('modeller'):
        for dosya in os.listdir('modeller'):
            if dosya.endswith('_model.pkl') and dosya != 'TUM_PIYASA_model.pkl':
                mevcut_markalar.add(dosya.split('_')[0])
    return list(mevcut_markalar)

def akilli_metin_duzelt(kullanici_girdisi, dogru_liste):
    girdi_formatli = dosya_adi_yap(kullanici_girdisi)
    if girdi_formatli in dogru_liste:
        return girdi_formatli
    benzerler = difflib.get_close_matches(girdi_formatli, dogru_liste, n=1, cutoff=0.5)
    if benzerler:
        print(f"🪄 Marka yazımı düzeltildi: '{kullanici_girdisi}' -> '{benzerler[0]}'")
        return benzerler[0]
    return girdi_formatli

def piyasa_dalgalanmasini_bul(marka, seri, yil):
    try:
        df = pd.read_csv("cleaned_dataset.csv", low_memory=False)
        benzer_araclar = df[(df['Marka'].str.upper() == marka.upper()) & 
                            (df['Seri'].str.upper() == seri.upper()) & 
                            (df['Yıl'].between(yil - 1, yil + 1))]
        if len(benzer_araclar) > 5:
            sapma = benzer_araclar['Fiyat'].std()
            ortalama = benzer_araclar['Fiyat'].mean()
            return max(0.10, min(sapma / ortalama, 0.18))
    except:
        pass
    return 0.12 

def arac_fiyatini_tahmin_et(arac_bilgileri, detayli_ekspertiz):
    print("\n⏳ Yapay Zeka Ekspertiz Raporunu İşliyor, Lütfen Bekleyin...")
    
    ham_marka = arac_bilgileri.get('Marka', '')
    ham_seri = arac_bilgileri.get('Seri', '')
    ham_kasa = arac_bilgileri.get('Kasa Tipi', '')
    
    bilinen_markalar = sistemdeki_markalari_ogren()
    dosya_marka = akilli_metin_duzelt(ham_marka, bilinen_markalar)
    dosya_seri = dosya_adi_yap(ham_seri)
    dosya_kasa = dosya_adi_yap(ham_kasa)
    
    arac_bilgileri['Marka'] = ham_marka.capitalize()
    arac_bilgileri['Seri'] = ham_seri.capitalize()
    arac_bilgileri['Kasa Tipi'] = ham_kasa.capitalize()
    
    yollar = [
        (f"modeller/{dosya_marka}_{dosya_seri}", f"🎯 SPESİFİK SERİ UZMANI ({dosya_marka} {dosya_seri})"),
        (f"modeller/{dosya_marka}_{dosya_kasa}", f"🛡️ KASA TİPİ YEDEK UZMANI ({dosya_marka} {dosya_kasa})"),
        (f"modeller/{dosya_marka}_GENEL", f"🪂 MARKA GENEL UZMANI ({dosya_marka})"),
        (f"modeller/TUM_PIYASA", "🌍 TÜRKİYE PİYASA UZMANI (Genel Kurtarıcı)")
    ]
    
    secilen_yol = None
    kullanilan_model_adi = ""
    for yol, ad in yollar:
        if os.path.exists(yol + "_model.pkl") and os.path.exists(yol + "_dict.pkl"):
            secilen_yol = yol
            kullanilan_model_adi = ad
            break
            
    if not secilen_yol:
        print("❌ Sistemde bu aracı tahmin edecek hiçbir model bulunamadı!")
        return
        
    model = joblib.load(secilen_yol + "_model.pkl")
    encoding_dict = joblib.load(secilen_yol + "_dict.pkl")
    
    yil = arac_bilgileri.get('Yıl', 2020)
    model_donanim = arac_bilgileri.get('Model', '')
    arac_bilgileri['Arac_Yasi'] = 2026 - yil
    if arac_bilgileri['Arac_Yasi'] <= 0: arac_bilgileri['Arac_Yasi'] = 1
    
    df = pd.DataFrame([arac_bilgileri])
    
    for col in list(df.columns):
        if col in encoding_dict:
            sozluk = encoding_dict[col]
            deger = str(df.iloc[0][col])
            df[col + '_Target'] = sozluk.get(deger, np.mean(list(sozluk.values())))
            df = df.drop(columns=[col])
            
    beklenen_sutunlar = model.feature_names_in_
    for col in beklenen_sutunlar:
        if col not in df.columns:
            df[col] = 0
    df = df[beklenen_sutunlar]
    
    ham_fiyat = np.expm1(model.predict(df)[0])
    fiyat_carpani = 1.0
    kirmizi_cizgiler = []
    artilar = [] # YENİ: Araca değer katan özellikler listesi
    
    # 1. YENİ EKLENEN: Ağır Hasar Kontrolü (Fiyatı fena çakar)
    if detayli_ekspertiz.get('Agir_Hasar_Kaydi', False):
        fiyat_carpani -= 0.18
        kirmizi_cizgiler.append("AĞIR HASAR / PERT KAYDI (-%18.0)")

    # 2. YENİ EKLENEN: Periyodik Bakım Kontrolü (Fiyata prim yaptırır)
    if detayli_ekspertiz.get('Periyodik_Bakim_Duzenli', False):
        fiyat_carpani += 0.04
        artilar.append("Düzenli Periyodik Bakım Geçmişi (+%4.0)")

    # Tramer Oransal Hesabı
    tramer = detayli_ekspertiz.get('Tramer_Tutari_TL', 0)
    if tramer > 0: 
        tramer_etkisi = min(tramer / ham_fiyat, 0.15)
        fiyat_carpani -= tramer_etkisi
        kirmizi_cizgiler.append(f"Tramer Kaydı ({tramer:,.0f} TL) -> -%{tramer_etkisi*100:.1f} Değer Kaybı")

    kritik = detayli_ekspertiz.get('Kritik_Noktalar_Islemli_Mi', {})
    if kritik.get('Sase', False): fiyat_carpani -= 0.12; kirmizi_cizgiler.append("Şase İşlemli (-%12)")
    if kritik.get('Podye', False): fiyat_carpani -= 0.08; kirmizi_cizgiler.append("Podye İşlemli (-%8)")
    if kritik.get('Direkler', False): fiyat_carpani -= 0.10; kirmizi_cizgiler.append("Direkler İşlemli (-%10)")
    if kritik.get('Bagaj_Havuzu', False): fiyat_carpani -= 0.06; kirmizi_cizgiler.append("Bagaj Havuzu İşlemli (-%6)")
    if kritik.get('Airbag', False): fiyat_carpani -= 0.15; kirmizi_cizgiler.append("Airbag İşlemli (-%15)")

    kaporta = detayli_ekspertiz.get('Kaporta_Durumu', {})
    parca_agirliklari = {
        'Tavan': {'Boyali': 0.06, 'Lokal_Boyali': 0.02, 'Degisen': 0.12},
        'Kaput': {'Boyali': 0.03, 'Lokal_Boyali': 0.01, 'Degisen': 0.06},
        'Bagaj': {'Boyali': 0.02, 'Lokal_Boyali': 0.01, 'Degisen': 0.04},
        'Kapi':  {'Boyali': 0.015, 'Lokal_Boyali': 0.005, 'Degisen': 0.03},
        'Camurluk': {'Boyali': 0.01, 'Lokal_Boyali': 0.005, 'Degisen': 0.02}
    }
    for parca, durum in kaporta.items():
        if durum in ['Orijinal', 'Plastik_Parca']: continue
        kat = 'Kapi' if 'Kapi' in parca else 'Camurluk' if 'Camurluk' in parca else \
              'Tavan' if 'Tavan' in parca else 'Kaput' if 'Kaput' in parca else 'Bagaj'
        oran = parca_agirliklari[kat].get(durum, 0)
        fiyat_carpani -= oran
        if oran > 0: kirmizi_cizgiler.append(f"{parca.replace('_', ' ')}: {durum.replace('_', ' ')} (-%{oran*100:.1f})")

    fiyat_carpani = max(0.55, fiyat_carpani) # Araba pert bile olsa fiyatı sıfırlamayalım
    guncel_ana_fiyat = ham_fiyat * fiyat_carpani

    puanlar = detayli_ekspertiz.get('Kondisyon_Puanlari_1_10', {})
    puan_katsayilari = {'Motor': 4.0, 'Sanziman': 4.0, 'AltTakim': 3.0, 'Klima': 2.0, 'IcKozmetik': 2.0, 'Lastik': 1.0}
    toplam_puan = sum(puanlar.get(k, 5) * v for k, v in puan_katsayilari.items())
    maksimum_puan = sum(10 * v for v in puan_katsayilari.values())
    basari_yuzdesi = toplam_puan / maksimum_puan

    piyasa_sapmasi = piyasa_dalgalanmasini_bul(arac_bilgileri['Marka'], ham_seri, yil)
    ana_dip = guncel_ana_fiyat * (1 - piyasa_sapmasi)
    ana_tavan = guncel_ana_fiyat * (1 + piyasa_sapmasi)
    ana_makas = ana_tavan - ana_dip

    odak = ana_dip + (ana_makas * basari_yuzdesi)
    dar_makas_payi = ana_makas * 0.15
    dar_dip = max(ana_dip, odak - dar_makas_payi)
    dar_tavan = min(ana_tavan, odak + dar_makas_payi)

    print("\n" + "="*65)
    print("✨ YAPAY ZEKA OTO EKSPERTİZ VE DEĞERLEME RAPORU ✨")
    print("="*65)
    print(f"🚗 HESAPLANAN ARAÇ            : {arac_bilgileri['Marka']} {ham_seri.capitalize()} {model_donanim}")
    print(f"🧠 KULLANILAN YAPAY ZEKA BEYNİ : {kullanilan_model_adi}")
    print("-" * 65)
    print(f"Araç Ham Piyasa Değeri        : {round(ham_fiyat, -3):,.0f} TL")
    
    if artilar:
        print("\n🌟 ARACA DEĞER KATAN ÖZELLİKLER:")
        for arti in artilar: print(f"  + {arti}")

    if kirmizi_cizgiler:
        print("\n🚨 DEĞER KAYBI YARATAN KUSURLAR:")
        for kusur in kirmizi_cizgiler: print(f"  - {kusur}")
        
    print("-" * 65)
    print(f"Net Ekspertiz Fiyat Çarpanı   : %{(fiyat_carpani)*100:.1f}")
    print(f"Mekanik & İç Kozmetik Puanı   : %{basari_yuzdesi*100:.1f}")
    print(f"Geniş Piyasa Ağı (Sınır)      : {round(ana_dip, -3):,.0f} TL - {round(ana_tavan, -3):,.0f} TL")
    print("-" * 65)
    print("🎯 EKSPERTİZ SONRASI NOKTA ATIŞI FİYAT BANDI:")
    print(f"🟢 DİP FİYAT (Acil / Bayi)    : {round(dar_dip, -3):,.0f} TL")
    print(f"🔴 TAVAN FİYAT (Kullanıcı)    : {round(dar_tavan, -3):,.0f} TL")
    print("="*65)

def sayi_al(mesaj, varsayilan=5):
    try:
        deger = input(mesaj)
        return int(deger) if deger.strip() != "" else varsayilan
    except:
        return varsayilan

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("HOŞGELDİNİZ - ARAÇ DEĞERLEME VE EKSPERTİZ GİRİŞ SİSTEMİ")
    print("#"*60)
    
    print("\n--- 1. ARAÇ TEMEL BİLGİLERİ ---")
    arac = {
        'Marka': input("Marka (Örn: Opel): ").strip().capitalize(),
        'Seri': input("Seri (Örn: Astra, Egea, A3): ").strip(),
        'Model': input("Model/Donanım (Örn: 1.3 Multijet Easy): ").strip(),
        'Yıl': sayi_al("Yıl (Örn: 2017): ", 2017),
        'Kasa Tipi': input("Kasa Tipi (Hatchback/Sedan/SUV vs.): ").strip().capitalize(),
        'Kilometre': sayi_al("Kilometre (Örn: 140000): ", 100000),
        'Vites Tipi': input("Vites (Manuel/Otomatik/Yarı Otomatik): ").strip().capitalize(),
        'Yakıt Tipi': input("Yakıt (Benzin/Dizel/LPG & Benzin): ").strip().capitalize(),
        'Renk': input("Renk (Örn: Siyah): ").strip().capitalize(),
        'Çekiş': input("Çekiş (Örn: Önden Çekiş): ").strip().title(),
        'Boya-değişen': 'Hatasız' 
    }

    print("\n--- 2. GEÇMİŞ VE TRAMER BİLGİLERİ ---")
    # Yeni eklenen sorular!
    agir_hasar_cevap = input("Ağır Hasar (Pert) Kaydı var mı? (E/H): ").strip().upper()
    bakim_cevap = input("Periyodik bakımları zamanında / yetkili serviste yapılmış mı? (E/H): ").strip().upper()
    
    tramer_tutari = sayi_al("Tramer / Hasar Kaydı Tutarı (Yoksa 0): ", 0)
    
    print("\n--- 3. KRİTİK NOKTALAR ---")
    kritik = {}
    print("Aşağıdaki noktalarda İŞLEM/HASAR varsa 'E', yoksa 'H' veya boş bırakıp Enter'a basın.")
    for nokta in ['Sase', 'Podye', 'Direkler', 'Bagaj_Havuzu', 'Airbag']:
        cevap = input(f"{nokta.replace('_', ' ')} İşlemli mi? (E/H): ").strip().upper()
        kritik[nokta] = True if cevap == 'E' else False

    print("\n--- 4. KAPORTA DURUMU ---")
    print("Seçenekler: 1-Orijinal, 2-Boyali, 3-Lokal Boyali, 4-Degisen, 5-Plastik")
    durum_map = {'1': 'Orijinal', '2': 'Boyali', '3': 'Lokal_Boyali', '4': 'Degisen', '5': 'Plastik_Parca'}
    kaporta = {}
    parcalar = ['Tavan', 'Kaput', 'Bagaj', 'Sol_On_Camurluk', 'Sol_Arka_Camurluk', 
                'Sag_On_Camurluk', 'Sag_Arka_Camurluk', 'Sol_On_Kapi', 'Sol_Arka_Kapi', 
                'Sag_On_Kapi', 'Sag_Arka_Kapi']
    
    for p in parcalar:
        sec = input(f"{p.replace('_', ' ')} durumu (1-5, Orijinal için boş bırak): ").strip()
        kaporta[p] = durum_map.get(sec, 'Orijinal')

    print("\n--- 5. KONDİSYON SKORLARI (1-10 ARASI PUAN VERİN) ---")
    kondisyon = {
        'Motor': sayi_al("Motor Performansı (1-10): ", 5),
        'Sanziman': sayi_al("Şanzıman ve Vites Geçişleri (1-10): ", 5),
        'AltTakim': sayi_al("Alt Takım ve Süspansiyon (1-10): ", 5),
        'Klima': sayi_al("Klima ve Elektronik (1-10): ", 5),
        'IcKozmetik': sayi_al("İç Kozmetik / Koltuklar (1-10): ", 5),
        'Lastik': sayi_al("Lastik ve Akü Durumu (1-10): ", 5)
    }

    ekspertiz = {
        'Agir_Hasar_Kaydi': True if agir_hasar_cevap == 'E' else False,
        'Periyodik_Bakim_Duzenli': True if bakim_cevap == 'E' else False,
        'Tramer_Tutari_TL': tramer_tutari,
        'Kritik_Noktalar_Islemli_Mi': kritik,
        'Kaporta_Durumu': kaporta,
        'Kondisyon_Puanlari_1_10': kondisyon
    }

    arac_fiyatini_tahmin_et(arac, ekspertiz)