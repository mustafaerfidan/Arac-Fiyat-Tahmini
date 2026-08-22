import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import xgboost as xgb
import warnings
import re
warnings.filterwarnings('ignore')

# Dosya isimlerinde sorun çıkarmaması için metin temizleyici (Örn: "Alfa Romeo" -> "ALFA_ROMEO")
def dosya_adi_yap(metin):
    return re.sub(r'[^a-zA-Z0-9]', '_', str(metin).strip().upper())

# TEK MERKEZDEN EĞİTİM YAPAN FONKSİYON
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
    
    # --- SENİN EFSANE MANTIĞIN: ARALIK İSABET ORANI ---
    # Bu grubun piyasa dalgalanmasını (makasını) buluyoruz
    grup_sapmasi = alt_veri['Fiyat'].std() / alt_veri['Fiyat'].mean()
    makas = max(0.03, min(grup_sapmasi, 0.08)) # %3 ile %8 arası sınırlandır
    
    # Alt ve üst sınırları test seti için oluşturuyoruz
    alt_sinirlar = tahminler * (1 - makas)
    ust_sinirlar = tahminler * (1 + makas)
    
    # Gerçek fiyatların kaç tanesi bizim makasımızın tam içine düştü?
    isabet_sayisi = ((gercek >= alt_sinirlar) & (gercek <= ust_sinirlar)).sum()
    isabet_orani = (isabet_sayisi / len(gercek)) * 100
    # --------------------------------------------------

    r2 = r2_score(gercek, tahminler)
    
    # Ekrana artık sadece R2 değil, senin İsabet Oranını da basıyoruz!
    print(f"   ✅ {aciklama} | Nokta Atışı R²: %{r2*100:.1f} | Makas İsabeti: %{isabet_orani:.1f}")

    joblib.dump(model, f"modeller/{dosya_prefix}_model.pkl")
    joblib.dump(encoding_sozlugu, f"modeller/{dosya_prefix}_dict.pkl")
    
    return isabet_orani # Artık sistem başarısını R2'ye göre değil, senin isabet oranına göre ölçecek!

def tam_sistem_egitimi():
    print("⏳ Temizlenmiş veri yükleniyor (cleaned_dataset.csv)...")
    df = pd.read_csv("cleaned_dataset.csv", low_memory=False)

    # Temel eksikleri at ve Araç Yaşını hesapla (2026'ya göre)
    df = df.dropna(subset=['Fiyat', 'Kilometre', 'Yıl', 'Marka', 'Kasa Tipi'])
    df['Arac_Yasi'] = 2026 - df['Yıl']
    df['Arac_Yasi'] = df['Arac_Yasi'].replace(0, 1)

    # Modellerin kaydedileceği klasörü oluştur
    os.makedirs('modeller', exist_ok=True)
    
    # İşimize yaramayacak gereksiz sütunları sil
    silinecekler = ['İlan Başlığı', 'Ortalama Yakıt Tüketimi', 'Ort. Yakıt Tüketimi', 'Yıl', 'Yakıt Deposu', 'Motor Hacmi', 'Motor Gücü', 'Ağır Hasarlı', 'Boya/Değişen']
    df = df.drop(columns=[col for col in silinecekler if col in df.columns], errors='ignore')
    df = df.dropna()

    genel_r2_listesi = []

    print("\n" + "="*50)
    print("🚀 AŞAMA 1: MİKRO UZMANLAR EĞİTİLİYOR (Marka + Kasa Tipi)")
    print("="*50)
    for (marka, kasa_tipi), alt_veri in df.groupby(['Marka', 'Kasa Tipi']):
        prefix = f"{dosya_adi_yap(marka)}_{dosya_adi_yap(kasa_tipi)}"
        aciklama = f"UZMAN: {marka.upper()} {kasa_tipi.upper()}"
        r2 = uzman_egit_ve_kaydet(alt_veri, prefix, aciklama)
        if r2: genel_r2_listesi.append(r2)

    print("\n" + "="*50)
    print("🪂 AŞAMA 2: YEDEK PARAŞÜT 1 - MARKA GENEL UZMANLARI EĞİTİLİYOR")
    print("="*50)
    for marka, alt_veri in df.groupby('Marka'):
        prefix = f"{dosya_adi_yap(marka)}_GENEL"
        aciklama = f"MARKA GENEL: {marka.upper()}"
        uzman_egit_ve_kaydet(alt_veri, prefix, aciklama)

    print("\n" + "="*50)
    print("🌍 AŞAMA 3: YEDEK PARAŞÜT 2 - TÜM PİYASA UZMANI EĞİTİLİYOR")
    print("="*50)
    uzman_egit_ve_kaydet(df, "TUM_PIYASA", "TÜRKİYE PİYASASI GENEL UZMANI")

    ortalama_basari = np.mean(genel_r2_listesi) 
    print("\n" + "="*50)
    print("🏆 BÜTÜN HİYERARŞİK MODELLER VE YEDEK PARAŞÜTLER BAŞARIYLA KAYDEDİLDİ 🏆")
    print(f"Sistemdeki 'Mikro Uzmanların' Ortalama Başarı Oranı: %{ortalama_basari:.2f}")
    print("="*50)

if __name__ == "__main__":
    tam_sistem_egitimi()