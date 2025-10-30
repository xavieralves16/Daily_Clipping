import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
from urllib.parse import urljoin

ARQUIVO_SAIDA = r"C:\Users\XAlves\OneDrive - Metalurgica Progresso, S.A\Clipping\Daily_Clipping\clipping.html"
URL_LUSA_ECONOMIA = "https://www.lusa.pt/economia"
URL_NYTIMES_BUSINESS = "https://www.nytimes.com/section/business"
NUM_NOTICIAS_PT = 17
NUM_NOTICIAS_INT = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}

def obter_dados_economicos():
    moedas = ["USD", "GBP", "CHF", "JPY", "CNY", "CAD", "AUD", "BRL", "INR", "ZAR"]
    dados = {}
    pasta = os.path.dirname(ARQUIVO_SAIDA) or "."
    caminho_dados = os.path.join(pasta, "ultimas_taxas.json")
    anteriores = {}
    if os.path.exists(caminho_dados):
        try:
            with open(caminho_dados, "r", encoding="utf-8") as f:
                anteriores = json.load(f)
        except Exception:
            anteriores = {}
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=12)
        data = r.json()
        if data.get("result") == "success" and "rates" in data:
            rates = data["rates"]
            for m in moedas:
                v = rates.get(m)
                if v:
                    v = round(float(v), 3)
                    var = None
                    if m in anteriores and anteriores[m] > 0:
                        var = ((v - anteriores[m]) / anteriores[m]) * 100.0
                    dados[m] = {"valor": v, "variacao": var}
                else:
                    dados[m] = {"valor": "N/D", "variacao": None}
    except Exception as e:
        print(f"⚠️ Erro a obter câmbios: {e}")
    try:
        atuais = {m: float(dados[m]["valor"]) for m in dados if isinstance(dados[m]["valor"], (int, float))}
        with open(caminho_dados, "w", encoding="utf-8") as f:
            json.dump(atuais, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Não foi possível gravar ultimas_taxas.json: {e}")
    nomes = {
        "USD": "Dólar Americano (USD)",
        "GBP": "Libra Esterlina (GBP)",
        "CHF": "Franco Suíço (CHF)",
        "JPY": "Iene Japonês (JPY)",
        "CNY": "Yuan Chinês (CNY)",
        "CAD": "Dólar Canadiano (CAD)",
        "AUD": "Dólar Australiano (AUD)",
        "BRL": "Real Brasileiro (BRL)",
        "INR": "Rupia Indiana (INR)",
        "ZAR": "Rand Sul-Africano (ZAR)",
    }
    return {nomes[k]: v for k, v in dados.items() if k in nomes}

def _limpa_texto(t):
    t = (t or "").strip().replace("\n", " ")
    while "  " in t:
        t = t.replace("  ", " ")
    return t

def _corta(txt, n=240):
    txt = _limpa_texto(txt)
    if len(txt) <= n:
        return txt
    return txt[: n - 3].rsplit(" ", 1)[0] + "..."

def recolher_noticias():
    noticias = {"Portugal": []}
    try:
        html = requests.get(URL_LUSA_ECONOMIA, headers=HEADERS, timeout=12).text
        soup = BeautifulSoup(html, "html.parser")
        artigos = []
        artigos.extend(soup.select("article"))
        artigos.extend(soup.select('div[class*="news"], li[class*="news"]'))
        artigos.extend(soup.select('div[class*="article"], li[class*="article"]'))
        vistos = set()
        cards = []
        for a in artigos:
            if id(a) not in vistos:
                vistos.add(id(a))
                cards.append(a)
        items = []
        for card in cards:
            h = card.find(["h1", "h2", "h3"])
            a = h.find("a") if h else card.find("a")
            titulo = _limpa_texto(h.get_text()) if h else _limpa_texto(a.get_text() if a else "")
            href = a["href"] if a and a.has_attr("href") else ""
            if not titulo or not href:
                continue
            link = urljoin("https://www.lusa.pt", href)
            p = card.find("p")
            resumo = _corta(p.get_text() if p else "")
            img = card.find("img")
            imagem = None
            if img:
                if img.has_attr("src") and img["src"]:
                    imagem = urljoin("https://www.lusa.pt", img["src"])
                elif img.has_attr("data-src"):
                    imagem = urljoin("https://www.lusa.pt", img["data-src"])
            items.append({
                "titulo": titulo,
                "descricao": resumo,
                "link": link,
                "imagem": imagem
            })
            if len(items) >= NUM_NOTICIAS_PT:
                break
        noticias["Portugal"] = items
    except Exception as e:
        print(f"⚠️ Erro a extrair da LUSA: {e}")
    return noticias

def recolher_noticias_internacionais():
    noticias = []
    try:
        html = requests.get(URL_NYTIMES_BUSINESS, headers=HEADERS, timeout=12).text
        soup = BeautifulSoup(html, "html.parser")
        artigos = soup.select("section[data-testid='block-Briefings'] article, section[data-testid='stream-panel'] article")
        if not artigos:
            artigos = soup.select("article")
        for art in artigos[:NUM_NOTICIAS_INT]:
            titulo_tag = art.find(["h2", "h3"])
            titulo = _limpa_texto(titulo_tag.get_text() if titulo_tag else "")
            a = titulo_tag.find("a") if titulo_tag else art.find("a")
            link = urljoin("https://www.nytimes.com", a["href"]) if a and a.has_attr("href") else None
            resumo_tag = art.find("p")
            resumo = _corta(resumo_tag.get_text()) if resumo_tag else "No summary available."
            img = art.find("img")
            imagem = None
            if img and img.has_attr("src"):
                imagem = img["src"]
            noticias.append({
                "titulo": titulo,
                "descricao": resumo,
                "link": link,
                "imagem": imagem
            })
    except Exception as e:
        print(f"⚠️ Erro a extrair da NY Times: {e}")
    return {"Internacional": noticias}

def gerar_html(noticias, economia):
    data_str = datetime.now().strftime("%d/%m/%Y")
    html = f"""<!DOCTYPE html>
<html lang='pt'>
<head>
<meta charset='UTF-8'>
<title>Clipping Diário — {data_str}</title>
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: #f4f6f8;
        margin: 0; padding: 0; color: #333;
    }}
    .container {{
        max-width: 900px; margin: 40px auto; background: #fff;
        border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden;
    }}
    header {{ background-color: #0078d4; color: #fff; padding: 25px; text-align: center; }}
    header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
    header p {{ margin: 5px 0 0; font-size: 14px; color: #e0e0e0; }}
    section {{ padding: 30px 40px; }}
    h2 {{
        color: #0078d4; border-bottom: 2px solid #0078d4;
        padding-bottom: 5px; margin-top: 40px; font-size: 20px;
    }}
    .economia {{
        display: grid; grid-template-columns: 1fr 1fr; gap: 8px 30px;
        font-size: 15px; line-height: 1.6;
    }}
    .economia span {{ font-weight: bold; }}
    .up {{ color: #28a745; }} .down {{ color: #dc3545; }}
    .news-item {{
        margin-bottom: 18px; border: 1px solid #e0e0e0; border-radius: 10px;
        padding: 14px 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }}
    .news-item strong {{ color: #111; font-size: 17px; display: block; margin-bottom: 6px; }}
    .news-item p {{ color: #444; margin: 6px 0 10px; font-size: 15px; }}
    .news-item img {{
        display: block; max-width: 100%; height: auto; border-radius: 8px; margin: 8px 0;
    }}
    a {{ color: #0078d4; text-decoration: none; font-weight: 500; }}
    a:hover {{ text-decoration: underline; }}
    footer {{ background-color: #f0f0f0; text-align: center; padding: 15px;
             font-size: 12px; color: #777; border-top: 1px solid #ddd; }}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>Clipping Diário</h1>
        <p>{data_str}</p>
    </header>

    <section>
        <h2>Dados Económicos</h2>
        <div class="economia">
"""
    for nome, info in economia.items():
        valor = info["valor"]
        variacao = info["variacao"]
        valor_txt = f"{valor}" if isinstance(valor, (int, float)) else valor
        if isinstance(variacao, (int, float)) and variacao is not None:
            cor = "up" if variacao >= 0 else "down"
            simbolo = "▲" if variacao >= 0 else "▼"
            var_txt = f"<span class='{cor}'>{simbolo} {abs(variacao):.2f}%</span>"
        else:
            var_txt = ""
        html += f"<div><span>{nome}:</span> {valor_txt} {var_txt}</div>\n"
    html += "</div>\n</section>\n"
    for cat, lista in noticias.items():
        html += f"<section><h2>{cat}</h2>\n"
        if not lista:
            html += "<p><em>Sem notícias disponíveis.</em></p>\n"
        for n in lista:
            html += "<div class='news-item'>\n"
            html += f"<strong>{n['titulo']}</strong>\n"
            html += f"<p>{n['descricao']}</p>\n"
            if n.get("imagem"):
                html += f"<img src='{n['imagem']}' alt='Imagem da notícia'>\n"
            html += f"<a href='{n['link']}'>Ler mais ➜</a>\n"
            html += "</div>\n"
        html += "</section>\n"
    html += f"""
    <footer>
        <p>Gerado automaticamente por sistema de clipping — {data_str}</p>
    </footer>
</div>
</body>
</html>"""
    os.makedirs(os.path.dirname(ARQUIVO_SAIDA) or ".", exist_ok=True)
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[✔] Clipping atualizado: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    noticias_pt = recolher_noticias()
    noticias_int = recolher_noticias_internacionais()
    economia = obter_dados_economicos()
    todas = {**noticias_pt, **noticias_int}
    gerar_html(todas, economia)
