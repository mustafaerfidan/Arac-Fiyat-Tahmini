import csv
import glob
import os
import pandas as pd


def csv_birlestir_esnek():
  dosya_listesi = glob.glob("*_veriseti.csv")

  if not dosya_listesi:
    print(
        "❌ HATA: Klasörde birleştirilecek '*_veriseti.csv' dosyası bulunamadı!"
    )
    return

  print(
    f"📂 Toplam {len(dosya_listesi)} adet CSV dosyası bulundu. Esnek okuma"
    " moduyla birleştiriliyor...\n"
  )

  tum_veriler = []
  basarili_dosya = 0

  for dosya in dosya_listesi:
    try:
      # utf-8-sig ve errors='ignore' ile olası bozuk karakterleri de tolere ediyoruz
      with open(dosya, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f)
        satir_sayisi = 0
        for satir in reader:
          # DictReader her satırı sözlük olarak okur, sütun sayısı tutmasa bile çökmez
          tum_veriler.append(satir)
          satir_sayisi += 1

      basarili_dosya += 1
      print(f"✔ Yüklendi: {dosya} ({satir_sayisi} ilan)")
    except Exception as e:
      print(f"⚠️ UYARI: '{dosya}' okunurken beklenmeyen hata: {e}")

  if tum_veriler:
    print(
        "\n⏳ Veriler DataFrame'e dönüştürülüyor ve sütunlar hizalanıyor..."
    )
    # Tüm sözlükleri otomatik olarak ortak sütun yapısına kavuşturur
    master_df = pd.DataFrame(tum_veriler)

    # Olası tekrar eden başlık satırlarını veya tamamen boş satırları temizle
    master_df = master_df.dropna(how="all")

    cikti_dosyasi = "master_dataset.csv"
    master_df.to_csv(cikti_dosyasi, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 50)
    print("🎉 BİRLEŞTİRME İŞLEMİ KUSURSUZ TAMAMLANDI!")
    print(f"📂 Okunan Dosya Sayısı      : {basarili_dosya} / {len(dosya_listesi)}")
    print(f"📊 Toplam Satır (İlan) Sayısı : {len(master_df)}")
    print(f"📋 Toplam Farklı Sütun Sayısı: {len(master_df.columns)}")
    print(f"💾 Kaydedilen Dosya          : {cikti_dosyasi}")
    print("=" * 50)
  else:
    print("❌ Hiç veri okunamadı.")


if __name__ == "__main__":
  csv_birlestir_esnek()