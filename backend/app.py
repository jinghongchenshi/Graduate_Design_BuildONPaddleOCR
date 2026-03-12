from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from services.ocr_service import OCRService
from utils.file_utils import ensure_dir, unique_filename

CONFIG_PATH = "config.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

upload_dir = ensure_dir(config["paths"]["upload_dir"])
result_dir = ensure_dir(config["paths"]["result_dir"])

ocr_service = OCRService(CONFIG_PATH)

app = FastAPI(title="OCR Web System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
app.mount("/results", StaticFiles(directory=result_dir), name="results")


@app.get("/api/health")
def health() -> dict:
    return {"code": 0, "message": "ok"}


@app.post("/api/ocr/image")
async def ocr_image(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise HTTPException(status_code=400, detail="不支持的图片格式")

    save_name = unique_filename(file.filename)
    save_path = upload_dir / save_name

    with open(save_path, "wb") as f:
        f.write(await file.read())

    vis_name = save_name.rsplit(".", 1)[0] + "_vis.png"
    vis_path = result_dir / vis_name

    result = ocr_service.run_ocr(str(save_path), str(vis_path))

    return {
        "code": 0,
        "message": "success",
        "data": {
            "image_url": f"/uploads/{save_name}",
            "vis_url": f"/results/{vis_name}" if result["vis_path"] else None,
            "texts": result["texts"],
        },
    }


@app.post("/api/model/reload")
def reload_model() -> dict:
    ocr_service.reload_model()
    return {"code": 0, "message": "模型已重新加载"}