from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

import httpx
import pandas as pd
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_TITLE = "Classificador de Tickets"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_title": APP_TITLE,
            "default_model": OLLAMA_MODEL,
        },
    )


def _load_dataframe(upload: UploadFile) -> pd.DataFrame:
    data = upload.file.read()
    filename = upload.filename or ""
    if filename.lower().endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(data))
    else:
        df = pd.read_csv(io.BytesIO(data), sep=None, engine="python")
    return df


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "numero do ticket": "ticket",
        "número do ticket": "ticket",
        "numero": "ticket",
        "descrição": "descricao",
        "descricao": "descricao",
        "data": "data",
        "autor": "autor",
    }
    normalized = {
        col: mapping.get(col.strip().lower(), col.strip().lower()) for col in df.columns
    }
    df = df.rename(columns=normalized)
    return df


def _validate_columns(df: pd.DataFrame) -> list[str]:
    required = {"ticket", "descricao", "data", "autor"}
    missing = sorted(required - set(df.columns))
    return missing


async def _classify_ticket(client: httpx.AsyncClient, row: dict[str, Any]) -> dict[str, str]:
    prompt = (
        "Você é um assistente de suporte que classifica tickets. "
        "Analise a descrição e responda apenas em JSON com as chaves "
        '"acao" e "grupo". '
        "A ação deve ser curta (ex: 'encaminhar para TI', 'prioridade alta', "
        "'responder com template', 'escalar para liderança'). "
        "O grupo deve ser um rótulo curto para agrupar tickets similares.\n\n"
        f"Ticket: {row.get('ticket')}\n"
        f"Descrição: {row.get('descricao')}\n"
        f"Data: {row.get('data')}\n"
        f"Autor: {row.get('autor')}\n"
    )
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return {"raw": data.get("response", "").strip()}


def _safe_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)


@app.post("/classificar", response_class=HTMLResponse)
async def classify(
    request: Request,
    arquivo: UploadFile = File(...),
    modelo: str = Form(OLLAMA_MODEL),
) -> HTMLResponse:
    global OLLAMA_MODEL
    OLLAMA_MODEL = modelo

    try:
        df = _load_dataframe(arquivo)
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "app_title": APP_TITLE,
                "default_model": OLLAMA_MODEL,
                "error": (
                    "Não foi possível ler o arquivo enviado. "
                    "Verifique se o CSV/XLSX está no formato correto. "
                    f"Detalhes: {exc}"
                ),
            },
        )
    df = _normalize_columns(df)
    missing = _validate_columns(df)
    if missing:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "app_title": APP_TITLE,
                "default_model": OLLAMA_MODEL,
                "error": f"Colunas obrigatórias ausentes: {', '.join(missing)}",
            },
        )

    df = df.fillna("")
    results = []
    async with httpx.AsyncClient() as client:
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            row_dict["data"] = _safe_date(row_dict.get("data"))
            result = await _classify_ticket(client, row_dict)
            results.append({**row_dict, **result})

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "app_title": APP_TITLE,
            "results": results,
            "total": len(results),
            "model": OLLAMA_MODEL,
        },
    )
