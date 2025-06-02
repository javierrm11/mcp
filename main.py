import asyncio
import os
from fastapi import FastAPI
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import httpx  # para llamadas a la API de Vertex AI

load_dotenv()

# Clave de API de Vertex AI
API_KEY = "AIzaSyAa6VPP3RlcL6Jsy72skb7l2KSIuvF9r80"  # agrega esta clave en tu .env

mcp = FastMCP()
app = FastAPI()

# ------------------------------- TOOLS -------------------------------

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
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_selector("h2:text('Avión más rápido')", timeout=40000)
            contenedor = page.locator("h2:text('Avión más rápido')").first.locator("..")
            hex_linea = await contenedor.locator("p:has-text('Hex:')").text_content()
            velocidad_linea = await contenedor.locator("p:has-text('Velocidad:')").text_content()
            hex_valor = hex_linea.split("Hex:")[-1].strip()
            velocidad_valor = velocidad_linea.split("Velocidad:")[-1].strip()
            return f"El avión más rápido en {region} es {hex_valor} con una velocidad de {velocidad_valor}."
    except PlaywrightTimeoutError:
        return f"No se encontró el bloque 'Avión más rápido' en la región {region}"
    except Exception as e:
        return f"Error al obtener el avión más rápido: {str(e)}"
    finally:
        if browser:
            await browser.close()


@mcp.tool()
async def explica_consumo_emisiones(pregunta: str) -> str:
    pregunta = pregunta.lower()
    if ("emisiones" in pregunta or "co2" in pregunta or "dioxido" in pregunta) and \
       ("consumo" in pregunta or "gasta" in pregunta or "combustible" in pregunta or "litros" in pregunta):
        return (
            "Para calcular el consumo de combustible y las emisiones de CO2, se estima la resistencia aerodinámica, "
            "el consumo específico (TSFC), y se multiplica por un factor de 3.16 para obtener el CO2."
        )
    if "emisiones" in pregunta or "co2" in pregunta or "dioxido" in pregunta:
        return (
            "Las emisiones de CO2 se estiman multiplicando el combustible quemado por un factor de 3.16."
        )
    if "consumo" in pregunta or "gasta" in pregunta or "combustible" in pregunta or "litros" in pregunta:
        return (
            "El consumo se calcula a partir de la resistencia aerodinámica y el TSFC del motor."
        )
    return (
        "Pregunta sobre consumo o emisiones para darte una explicación técnica."
    )


async def obtener_dato_vuelo(vuelo: str, selector: str, timeout=30000) -> str:
    vuelo = vuelo.strip().upper()
    url = f"https://es.flightaware.com/live/flight/{vuelo}"
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_selector(selector, timeout=timeout)
            texto = await page.locator(selector).first.text_content()
            return texto.strip() if texto else "desconocido"
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None
    finally:
        if browser:
            await browser.close()


@mcp.tool()
async def origenVuelo(vuelo: str) -> str:
    origen = await obtener_dato_vuelo(vuelo, ".flightPageSummaryCity")
    if origen is None:
        return f"No se pudo obtener el origen del vuelo {vuelo}."
    return f"Origen: {origen}"


@mcp.tool()
async def destinoVuelo(vuelo: str) -> str:
    destino = await obtener_dato_vuelo(vuelo, ".flightPageSummaryCity")
    if destino is None:
        return f"No se pudo obtener el destino del vuelo {vuelo}."
    return f"Destino: {destino}"


@mcp.tool()
async def trackVuelo(vuelo: str) -> str:
    vuelo = vuelo.strip().upper()
    url = f"https://es.flightaware.com/live/flight/{vuelo}"
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_selector(".flightPageSummaryCity", timeout=30000)
            await page.wait_for_selector(".destinationCity", timeout=30000)
            origen = await page.locator(".flightPageSummaryCity").first.text_content()
            destino = await page.locator(".destinationCity").first.text_content()
            return f"Origen: {origen.strip()} - Destino: {destino.strip()}"
    except Exception as e:
        return f"Error al obtener el track del vuelo: {str(e)}"
    finally:
        if browser:
            await browser.close()


@mcp.tool()
async def tiempoVuelo(vuelo: str) -> str:
    tiempo = await obtener_dato_vuelo(vuelo, ".flightPageProgressTotal strong")
    if tiempo is None:
        return f"No se pudo obtener el tiempo del vuelo {vuelo}."
    return f"Tiempo total de vuelo: {tiempo}"


# ------------------------------- VERTEX AI API KEY HTTP -------------------------------

async def gpt_response(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/chat-bison-001:generateText?key={API_KEY}"
    data = {
        "prompt": {"text": prompt},
        "temperature": 0.7,
        "maxOutputTokens": 500
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["output"].strip()
        except Exception as e:
            return f"Error al consultar Vertex AI: {str(e)}"


# ------------------------------- API /ask -------------------------------

class Query(BaseModel):
    prompt: str

@app.post("/ask")
async def ask(query: Query):
    prompt = query.prompt.lower()

    try:
        if "avion mas rapido" in prompt:
            for region in ["españa", "europa", "américa", "africa", "asia", "oceania"]:
                if region in prompt:
                    return {"response": await avion_mas_rapido(region.capitalize())}
            return {"response": "No se especificó una región válida."}
        elif "consumo" in prompt or "emisiones" in prompt:
            return {"response": await explica_consumo_emisiones(prompt)}
        elif "origen" in prompt:
            vuelo = prompt.split()[-1]
            return {"response": await origenVuelo(vuelo)}
        elif "destino" in prompt:
            vuelo = prompt.split()[-1]
            return {"response": await destinoVuelo(vuelo)}
        elif "track" in prompt or "ruta" in prompt:
            vuelo = prompt.split()[-1]
            return {"response": await trackVuelo(vuelo)}
        elif "tiempo" in prompt or "duración" in prompt:
            vuelo = prompt.split()[-1]
            return {"response": await tiempoVuelo(vuelo)}
        else:
            gpt_reply = await gpt_response(query.prompt)
            return {"response": gpt_reply}
    except Exception as e:
        return {"error": str(e)}


# ------------------------------- SERVIDOR -------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
