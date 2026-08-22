import pandas as pd

def veriyi_kesfet():
    print("⏳ Dev veri seti yükleniyor, lütfen bekleyin...\n")
    
    # low_memory=False uyarısını kapatmak ve hızlı okumak için
    df = pd.read_csv("master_dataset.csv", low_memory=False)
    
    baslangic_sayisi = len(df)
    print(f"📊 Başlangıçtaki Toplam İlan Sayısı : {baslangic_sayisi}")
    
    # Bütün sütunları tamamen aynı olan kopya ilanları (duplicates) sil
    df = df.drop_duplicates()
    
    kalan_sayi = len(df)
    silinen_sayi = baslangic_sayisi - kalan_sayi
    print(f"🗑️ Tekrar Eden (Kopya) İlanlar Silindi: {silinen_sayi} adet")
    print(f"✅ Temizlenmiş Net İlan Sayısı       : {kalan_sayi}\n")
    
    print("="*50)
    print("📋 SÜTUN İSİMLERİ VE VERİ TİPLERİ:")
    print("="*50)
    print(df.info())
    
    print("\n" + "="*50)
    print("👀 İLK 2 SATIRIN ÖRNEK GÖRÜNTÜSÜ:")
    print("="*50)
    # Ekrana düzgün sığması için to_string() kullanıyoruz
    print(df.head(2).to_string())

if __name__ == "__main__":
    veriyi_kesfet()