from bs4 import BeautifulSoup

def ilan_linklerini_topla(page, liste_url):
    print(f"\nKategori ana linki: {liste_url}")
    
    tum_ilan_linkleri = set()
    sayfa_no = 1
    
    while True: # Sayfalar bitene kadar dönecek sonsuz döngü
        # 1. sayfa dışındakiler için URL'nin sonuna "?page=2", "?page=3" ekliyoruz
        if sayfa_no == 1:
            guncel_url = liste_url
        else:
            ayrac = "&" if "?" in liste_url else "?"
            guncel_url = f"{liste_url}{ayrac}page={sayfa_no}"
            
        print(f"[{sayfa_no}. Sayfa] Taranıyor: {guncel_url}")
        
        # HIZLANDIRMA 1: Resimleri bekleme, sadece HTML kodları inince devam et
        page.goto(guncel_url, timeout=60000, wait_until="domcontentloaded")
        
        # HIZLANDIRMA 2: 4 saniyelik sabit beklemeyi tamamen sildik.
        
        # Sayfanın aşağısındaki ilanların da (tembel yükleme / lazy load) yüklenmesi için kaydırma işlemi
        page.evaluate("window.scrollBy(0, 2000)")
        
        # HIZLANDIRMA 3: 2 saniyelik beklemeyi sadece yarım saniyeye (500 ms) indirdik
        page.wait_for_timeout(500) 
        
        html_icerigi = page.content()
        soup = BeautifulSoup(html_icerigi, "html.parser")
        tum_linkler = soup.find_all("a", href=True)
        
        sayfadaki_ilan_sayisi = 0
        
        # Linkleri filtreleyip tam URL'ye çeviriyoruz
        for a_etiketi in tum_linkler:
            href = a_etiketi["href"]
            if href.startswith("/ilan/galeriden-satilik-") or href.startswith("/ilan/sahibinden-satilik-"):
                tam_link = f"https://www.arabam.com{href}"
                
                # Link daha önce eklenmediyse listeye ekle
                if tam_link not in tum_ilan_linkleri:
                    tum_ilan_linkleri.add(tam_link)
                    sayfadaki_ilan_sayisi += 1
                    
        print(f"Bu sayfada {sayfadaki_ilan_sayisi} yeni ilan bulundu. (Kategoride Toplanan: {len(tum_ilan_linkleri)})")
        
        # Eğer bu sayfada HİÇ YENİ İLAN bulamadıysak (yani son sayfayı geçtiysek) döngüyü bitir
        if sayfadaki_ilan_sayisi == 0:
            print(f"Son sayfaya ulaşıldı. Bu kategori için toplam {len(tum_ilan_linkleri)} ilan toplandı!")
            break
            
        sayfa_no += 1 # Sonraki sayfaya geçmek için numarayı artır
        
    return list(tum_ilan_linkleri)