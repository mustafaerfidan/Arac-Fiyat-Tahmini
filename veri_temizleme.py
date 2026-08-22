import pandas as pd

def veriyi_temizle():
    print("⏳ Ham veri seti yükleniyor (master_dataset.csv)...")
    df = pd.read_csv("master_dataset.csv", low_memory=False)
    
    # 1. KOPYA İLANLARI KALICI OLARAK SİL (Önceki testte yaptığımızı uyguluyoruz)
    df = df.drop_duplicates()
    
    # 2. GEREKSİZ/BOZUK SÜTUNLARI TEMİZLE
    silinecek_sutunlar = [col for col in df.columns if 'Unnamed' in col]
    df = df.drop(columns=silinecek_sutunlar, errors='ignore')
    
    print("🧹 Metin formatındaki sayılar dönüştürülüyor (Fiyat, Kilometre, Yıl)...")
    
    # 3. FİYAT TEMİZLİĞİ ("348.000 TL" -> 348000)
    if 'Fiyat' in df.columns:
        df['Fiyat'] = df['Fiyat'].astype(str).str.replace(' TL', '', regex=False)
        df['Fiyat'] = df['Fiyat'].str.replace('.', '', regex=False)
        df['Fiyat'] = pd.to_numeric(df['Fiyat'], errors='coerce')
        
    # 4. KİLOMETRE TEMİZLİĞİ ("262.000 km" -> 262000)
    if 'Kilometre' in df.columns:
        df['Kilometre'] = df['Kilometre'].astype(str).str.replace(' km', '', regex=False)
        df['Kilometre'] = df['Kilometre'].str.replace('.', '', regex=False)
        df['Kilometre'] = pd.to_numeric(df['Kilometre'], errors='coerce')
        
    # 5. YIL TEMİZLİĞİ
    if 'Yıl' in df.columns:
        df['Yıl'] = pd.to_numeric(df['Yıl'], errors='coerce')

    # 6. BOZUK / EKSİK SATIRLARI SİL
    eski_satir = len(df)
    # Fiyatı, Kilometresi veya Yılı "NaN" (Boş) dönen ilanları veri setinden at
    df = df.dropna(subset=['Fiyat', 'Kilometre', 'Yıl'])
    
    # 7. AYKIRI DEĞER (OUTLIER) FİLTRESİ
    # Yanlışlıkla fiyatı 10 TL yazılan veya yılı 3000 girilen hatalı ilanları dışla
    df = df[(df['Fiyat'] > 50000) & (df['Yıl'] > 1970) & (df['Yıl'] <= 2026)]
    
    yeni_satir = len(df)
    fark = eski_satir - yeni_satir
    
    print("\n" + "="*50)
    print("✨ VERİ TEMİZLİĞİ TAMAMLANDI ✨")
    print(f"🗑️ Atılan Hatalı/Eksik Satır Sayısı : {fark}")
    print(f"✅ Eğitime Hazır Net İlan Sayısı    : {yeni_satir}")
    print("="*50)
    
    # TEMİZLENMİŞ VERİYİ KAYDET
    cikti = "cleaned_dataset.csv"
    df.to_csv(cikti, index=False, encoding="utf-8-sig")
    print(f"💾 Temizlenmiş veri '{cikti}' olarak kaydedildi.")
    
if __name__ == "__main__":
    veriyi_temizle()