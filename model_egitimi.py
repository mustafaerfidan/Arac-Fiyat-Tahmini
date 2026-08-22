import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

def model_egit():
    print("⏳ Eğitime hazır veri seti yükleniyor (ml_ready_dataset.csv)...")
    df = pd.read_csv("ml_ready_dataset.csv", low_memory=False)

    # Temizlik: Önceki adımdan kalan bozuk 'Boya-değişen' sütununu tamamen at
    if 'Boya/Değişen' in df.columns:
        df = df.drop(columns=['Boya/Değişen'], errors='ignore')
    if 'Boya-değişen' in df.columns:
        df = df.drop(columns=['Boya-değişen'], errors='ignore')

    # Boş (NaN) verisi kalmış satır varsa kazaya kurban gitmemek için düşür
    df = df.dropna()

    q_low = df["Fiyat"].quantile(0.01) # En ucuz %1'lik çöp ilanlar
    q_hi  = df["Fiyat"].quantile(0.99) # En pahalı %1'lik troll ilanlar
    df = df[(df["Fiyat"] < q_hi) & (df["Fiyat"] > q_low)]
    # ------------------------------------------------------------



    print(f"📊 Toplam {len(df)} adet ilan ile eğitim başlıyor...")

    # X (Özellikler/Parametreler) ve y (Hedef/Tahmin Edilecek Fiyat) ayrımı
    X = df.drop(columns=['Fiyat'])
    y = df['Fiyat']

    # Veriyi %80 Eğitim, %20 Test olarak ayırma
    print("✂️ Veri seti %80 Eğitim ve %20 Test olarak bölünüyor...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # MODEL TANIMLAMA VE EĞİTME
    print("🚀 Random Forest (Rastgele Orman) Algoritması eğitiliyor...")
    print("⚠️ DİKKAT: Veri seti çok büyük (220 bin satır) olduğu için bu işlem bilgisayarının hızına göre 1 ila 5 dakika sürebilir. Lütfen bekleyin...")
    
    # n_jobs=-1 parametresi bilgisayarının tüm işlemci çekirdeklerini kullanmasını sağlar
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # TAHMİN VE BAŞARI ÖLÇÜMÜ
    print("🎯 Model daha önce hiç görmediği %20'lik test verisi üzerinde test ediliyor...")
    tahminler = model.predict(X_test)

    r2 = r2_score(y_test, tahminler)
    mae = mean_absolute_error(y_test, tahminler)

    print("\n" + "="*50)
    print("🏆 MODEL BAŞARI SONUÇLARI 🏆")
    print("="*50)
    print(f"Başarı Oranı (R^2 Skoru) : % {r2 * 100:.2f}")
    print(f"Ortalama Hata Payı (MAE) : {mae:,.0f} TL")
    print("="*50)

if __name__ == "__main__":
    model_egit()