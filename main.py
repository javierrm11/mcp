import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import uvicorn
import os

mcp = FastMCP()
app = FastAPI()

# ------------------------------- HERRAMIENTAS -------------------------------

@mcp.tool()
async def avion_mas_rapido(region: str) -> str:
    region_map = {
        "España": "Spain", "Europa": "Europe", "América": "America", "America": "America",
        "América del Norte": "America", "America del Norte": "America",
        "América del Sur": "America", "America del Sur": "America",
        "África": "Africa", "Africa": "Africa", "Asia": "Asia",
        "Oceanía": "Oceania", "Oceania": "Oceania",
    }
    region_api = region_map.get(region.strip(), region.capitalize())
    url = f"https://api-vuelos-eight.vercel.app/{region_api}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        try:
            await page.wait_for_selector("h2:text('Avión más rápido')", timeout=40000)
        except:
            await browser.close()
            return f"No se encontró el bloque 'Avión más rápido' en la región {region}"

        contenedor = page.locator("h2:text('Avión más rápido')").first.locator("..")
        hex_linea = await contenedor.locator("p:has-text('Hex:')").text_content()
        velocidad_linea = await contenedor.locator("p:has-text('Velocidad:')").text_content()

        hex_valor = hex_linea.split("Hex:")[-1].strip()
        velocidad_valor = velocidad_linea.split("Velocidad:")[-1].strip()

        await browser.close()
        return f"El avión más rápido en {region} es {hex_valor} con una velocidad de {velocidad_valor}."

@mcp.tool()
async def explica_consumo_emisiones(pregunta: str) -> str:
    pregunta = pregunta.lower()
    if ("emisiones" in pregunta or "co2" in pregunta or "dioxido" in pregunta) and ("consumo" in pregunta or "gasta" in pregunta or "combustible" in pregunta or "litros" in pregunta):
        return (
            "Para calcular el consumo de combustible, primero estimamos la resistencia aerodinámica que debe vencer el avión, "
            "la cual depende de la velocidad y la densidad del aire (que varía con la altitud). "
            "A partir de esta resistencia y del consumo específico de combustible (TSFC), calculamos cuánta masa de combustible se quema por segundo. "
            "Luego, para obtener el consumo en litros, usamos la densidad del combustible. "
            "Para estimar las emisiones de CO2, multiplicamos la masa total de combustible consumido por un factor de 3.16, "
            "que representa los kilogramos de CO2 emitidos por cada kilogramo de combustible quemado."
        )
    if "emisiones" in pregunta or "co2" in pregunta or "dioxido" in pregunta:
        return (
            "Para calcular las emisiones de CO2, primero estimamos cuánto combustible consume el avión durante el vuelo. "
            "Esto se hace calculando la resistencia aerodinámica que debe vencer el avión. "
            "Multiplicamos esta resistencia por el consumo específico de combustible (TSFC), y finalmente por un factor de 3.16, "
            "que representa los kg de CO2 generados por cada kg de combustible quemado."
        )
    if "consumo" in pregunta or "gasta" in pregunta or "combustible" in pregunta or "litros" in pregunta:
        return (
            "El consumo se estima con base en la velocidad, altitud y características del avión. "
            "Se calcula la resistencia aerodinámica y se multiplica por el TSFC (consumo específico). "
            "La masa de combustible se convierte a litros según la densidad del combustible usado."
        )
    return (
        "Esta herramienta explica cómo se calcula el consumo de combustible y las emisiones de CO2. "
        "Puedes preguntar cosas como: '¿Cómo se calcula el consumo?' o '¿Cuánto CO2 emite un vuelo?'"
    )

@mcp.tool()
async def origenVuelo(vuelo: str) -> str:
    vuelo = vuelo.strip().upper()
    url = f"https://es.flightaware.com/live/flight/{vuelo}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        try:
            await page.wait_for_selector(".flightPageSummaryCity", timeout=30000)
        except:
            await browser.close()
            return f"No se pudo obtener el origen del vuelo {vuelo}."
        origen = await page.locator(".flightPageSummaryCity").first.text_content()
        await browser.close()
        return f"Origen: {origen.strip() if origen else 'desconocido'}"

@mcp.tool()
async def destinoVuelo(vuelo: str) -> str:
    vuelo = vuelo.strip().upper()
    url = f"https://es.flightaware.com/live/flight/{vuelo}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        try:
            await page.wait_for_selector(".flightPageSummaryCity", timeout=30000)
        except:
            await browser.close()
            return f"No se pudo obtener el destino del vuelo {vuelo}."
        destino = await page.locator(".flightPageSummaryCity").first.text_content()
        await browser.close()
        return f"Destino: {destino.strip() if destino else 'desconocido'}"

@mcp.tool()
async def trackVuelo(vuelo: str) -> str:
    vuelo = vuelo.strip().upper()
    url = f"https://es.flightaware.com/live/flight/{vuelo}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        try:
            await page.wait_for_selector(".flightPageSummaryCity", timeout=30000)
            await page.wait_for_selector(".destinationCity", timeout=30000)
        except:
            await browser.close()
            return f"No se pudo obtener el track del vuelo {vuelo}."
        origen = await page.locator(".flightPageSummaryCity").first.text_content()
        destino = await page.locator(".destinationCity").first.text_content()
        await browser.close()
        return f"Origen: {origen.strip() if origen else 'desconocido'} - Destino: {destino.strip() if destino else 'desconocido'}"

@mcp.tool()
async def tiempoVuelo(vuelo: str) -> str:
    vuelo = vuelo.strip().upper()
    url = f"https://es.flightaware.com/live/flight/{vuelo}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        try:
            await page.wait_for_selector(".flightPageProgressTotal strong", timeout=30000)
        except:
            await browser.close()
            return f"No se pudo obtener el tiempo del vuelo {vuelo}."
        tiempo = await page.locator(".flightPageProgressTotal strong").first.text_content()
        await browser.close()
        return f"Tiempo total de vuelo: {tiempo.strip() if tiempo else 'desconocido'}"

# ------------------------------- ENDPOINT /ask -------------------------------

class Query(BaseModel):
    prompt: str

@app.post("/ask")
async def ask(query: Query):
    try:
        response = await mcp.run(query.prompt)  # ✅ CORREGIDO
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}

# ------------------------------- UVICORN para Railway -------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
