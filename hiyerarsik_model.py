import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import xgboost as xgb
import warnings
import re
warnings.filterwarnings('ignore')

def dosya_adi_yap(metin):
    # Türkçe karakterleri ve boşlukları sistemin anlayacağı standart formata çevirir (Örn: "1 SERİSİ" -> "1_SERISI")
    metin = str(metin).replace('İ', 'I').replace('ı', 'i').replace('Ş', 'S').replace('ş', 's')
    metin = metin.replace('Ğ', 'G').replace('ğ', 'g').replace('Ü', 'U').replace('ü', 'u')
    metin = metin.replace('Ö', 'O').replace('ö', 'o').replace('Ç', 'C').replace('ç', 'c')
    return re.sub(r'[^a-zA-Z0-9]', '_', metin.strip().upper())

def uzman_egit_ve_kaydet(alt_veri, dosya_prefix, aciklama):
    if len(alt_veri) < 50:
        return None 
        
    alt_veri = alt_veri.copy()
    
    Q1 = alt_veri['Fiyat'].quantile(0.15)
    Q3 = alt_veri['Fiyat'].quantile(0.85)
    IQR = Q3 - Q1
    alt_veri = alt_veri[(alt_veri['Fiyat'] >= (Q1 - 1.5 * IQR)) & (alt_veri['Fiyat'] <= (Q3 + 1.5 * IQR))]
    
    kategorik = ['Marka', 'Kasa Tipi', 'Seri', 'Model', 'Vites Tipi', 'Yakıt Tipi', 'Renk', 'Boya-değişen', 'Çekiş']
    mevcut_kategorik = [col for col in kategorik if col in alt_veri.columns]
    
    encoding_sozlugu = {}
    for col in mevcut_kategorik:
        alt_veri[col] = alt_veri[col].astype(str)
        ortalama_fiyatlar = alt_veri.groupby(col)['Fiyat'].mean().to_dict()
        encoding_sozlugu[col] = ortalama_fiyatlar
        alt_veri[col + '_Target'] = alt_veri[col].map(ortalama_fiyatlar)
        alt_veri = alt_veri.drop(columns=[col])
            
    alt_veri = alt_veri.dropna()
    if len(alt_veri) < 20: 
        return None

    X = alt_veri.drop(columns=['Fiyat'])
    y = np.log1p(alt_veri['Fiyat'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=7, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    tahminler = np.expm1(model.predict(X_test))
    gercek = np.expm1(y_test)
    
    grup_sapmasi = alt_veri['Fiyat'].std() / alt_veri['Fiyat'].mean()
    makas = max(0.10, min(grup_sapmasi, 0.18)) 
    
    alt_sinirlar = tahminler * (1 - makas)
    ust_sinirlar = tahminler * (1 + makas)
    
    isabet_sayisi = ((gercek >= alt_sinirlar) & (gercek <= ust_sinirlar)).sum()
    isabet_orani = (isabet_sayisi / len(gercek)) * 100
    
    hata_ust = np.maximum(0, gercek - ust_sinirlar)
    hata_alt = np.maximum(0, alt_sinirlar - gercek)
    toplam_makas_disi_hata = hata_ust + hata_alt
    ticari_ortalama_hata = np.mean(toplam_makas_disi_hata)

    print(f"   ✅ {aciklama} | Makas İsabeti: %{isabet_orani:.1f} | Sınır Taşan Hata: {ticari_ortalama_hata:,.0f} TL")

    joblib.dump(model, f"modeller/{dosya_prefix}_model.pkl")
    joblib.dump(encoding_sozlugu, f"modeller/{dosya_prefix}_dict.pkl")
    
    return isabet_orani

def tam_sistem_egitimi():
    print("⏳ Temizlenmiş veri yükleniyor (cleaned_dataset.csv)...")
    df = pd.read_csv("cleaned_dataset.csv", low_memory=False)

    df = df.dropna(subset=['Fiyat', 'Kilometre', 'Yıl', 'Marka', 'Seri', 'Kasa Tipi'])
    df['Arac_Yasi'] = 2026 - df['Yıl']
    df['Arac_Yasi'] = df['Arac_Yasi'].replace(0, 1)

    os.makedirs('modeller', exist_ok=True)
    
    silinecekler = ['İlan Başlığı', 'Ortalama Yakıt Tüketimi', 'Ort. Yakıt Tüketimi', 'Yıl', 'Yakıt Deposu', 'Motor Hacmi', 'Motor Gücü', 'Ağır Hasarlı', 'Boya/Değişen']
    df = df.drop(columns=[col for col in silinecekler if col in df.columns], errors='ignore')
    df = df.dropna()

    genel_r2_listesi = []

    print("\n" + "="*60)
    print("🚀 AŞAMA 1: NOKTA ATIŞI SERİ UZMANLARI EĞİTİLİYOR (Örn: AUDI A3)")
    print("="*60)
    for (marka, seri), alt_veri in df.groupby(['Marka', 'Seri']):
        prefix = f"{dosya_adi_yap(marka)}_{dosya_adi_yap(seri)}"
        aciklama = f"SERİ UZMANI: {marka.upper()} {seri.upper()}"
        r2 = uzman_egit_ve_kaydet(alt_veri, prefix, aciklama)
        if r2: genel_r2_listesi.append(r2)

    print("\n" + "="*60)
    print("🛡️ AŞAMA 2: KASA TİPİ YEDEK UZMANLARI EĞİTİLİYOR (Örn: AUDI SEDAN)")
    print("="*60)
    for (marka, kasa), alt_veri in df.groupby(['Marka', 'Kasa Tipi']):
        prefix = f"{dosya_adi_yap(marka)}_{dosya_adi_yap(kasa)}"
        aciklama = f"KASA UZMANI: {marka.upper()} {kasa.upper()}"
        r2 = uzman_egit_ve_kaydet(alt_veri, prefix, aciklama)
        if r2: genel_r2_listesi.append(r2)

    print("\n" + "="*60)
    print("🪂 AŞAMA 3: MARKA GENEL UZMANLARI EĞİTİLİYOR (Örn: AUDI GENEL)")
    print("="*60)
    for marka, alt_veri in df.groupby('Marka'):
        prefix = f"{dosya_adi_yap(marka)}_GENEL"
        aciklama = f"MARKA GENEL: {marka.upper()}"
        uzman_egit_ve_kaydet(alt_veri, prefix, aciklama)

    print("\n" + "="*60)
    print("🌍 AŞAMA 4: TÜM PİYASA UZMANI EĞİTİLİYOR (Son Kurtarıcı)")
    print("="*60)
    uzman_egit_ve_kaydet(df, "TUM_PIYASA", "TÜRKİYE PİYASASI GENEL UZMANI")

    ortalama_basari = np.mean(genel_r2_listesi)
    print("\n" + "="*60)
    print("🏆 ŞELALE MİMARİSİ BAŞARIYLA İNŞA EDİLDİ 🏆")
    print(f"Seri ve Kasa Uzmanlarının Ortalama Başarı Oranı: %{ortalama_basari:.2f}")
    print("="*60)

if __name__ == "__main__":
    tam_sistem_egitimi()