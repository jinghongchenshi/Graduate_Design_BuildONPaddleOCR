<template>
  <div class="page">
    <div class="bg bg1"></div>
    <div class="bg bg2"></div>
    <div class="bg bg3"></div>

    <!-- 加载遮罩 -->
    <div v-if="loading" class="loading-mask">
      <div class="loading-card glass">
        <div class="spinner"></div>
        <div class="loading-title">
          {{ uploadPercent < 100 ? "正在上传图片..." : "正在识别，请稍候..." }}
        </div>
        <div class="loading-desc">
          {{
            uploadPercent < 100
              ? `上传进度：${uploadPercent}%`
              : "系统正在调用 OCR 模型处理图片"
          }}
        </div>
        <div class="progress-wrap">
          <div class="progress-bar" :style="{ width: `${progressDisplay}%` }"></div>
        </div>
      </div>
    </div>

    <header class="hero glass">
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

    <!-- 顶部紧凑操作栏 -->
    <div ref="topBarAnchorRef" class="top-bar-anchor"></div>
    <div
      v-if="isTopBarPinned"
      class="top-bar-placeholder"
      :style="{ height: `${topBarHeight}px` }"
    ></div>
    <section
      ref="topBarRef"
      class="top-bar glass"
      :class="{ pinned: isTopBarPinned, compact: isTopBarPinned }"
    >
      <div class="left-actions">
        <label
          for="ocr-file-input"
          class="file-btn"
          :class="{ disabled: loading, selected: !!fileName }"
          :title="fileName || '未选择文件'"
          :data-filename="fileName || '未选择文件'"
        >
          <span class="file-btn-main">{{ fileName ? "更换图片" : "选择图片" }}</span>
          <span class="file-btn-sub">{{ fileName ? "已选择文件" : "未选择文件" }}</span>
        </label>

        <input
          id="ocr-file-input"
          ref="fileInputRef"
          class="hidden-file-input"
          type="file"
          accept="image/*"
          @change="handleFileChange"
          :disabled="loading"
        />

        <button class="primary" @click="startOCR" :disabled="!file || loading">
          {{ loading ? "识别中..." : "开始识别" }}
        </button>

        <button class="secondary" @click="copyMergedText" :disabled="!filteredTexts.length || loading">
          复制文本
        </button>

        <button class="secondary" @click="exportTxt" :disabled="!filteredTexts.length || loading">
          导出 TXT
        </button>

        <button class="danger" @click="clearAll" :disabled="loading">
          清空
        </button>
      </div>

      <div class="right-controls">
        <div class="threshold-card">
          <div class="threshold-label">
            <span>置信度阈值</span>
            <strong>{{ confidenceThreshold.toFixed(2) }}</strong>
          </div>
          <input
            v-model.number="confidenceThreshold"
            type="range"
            min="0"
            max="1"
            step="0.01"
            class="threshold-slider"
          />
        </div>
      </div>
    </section>

    <section class="stats-row">
      <div class="stat-card glass">
        <div class="stat-label">当前文件</div>
        <div class="stat-value">{{ fileName || "未选择" }}</div>
      </div>
      <div class="stat-card glass">
        <div class="stat-label">原始行数</div>
        <div class="stat-value">{{ texts.length }}</div>
      </div>
      <div class="stat-card glass">
        <div class="stat-label">当前显示</div>
        <div class="stat-value">{{ filteredTexts.length }}</div>
      </div>
      <div class="stat-card glass">
        <div class="stat-label">当前状态</div>
        <div class="stat-value">{{ statusText }}</div>
      </div>
    </section>

    <section class="viewer-grid">
      <!-- 原图 -->
      <div class="panel glass">
        <div class="panel-header">
          <h2>原图</h2>
          <div v-if="imagePreview" class="viewer-tools">
            <button class="tool-btn" @click="changeZoom('src', -0.1)">－</button>
            <span class="zoom-badge">Zoom: {{ Math.round(srcZoom * 100) }}%</span>
            <button class="tool-btn" @click="changeZoom('src', 0.1)">＋</button>
            <button class="tool-btn reset-btn" @click="resetZoom('src')">复位</button>
          </div>
        </div>

        <div
          ref="srcShellRef"
          class="canvas-shell"
          :class="{ pannable: !!imagePreview, panning: panState.active && panState.kind === 'src' }"
          @wheel.prevent="handleWheelZoom('src', $event)"
          @mousedown="startPan('src', $event)"
        >
          <!-- 空状态 -->
          <div
            v-if="!imagePreview"
            class="empty-upload-zone"
            :class="{ dragover: dragActive, disabled: loading }"
            @click="triggerFileSelect"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <div class="empty-upload-icon">🖼️</div>
            <div class="empty-upload-title">拖拽图片到这里也可以上传</div>
            <div class="empty-upload-desc">
              支持 JPG / PNG / BMP / WEBP，也支持直接截图后按 <strong>Ctrl + V</strong> 粘贴图片
            </div>
            <div class="empty-upload-action">{{ loading ? "处理中..." : "点击选择图片" }}</div>

            <div v-if="loading" class="progress-wrap inline-progress zone-progress">
              <div class="progress-bar" :style="{ width: `${progressDisplay}%` }"></div>
            </div>
          </div>

          <!-- 有图状态 -->
          <div
            v-else
            class="stage"
            :style="getStageStyle('src')"
          >
            <img
              ref="srcImgRef"
              :src="imagePreview"
              class="stage-img"
              @load="handleImageLoad('src')"
              draggable="false"
            />
          </div>
        </div>
      </div>

      <!-- 可视化结果 -->
      <div class="panel glass">
        <div class="panel-header">
          <h2>检测结果</h2>
          <div class="viewer-tools">
            <button
              v-if="visUrl"
              class="tool-btn"
              @click="changeZoom('vis', -0.1)"
            >
              －
            </button>
            <span v-if="visUrl" class="zoom-badge">Zoom: {{ Math.round(visZoom * 100) }}%</span>
            <button
              v-if="visUrl"
              class="tool-btn"
              @click="changeZoom('vis', 0.1)"
            >
              ＋
            </button>
            <button
              v-if="visUrl"
              class="tool-btn reset-btn"
              @click="resetZoom('vis')"
            >
              复位
            </button>
            <button
              v-if="visUrl && texts.length"
              class="mini-btn"
              @click="toggleOverlayText"
            >
              {{ showOverlayText ? "隐藏框中文字" : "显示框中文字" }}
            </button>
          </div>
        </div>

        <div
          ref="visShellRef"
          class="canvas-shell"
          :class="{ pannable: !!visUrl, panning: panState.active && panState.kind === 'vis' }"
          @wheel.prevent="handleWheelZoom('vis', $event)"
          @mousedown="startPan('vis', $event)"
        >
          <div
            v-if="visUrl"
            class="stage"
            :style="getStageStyle('vis')"
          >
            <img
              ref="visImgRef"
              :src="backendBase + visUrl"
              class="stage-img"
              @load="handleImageLoad('vis')"
              draggable="false"
            />

            <!-- 可鼠标划取复制的文字层 -->
            <div
              v-if="showOverlayText && visMeta.baseWidth > 0 && reviewItems.length"
              class="ocr-overlay"
              :style="{
                width: `${visMeta.baseWidth * visZoom}px`,
                height: `${visMeta.baseHeight * visZoom}px`
              }"
            >
              <div
                v-for="item in reviewItems"
                :key="item._filteredIndex"
                class="selectable-box"
                :class="[
                  getScoreClass(item.score),
                  { active: hoveredResultIndex === item._filteredIndex || focusedResultIndex === item._filteredIndex }
                ]"
                :style="getOverlayStyle(item.box)"
                :title="item.text"
                @mouseenter="hoveredResultIndex = item._filteredIndex"
                @mouseleave="hoveredResultIndex = null"
                @click.stop="focusResult(item._filteredIndex, { scrollCanvas: true, scrollTable: true })"
              >
                {{ item.text }}
              </div>
            </div>
          </div>

          <div v-else class="placeholder large-placeholder">
            {{ loading ? "正在生成可视化结果..." : "识别后这里显示检测框图" }}
          </div>
        </div>
      </div>
    </section>

    <section class="mini-stats-row">
      <div class="mini-card glass">
        <div class="mini-label">平均置信度</div>
        <div class="mini-value">{{ avgScoreText }}</div>
      </div>
      <div class="mini-card glass">
        <div class="mini-label">最高置信度</div>
        <div class="mini-value">{{ maxScoreText }}</div>
      </div>
      <div class="mini-card glass">
        <div class="mini-label">低于阈值行数</div>
        <div class="mini-value">{{ lowScoreCount }}</div>
      </div>
      <div class="mini-card glass">
        <div class="mini-label">当前模型</div>
        <div class="mini-value small-model">det_final_infer + rec_round6_infer</div>
      </div>
    </section>

    <!-- 标签页：让页面更紧凑 -->
    <section class="tabs-bar glass">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'result' }"
        @click="activeTab = 'result'"
      >
        识别结果
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'log' }"
        @click="activeTab = 'log'"
      >
        运行日志
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'model' }"
        @click="activeTab = 'model'"
      >
        模型说明
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'about' }"
        @click="activeTab = 'about'"
      >
        系统说明
      </button>
    </section>

    <section class="tab-panel glass">
      <!-- 识别结果 -->
      <template v-if="activeTab === 'result'">
        <div class="result-top">
          <div class="result-tip" :class="resultTipClass">
            {{ resultTipText }}
          </div>

          <div class="review-filter-bar">
            <button
              class="mini-filter-btn"
              :class="{ active: reviewFilterMode === 'all' }"
              @click="reviewFilterMode = 'all'"
            >
              全部结果
            </button>
            <button
              class="mini-filter-btn"
              :class="{ active: reviewFilterMode === 'low' }"
              @click="reviewFilterMode = 'low'"
            >
              仅低置信度
            </button>

            <div class="low-nav-group">
              <button
                class="mini-nav-btn"
                @click="focusPrevLowConfidence"
                :disabled="!lowConfidenceFilteredIndexes.length"
              >
                上一个低置信度
              </button>
              <button
                class="mini-nav-btn"
                @click="focusNextLowConfidence"
                :disabled="!lowConfidenceFilteredIndexes.length"
              >
                下一个低置信度
              </button>
            </div>

            <span class="review-filter-count">
              当前审阅 {{ reviewItems.length }} / {{ filteredTexts.length }}
            </span>

            <span class="review-filter-count">
              {{
                lowConfidenceFilteredIndexes.length
                  ? `低置信度导航 ${currentLowConfidenceNavIndex >= 0 ? currentLowConfidenceNavIndex + 1 : 0} / ${lowConfidenceFilteredIndexes.length}`
                  : '当前无低置信度结果'
              }}
            </span>
          </div>

          <div class="merged-box">
            <div class="merged-header">
              <span>合并文本</span>
              <span class="sub-tip">当前按阈值过滤后的文本结果</span>
            </div>
            <textarea readonly :value="mergedText"></textarea>
          </div>
        </div>

        <div class="table-wrap" v-if="reviewItems.length">
          <table>
            <thead>
              <tr>
                <th style="width: 80px;">序号</th>
                <th>文本</th>
                <th style="width: 120px;">置信度</th>
                <th style="width: 120px;">质量判断</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, reviewIndex) in reviewItems"
                :key="item._filteredIndex"
                :ref="el => setResultRowRef(el, item._filteredIndex)"
                :class="[
                  getScoreClass(item.score),
                  { active: hoveredResultIndex === item._filteredIndex || focusedResultIndex === item._filteredIndex }
                ]"
                @mouseenter="hoveredResultIndex = item._filteredIndex"
                @mouseleave="hoveredResultIndex = null"
                @click="focusResult(item._filteredIndex, { scrollCanvas: true, scrollTable: false })"
              >
                <td>{{ reviewIndex + 1 }}</td>
                <td>{{ item.text }}</td>
                <td>{{ Number(item.score).toFixed(4) }}</td>
                <td>
                  <span class="score-badge" :class="getScoreClass(item.score)">
                    {{ getScoreLabel(item.score) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="placeholder result-placeholder">
          当前审阅模式下暂无可显示结果
        </div>
      </template>

      <!-- 日志 -->
      <template v-else-if="activeTab === 'log'">
        <div class="log-box">
          <div v-for="(item, index) in logs" :key="index" class="log-item">
            {{ item }}
          </div>
        </div>
      </template>

      <!-- 模型说明 -->
      <template v-else-if="activeTab === 'model'">
        <div class="model-desc">
          <p><strong>检测模型：</strong>PP-OCRv5_mobile_det 微调版</p>
          <p><strong>识别模型：</strong>PP-OCRv5_mobile_rec 微调版</p>
          <p><strong>部署方式：</strong>FastAPI + Vue 前后端分离</p>
          <p><strong>适用场景：</strong>教材页面、截图文字、单行文字、表格类文本的检测与识别演示</p>
          <p><strong>前端增强：</strong>支持拖拽上传、Ctrl+V 粘贴、缩放查看、阈值过滤、框中文字显示/隐藏。</p>
        </div>
      </template>

      <!-- 系统说明 -->
      <template v-else>
        <div class="footer-desc">
          本系统用于演示教材场景下的 OCR 文本检测与识别流程。用户可上传图片，系统将调用后端模型完成检测与识别，并返回可视化结果与文本内容。
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from "vue";
import { uploadImage } from "./api";

const backendBase = "http://127.0.0.1:8000";
const LOW_CONFIDENCE_CUTOFF = 0.6;

const file = ref(null);
const fileName = ref("");
const imagePreview = ref("");
const visUrl = ref("");
const texts = ref([]);
const loading = ref(false);
const elapsedMs = ref(0);
const logs = ref(["系统已启动，请先选择图片。"]);
const uploadPercent = ref(0);
const dragActive = ref(false);
const showOverlayText = ref(true);

const confidenceThreshold = ref(0.3);
const activeTab = ref("result");
const hoveredResultIndex = ref(null);
const focusedResultIndex = ref(null);
const resultRowRefs = ref([]);
const reviewFilterMode = ref("all"); // all | low

const fileInputRef = ref(null);
const topBarRef = ref(null);
const topBarAnchorRef = ref(null);
const isTopBarPinned = ref(false);
const topBarHeight = ref(0);
const topBarPinStart = ref(0);

const srcShellRef = ref(null);
const visShellRef = ref(null);
const srcImgRef = ref(null);
const visImgRef = ref(null);

const srcZoom = ref(1);
const visZoom = ref(1);

const srcMeta = ref({
  naturalWidth: 0,
  naturalHeight: 0,
  baseWidth: 0,
  baseHeight: 0
});

const visMeta = ref({
  naturalWidth: 0,
  naturalHeight: 0,
  baseWidth: 0,
  baseHeight: 0
});

const panState = ref({
  active: false,
  kind: "",
  startX: 0,
  startY: 0,
  scrollLeft: 0,
  scrollTop: 0
});

let currentObjectUrl = "";

const filteredTexts = computed(() => {
  return texts.value.filter(item => Number(item.score || 0) >= confidenceThreshold.value);
});

const reviewItems = computed(() => {
  const base = filteredTexts.value.map((item, index) => ({
    ...item,
    _filteredIndex: index
  }));

  if (reviewFilterMode.value === "low") {
    return base.filter(item => Number(item.score || 0) < LOW_CONFIDENCE_CUTOFF);
  }

  return base;
});

const lowConfidenceFilteredIndexes = computed(() => {
  return filteredTexts.value
    .map((item, index) => (Number(item.score || 0) < LOW_CONFIDENCE_CUTOFF ? index : null))
    .filter(index => index !== null);
});

const currentLowConfidenceNavIndex = computed(() => {
  return lowConfidenceFilteredIndexes.value.indexOf(focusedResultIndex.value);
});

const mergedText = computed(() => {
  return filteredTexts.value.map(item => item.text).join("\n");
});

const elapsedText = computed(() => {
  if (!elapsedMs.value) return "-";
  return `${(elapsedMs.value / 1000).toFixed(2)} 秒`;
});

const statusText = computed(() => {
  if (loading.value) return uploadPercent.value < 100 ? "上传中" : "识别中";
  if (!file.value) return "待上传";
  if (file.value && !texts.value.length) return "待识别";
  return "已完成";
});

const avgScore = computed(() => {
  if (!filteredTexts.value.length) return 0;
  const total = filteredTexts.value.reduce((sum, item) => sum + Number(item.score || 0), 0);
  return total / filteredTexts.value.length;
});

const avgScoreText = computed(() => {
  if (!filteredTexts.value.length) return "-";
  return avgScore.value.toFixed(4);
});

const maxScoreText = computed(() => {
  if (!filteredTexts.value.length) return "-";
  const max = Math.max(...filteredTexts.value.map(item => Number(item.score || 0)));
  return max.toFixed(4);
});

const lowScoreCount = computed(() => {
  return texts.value.filter(item => Number(item.score || 0) < confidenceThreshold.value).length;
});

const progressDisplay = computed(() => {
  if (!loading.value) return 0;
  return uploadPercent.value < 100 ? uploadPercent.value : 100;
});

const resultTipText = computed(() => {
  if (!file.value) return "请先上传图片。";
  if (texts.value.length === 0 && !loading.value) return "当前已选择图片，但尚未执行识别。";
  if (texts.value.length > 0 && filteredTexts.value.length === 0) {
    return "当前阈值过高，结果已被全部过滤。可适当降低阈值。";
  }
  if (avgScore.value > 0 && avgScore.value < LOW_CONFIDENCE_CUTOFF) {
    return "当前识别结果整体置信度较低，建议更换更清晰的图片或继续优化模型。";
  }
  return "当前识别流程运行正常，已成功返回文本结果。";
});

const resultTipClass = computed(() => {
  if (!file.value) return "neutral";
  if (texts.value.length > 0 && filteredTexts.value.length === 0) return "warning";
  if (avgScore.value > 0 && avgScore.value < LOW_CONFIDENCE_CUTOFF) return "warning";
  return "success";
});

function addLog(message) {
  const time = new Date().toLocaleTimeString();
  logs.value.unshift(`[${time}] ${message}`);
}

function triggerFileSelect() {
  if (loading.value) return;
  fileInputRef.value?.click();
}

function setSelectedFile(selected) {
  if (!selected) return;

  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = "";
  }

  file.value = selected;
  fileName.value = selected.name || "粘贴图片.png";
  imagePreview.value = URL.createObjectURL(selected);
  currentObjectUrl = imagePreview.value;

  visUrl.value = "";
  texts.value = [];
  elapsedMs.value = 0;
  uploadPercent.value = 0;
  showOverlayText.value = true;
  focusedResultIndex.value = null;
  hoveredResultIndex.value = null;
  resultRowRefs.value = [];
  reviewFilterMode.value = "all";

  srcZoom.value = 1;
  visZoom.value = 1;

  srcMeta.value = { naturalWidth: 0, naturalHeight: 0, baseWidth: 0, baseHeight: 0 };
  visMeta.value = { naturalWidth: 0, naturalHeight: 0, baseWidth: 0, baseHeight: 0 };

  addLog(`已选择图片：${fileName.value}`);
}

function handleFileChange(event) {
  const selected = event.target.files[0];
  setSelectedFile(selected);
}

function handleDragOver() {
  if (loading.value) return;
  dragActive.value = true;
}

function handleDragLeave() {
  dragActive.value = false;
}

function handleDrop(event) {
  if (loading.value) return;
  dragActive.value = false;

  const dropped = event.dataTransfer.files[0];
  if (dropped) setSelectedFile(dropped);
}

function handlePaste(event) {
  if (loading.value) return;

  const items = event.clipboardData?.items || [];
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const pastedFile = item.getAsFile();
      if (pastedFile) {
        const ext = pastedFile.type.includes("png") ? ".png" : ".jpg";
        const wrappedFile = new File([pastedFile], `paste_image${ext}`, {
          type: pastedFile.type
        });
        setSelectedFile(wrappedFile);
        addLog("已通过剪贴板粘贴图片。");
        break;
      }
    }
  }
}

function clearAll() {
  file.value = null;
  fileName.value = "";
  visUrl.value = "";
  texts.value = [];
  elapsedMs.value = 0;
  uploadPercent.value = 0;
  dragActive.value = false;
  showOverlayText.value = true;
  focusedResultIndex.value = null;
  hoveredResultIndex.value = null;
  resultRowRefs.value = [];
  reviewFilterMode.value = "all";

  srcZoom.value = 1;
  visZoom.value = 1;

  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = "";
  }
  imagePreview.value = "";

  srcMeta.value = { naturalWidth: 0, naturalHeight: 0, baseWidth: 0, baseHeight: 0 };
  visMeta.value = { naturalWidth: 0, naturalHeight: 0, baseWidth: 0, baseHeight: 0 };

  logs.value = ["已清空，等待下一次识别。"];

  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
}

async function startOCR() {
  if (!file.value) {
    addLog("请先选择图片。");
    return;
  }

  loading.value = true;
  uploadPercent.value = 0;
  activeTab.value = "result";
  addLog("开始上传图片并执行 OCR 识别...");

  const start = performance.now();

  try {
    const res = await uploadImage(file.value, (percent) => {
      uploadPercent.value = percent;
    });

    const data = res.data.data;
    visUrl.value = data.vis_url;
    texts.value = data.texts || [];
    elapsedMs.value = performance.now() - start;
    uploadPercent.value = 100;
    focusedResultIndex.value = null;
    hoveredResultIndex.value = null;
    resultRowRefs.value = [];
    reviewFilterMode.value = "all";

    await nextTick();
    setTimeout(() => fitToShell("vis"), 30);

    addLog(`识别完成，共识别出 ${texts.value.length} 行文本。`);
    addLog(`识别耗时：${(elapsedMs.value / 1000).toFixed(2)} 秒。`);

    if (texts.value.length === 0) {
      addLog("未检测到有效文本。");
    } else if (filteredTexts.value.length === 0) {
      addLog("当前阈值下暂无可显示结果。");
    } else if (avgScore.value < LOW_CONFIDENCE_CUTOFF) {
      addLog("当前识别结果整体置信度较低。");
    }
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

function toggleOverlayText() {
  showOverlayText.value = !showOverlayText.value;
  addLog(showOverlayText.value ? "已显示检测框文字层。" : "已隐藏检测框文字层。");
}

function getScoreLabel(score) {
  const s = Number(score || 0);
  if (s >= 0.9) return "高";
  if (s >= LOW_CONFIDENCE_CUTOFF) return "中";
  return "低";
}

function getScoreClass(score) {
  const s = Number(score || 0);
  if (s >= 0.9) return "high";
  if (s >= LOW_CONFIDENCE_CUTOFF) return "mid";
  return "low";
}

function focusLowConfidenceByOffset(step = 1) {
  const indexes = lowConfidenceFilteredIndexes.value;
  if (!indexes.length) return;

  const currentPos = indexes.indexOf(focusedResultIndex.value);
  let targetPos = 0;

  if (currentPos === -1) {
    targetPos = step > 0 ? 0 : indexes.length - 1;
  } else {
    targetPos = (currentPos + step + indexes.length) % indexes.length;
  }

  focusResult(indexes[targetPos], { scrollCanvas: true, scrollTable: true });
}

function focusNextLowConfidence() {
  focusLowConfidenceByOffset(1);
}

function focusPrevLowConfidence() {
  focusLowConfidenceByOffset(-1);
}

function getShell(kind) {
  return kind === "src" ? srcShellRef.value : visShellRef.value;
}

function startPan(kind, event) {
  if (event.button !== 0) return;
  const shell = getShell(kind);
  if (!shell) return;
  if (event.target.closest(".selectable-box")) return;

  panState.value = {
    active: true,
    kind,
    startX: event.clientX,
    startY: event.clientY,
    scrollLeft: shell.scrollLeft,
    scrollTop: shell.scrollTop
  };

  document.body.style.userSelect = "none";
}

function handlePanMove(event) {
  if (!panState.value.active) return;
  const shell = getShell(panState.value.kind);
  if (!shell) return;

  const dx = event.clientX - panState.value.startX;
  const dy = event.clientY - panState.value.startY;

  shell.scrollLeft = panState.value.scrollLeft - dx;
  shell.scrollTop = panState.value.scrollTop - dy;
}

function endPan() {
  if (!panState.value.active) return;
  panState.value.active = false;
  document.body.style.userSelect = "";
}

function changeZoom(kind, delta) {
  const { shell, meta, zoomRef } = getShellAndMeta(kind);
  const prevZoom = zoomRef.value;
  const nextZoom = clampZoom(prevZoom + delta);

  if (nextZoom === prevZoom) return;

  if (!shell || !meta.baseWidth || !meta.baseHeight) {
    zoomRef.value = nextZoom;
    return;
  }

  const centerX = shell.scrollLeft + shell.clientWidth / 2;
  const centerY = shell.scrollTop + shell.clientHeight / 2;
  const ratio = nextZoom / prevZoom;

  zoomRef.value = nextZoom;

  nextTick(() => {
    shell.scrollLeft = Math.max(centerX * ratio - shell.clientWidth / 2, 0);
    shell.scrollTop = Math.max(centerY * ratio - shell.clientHeight / 2, 0);
  });
}

function resetZoom(kind) {
  const { zoomRef } = getShellAndMeta(kind);
  zoomRef.value = 1;

  nextTick(() => {
    centerStage(kind);
  });
}

function clampZoom(value) {
  return Math.min(4, Math.max(0.3, Number(value.toFixed(2))));
}

function handleWheelZoom(kind, event) {
  const delta = event.deltaY < 0 ? 0.08 : -0.08;
  changeZoom(kind, delta);
}

function handleImageLoad(kind) {
  const img = kind === "src" ? srcImgRef.value : visImgRef.value;
  if (!img) return;

  const meta = kind === "src" ? srcMeta : visMeta;
  meta.value.naturalWidth = img.naturalWidth || 0;
  meta.value.naturalHeight = img.naturalHeight || 0;

  fitToShell(kind);
}

function fitToShell(kind) {
  const shell = kind === "src" ? srcShellRef.value : visShellRef.value;
  const meta = kind === "src" ? srcMeta : visMeta;

  if (!shell || !meta.value.naturalWidth || !meta.value.naturalHeight) return;

  const maxW = Math.max(shell.clientWidth - 24, 80);
  const maxH = Math.max(shell.clientHeight - 24, 80);
  const ratio = Math.min(
    maxW / meta.value.naturalWidth,
    maxH / meta.value.naturalHeight,
    1
  );

  meta.value.baseWidth = Math.round(meta.value.naturalWidth * ratio);
  meta.value.baseHeight = Math.round(meta.value.naturalHeight * ratio);

  if (
    kind === "vis" &&
    srcMeta.value.baseWidth > 0 &&
    srcMeta.value.baseHeight > 0
  ) {
    meta.value.baseWidth = srcMeta.value.baseWidth;
    meta.value.baseHeight = srcMeta.value.baseHeight;
  }

  nextTick(() => {
    centerStage(kind);
  });
}

function getShellAndMeta(kind) {
  return kind === "src"
    ? {
        shell: srcShellRef.value,
        meta: srcMeta.value,
        zoomRef: srcZoom
      }
    : {
        shell: visShellRef.value,
        meta: visMeta.value,
        zoomRef: visZoom
      };
}

function centerStage(kind) {
  const { shell, meta, zoomRef } = getShellAndMeta(kind);
  if (!shell || !meta.baseWidth || !meta.baseHeight) return;

  const stageW = meta.baseWidth * zoomRef.value;
  const stageH = meta.baseHeight * zoomRef.value;

  shell.scrollLeft = Math.max((stageW - shell.clientWidth) / 2, 0);
  shell.scrollTop = Math.max((stageH - shell.clientHeight) / 2, 0);
}

function getStageStyle(kind) {
  const meta = kind === "src" ? srcMeta.value : visMeta.value;
  const zoom = kind === "src" ? srcZoom.value : visZoom.value;

  if (!meta.baseWidth || !meta.baseHeight) return {};

  return {
    width: `${meta.baseWidth * zoom}px`,
    height: `${meta.baseHeight * zoom}px`
  };
}

function getOverlayStyle(box) {
  if (!Array.isArray(box) || box.length === 0) return {};

  const points = box.map(p => ({
    x: Number(p[0]),
    y: Number(p[1])
  }));

  const minX = Math.min(...points.map(p => p.x));
  const maxX = Math.max(...points.map(p => p.x));
  const minY = Math.min(...points.map(p => p.y));
  const maxY = Math.max(...points.map(p => p.y));

  const stageWidth = visMeta.value.baseWidth * visZoom.value;
  const stageHeight = visMeta.value.baseHeight * visZoom.value;

  const scaleX = visMeta.value.naturalWidth ? stageWidth / visMeta.value.naturalWidth : 1;
  const scaleY = visMeta.value.naturalHeight ? stageHeight / visMeta.value.naturalHeight : 1;

  const width = Math.max((maxX - minX) * scaleX, 18);
  const height = Math.max((maxY - minY) * scaleY, 16);
  const fontSize = Math.max(Math.min(height * 0.62, 18), 10);

  return {
    left: `${minX * scaleX}px`,
    top: `${minY * scaleY}px`,
    width: `${width}px`,
    minHeight: `${height}px`,
    fontSize: `${fontSize}px`
  };
}

function getBoxBounds(box) {
  if (!Array.isArray(box) || box.length === 0) return null;

  const points = box.map(p => ({ x: Number(p[0]), y: Number(p[1]) }));
  return {
    minX: Math.min(...points.map(p => p.x)),
    maxX: Math.max(...points.map(p => p.x)),
    minY: Math.min(...points.map(p => p.y)),
    maxY: Math.max(...points.map(p => p.y))
  };
}

function setResultRowRef(el, index) {
  if (el) resultRowRefs.value[index] = el;
}

function focusResult(index, options = {}) {
  const { scrollCanvas = true, scrollTable = true } = options;
  const item = filteredTexts.value[index];
  if (!item) return;

  focusedResultIndex.value = index;

  if (scrollCanvas) {
    const shell = visShellRef.value;
    const bounds = getBoxBounds(item.box);
    if (shell && bounds && visMeta.value.naturalWidth && visMeta.value.naturalHeight) {
      const stageWidth = visMeta.value.baseWidth * visZoom.value;
      const stageHeight = visMeta.value.baseHeight * visZoom.value;
      const scaleX = stageWidth / visMeta.value.naturalWidth;
      const scaleY = stageHeight / visMeta.value.naturalHeight;

      const centerX = ((bounds.minX + bounds.maxX) / 2) * scaleX;
      const centerY = ((bounds.minY + bounds.maxY) / 2) * scaleY;

      shell.scrollTo({
        left: Math.max(centerX - shell.clientWidth / 2, 0),
        top: Math.max(centerY - shell.clientHeight / 2, 0),
        behavior: "smooth"
      });
    }
  }

  if (scrollTable) {
    const row = resultRowRefs.value[index];
    if (row && typeof row.scrollIntoView === "function") {
      row.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }
}

function updateTopBarMetrics() {
  const anchor = topBarAnchorRef.value;
  const bar = topBarRef.value;
  if (!anchor || !bar) return;

  const anchorRect = anchor.getBoundingClientRect();
  topBarPinStart.value = window.scrollY + anchorRect.top;
  topBarHeight.value = bar.offsetHeight;
}

function updateTopBarPin() {
  if (!topBarRef.value) return;
  const threshold = Math.max(topBarPinStart.value - 10, 0);
  isTopBarPinned.value = window.scrollY > threshold;
}

function handleResize() {
  fitToShell("src");
  fitToShell("vis");
  nextTick(() => {
    updateTopBarMetrics();
    updateTopBarPin();
  });
}

onMounted(() => {
  window.addEventListener("paste", handlePaste);
  window.addEventListener("resize", handleResize);
  window.addEventListener("scroll", updateTopBarPin, { passive: true });
  window.addEventListener("mousemove", handlePanMove);
  window.addEventListener("mouseup", endPan);

  nextTick(() => {
    updateTopBarMetrics();
    updateTopBarPin();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("paste", handlePaste);
  window.removeEventListener("resize", handleResize);
  window.removeEventListener("scroll", updateTopBarPin);
  window.removeEventListener("mousemove", handlePanMove);
  window.removeEventListener("mouseup", endPan);

  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
  }
});
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.page {
  position: relative;
  min-height: 100vh;
  padding: 18px;
  max-width: 1380px;
  margin: 0 auto;
  color: #14213d;
  font-family: "Microsoft YaHei", Arial, sans-serif;
  overflow-x: hidden;
}

.bg {
  position: fixed;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.28;
}

.bg1 {
  width: 260px;
  height: 260px;
  background: #7c3aed;
  top: -60px;
  left: -40px;
}

.bg2 {
  width: 320px;
  height: 320px;
  background: #38bdf8;
  top: 160px;
  right: -80px;
}

.bg3 {
  width: 280px;
  height: 280px;
  background: #22c55e;
  bottom: -80px;
  left: 30%;
}

.glass {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.64);
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow: 0 10px 24px rgba(31, 38, 135, 0.10);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.loading-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.26);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-card {
  width: 340px;
  border-radius: 22px;
  padding: 28px 24px;
  text-align: center;
}

.spinner {
  width: 56px;
  height: 56px;
  margin: 0 auto 18px;
  border: 5px solid rgba(59, 130, 246, 0.18);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.loading-title {
  font-size: 20px;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 8px;
}

.loading-desc {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 14px;
}

.progress-wrap {
  width: 100%;
  height: 10px;
  background: rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  overflow-x: hidden;
}

.inline-progress {
  margin-top: 14px;
}

.zone-progress {
  width: 260px;
  max-width: 80%;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #7c3aed, #06b6d4);
  border-radius: 999px;
  transition: width 0.25s ease;
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
  margin-bottom: 14px;
  padding: 18px 22px;
  border-radius: 22px;
  z-index: 1;
}

.hero h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0.5px;
}

.subtitle {
  margin-top: 6px;
  color: #475569;
  font-size: 14px;
}

.hero-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tag {
  padding: 8px 14px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  font-size: 13px;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.2);
}

.top-bar-anchor {
  width: 100%;
  height: 1px;
}

.top-bar {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 14px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 18px;
  margin-bottom: 14px;
  width: 100%;
  box-shadow: 0 12px 28px rgba(31, 38, 135, 0.16);
  transition: padding 0.22s ease, border-radius 0.22s ease, box-shadow 0.22s ease, opacity 0.22s ease;
  will-change: transform, opacity;
}

.top-bar.pinned {
  position: fixed;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: min(1380px, calc(100vw - 36px));
  z-index: 999;
  box-shadow: 0 18px 38px rgba(31, 38, 135, 0.20);
  animation: topBarSlideIn 0.22s ease;
}

.top-bar.compact {
  padding-top: 10px;
  padding-bottom: 10px;
  border-radius: 16px;
}

.top-bar.compact .file-btn {
  min-width: 120px;
  padding: 8px 14px;
  border-radius: 12px;
}

.top-bar.compact .file-btn-main {
  font-size: 13px;
}

.top-bar.compact .file-btn-sub {
  margin-top: 2px;
  font-size: 11px;
}

.top-bar.compact button {
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 14px;
}

.top-bar.compact .left-actions {
  gap: 8px;
}

.top-bar.compact .threshold-card {
  padding: 8px 10px;
  border-radius: 12px;
}

.top-bar.compact .threshold-label {
  font-size: 12px;
  margin-bottom: 6px;
}

.top-bar.compact .right-controls {
  align-items: center;
}

.top-bar-placeholder {
  width: 100%;
  margin-bottom: 14px;
}

@keyframes topBarSlideIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.left-actions {
  display: flex;
  gap: 10px;
  align-items: stretch;
  flex-wrap: wrap;
}

.right-controls {
  display: flex;
  justify-content: flex-end;
}

.threshold-card {
  width: 100%;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.threshold-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
  color: #475569;
}

.threshold-slider {
  width: 100%;
  cursor: pointer;
}

.file-btn {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  min-width: 132px;
  padding: 10px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.8);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  cursor: pointer !important;
  overflow: visible;
}

.file-btn:hover:not(.disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 26px rgba(37, 99, 235, 0.16);
  background: rgba(255, 255, 255, 0.92);
}

.file-btn:hover::after {
  content: attr(data-filename);
  position: absolute;
  left: 50%;
  top: calc(100% + 8px);
  transform: translateX(-50%);
  max-width: 320px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.92);
  color: #fff;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.22);
  z-index: 1200;
  pointer-events: none;
}

.file-btn:active:not(.disabled) {
  transform: scale(0.98);
}

.file-btn.selected {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.9), rgba(243, 232, 255, 0.9));
  border-color: rgba(96, 165, 250, 0.65);
}

.file-btn,
.file-btn * {
  cursor: pointer !important;
  user-select: none;
}

.file-btn.disabled,
.file-btn.disabled * {
  cursor: not-allowed !important;
  opacity: 0.6;
}

.hidden-file-input {
  position: fixed;
  left: -9999px;
  top: -9999px;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.file-btn-main {
  font-weight: 700;
  color: #1e3a8a;
  font-size: 14px;
}

.file-btn-sub {
  margin-top: 3px;
  font-size: 12px;
  color: #64748b;
}

button {
  padding: 10px 16px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary {
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.22);
}

.secondary {
  color: #2563eb;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(147, 197, 253, 0.9);
}

.danger {
  color: #dc2626;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(252, 165, 165, 0.9);
}

.stats-row,
.mini-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 14px;
  position: relative;
  z-index: 1;
}

.stat-card,
.mini-card {
  padding: 14px 16px;
  border-radius: 18px;
}

.stat-label,
.mini-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  word-break: break-word;
}

.mini-value {
  font-size: 17px;
  font-weight: 700;
  word-break: break-word;
}

.small-model {
  font-size: 14px;
  line-height: 1.5;
}

.viewer-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
  position: relative;
  z-index: 1;
  align-items: start;
}

.panel,
.tabs-bar,
.tab-panel {
  position: relative;
  z-index: 1;
}

.panel {
  border-radius: 22px;
  padding: 16px;
  min-width: 0;
  overflow-x: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
}

.viewer-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tool-btn {
  padding: 6px 10px;
  border-radius: 10px;
  font-size: 13px;
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(191, 219, 254, 0.9);
  color: #2563eb;
}

.reset-btn {
  color: #334155;
}

.zoom-badge {
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(255,255,255,0.74);
  border: 1px solid rgba(226, 232, 240, 0.9);
  font-size: 13px;
  color: #334155;
}

.mini-btn {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(191, 219, 254, 0.9);
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
}

.canvas-shell {
  height: 430px;
  width: 100%;
  min-width: 0;
  overflow: auto;
  border: 1px dashed rgba(148, 163, 184, 0.45);
  border-radius: 16px;
  background: rgba(255,255,255,0.24);
  padding: 10px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.canvas-shell.pannable,
.canvas-shell.pannable .stage-img {
  cursor: grab;
}

.canvas-shell.panning,
.canvas-shell.panning .stage-img {
  cursor: grabbing;
}

.empty-upload-zone {
  width: 100%;
  height: 100%;
  border-radius: 16px;
  border: 1.5px dashed rgba(125, 147, 191, 0.45);
  background: radial-gradient(circle at top left, rgba(255,255,255,0.55), rgba(255,255,255,0.22));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 28px;
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease, background 0.22s ease;
}

.empty-upload-zone:hover:not(.disabled) {
  transform: translateY(-4px) scale(1.01);
  border-color: rgba(59, 130, 246, 0.65);
  box-shadow: 0 18px 36px rgba(59, 130, 246, 0.12);
  background: radial-gradient(circle at top left, rgba(255,255,255,0.78), rgba(235,245,255,0.42));
}

.empty-upload-zone.dragover {
  transform: scale(1.015);
  border-color: rgba(37, 99, 235, 0.78);
  box-shadow: 0 18px 40px rgba(37, 99, 235, 0.18);
}

.empty-upload-zone.disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.empty-upload-icon {
  font-size: 44px;
  margin-bottom: 12px;
  transition: transform 0.22s ease;
}

.empty-upload-zone:hover:not(.disabled) .empty-upload-icon {
  transform: translateY(-4px) scale(1.08);
}

.empty-upload-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e3a8a;
  margin-bottom: 8px;
}

.empty-upload-desc {
  font-size: 15px;
  line-height: 1.8;
  color: #64748b;
  max-width: 640px;
}

.empty-upload-action {
  margin-top: 16px;
  padding: 10px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
}

.stage {
  position: relative;
  line-height: 0;
  flex: none;
  margin: auto;
}

.stage-img {
  width: 100%;
  height: 100%;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
  border-radius: 10px;
}

.large-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.ocr-overlay {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
}

.selectable-box {
  position: absolute;
  pointer-events: auto;
  user-select: text;
  -webkit-user-select: text;
  cursor: text;
  padding: 1px 4px;
  border-radius: 6px;
  border: 1px dashed rgba(59, 130, 246, 0.45);
  background: rgba(255, 255, 255, 0.52);
  color: #0f172a;
  overflow-x: hidden;
  white-space: nowrap;
  line-height: 1.15;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.selectable-box.high {
  border-color: rgba(34, 197, 94, 0.95);
  background: rgba(240, 253, 244, 0.82);
}

.selectable-box.mid {
  border-color: rgba(234, 179, 8, 0.95);
  background: rgba(254, 249, 195, 0.82);
}

.selectable-box.low {
  border-color: rgba(239, 68, 68, 0.95);
  background: rgba(254, 226, 226, 0.82);
}

.selectable-box.active {
  border-color: rgba(37, 99, 235, 0.95);
  background: rgba(219, 234, 254, 0.88);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.18);
}

.tabs-bar {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 16px;
  margin-bottom: 10px;
}

.tab-btn {
  padding: 10px 16px;
  border-radius: 12px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(203, 213, 225, 0.9);
  color: #475569;
}

.tab-btn.active {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.2);
}

.tab-panel {
  min-height: 320px;
  max-height: 430px;
  border-radius: 22px;
  padding: 16px;
  overflow: auto;
}

.result-top {
  margin-bottom: 12px;
}

.result-tip {
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 12px;
}

.result-tip.neutral {
  background: rgba(248, 250, 252, 0.86);
  color: #475569;
}

.result-tip.warning {
  background: rgba(255, 247, 230, 0.85);
  color: #ad6800;
  border: 1px solid rgba(255, 213, 145, 0.85);
}

.result-tip.success {
  background: rgba(246, 255, 237, 0.86);
  color: #389e0d;
  border: 1px solid rgba(183, 235, 143, 0.85);
}

.review-filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.mini-filter-btn {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(203, 213, 225, 0.9);
  color: #475569;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.mini-filter-btn.active {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 8px 16px rgba(37, 99, 235, 0.18);
}

.low-nav-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.mini-nav-btn {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(203, 213, 225, 0.9);
  color: #475569;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.review-filter-count {
  font-size: 13px;
  color: #64748b;
}

.merged-box {
  margin-bottom: 12px;
}

.merged-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
  flex-wrap: wrap;
}

.sub-tip {
  color: #64748b;
  font-size: 13px;
}

.merged-box textarea {
  width: 100%;
  min-height: 110px;
  resize: vertical;
  border: 1px solid rgba(203, 213, 225, 0.9);
  border-radius: 14px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.7;
  background: rgba(255, 255, 255, 0.62);
}

.table-wrap {
  max-height: 220px;
  overflow: auto;
  border-radius: 14px;
}

.table-wrap tbody tr {
  cursor: pointer;
  transition: background 0.16s ease, box-shadow 0.16s ease;
}

.table-wrap tbody tr:hover {
  background: rgba(37, 99, 235, 0.08);
}

.table-wrap tbody tr.active {
  background: rgba(37, 99, 235, 0.14);
}

.table-wrap tbody tr.high td:first-child {
  box-shadow: inset 4px 0 0 rgba(34, 197, 94, 0.95);
}

.table-wrap tbody tr.mid td:first-child {
  box-shadow: inset 4px 0 0 rgba(234, 179, 8, 0.95);
}

.table-wrap tbody tr.low td:first-child {
  box-shadow: inset 4px 0 0 rgba(239, 68, 68, 0.95);
}

table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.58);
  border-radius: 14px;
  overflow-x: hidden;
}

th,
td {
  border: 1px solid rgba(226, 232, 240, 0.9);
  padding: 12px;
  text-align: left;
  vertical-align: top;
}

th {
  background: rgba(239, 246, 255, 0.92);
}

tbody tr {
  transition: background 0.15s ease;
}

tbody tr.active {
  background: rgba(219, 234, 254, 0.62);
}

.placeholder {
  color: #64748b;
  padding: 20px;
  text-align: center;
}

.result-placeholder {
  padding: 20px 0;
}

.score-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.score-badge.high {
  background: rgba(240, 253, 244, 0.95);
  color: #15803d;
}

.score-badge.mid {
  background: rgba(254, 249, 195, 0.95);
  color: #a16207;
}

.score-badge.low {
  background: rgba(254, 226, 226, 0.95);
  color: #dc2626;
}

.log-box {
  min-height: 260px;
  max-height: 360px;
  overflow: auto;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.42);
  padding: 12px;
}

.log-item {
  padding: 6px 0;
  border-bottom: 1px dashed rgba(203, 213, 225, 0.85);
  font-size: 14px;
}

.log-item:last-child {
  border-bottom: none;
}

.model-desc p,
.footer-desc {
  margin: 8px 0;
  line-height: 1.8;
  color: #334155;
}

@media (max-width: 1080px) {
  .top-bar {
    grid-template-columns: 1fr;
  }

  .viewer-grid,
  .stats-row,
  .mini-stats-row {
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