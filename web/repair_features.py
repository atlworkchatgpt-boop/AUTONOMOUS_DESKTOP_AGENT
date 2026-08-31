from __future__ import annotations
import base64, json, os, tempfile, uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from web.chess_service import list_history, get_history, analyze_history

router=APIRouter(prefix="/api/v2",tags=["repaired-features"])
ROOT=Path(__file__).resolve().parent.parent
UPLOAD=ROOT/"web"/"uploads"; GENERATED=ROOT/"web"/"static"/"generated"
UPLOAD.mkdir(parents=True,exist_ok=True); GENERATED.mkdir(parents=True,exist_ok=True)

def _key():
    k=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not k:raise HTTPException(503,"GEMINI_API_KEY is not configured.")
    return k

def _extract(path:Path)->str:
    ext=path.suffix.lower()
    try:
        if ext in {".txt",".md",".py",".js",".css",".html",".htm",".json",".csv",".log",".xml",".yaml",".yml"}:
            return path.read_text(encoding="utf-8",errors="replace")[:30000]
        if ext==".pdf":
            from pypdf import PdfReader
            return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)[:30000]
        if ext==".docx":
            from docx import Document
            return "\n".join(p.text for p in Document(str(path)).paragraphs)[:30000]
    except Exception as e:return f"[Could not extract text: {e}]"
    return ""

@router.post("/upload")
async def upload(file:UploadFile=File(...)):
    name=Path(file.filename or "upload.bin").name
    dest=UPLOAD/(uuid.uuid4().hex+"_"+name); dest.write_bytes(await file.read()); text=_extract(dest)
    return {"ok":True,"filename":name,"stored_as":dest.name,"text":text,"text_preview":text[:1500]}

@router.get("/chess/history")
async def chess_history():return {"ok":True,"games":list_history()}
@router.get("/chess/history/{game_id}")
async def chess_game(game_id:str):
    g=get_history(game_id)
    if not g:raise HTTPException(404,"Game not found")
    return {"ok":True,"game":g}
@router.get("/chess/analyze/{game_id}")
async def chess_analyze(game_id:str):
    x=analyze_history(game_id)
    if not x:raise HTTPException(404,"Game not found")
    return {"ok":True,**x}

class Prompt(BaseModel):prompt:str
@router.post("/image")
async def image(body:Prompt):
    prompt=(body.prompt or "").strip()
    if not prompt:raise HTTPException(400,"Image prompt is empty.")
    try:
        from google import genai
        from google.genai import types
        client=genai.Client(api_key=_key())
        response=client.models.generate_content(model="gemini-3.1-flash-image",contents=prompt,config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"]))
        image_data=None
        for cand in response.candidates or []:
            for part in getattr(getattr(cand,"content",None),"parts",[]) or []:
                inline=getattr(part,"inline_data",None)
                if inline and getattr(inline,"data",None):image_data=inline.data;break
            if image_data:break
        if not image_data:raise RuntimeError("No image returned by Gemini.")
        out=GENERATED/("image_"+uuid.uuid4().hex+".png")
        out.write_bytes(base64.b64decode(image_data) if isinstance(image_data,str) else bytes(image_data))
        return {"ok":True,"url":"/static/generated/"+out.name}
    except HTTPException:raise
    except Exception as e:raise HTTPException(500,"Image generation failed: "+str(e))

@router.post("/video")
async def video(body:Prompt):
    prompt=(body.prompt or "").strip()
    if not prompt:raise HTTPException(400,"Video prompt is empty.")
    try:
        from google import genai
        client=genai.Client(api_key=_key())
        op=client.models.generate_videos(model="veo-3.1-generate-preview",prompt=prompt)
        name=getattr(op,"name",None)
        if not name:raise RuntimeError("Video operation name missing.")
        return {"ok":True,"operation_id":str(name)}
    except HTTPException:raise
    except Exception as e:raise HTTPException(500,"Video generation failed: "+str(e))

@router.get("/video/status/{operation_id:path}")
async def video_status(operation_id:str):
    try:
        from google import genai
        from google.genai import types
        client=genai.Client(api_key=_key())
        op=types.GenerateVideosOperation(name=operation_id)
        op=client.operations.get(op)
        if not getattr(op,"done",False):return {"status":"processing"}
        if getattr(op,"error",None):return {"status":"failed","error":str(op.error)}
        videos=getattr(getattr(op,"response",None),"generated_videos",None) or []
        if not videos:raise RuntimeError("Completed operation returned no video.")
        out=GENERATED/("video_"+uuid.uuid4().hex+".mp4")
        client.files.download(file=videos[0].video,destination=str(out))
        return {"status":"completed","url":"/static/generated/"+out.name}
    except HTTPException:raise
    except Exception as e:raise HTTPException(500,"Video status failed: "+str(e))
