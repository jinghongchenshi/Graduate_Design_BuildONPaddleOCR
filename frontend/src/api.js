import axios from "axios";

const request = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 600000
});

export function uploadImage(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);

  return request.post("/api/ocr/image", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress: (event) => {
      if (!event.total) return;
      const percent = Math.round((event.loaded * 100) / event.total);
      if (typeof onProgress === "function") {
        onProgress(percent);
      }
    }
  });
}

export function getModelInfo() {
  return request.get("/api/model/info");
}

export function getModelOptions() {
  return request.get("/api/model/options");
}

export function selectModel(modelId) {
  return request.post("/api/model/select", {
    model_id: modelId
  });
}
