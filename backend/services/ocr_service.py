from __future__ import annotations

from typing import Any
import cv2
import yaml
import numpy as np
from paddleocr import PaddleOCR


class OCRService:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        self.cfg = self._load_config(config_path)
        self.ocr = self._build_ocr()

    def _load_config(self, config_path: str) -> dict[str, Any]:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _build_ocr(self) -> PaddleOCR:
        ocr_cfg = self.cfg["ocr"]
        return PaddleOCR(
            device=ocr_cfg["device"],
            lang=ocr_cfg["lang"],
            text_detection_model_name=ocr_cfg["text_detection_model_name"],
            text_detection_model_dir=ocr_cfg["text_detection_model_dir"],
            text_recognition_model_name=ocr_cfg["text_recognition_model_name"],
            text_recognition_model_dir=ocr_cfg["text_recognition_model_dir"],
            text_rec_input_shape=tuple(ocr_cfg["text_rec_input_shape"]),
            use_doc_orientation_classify=ocr_cfg["use_doc_orientation_classify"],
            use_doc_unwarping=ocr_cfg["use_doc_unwarping"],
            use_textline_orientation=ocr_cfg["use_textline_orientation"],
        )

    def reload_model(self) -> None:
        self.cfg = self._load_config(self.config_path)
        self.ocr = self._build_ocr()

    def _draw_boxes_only(self, image_path: str, boxes: list, vis_path: str) -> None:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        for box in boxes:
            pts = np.array(box, dtype=np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, (0, 255, 0), 2)

        cv2.imwrite(vis_path, img)

    def run_ocr(self, image_path: str, vis_path: str) -> dict[str, Any]:
        output = self.ocr.predict(image_path)

        if not output:
            return {
                "texts": [],
                "vis_path": None,
            }

        first = output[0]

        if hasattr(first, "to_dict"):
            data = first.to_dict()
        elif isinstance(first, dict):
            data = first
        else:
            try:
                data = dict(first)
            except Exception:
                raise ValueError(f"无法解析 OCR 输出类型: {type(first)}")

        if isinstance(data.get("res"), dict):
            data = data["res"]

        dt_polys = data.get("dt_polys", [])
        rec_texts = data.get("rec_texts", [])
        rec_scores = data.get("rec_scores", [])

        lines = []
        for i in range(min(len(dt_polys), len(rec_texts), len(rec_scores))):
            box = dt_polys[i].tolist() if hasattr(dt_polys[i], "tolist") else dt_polys[i]
            text = rec_texts[i]
            score = float(rec_scores[i])

            lines.append({
                "text": text,
                "score": score,
                "box": box,
            })

        if dt_polys is not None and len(dt_polys) > 0:
            boxes = [b.tolist() if hasattr(b, "tolist") else b for b in dt_polys]
            self._draw_boxes_only(image_path, boxes, vis_path)
            final_vis_path = vis_path
        else:
            final_vis_path = None

        return {
            "texts": lines,
            "vis_path": final_vis_path,
        }