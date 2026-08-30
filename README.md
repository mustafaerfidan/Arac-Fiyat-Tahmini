# İkinci El Araç Değerleme ve Dinamik Ekspertiz Sistemi

Bu proje, ikinci el araç piyasasındaki fiyat belirleme süreçlerini optimize etmek amacıyla geliştirilmiş, çok katmanlı makine öğrenmesi mimarisine dayanan gelişmiş bir değerleme ve ekspertiz motorudur. Standart regresyon modellerinin aksine, araç fiyatlarını piyasa gerçeklerine (lokal hasarlar, ağır kusurlar, donanım paketleri ve periyodik bakım geçmişi) göre dinamik olarak çarpanlara ayırır ve daraltılmış bir fiyat bandı sunar.

## Temel Özellikler ve Mimari Yapı

### 1. Dört Katmanlı Şelale (Cascading Fallback) Mimarisi
Sistem, eksik veya azınlık verilerle karşılaştığında çökmemek veya tutarsız sonuçlar vermemek için hiyerarşik bir modelleme stratejisi kullanır. Kullanıcıdan gelen sorgu sırasıyla şu katmanlardan geçirilir:
* **Katman 1 (Seri Uzmanı):** Doğrudan marka ve seri odaklı model (Örn: Audi A3). En yüksek öncelik.
* **Katman 2 (Kasa Tipi Uzmanı):** Seri verisi yetersizse, kasanın genel dinamiklerine göre çalışan model (Örn: Audi Sedan).
* **Katman 3 (Marka Genel Uzmanı):** Spesifik kasa bulunamadığında markanın genel piyasa algısını ölçen model (Örn: Audi Genel).
* **Katman 4 (Tüm Piyasa Uzmanı):** Hiçbir eşleşme bulunamazsa devreye giren genel kurtarıcı model.

### 2. Doğal Dil İşleme (NLP) ile Hata Tolere Etme
Son kullanıcı veya veri giriş personeli tarafından yapılabilecek yazım hataları (typo), Python'un yerleşik `difflib` kütüphanesi kullanılarak arka planda tespit edilir ve sistemdeki geçerli "Master Data" sözlüğüne göre otomatik olarak düzeltilir. (Örn: "ople" -> "OPEL"). Bu sayede kullanıcı hatalarından kaynaklı sistem kesintileri sıfıra indirilmiştir.

### 3. Dinamik Ekspertiz ve Değer Kaybı Algoritması
Yapay zekanın ürettiği ham piyasa değeri, detaylı bir ekspertiz algoritmasından geçirilerek nihai fiyata ulaşılır:
* **Hayati Kusurlar:** Ağır hasar (pert) kaydı, önden kaza, şase veya podye işlemleri gibi durumlar fiyata doğrudan ve yüksek oranda negatif çarpan olarak yansır.
* **Kaporta Ağırlıklandırması:** Her kaporta parçasının piyasadaki değeri farklıdır. Sistemin algoritmasında bir tavan değişimi ile çamurluk boyası aynı oranda değer kaybı yaratmaz; gerçek piyasa dinamiklerine göre matematiksel ağırlıklandırma yapılmıştır.
* **Değer Katan Özellikler (Prim):** Düzenli yetkili servis bakımı veya yedek anahtar varlığı gibi unsurlar araca pozitif çarpan olarak eklenir.
* **Kondisyon Puanlaması:** Motor, şanzıman, baskı balata, fren sistemi ve dış kozmetik gibi detaylar 1 ile 10 arasında puanlanarak nihai fiyat bandının (dip ve tavan fiyat) belirlenmesinde rol oynar.

## Kullanılan Teknolojiler

* **Python 3.12+**
* **XGBoost:** Temel regresyon ve ağaç tabanlı öğrenme modeli.
* **Pandas & NumPy:** Veri manipülasyonu, temizleme ve matris operasyonları.
* **Scikit-learn:** Veri setinin bölünmesi (train/test) ve model başarı ölçümleri (R2, isabet oranı).
* **Joblib:** Eğitilmiş modellerin (pkl) ve sözlüklerin serileştirilerek saklanması.

## Kurulum ve Çalıştırma

1. Projeyi bilgisayarınıza klonlayın:
```bash
git clone [https://github.com/mustafaerfidan/Arac-Fiyat-Tahmini.git](https://github.com/mustafaerfidan/Arac-Fiyat-Tahmini.git)
cd Arac-Fiyat-Tahmini