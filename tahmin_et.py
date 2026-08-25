import pandas as pd
import numpy as np
import joblib
import os
import re
import difflib
import warnings
warnings.filterwarnings('ignore')

def dosya_adi_yap(metin):
    return re.sub(r'[^a-zA-Z0-9]', '_', str(metin).strip().upper())

# YENİ: SİSTEMDEKİ MEVCUT MARKALARI VE KASALARI BULAN AKILLI FONKSİYON
def sistemdeki_modelleri_ogren():
    mevcut_markalar = set()
    mevcut_kasalar = set()
    
    if os.path.exists('modeller'):
        for dosya in os.listdir('modeller'):
            if dosya.endswith('_model.pkl'):
                isim_kismi = dosya.replace('_model.pkl', '')
                parcalar = isim_kismi.split('_')
                if "GENEL" in parcalar:
                    mevcut_markalar.add(parcalar[0])
                elif "TUM" not in parcalar:
                    mevcut_markalar.add(parcalar[0])
                    if len(parcalar) > 1:
                        mevcut_kasalar.add(parcalar[1])
                        
    return list(mevcut_markalar), list(mevcut_kasalar)

# YENİ: YAZIM HATALARINI (TYPO) OTOMATİK DÜZELTEN NLP FONKSİYONU
def akilli_metin_duzelt(kullanici_girdisi, dogru_liste):
    girdi_formatli = dosya_adi_yap(kullanici_girdisi)
    
    # Eğer doğrudan eşleşme varsa uzatma
    if girdi_formatli in dogru_liste:
        return girdi_formatli
        
    # Doğrudan eşleşme yoksa, benzerliğe bak ("ople" -> "OPEL" gibi)
    benzerler = difflib.get_close_matches(girdi_formatli, dogru_liste, n=1, cutoff=0.5)
    
    if benzerler:
        print(f"🪄 Yazım düzeltildi: '{kullanici_girdisi}' -> '{benzerler[0]}'")
        return benzerler[0]
        
    return girdi_formatli # Hiçbir şeye benzetemezse olduğu gibi bırak

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
    
    # 1. AKILLI DÜZELTME AŞAMASI
    ham_marka = arac_bilgileri.get('Marka', '')
    ham_kasa = arac_bilgileri.get('Kasa Tipi', '')
    
    bilinen_markalar, bilinen_kasalar = sistemdeki_modelleri_ogren()
    
    dosya_marka = akilli_metin_duzelt(ham_marka, bilinen_markalar)
    dosya_kasa = akilli_metin_duzelt(ham_kasa, bilinen_kasalar)
    
    # Tahmin için kullanılacak gerçek değişkenler
    arac_bilgileri['Marka'] = ham_marka.capitalize() # Görsellik için
    arac_bilgileri['Kasa Tipi'] = ham_kasa.capitalize()
    
    # 2. MODEL SEÇİMİ AŞAMASI
    yollar = [
        (f"modeller/{dosya_marka}_{dosya_kasa}", f"🎯 MİKRO UZMAN ({dosya_marka} {dosya_kasa})"),
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
    seri = arac_bilgileri.get('Seri', '')
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
    
    # FİYAT VE ÇARPAN HESAPLAMALARI (Önceki mantığın aynısı)
    ham_fiyat = np.expm1(model.predict(df)[0])
    fiyat_carpani = 1.0
    
    tramer = detayli_ekspertiz.get('Tramer_Tutari_TL', 0)
    if tramer > 0: fiyat_carpani -= min(tramer / ham_fiyat, 0.15)

    kritik = detayli_ekspertiz.get('Kritik_Noktalar_Islemli_Mi', {})
    if kritik.get('Sase', False): fiyat_carpani -= 0.12
    if kritik.get('Podye', False): fiyat_carpani -= 0.08
    if kritik.get('Direkler', False): fiyat_carpani -= 0.10
    if kritik.get('Bagaj_Havuzu', False): fiyat_carpani -= 0.06
    if kritik.get('Airbag', False): fiyat_carpani -= 0.15

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
        fiyat_carpani -= parca_agirliklari[kat].get(durum, 0)

    fiyat_carpani = max(0.55, fiyat_carpani)
    guncel_ana_fiyat = ham_fiyat * fiyat_carpani

    puanlar = detayli_ekspertiz.get('Kondisyon_Puanlari_1_10', {})
    puan_katsayilari = {'Motor': 4.0, 'Sanziman': 4.0, 'AltTakim': 3.0, 'Klima': 2.0, 'IcKozmetik': 2.0, 'Lastik': 1.0}
    toplam_puan = sum(puanlar.get(k, 5) * v for k, v in puan_katsayilari.items())
    maksimum_puan = sum(10 * v for v in puan_katsayilari.values())
    basari_yuzdesi = toplam_puan / maksimum_puan

    piyasa_sapmasi = piyasa_dalgalanmasini_bul(marka, seri, yil)
    ana_dip = guncel_ana_fiyat * (1 - piyasa_sapmasi)
    ana_tavan = guncel_ana_fiyat * (1 + piyasa_sapmasi)
    ana_makas = ana_tavan - ana_dip

    odak = ana_dip + (ana_makas * basari_yuzdesi)
    dar_makas_payi = ana_makas * 0.15
    dar_dip = max(ana_dip, odak - dar_makas_payi)
    dar_tavan = min(ana_tavan, odak + dar_makas_payi)

    # YENİ: HANGİ BEYNİN KULLANILDIĞINI GÖSTEREN ŞEFFAF RAPOR EKRANI
    print("\n" + "="*65)
    print("✨ YAPAY ZEKA OTO EKSPERTİZ VE DEĞERLEME RAPORU ✨")
    print("="*65)
    print(f"🧠 KULLANILAN YAPAY ZEKA BEYNİ : {kullanilan_model_adi}")
    print("-" * 65)
    print(f"Araç Ham Piyasa Değeri        : {round(ham_fiyat, -3):,.0f} TL")
    print(f"Mekanik & İç Kozmetik Puanı   : %{basari_yuzdesi*100:.1f}")
    print(f"Geniş Piyasa Ağı (Sınır)      : {round(ana_dip, -3):,.0f} TL - {round(ana_tavan, -3):,.0f} TL")
    print("-" * 65)
    print("🎯 EKSPERTİZ SONRASI NOKTA ATIŞI FİYAT BANDI:")
    print(f"🟢 DİP FİYAT (Acil / Bayi)    : {round(dar_dip, -3):,.0f} TL")
    print(f"🔴 TAVAN FİYAT (Kullanıcı)    : {round(dar_tavan, -3):,.0f} TL")
    print("="*65)

# (Kullanıcıdan veri alan sayi_al ve __main__ blokları öncekiyle tamamen aynı kalacak)