import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import uvicorn

mcp = FastMCP()

@mcp.tool()
async def avion_mas_rapido(region: str) -> str:
    # Aqui pondrias tu scraping real
    return f"Simulando avión más rápido para {region}"

app = FastAPI()

class Query(BaseModel):
    prompt: str

@app.post("/ask")
async def ask(query: Query):
    response = await mcp.run_once(query.prompt)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
