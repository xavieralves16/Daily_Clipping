import requests
import feedparser
from datetime import datetime
import os
from bs4 import BeautifulSoup

ARQUIVO_SAIDA = r"C:\Users\XAlves\OneDrive - Metalurgica Progresso, S.A\Clipping\Daily_Clipping\clipping.html"


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
    API_KEY = "9c99f35801d7649cb3342a1a5365f8ae"
    try:
        url = f"https://api.exchangerate.host/latest?access_key={API_KEY}&base=EUR&symbols=USD"
        resp = requests.get(url)
        data = resp.json()

        if "rates" in data and "USD" in data["rates"]:
            eur_usd = round(data["rates"]["USD"], 3)
        else:
            print("⚠️ Resposta inesperada da API:", data)
            eur_usd = "N/D"

    except Exception as e:
        print(f"⚠️ Erro ao obter câmbio EUR/USD: {e}")
        eur_usd = "Erro"

    return {"EUR/USD": eur_usd}


def gerar_html(noticias, economia):
    data = datetime.now().strftime("%d/%m/%Y")
    html = f"""<!DOCTYPE html>
<html lang='pt'>
<head>
<meta charset='UTF-8'>
<title>Clipping Diário — {data}</title>
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: #f4f6f8;
        margin: 0;
        padding: 0;
        color: #333;
    }}
    .container {{
        max-width: 800px;
        margin: 40px auto;
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        overflow: hidden;
    }}
    header {{
        background-color: #0078d4;
        color: white;
        padding: 25px;
        text-align: center;
    }}
    header h1 {{
        margin: 0;
        font-size: 26px;
        font-weight: 600;
    }}
    header p {{
        margin: 5px 0 0;
        font-size: 14px;
        color: #e0e0e0;
    }}
    section {{
        padding: 30px 40px;
    }}
    h2 {{
        color: #0078d4;
        border-bottom: 2px solid #0078d4;
        padding-bottom: 5px;
        margin-top: 40px;
        font-size: 20px;
    }}
    .news-item {{
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #eee;
    }}
    .news-item:last-child {{
        border-bottom: none;
    }}
    .news-item strong {{
        color: #222;
        font-size: 16px;
    }}
    .news-item p {{
        margin: 5px 0;
        line-height: 1.5;
        color: #555;
    }}
    a {{
        color: #0078d4;
        text-decoration: none;
        font-weight: 500;
    }}
    a:hover {{
        text-decoration: underline;
    }}
    footer {{
        background-color: #f0f0f0;
        text-align: center;
        padding: 15px;
        font-size: 12px;
        color: #777;
        border-top: 1px solid #ddd;
    }}
    ul {{
        list-style: none;
        padding: 0;
    }}
    li {{
        padding: 4px 0;
    }}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>Clipping Diário</h1>
        <p>{data}</p>
    </header>

    <section>
        <h2>Dados Económicos</h2>
        <ul>
"""
    # Bloco de economia
    for nome, valor in economia.items():
        html += f"<li><b>{nome}:</b> {valor}</li>"
    html += "</ul>"

    # Bloco de notícias
    for cat, lista in noticias.items():
        html += f"<h2>{cat}</h2>"
        for n in lista:
            html += f"""
            <div class='news-item'>
                <strong>{n['titulo']}</strong>
                <p>{n['descricao']}</p>
                <a href='{n['link']}'>Ler mais ➜</a>
            </div>
            """
    html += f"""
    </section>
    <footer>
        <p>Gerado automaticamente por sistema de clipping — {data}</p>
    </footer>
</div>
</body></html>"""

    # Gravar no OneDrive
    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[✔] Clipping atualizado: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    noticias = recolher_noticias()
    economia = obter_dados_economicos()
    gerar_html(noticias, economia)