import pandas as pd
import numpy as np
import joblib
import os
import re
import warnings
warnings.filterwarnings('ignore')

def dosya_adi_yap(metin):
    return re.sub(r'[^a-zA-Z0-9]', '_', str(metin).strip().upper())

def piyasa_dalgalanmasini_bul(marka, seri, yil):
    # Ana veri setine gidip tam olarak o aracın "benzerlerini" buluyoruz
    try:
        df = pd.read_csv("cleaned_dataset.csv", low_memory=False)
        # Sadece o markanın, o serisinin, o yılına ait (veya +- 1 yıl) araçları filtrele
        benzer_araclar = df[(df['Marka'] == marka) & 
                            (df['Seri'] == seri) & 
                            (df['Yıl'].between(yil - 1, yil + 1))]
        
        if len(benzer_araclar) > 5:
            # Standart Sapmayı hesapla (Piyasa ne kadar oynak?)
            sapma = benzer_araclar['Fiyat'].std()
            ortalama = benzer_araclar['Fiyat'].mean()
            yuzdesel_oynama = sapma / ortalama
            
            # Dalgalanmayı minimum %3, maksimum %8 ile sınırla ki uçuk sonuçlar çıkmasın
            return max(0.03, min(yuzdesel_oynama, 0.08))
    except:
        pass
    
    return 0.05 # Eğer araçtan piyasada hiç yoksa standart %5 sapma kullan

def arac_fiyatini_tahmin_et(arac_bilgileri):
    print("\n🔍 Yapay Zeka Aracı İnceliyor...")
    
    marka = arac_bilgileri.get('Marka', '')
    seri = arac_bilgileri.get('Seri', '')
    yil = arac_bilgileri.get('Yıl', 2020)
    kasa = arac_bilgileri.get('Kasa Tipi', '')
    
    dosya_marka = dosya_adi_yap(marka)
    dosya_kasa = dosya_adi_yap(kasa)
    
    yollar = [
        (f"modeller/{dosya_marka}_{dosya_kasa}", f"🎯 MİKRO UZMAN (Sadece {marka} {kasa} bilen YZ)"),
        (f"modeller/{dosya_marka}_GENEL", f"🪂 YEDEK PARAŞÜT 1 (Tüm {marka} modellerini bilen YZ)"),
        (f"modeller/TUM_PIYASA", "🌍 YEDEK PARAŞÜT 2 (Türkiye Piyasa Uzmanı)")
    ]
    
    secilen_yol = None
    for yol, ad in yollar:
        if os.path.exists(yol + "_model.pkl") and os.path.exists(yol + "_dict.pkl"):
            secilen_yol = yol
            print(f"{ad} devreye girdi.")
            break
            
    if not secilen_yol:
        print("❌ Sistemde bu aracı tahmin edecek model bulunamadı!")
        return
        
    model = joblib.load(secilen_yol + "_model.pkl")
    encoding_dict = joblib.load(secilen_yol + "_dict.pkl")
    
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
    
    # XGBoost tahmini
    gercek_tahmin = np.expm1(model.predict(df)[0])
    
    # SENİN MANTIĞIN: Piyasadaki benzer araçların dalgalanmasına göre makas belirleme
    piyasa_sapmasi = piyasa_dalgalanmasini_bul(marka, seri, yil)
    alt_fiyat = gercek_tahmin * (1 - piyasa_sapmasi)
    ust_fiyat = gercek_tahmin * (1 + piyasa_sapmasi)
    
    print("\n" + "="*55)
    print("✨ YAPAY ZEKA DEĞERLEME RAPORU ✨")
    print("="*55)
    print(f"Piyasa Ortalaması (Nokta Atışı) : {gercek_tahmin:,.0f} TL")
    print("-" * 55)
    print(f"Piyasadan Alınan Makas Oranı    : ± % {piyasa_sapmasi*100:.1f}")
    print(f"🟢 HIZLI SATIŞ FİYATI (Alt Sınır): {round(alt_fiyat, -3):,.0f} TL")
    print(f"🔴 TOK SATICI FİYATI (Üst Sınır) : {round(ust_fiyat, -3):,.0f} TL")
    print("="*55)


if __name__ == "__main__":
    test_araci = {
        'Marka': 'Opel',
        'Kasa Tipi': 'Hatchback',
        'Seri': 'Astra',
        'Model': '1.6 Essentia',
        'Yıl': 2012,
        'Kilometre': 140000,
        'Vites Tipi': 'Manuel',
        'Yakıt Tipi': 'Benzin',
        'Renk': 'Siyah',
        'Boya-değişen': 'Hatasız',
        'Çekiş': 'Önden Çekiş'
    }
    
    arac_fiyatini_tahmin_et(test_araci)