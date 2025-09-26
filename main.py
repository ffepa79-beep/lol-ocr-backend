import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import easyocr
from rapidfuzz import process
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
reader = easyocr.Reader(['en'], gpu=False)

app = FastAPI()

def extrair_texto_da_imagem(file_path):
    resultado = reader.readtext(file_path, detail=0)
    return resultado

def buscar_no_banco(nome_extraido):
    dados = supabase.table("invocadores").select("nome").execute()
    nomes_banco = [item["nome"] for item in dados.data]
    match = process.extractOne(nome_extraido, nomes_banco, score_cutoff=80)
    if match:
        return {"nome": match[0], "confiança": match[1]}
    return None

@app.post("/verificar-nome/")
async def verificar_nome(file: UploadFile = File(...)):
    try:
        caminho = f"temp_{file.filename}"
        with open(caminho, "wb") as f:
            f.write(await file.read())

        textos = extrair_texto_da_imagem(caminho)
        resultados = []

        for texto in textos:
            match = buscar_no_banco(texto.lower().strip())
            resultados.append({"texto": texto, "match": match})

        os.remove(caminho)
        return JSONResponse(content={"resultados": resultados})
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)
