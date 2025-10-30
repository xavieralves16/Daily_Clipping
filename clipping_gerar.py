import requests
import feedparser
from datetime import datetime
import os
from bs4 import BeautifulSoup

ARQUIVO_SAIDA = os.path.expanduser("/Clipping/Daily_Clipping/clipping.html")


FONTES = {
    "Economia": ["https://eco.sapo.pt/feed/", "https://jornaleconomico.pt/feed"],
    "Política": ["https://expresso.pt/rss/politica.html"],
    "Sociedade": ["https://observador.pt/seccao/sociedade/feed/"]
}

def recolher_noticias():
    noticias = {}
    for categoria, urls in FONTES.items():
        noticias[categoria] = []
        for url in urls:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  
                noticias[categoria].append({
                    "titulo": entry.title,
                    "link": entry.link,
                    "descricao": BeautifulSoup(entry.summary, "html.parser").text[:200]
                })
    return noticias


def obter_dados_economicos():
    try:
        resp = requests.get("https://api.exchangerate.host/latest?base=EUR&symbols=USD")
        data = resp.json()
        if "rates" in data and "USD" in data["rates"]:
            eur_usd = round(data["rates"]["USD"], 3)
        else:
            eur_usd = "N/D"
    except Exception as e:
        print(f"⚠️ Erro ao obter câmbio EUR/USD: {e}")
        eur_usd = "Erro"
    return {"EUR/USD": eur_usd}


def gerar_html(noticias, economia):
    data = datetime.now().strftime("%d/%m/%Y")
    html = f"""<!DOCTYPE html>
<html lang='pt'><head>
<meta charset='UTF-8'><title>Clipping Diário {data}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
h1 {{ color: #0078d4; }}
h2 {{ color: #444; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
a {{ color: #0078d4; text-decoration: none; }}
</style></head><body>
<h1>Clipping Diário — {data}</h1>
<h3>Dados Económicos</h3>
<ul>
<li><b>EUR/USD:</b> {economia['EUR/USD']}</li>
</ul>
"""

    for cat, lista in noticias.items():
        html += f"<h2>{cat}</h2>"
        for n in lista:
            html += f"<p><b>{n['titulo']}</b><br>{n['descricao']}<br><a href='{n['link']}'>Ler mais</a></p>"
    html += "</body></html>"

    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[✔] Clipping atualizado: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    noticias = recolher_noticias()
    economia = obter_dados_economicos()
    gerar_html(noticias, economia)