import pandas as pd
from sklearn.preprocessing import LabelEncoder

def model_icin_hazirla():
    print("⏳ Temizlenmiş veri yükleniyor (cleaned_dataset.csv)...")
    df = pd.read_csv("cleaned_dataset.csv", low_memory=False)

    print("🛠️ Özellik Mühendisliği (Feature Engineering) yapılıyor...")
    
    # 1. Araç Yaşı Hesaplama (İçinde bulunduğumuz 2026 yılına göre)
    if 'Yıl' in df.columns:
        df['Arac_Yasi'] = 2026 - df['Yıl']
        # 2026 model araçların yaşı 0 çıkacaktır. Matematiksel hataları önlemek için yaşı 0 olanları 1 yapıyoruz.
        df['Arac_Yasi'] = df['Arac_Yasi'].replace(0, 1)
        
    # 2. Yıllık Ortalama Kilometre (Araç yılda ortalama kaç km yapmış?)
    if 'Kilometre' in df.columns and 'Arac_Yasi' in df.columns:
        df['Yillik_Ort_Km'] = (df['Kilometre'] / df['Arac_Yasi']).astype(int)

    print("🔢 Kategorik veriler sayısallaştırılıyor (Label Encoding)...")
    
    # Algoritmaların anlaması için metinleri (String) sayılara (Integer) çeviriyoruz
    kategorik_sutunlar = ['Marka', 'Seri', 'Model', 'Vites Tipi', 'Yakıt Tipi', 'Kasa Tipi', 'Renk', 'Boya-değişen', 'Çekiş']
    
    le = LabelEncoder()
    for sutun in kategorik_sutunlar:
        if sutun in df.columns:
            # Boş değerleri 'Bilinmiyor' olarak doldur ki kod çökmesin
            df[sutun] = df[sutun].fillna('Bilinmiyor').astype(str)
            # Metni sayıya çevir (Örn: Manuel -> 0, Otomatik -> 1)
            df[sutun + '_Kod'] = le.fit_transform(df[sutun])
            # Sayıya çevrilen eski metin sütununu veri setinden at
            df = df.drop(columns=[sutun])

    # Modelin kafasını karıştıracak, matematiksel karşılığı olmayan metin sütunlarını temizle
    silinecekler = ['İlan Başlığı', 'Ortalama Yakıt Tüketimi', 'Ort. Yakıt Tüketimi', 'Yıl', 'Yakıt Deposu', 'Motor Hacmi', 'Motor Gücü', 'Ağır Hasarlı']
    df = df.drop(columns=[col for col in silinecekler if col in df.columns], errors='ignore')

    print("\n📈 Fiyat ile olan Korelasyon (İlişki) Değerleri:")
    print("-" * 50)
    # Sadece sayısal kalan sütunların Fiyat ile olan ilişkisine bakıyoruz
    sayisal_df = df.select_dtypes(include=['number'])
    korelasyon = sayisal_df.corr()['Fiyat'].sort_values(ascending=False)
    print(korelasyon)

    cikti = "ml_ready_dataset.csv"
    df.to_csv(cikti, index=False, encoding="utf-8-sig")
    
    print("\n" + "="*50)
    print(f"🚀 VERİ SETİ MAKİNE ÖĞRENMESİ MODELİNE %100 HAZIR!")
    print(f"💾 Son dosya '{cikti}' olarak kaydedildi.")
    print("="*50)

if __name__ == "__main__":
    model_icin_hazirla()