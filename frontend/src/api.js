import axios from "axios";

const request = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 600000
});

export function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request.post("/api/ocr/image", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
}