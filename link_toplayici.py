from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def ilan_linklerini_topla(liste_url):
    print(f"\nListe sayfasına gidiliyor: {liste_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Sunucuya geçince bunu True yapacağız
        page = browser.new_page()
        
        page.goto(liste_url, timeout=60000)
        print("Sayfanın yüklenmesi bekleniyor...")
        page.wait_for_timeout(6000)
        
        page.evaluate("window.scrollBy(0, 2000)")
        page.wait_for_timeout(2000)
        
        html_icerigi = page.content()
        browser.close()
        
        soup = BeautifulSoup(html_icerigi, "html.parser")
        tum_linkler = soup.find_all("a", href=True)
        
        ilan_linkleri = set() 
        
        for a_etiketi in tum_linkler:
            href = a_etiketi["href"]
            if href.startswith("/ilan/galeriden-satilik-") or href.startswith("/ilan/sahibinden-satilik-"):
                tam_link = f"https://www.arabam.com{href}"
                ilan_linkleri.add(tam_link)
                
        ilan_listesi = list(ilan_linkleri)
        print(f"Bu sayfada {len(ilan_listesi)} adet ilan linki bulundu.")
            
        return ilan_listesi