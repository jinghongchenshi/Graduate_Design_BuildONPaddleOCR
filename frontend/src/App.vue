<template>
  <div class="page">
    <!-- 加载遮罩 -->
    <div v-if="loading" class="loading-mask">
      <div class="loading-card">
        <div class="spinner"></div>
        <div class="loading-title">正在识别，请稍候...</div>
        <div class="loading-desc">系统正在调用 OCR 模型处理图片</div>
      </div>
    </div>

    <header class="hero">
      <div>
        <h1>教材 OCR 识别系统</h1>
        <p class="subtitle">基于 PaddleOCR 的教材文本检测与识别网页演示系统</p>
      </div>
      <div class="hero-tags">
        <span class="tag">Vue 3</span>
        <span class="tag">FastAPI</span>
        <span class="tag">Det + Rec</span>
      </div>
    </header>

    <section class="info-cards">
      <div class="card small">
        <div class="card-title">当前文件</div>
        <div class="card-value">{{ fileName || "未选择" }}</div>
      </div>
      <div class="card small">
        <div class="card-title">识别行数</div>
        <div class="card-value">{{ texts.length }}</div>
      </div>
      <div class="card small">
        <div class="card-title">识别耗时</div>
        <div class="card-value">{{ elapsedText }}</div>
      </div>
      <div class="card small">
        <div class="card-title">当前模型</div>
        <div class="card-value">det_final_infer + rec_round6_infer</div>
      </div>
    </section>

    <section class="toolbar">
      <label class="file-btn" :class="{ disabled: loading }">
        选择图片
        <input type="file" accept="image/*" @change="handleFileChange" :disabled="loading" />
      </label>

      <button class="primary" @click="startOCR" :disabled="!file || loading">
        {{ loading ? "识别中..." : "开始识别" }}
      </button>

      <button class="secondary" @click="copyMergedText" :disabled="!texts.length || loading">
        复制文本
      </button>

      <button class="secondary" @click="exportTxt" :disabled="!texts.length || loading">
        导出 TXT
      </button>

      <button class="danger" @click="clearAll" :disabled="loading">
        清空
      </button>
    </section>

    <section class="content">
      <div class="panel">
        <div class="panel-header">
          <h2>原图</h2>
        </div>
        <div class="img-box">
          <img v-if="imagePreview" :src="imagePreview" class="preview" />
          <div v-else class="placeholder">请选择一张图片</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2>检测框可视化结果</h2>
        </div>
        <div class="img-box">
          <img v-if="visUrl" :src="backendBase + visUrl" class="preview" />
          <div v-else class="placeholder">
            {{ loading ? "正在生成可视化结果..." : "识别后这里显示检测框图" }}
          </div>
        </div>
      </div>
    </section>

    <section class="result-panel">
      <div class="panel-header">
        <h2>识别结果</h2>
      </div>

      <div class="merged-box">
        <div class="merged-header">合并文本</div>
        <textarea readonly :value="mergedText"></textarea>
      </div>

      <table v-if="texts.length">
        <thead>
          <tr>
            <th style="width: 80px;">序号</th>
            <th>文本</th>
            <th style="width: 120px;">置信度</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in texts" :key="index">
            <td>{{ index + 1 }}</td>
            <td>{{ item.text }}</td>
            <td>{{ Number(item.score).toFixed(4) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-else class="placeholder result-placeholder">暂无识别结果</div>
    </section>

    <section class="log-panel">
      <div class="panel-header">
        <h2>运行日志</h2>
      </div>
      <div class="log-box">
        <div v-for="(item, index) in logs" :key="index" class="log-item">
          {{ item }}
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { uploadImage } from "./api";

const backendBase = "http://127.0.0.1:8000";

const file = ref(null);
const fileName = ref("");
const imagePreview = ref("");
const visUrl = ref("");
const texts = ref([]);
const loading = ref(false);
const elapsedMs = ref(0);
const logs = ref(["系统已启动，请先选择图片。"]);

const mergedText = computed(() => {
  return texts.value.map(item => item.text).join("\n");
});

const elapsedText = computed(() => {
  if (!elapsedMs.value) return "-";
  return `${(elapsedMs.value / 1000).toFixed(2)} 秒`;
});

function addLog(message) {
  const time = new Date().toLocaleTimeString();
  logs.value.unshift(`[${time}] ${message}`);
}

function handleFileChange(event) {
  const selected = event.target.files[0];
  if (!selected) return;

  file.value = selected;
  fileName.value = selected.name;
  imagePreview.value = URL.createObjectURL(selected);
  visUrl.value = "";
  texts.value = [];
  elapsedMs.value = 0;

  addLog(`已选择图片：${selected.name}`);
}

function clearAll() {
  file.value = null;
  fileName.value = "";
  imagePreview.value = "";
  visUrl.value = "";
  texts.value = [];
  elapsedMs.value = 0;
  logs.value = ["已清空，等待下一次识别。"];
}

async function startOCR() {
  if (!file.value) {
    addLog("请先选择图片。");
    return;
  }

  loading.value = true;
  addLog("开始上传图片并执行 OCR 识别...");

  const start = performance.now();

  try {
    const res = await uploadImage(file.value);
    const data = res.data.data;

    visUrl.value = data.vis_url;
    texts.value = data.texts || [];
    elapsedMs.value = performance.now() - start;

    addLog(`识别完成，共识别出 ${texts.value.length} 行文本。`);
    addLog(`识别耗时：${(elapsedMs.value / 1000).toFixed(2)} 秒。`);
  } catch (error) {
    console.error(error);
    addLog("识别失败，请检查后端是否启动，或查看后端报错信息。");
  } finally {
    loading.value = false;
  }
}

async function copyMergedText() {
  if (!mergedText.value) return;

  try {
    await navigator.clipboard.writeText(mergedText.value);
    addLog("已复制识别文本到剪贴板。");
  } catch (error) {
    console.error(error);
    addLog("复制失败，可能是浏览器权限限制。");
  }
}

function exportTxt() {
  if (!mergedText.value) return;

  const blob = new Blob([mergedText.value], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  const baseName = fileName.value ? fileName.value.replace(/\.[^.]+$/, "") : "ocr_result";
  a.href = url;
  a.download = `${baseName}_ocr_result.txt`;
  a.click();

  URL.revokeObjectURL(url);
  addLog("已导出 TXT 结果文件。");
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 28px;
  font-family: "Microsoft YaHei", Arial, sans-serif;
  color: #1f2329;
  background: #f5f7fb;
  min-height: 100vh;
  position: relative;
}

.loading-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-card {
  width: 320px;
  background: #fff;
  border-radius: 18px;
  padding: 28px 24px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
  text-align: center;
}

.spinner {
  width: 52px;
  height: 52px;
  margin: 0 auto 18px;
  border: 5px solid #dbeafe;
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.loading-title {
  font-size: 20px;
  font-weight: 700;
  color: #1677ff;
  margin-bottom: 8px;
}

.loading-desc {
  color: #666;
  font-size: 14px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 28px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
  box-shadow: 0 8px 24px rgba(22, 119, 255, 0.08);
}

.hero h1 {
  margin: 0;
  font-size: 40px;
}

.subtitle {
  margin-top: 8px;
  color: #666;
  font-size: 15px;
}

.hero-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tag {
  padding: 8px 14px;
  background: #1677ff;
  color: #fff;
  border-radius: 999px;
  font-size: 13px;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
}

.card-title {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.card-value {
  font-size: 18px;
  font-weight: 700;
  word-break: break-word;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.file-btn {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #d9d9d9;
  cursor: pointer;
  min-width: 110px;
}

.file-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-btn input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

button {
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary {
  background: #1677ff;
  color: #fff;
}

.secondary {
  background: #f0f5ff;
  color: #1677ff;
  border: 1px solid #b7d3ff;
}

.danger {
  background: #fff1f0;
  color: #cf1322;
  border: 1px solid #ffb3b3;
}

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.panel,
.result-panel,
.log-panel {
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.panel-header h2 {
  margin: 0;
  font-size: 22px;
}

.img-box {
  min-height: 380px;
  border: 1px dashed #c8d1e0;
  border-radius: 12px;
  background: #fafcff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

.preview {
  max-width: 100%;
  max-height: 700px;
  display: block;
}

.placeholder {
  color: #8a94a6;
  padding: 20px;
  text-align: center;
}

.merged-box {
  margin-bottom: 18px;
}

.merged-header {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 8px;
}

.merged-box textarea {
  width: 100%;
  min-height: 130px;
  resize: vertical;
  border: 1px solid #d9d9d9;
  border-radius: 10px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.7;
  background: #fafafa;
}

.result-placeholder {
  padding: 24px 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}

th,
td {
  border: 1px solid #e5eaf3;
  padding: 12px;
  text-align: left;
  vertical-align: top;
}

th {
  background: #f7faff;
}

.log-box {
  min-height: 120px;
  max-height: 260px;
  overflow: auto;
  border: 1px solid #e5eaf3;
  border-radius: 12px;
  background: #fafafa;
  padding: 12px;
}

.log-item {
  padding: 6px 0;
  border-bottom: 1px dashed #e6e6e6;
  font-size: 14px;
}

.log-item:last-child {
  border-bottom: none;
}

@media (max-width: 960px) {
  .content,
  .info-cards {
    grid-template-columns: 1fr;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .hero h1 {
    font-size: 30px;
  }
}
</style>