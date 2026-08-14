from bs4 import BeautifulSoup

def ilan_linklerini_topla(page, liste_url):
    print(f"\nListe sayfasına gidiliyor: {liste_url}")
    
    # main.py dosyasında açılan tarayıcı sekmesini (page) kullanıyoruz
    page.goto(liste_url, timeout=60000)
    print("Sayfanın yüklenmesi bekleniyor...")
    page.wait_for_timeout(6000)
    
    # Sayfanın aşağısındaki ilanların da yüklenmesi için kaydırma işlemi
    page.evaluate("window.scrollBy(0, 2000)")
    page.wait_for_timeout(2000)
    
    html_icerigi = page.content()
    
    # BeautifulSoup ile HTML kodlarını parçalıyoruz
    soup = BeautifulSoup(html_icerigi, "html.parser")
    tum_linkler = soup.find_all("a", href=True)
    
    ilan_linkleri = set() 
    
    # Linkleri filtreleyip tam URL'ye çeviriyoruz
    for a_etiketi in tum_linkler:
        href = a_etiketi["href"]
        if href.startswith("/ilan/galeriden-satilik-") or href.startswith("/ilan/sahibinden-satilik-"):
            tam_link = f"https://www.arabam.com{href}"
            ilan_linkleri.add(tam_link)
            
    ilan_listesi = list(ilan_linkleri)
    print(f"Bu sayfada {len(ilan_listesi)} adet ilan linki bulundu.")
        
    return ilan_listesi