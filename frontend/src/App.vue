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

    <div v-if="showHelpModal" class="help-modal-mask" @click="closeHelpModal">
      <div class="help-modal glass" @click.stop>
        <div class="help-modal-header">
          <div>
            <h3>使用帮助</h3>
            <p>快捷键、鼠标操作与复核说明</p>
          </div>
          <button class="help-close-btn" @click="closeHelpModal">×</button>
        </div>

        <div class="help-modal-body">
          <div class="help-section">
            <h4>快捷键操作</h4>
            <div class="help-kbd-grid">
              <div class="help-kbd-item"><kbd>A</kbd><span>上一条结果（全部结果导航）</span></div>
              <div class="help-kbd-item"><kbd>D</kbd><span>下一条结果（全部结果导航）</span></div>
              <div class="help-kbd-item"><kbd>Z</kbd><span>上一个低置信度</span></div>
              <div class="help-kbd-item"><kbd>C</kbd><span>下一个低置信度</span></div>
              <div class="help-kbd-item"><kbd>J</kbd><span>上一个需复核</span></div>
              <div class="help-kbd-item"><kbd>L</kbd><span>下一个需复核</span></div>
              <div class="help-kbd-item"><kbd>1</kbd><span>标记为未检查</span></div>
              <div class="help-kbd-item"><kbd>2</kbd><span>标记为已检查</span></div>
              <div class="help-kbd-item"><kbd>3</kbd><span>标记为需复核</span></div>
              <div class="help-kbd-item"><kbd>Q</kbd><span>切换到全部结果</span></div>
              <div class="help-kbd-item"><kbd>F</kbd><span>切换到仅低置信度</span></div>
              <div class="help-kbd-item"><kbd>T</kbd><span>切换到仅高置信度</span></div>
              <div class="help-kbd-item"><kbd>W</kbd><span>切换到仅未检查</span></div>
              <div class="help-kbd-item"><kbd>E</kbd><span>切换到仅需复核</span></div>
              <div class="help-kbd-item"><kbd>R</kbd><span>复位右侧检测结果缩放</span></div>
              <div class="help-kbd-item"><kbd>Esc</kbd><span>关闭帮助浮窗</span></div>
            </div>
          </div>

          <div class="help-section">
            <h4>鼠标操作</h4>
            <ul class="help-list">
              <li><strong>Ctrl + 左键</strong>：增选或取消选中单条记录。</li>
              <li><strong>Shift + 左键</strong>：按当前列表顺序连续多选一段记录。</li>
              <li>点击表格中的某一行，可自动定位到右侧对应检测框。</li>
              <li>点击右侧检测框中的文字，也会联动高亮表格中的对应结果。</li>
              <li>滚轮可对图片进行缩放，双击图片区域可快速复位。</li>
              <li>按住左键拖动画布，可查看放大后的细节区域。</li>
              <li>支持拖拽图片上传，也支持截图后按 <strong>Ctrl + V</strong> 粘贴图片。</li>
            </ul>
          </div>

          <div class="help-section">
            <h4>复核说明</h4>
            <ul class="help-list">
              <li>可将结果标记为 <strong>未检查</strong>、<strong>已检查</strong>、<strong>需复核</strong>。</li>
              <li>支持按筛选模式查看：全部、仅低置信度、仅高置信度、仅未检查、仅需复核。</li>
              <li>导出 CSV 时会一并导出当前结果的检查状态。</li>
              <li>支持对“当前筛选结果”进行批量标记。</li>
              <li>同一图片的复核状态会自动保存在本地，重新打开后会尝试恢复。</li>
            </ul>
          </div>

          <div class="help-section">
            <h4>使用建议</h4>
            <ul class="help-list">
              <li>先用低置信度筛选快速检查明显问题，再切换到全部结果做整体复核。</li>
              <li>遇到可疑结果可先标记为“需复核”，最后统一通过需复核导航处理。</li>
              <li>若识别效果较差，可尝试更清晰的截图或优化后端模型。</li>
            </ul>
          </div>
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
        >
          <span class="file-btn-main">{{ fileName ? "更换图片" : "选择图片" }}</span>
          <span class="file-btn-sub">{{ fileName ? "已选择文件" : "未选择文件" }}</span>
          <span class="file-hover-name">{{ fileName || "未选择文件" }}</span>
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

        <button class="secondary" @click="exportCsv" :disabled="!reviewItems.length || loading">
          导出 CSV
        </button>

        <button class="secondary help-trigger-btn" @click="openHelpModal">
          帮助
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

        <div class="canvas-frame">
          <div v-if="srcZoomToast" class="zoom-toast">
            {{ Math.round(srcZoom * 100) }}%
          </div>

          <div
            ref="srcShellRef"
            class="canvas-shell"
            :class="{ pannable: !!imagePreview, panning: panState.active && panState.kind === 'src' }"
            @wheel.prevent="handleWheelZoom('src', $event)"
            @mousedown="startPan('src', $event)"
            @dblclick.stop.prevent="imagePreview && resetZoom('src')"
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

        <div class="canvas-frame">
          <div v-if="visZoomToast" class="zoom-toast">
            {{ Math.round(visZoom * 100) }}%
          </div>

          <div
            ref="visShellRef"
            class="canvas-shell"
            :class="{ pannable: !!visUrl, panning: panState.active && panState.kind === 'vis' }"
            @wheel.prevent="handleWheelZoom('vis', $event)"
            @mousedown="startPan('vis', $event)"
            @dblclick.stop.prevent="visUrl && resetZoom('vis')"
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
                    { 
                      selected: isResultSelected(item._filteredIndex),
                      active: hoveredResultIndex === item._filteredIndex || focusedResultIndex === item._filteredIndex 
                    }
                  ]"
                  :style="getOverlayStyle(item.box)"
                  :title="item.text"
                  @mouseenter="hoveredResultIndex = item._filteredIndex"
                  @mouseleave="hoveredResultIndex = null"
                  @click.stop="handleResultSelection(item._filteredIndex, $event, { scrollCanvas: true, scrollTable: true })"
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
        <div class="mini-value small-model">{{ modelSummaryText }}</div>
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

          <div class="summary-strip">
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">总识别</span>
              <strong>{{ texts.length }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">阈值后显示</span>
              <strong>{{ filteredTexts.length }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">当前审阅</span>
              <strong>
                {{ reviewItems.length ? `${currentReviewNavIndex >= 0 ? currentReviewNavIndex + 1 : 0} / ${reviewItems.length}` : "0 / 0" }}
              </strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">低置信度</span>
              <strong>{{ lowConfidenceFilteredIndexes.length }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">未检查</span>
              <strong>{{ uncheckedCount }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">需复核</span>
              <strong>{{ needsReviewCount }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">已修正</span>
              <strong>{{ editedCount }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">平均置信度</span>
              <strong>{{ avgScoreText }}</strong>
            </div>
            <div class="summary-chip glass-lite">
              <span class="summary-chip-label">审阅模式</span>
              <strong>
                {{
                  reviewFilterMode === "low"
                    ? "仅低置信度"
                    : reviewFilterMode === "high"
                    ? "仅高置信度"
                    : reviewFilterMode === "unchecked"
                    ? "仅未检查"
                    : reviewFilterMode === "needsReview"
                    ? "仅需复核"
                    : "全部结果"
                }}
              </strong>
            </div>
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
            <button
              class="mini-filter-btn"
              :class="{ active: reviewFilterMode === 'high' }"
              @click="reviewFilterMode = 'high'"
            >
              仅高置信度
            </button>
            <button
              class="mini-filter-btn"
              :class="{ active: reviewFilterMode === 'unchecked' }"
              @click="reviewFilterMode = 'unchecked'"
            >
              仅未检查
            </button>
            <button
              class="mini-filter-btn"
              :class="{ active: reviewFilterMode === 'needsReview' }"
              @click="reviewFilterMode = 'needsReview'"
            >
              仅需复核
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

            <div class="low-nav-group">
              <button
                class="mini-nav-btn"
                @click="focusPrevNeedsReview"
                :disabled="!needsReviewFilteredIndexes.length"
              >
                上一个需复核
              </button>
              <button
                class="mini-nav-btn"
                @click="focusNextNeedsReview"
                :disabled="!needsReviewFilteredIndexes.length"
              >
                下一个需复核
              </button>
            </div>

            <span class="review-filter-count">
              当前审阅 {{ currentReviewNavIndex >= 0 ? currentReviewNavIndex + 1 : 0 }} / {{ reviewItems.length }}
            </span>

            <span class="review-filter-count">
              {{
                lowConfidenceFilteredIndexes.length
                  ? `低置信度导航 ${currentLowConfidenceNavIndex >= 0 ? currentLowConfidenceNavIndex + 1 : 0} / ${lowConfidenceFilteredIndexes.length}`
                  : '当前无低置信度结果'
              }}
            </span>

            <span class="review-filter-count">
              {{
                needsReviewFilteredIndexes.length
                  ? `需复核导航 ${currentNeedsReviewNavIndex >= 0 ? currentNeedsReviewNavIndex + 1 : 0} / ${needsReviewFilteredIndexes.length}`
                  : '当前无需复核结果'
              }}
            </span>

            <div class="shortcut-tip">
              快捷键：A/D 上一条/下一条　Z/C 上下低置信度　J/L 上下需复核　1 未检查　2 已检查　3 需复核　Q 全部　F 仅低置信度　T 仅高置信度　W 仅未检查　E 仅需复核　R 复位右图。支持 Ctrl/Shift + 左键多选，批量操作优先作用于选中项。
            </div>
          </div>

          <div class="batch-review-bar glass-lite">
            <div class="batch-review-info">
              <span class="batch-review-title">批量操作</span>
              <span class="batch-review-desc">
                {{
                  selectedReviewItems.length
                    ? `当前已选中 ${selectedReviewItems.length} 条，批量操作将优先作用于选中项`
                    : `当前未选中记录，默认对当前筛选结果 ${reviewItems.length} 条生效`
                }}
              </span>
            </div>

            <div class="batch-review-actions">
              <button
                class="batch-action-btn"
                @click="applyBulkReviewStatus('unchecked')"
                :disabled="!effectiveBulkItems.length"
              >
                批量标记为未检查
              </button>
              <button
                class="batch-action-btn"
                @click="applyBulkReviewStatus('checked')"
                :disabled="!effectiveBulkItems.length"
              >
                批量标记为已检查
              </button>
              <button
                class="batch-action-btn danger-batch"
                @click="applyBulkReviewStatus('needsReview')"
                :disabled="!effectiveBulkItems.length"
              >
                批量标记为需复核
              </button>
              <button
                class="batch-action-btn"
                @click="clearSelectedResults"
                :disabled="!selectedResultIndexes.length"
              >
                清空选中
              </button>
            </div>
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
                <th>原始文本</th>
                <th>复核修正</th>
                <th style="width: 120px;">置信度</th>
                <th style="width: 120px;">质量判断</th>
                <th style="width: 120px;">检查状态</th>
                <th style="width: 280px;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, reviewIndex) in reviewItems"
                :key="item._filteredIndex"
                :ref="el => setResultRowRef(el, item._filteredIndex)"
                :class="[
                  getScoreClass(item.score),
                  {
                    selected: isResultSelected(item._filteredIndex),
                    active: hoveredResultIndex === item._filteredIndex || focusedResultIndex === item._filteredIndex
                  }
                ]"
                @mouseenter="hoveredResultIndex = item._filteredIndex"
                @mouseleave="hoveredResultIndex = null"
                @click="handleResultSelection(item._filteredIndex, $event, { scrollCanvas: true, scrollTable: false })"
              >
                <td>{{ reviewIndex + 1 }}</td>
                <td>
                  <div class="raw-text-cell">{{ item.text }}</div>
                </td>
                <td>
                  <div class="edit-cell">
                    <textarea
                      class="review-edit-input"
                      :value="getEditedText(item._textIndex)"
                      placeholder="输入复核后的文本；留空时默认使用原始识别结果"
                      @click.stop
                      @input="setEditedText(item._textIndex, $event.target.value)"
                    ></textarea>
                    <div class="edit-cell-meta">
                      <span
                        class="edit-indicator"
                        :class="{ edited: isTextEdited(item._textIndex, item.text) }"
                      >
                        {{ isTextEdited(item._textIndex, item.text) ? "已修正" : "未修正" }}
                      </span>
                      <button
                        class="inline-link-btn"
                        @click.stop="resetEditedText(item._textIndex)"
                        :disabled="!getEditedText(item._textIndex)"
                      >
                        恢复原文
                      </button>
                    </div>
                  </div>
                </td>
                <td>{{ Number(item.score).toFixed(4) }}</td>
                <td>
                  <span class="score-badge" :class="getScoreClass(item.score)">
                    {{ getScoreLabel(item.score) }}
                  </span>
                </td>
                <td>
                  <span class="review-badge" :class="getReviewStatusClass(item._textIndex)">
                    {{ getReviewStatusLabel(item._textIndex) }}
                  </span>
                </td>
                <td>
                  <div class="review-actions">
                    <button
                      class="status-action-btn"
                      :class="{ active: getReviewStatus(item._textIndex) === 'unchecked' }"
                      @click.stop="setReviewStatus(item._textIndex, 'unchecked')"
                    >
                      未检查
                    </button>
                    <button
                      class="status-action-btn"
                      :class="{ active: getReviewStatus(item._textIndex) === 'checked' }"
                      @click.stop="setReviewStatus(item._textIndex, 'checked')"
                    >
                      已检查
                    </button>
                    <button
                      class="status-action-btn"
                      :class="{ active: getReviewStatus(item._textIndex) === 'needsReview' }"
                      @click.stop="setReviewStatus(item._textIndex, 'needsReview')"
                    >
                      需复核
                    </button>
                  </div>
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
          <p><strong>检测模型：</strong>{{ currentModel.det_model_name }}</p>
          <p><strong>检测目录：</strong>{{ currentModel.det_model_dir }}</p>
          <p><strong>识别模型：</strong>{{ currentModel.rec_model_name }}</p>
          <p><strong>识别目录：</strong>{{ currentModel.rec_model_dir }}</p>
          <p><strong>运行设备：</strong>{{ currentModel.device }}</p>
          <p><strong>语言：</strong>{{ currentModel.lang }}</p>
          <p><strong>识别输入尺寸：</strong>{{ modelShapeText }}</p>
          <p><strong>部署方式：</strong>FastAPI + Vue 前后端分离</p>
          <p><strong>适用场景：</strong>教材页面、截图文字、单行文字、表格类文本的检测与识别演示</p>
          <p>
            <strong>方向增强：</strong>
            文档方向分类 {{ currentModel.use_doc_orientation_classify ? "开启" : "关闭" }}，
            文档矫正 {{ currentModel.use_doc_unwarping ? "开启" : "关闭" }}，
            文本行方向 {{ currentModel.use_textline_orientation ? "开启" : "关闭" }}。
          </p>
          <p><strong>前端增强：</strong>支持拖拽上传、Ctrl+V 粘贴、缩放查看、阈值过滤、框中文字显示/隐藏、复核修正编辑。</p>
          <p v-if="modelInfoLoading"><strong>模型状态：</strong>正在同步后端模型信息...</p>
          <p v-else-if="modelInfoError"><strong>模型状态：</strong>{{ modelInfoError }}</p>
          <p v-else><strong>模型状态：</strong>已与后端配置同步。</p>
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
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { uploadImage, getModelInfo } from "./api";

const backendBase = "http://127.0.0.1:8000";
const LOW_CONFIDENCE_CUTOFF = 0.6;
const MODEL_INFO_REFRESH_MS = 15000;

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
const showHelpModal = ref(false);

const confidenceThreshold = ref(0.3);
const activeTab = ref("result");
const hoveredResultIndex = ref(null);
const focusedResultIndex = ref(null);
const resultRowRefs = ref([]);
const reviewFilterMode = ref("all"); // all | low | high | unchecked | needsReview
const reviewStatusMap = ref({});
const reviewEditMap = ref({});
const modelInfoLoading = ref(false);
const modelInfoError = ref("");
const currentModel = ref({
  device: "-",
  lang: "-",
  det_model_name: "-",
  det_model_dir: "-",
  rec_model_name: "-",
  rec_model_dir: "-",
  text_rec_input_shape: [],
  use_doc_orientation_classify: false,
  use_doc_unwarping: false,
  use_textline_orientation: false
});

const selectedResultIndexes = ref([]);
const selectionAnchorIndex = ref(null);

const reviewStorageKey = computed(() => {
  if (!file.value) return "";
  return `ocr-review-state::${file.value.name}::${file.value.size}::${file.value.lastModified || 0}`;
});

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

const srcZoomToast = ref(false);
const visZoomToast = ref(false);

let srcZoomToastTimer = null;
let visZoomToastTimer = null;

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
let modelInfoTimer = null;

const filteredTexts = computed(() => {
  return texts.value
    .map((item, index) => ({
      ...item,
      _textIndex: index
    }))
    .filter(item => Number(item.score || 0) >= confidenceThreshold.value);
});

const reviewItems = computed(() => {
  const base = filteredTexts.value.map((item, index) => ({
    ...item,
    _filteredIndex: index
  }));

  if (reviewFilterMode.value === "low") {
    return base.filter(item => Number(item.score || 0) < LOW_CONFIDENCE_CUTOFF);
  }

  if (reviewFilterMode.value === "high") {
    return base.filter(item => Number(item.score || 0) >= 0.9);
  }

  if (reviewFilterMode.value === "unchecked") {
    return base.filter(item => getReviewStatus(item._textIndex) === "unchecked");
  }

  if (reviewFilterMode.value === "needsReview") {
    return base.filter(item => getReviewStatus(item._textIndex) === "needsReview");
  }

  return base;
});

const lowConfidenceFilteredIndexes = computed(() => {
  return filteredTexts.value
    .map((item, index) => (Number(item.score || 0) < LOW_CONFIDENCE_CUTOFF ? index : null))
    .filter(index => index !== null);
});

const highConfidenceFilteredIndexes = computed(() => {
  return filteredTexts.value
    .map((item, index) => (Number(item.score || 0) >= 0.9 ? index : null))
    .filter(index => index !== null);
});

const allFilteredIndexes = computed(() => {
  return filteredTexts.value.map((_, index) => index);
});

const currentAllNavIndex = computed(() => {
  return allFilteredIndexes.value.indexOf(focusedResultIndex.value);
});

const currentLowConfidenceNavIndex = computed(() => {
  return lowConfidenceFilteredIndexes.value.indexOf(focusedResultIndex.value);
});

const currentReviewNavIndex = computed(() => {
  return reviewItems.value.findIndex(
    item => item._filteredIndex === focusedResultIndex.value
  );
});

const uncheckedCount = computed(() => {
  return filteredTexts.value.filter(
    item => getReviewStatus(item._textIndex) === "unchecked"
  ).length;
});

const needsReviewFilteredIndexes = computed(() => {
  return filteredTexts.value
    .map((item, index) => (getReviewStatus(item._textIndex) === "needsReview" ? index : null))
    .filter(index => index !== null);
});

const currentNeedsReviewNavIndex = computed(() => {
  return needsReviewFilteredIndexes.value.indexOf(focusedResultIndex.value);
});

const needsReviewCount = computed(() => {
  return filteredTexts.value.filter(
    item => getReviewStatus(item._textIndex) === "needsReview"
  ).length;
});

const selectedReviewItems = computed(() => {
  return reviewItems.value.filter(item =>
    selectedResultIndexes.value.includes(item._filteredIndex)
  );
});

const effectiveBulkItems = computed(() => {
  return selectedReviewItems.value.length ? selectedReviewItems.value : reviewItems.value;
});

const editedCount = computed(() => {
  return filteredTexts.value.filter(item => isTextEdited(item._textIndex, item.text)).length;
});

const mergedText = computed(() => {
  return filteredTexts.value.map(item => getFinalText(item._textIndex, item.text)).join("\n");
});

const modelSummaryText = computed(() => {
  const det = currentModel.value.det_model_name || currentModel.value.det_model_dir || "-";
  const rec = currentModel.value.rec_model_name || currentModel.value.rec_model_dir || "-";

  if (modelInfoLoading.value) {
    return "模型信息同步中...";
  }

  if (modelInfoError.value) {
    return "模型信息读取失败";
  }

  return `${det} + ${rec}`;
});

const modelShapeText = computed(() => {
  return currentModel.value.text_rec_input_shape?.length
    ? currentModel.value.text_rec_input_shape.join(" × ")
    : "-";
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

async function fetchCurrentModelInfo(showLog = false) {
  modelInfoLoading.value = true;
  modelInfoError.value = "";

  try {
    const res = await getModelInfo();
    if (res.data?.code === 0 && res.data?.data) {
      currentModel.value = {
        ...currentModel.value,
        ...res.data.data
      };

      if (showLog) {
        addLog(`已同步当前模型：${res.data.data.det_model_name} + ${res.data.data.rec_model_name}`);
      }
    } else {
      modelInfoError.value = "后端未返回有效的模型信息。";
    }
  } catch (error) {
    console.error("读取模型信息失败：", error);
    modelInfoError.value = "无法连接后端读取模型信息。";
  } finally {
    modelInfoLoading.value = false;
  }
}

function persistReviewState() {
  if (!reviewStorageKey.value) return;

  try {
    localStorage.setItem(
      reviewStorageKey.value,
      JSON.stringify({
        reviewStatusMap: reviewStatusMap.value,
        reviewEditMap: reviewEditMap.value,
        reviewFilterMode: reviewFilterMode.value
      })
    );
  } catch (error) {
    console.error("保存复核状态失败：", error);
  }
}

function loadPersistedReviewState() {
  if (!reviewStorageKey.value) return;

  try {
    const raw = localStorage.getItem(reviewStorageKey.value);
    if (!raw) return;

    const parsed = JSON.parse(raw);

    reviewStatusMap.value =
      parsed?.reviewStatusMap && typeof parsed.reviewStatusMap === "object"
        ? parsed.reviewStatusMap
        : {};

    reviewEditMap.value =
      parsed?.reviewEditMap && typeof parsed.reviewEditMap === "object"
        ? parsed.reviewEditMap
        : {};

    if (
      ["all", "low", "high", "unchecked", "needsReview"].includes(parsed?.reviewFilterMode)
    ) {
      reviewFilterMode.value = parsed.reviewFilterMode;
    }
  } catch (error) {
    console.error("读取复核状态失败：", error);
  }
}

watch(
  reviewStatusMap,
  () => {
    persistReviewState();
  },
  { deep: true }
);

watch(
  reviewEditMap,
  () => {
    persistReviewState();
  },
  { deep: true }
);

watch(reviewFilterMode, () => {
  persistReviewState();
});

watch(
  filteredTexts,
  (newList) => {
    const validIndexes = new Set(newList.map((_, index) => index));

    selectedResultIndexes.value = selectedResultIndexes.value.filter(index =>
      validIndexes.has(index)
    );

    if (
      selectionAnchorIndex.value !== null &&
      !validIndexes.has(selectionAnchorIndex.value)
    ) {
      selectionAnchorIndex.value = selectedResultIndexes.value.length
        ? selectedResultIndexes.value[selectedResultIndexes.value.length - 1]
        : null;
    }

    if (
      focusedResultIndex.value !== null &&
      !validIndexes.has(focusedResultIndex.value)
    ) {
      focusedResultIndex.value = null;
    }

    if (
      hoveredResultIndex.value !== null &&
      !validIndexes.has(hoveredResultIndex.value)
    ) {
      hoveredResultIndex.value = null;
    }
  },
  { deep: true }
);

function addLog(message) {
  const time = new Date().toLocaleTimeString();
  logs.value.unshift(`[${time}] ${message}`);
}

function openHelpModal() {
  showHelpModal.value = true;
}

function closeHelpModal() {
  showHelpModal.value = false;
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
  reviewStatusMap.value = {};
  reviewEditMap.value = {};
  selectedResultIndexes.value = [];
  selectionAnchorIndex.value = null;

  loadPersistedReviewState();

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
  reviewStatusMap.value = {};
  reviewEditMap.value = {};
  selectedResultIndexes.value = [];
  selectionAnchorIndex.value = null;

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
    reviewStatusMap.value = {};
    reviewEditMap.value = {};
    selectedResultIndexes.value = [];
    selectionAnchorIndex.value = null;

    loadPersistedReviewState();

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

function escapeCsvCell(value) {
  const text = String(value ?? "");
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function exportCsv() {
  if (!reviewItems.value.length) return;

  const header = ["序号", "原始文本", "复核修正", "最终文本", "置信度", "质量等级", "是否低置信度", "检查状态"];
  const rows = reviewItems.value.map((item, idx) => [
    idx + 1,
    item.text,
    getEditedText(item._textIndex),
    getFinalText(item._textIndex, item.text),
    Number(item.score || 0).toFixed(4),
    getScoreLabel(item.score),
    Number(item.score || 0) < LOW_CONFIDENCE_CUTOFF ? "是" : "否",
    getReviewStatusLabel(item._textIndex)
  ]);

  const csvText =
    "\ufeff" +
    [header, ...rows]
      .map(row => row.map(cell => escapeCsvCell(cell)).join(","))
      .join("\n");

  const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  const baseName = fileName.value ? fileName.value.replace(/\.[^.]+$/, "") : "ocr_result";
  const suffix = reviewFilterMode.value === "low"
    ? "low_confidence"
    : reviewFilterMode.value === "high"
    ? "high_confidence"
    : reviewFilterMode.value === "unchecked"
    ? "unchecked"
    : reviewFilterMode.value === "needsReview"
    ? "needs_review"
    : "all_results";

  a.href = url;
  a.download = `${baseName}_${suffix}.csv`;
  a.click();

  URL.revokeObjectURL(url);
  addLog(
    `已导出 CSV 结果文件（${
      reviewFilterMode.value === "low"
        ? "仅低置信度"
        : reviewFilterMode.value === "high"
        ? "仅高置信度"
        : reviewFilterMode.value === "unchecked"
        ? "仅未检查"
        : reviewFilterMode.value === "needsReview"
        ? "仅需复核"
        : "全部结果"
    }）。`
  );
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

function getReviewStatus(textIndex) {
  return reviewStatusMap.value[textIndex] || "unchecked";
}

function getEditedText(textIndex) {
  return reviewEditMap.value[textIndex] || "";
}

function getFinalText(textIndex, originalText) {
  const editedText = getEditedText(textIndex).trim();
  return editedText || originalText;
}

function isTextEdited(textIndex, originalText) {
  const editedText = getEditedText(textIndex).trim();
  return !!editedText && editedText !== originalText;
}

function setEditedText(textIndex, value) {
  reviewEditMap.value = {
    ...reviewEditMap.value,
    [textIndex]: value
  };

  if (value.trim() && getReviewStatus(textIndex) === "unchecked") {
    setReviewStatus(textIndex, "needsReview");
  }
}

function resetEditedText(textIndex) {
  const nextMap = { ...reviewEditMap.value };
  delete nextMap[textIndex];
  reviewEditMap.value = nextMap;
}

function setReviewStatus(textIndex, status) {
  reviewStatusMap.value = {
    ...reviewStatusMap.value,
    [textIndex]: status
  };
}

function getReviewStatusLabel(textIndex) {
  const status = getReviewStatus(textIndex);
  if (status === "checked") return "已检查";
  if (status === "needsReview") return "需复核";
  return "未检查";
}

function getReviewStatusClass(textIndex) {
  const status = getReviewStatus(textIndex);
  if (status === "checked") return "checked";
  if (status === "needsReview") return "needs-review";
  return "unchecked";
}

function isResultSelected(filteredIndex) {
  return selectedResultIndexes.value.includes(filteredIndex);
}

function clearSelectedResults() {
  selectedResultIndexes.value = [];
  selectionAnchorIndex.value = null;
}

function setSingleSelection(filteredIndex) {
  selectedResultIndexes.value = [filteredIndex];
  selectionAnchorIndex.value = filteredIndex;
}

function toggleResultSelection(filteredIndex) {
  const set = new Set(selectedResultIndexes.value);

  if (set.has(filteredIndex)) {
    set.delete(filteredIndex);
  } else {
    set.add(filteredIndex);
  }

  selectedResultIndexes.value = Array.from(set).sort((a, b) => a - b);
  selectionAnchorIndex.value = filteredIndex;
}

function selectRangeTo(filteredIndex, append = false) {
  const visibleIndexes = reviewItems.value.map(item => item._filteredIndex);
  if (!visibleIndexes.length) return;

  let anchor = selectionAnchorIndex.value;

  if (anchor === null || !visibleIndexes.includes(anchor)) {
    if (
      focusedResultIndex.value !== null &&
      visibleIndexes.includes(focusedResultIndex.value)
    ) {
      anchor = focusedResultIndex.value;
    } else {
      anchor = visibleIndexes[0];
    }
  }

  const start = visibleIndexes.indexOf(anchor);
  const end = visibleIndexes.indexOf(filteredIndex);

  if (start === -1 || end === -1) {
    selectedResultIndexes.value = append
      ? Array.from(new Set([...selectedResultIndexes.value, filteredIndex])).sort((a, b) => a - b)
      : [filteredIndex];
    selectionAnchorIndex.value = filteredIndex;
    return;
  }

  const [from, to] = start < end ? [start, end] : [end, start];
  const rangeIndexes = visibleIndexes.slice(from, to + 1);

  selectedResultIndexes.value = append
    ? Array.from(new Set([...selectedResultIndexes.value, ...rangeIndexes])).sort((a, b) => a - b)
    : rangeIndexes;

  selectionAnchorIndex.value = anchor;
}

function handleResultSelection(filteredIndex, event, options = {}) {
  const { scrollCanvas = true, scrollTable = false } = options;
  const isCtrlLike = event.ctrlKey || event.metaKey;
  const isShift = event.shiftKey;

  if (isShift) {
    selectRangeTo(filteredIndex, isCtrlLike);
  } else if (isCtrlLike) {
    toggleResultSelection(filteredIndex);
  } else {
    setSingleSelection(filteredIndex);
  }

  focusResult(filteredIndex, { scrollCanvas, scrollTable });
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

function focusAllByOffset(step = 1) {
  const indexes = allFilteredIndexes.value;
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

function focusNextAll() {
  focusAllByOffset(1);
}

function focusPrevAll() {
  focusAllByOffset(-1);
}

function focusNeedsReviewByOffset(step = 1) {
  const indexes = needsReviewFilteredIndexes.value;
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

function focusNextNeedsReview() {
  focusNeedsReviewByOffset(1);
}

function focusPrevNeedsReview() {
  focusNeedsReviewByOffset(-1);
}

function getActiveTargetFilteredIndex() {
  if (
    focusedResultIndex.value !== null &&
    focusedResultIndex.value >= 0 &&
    filteredTexts.value[focusedResultIndex.value]
  ) {
    return focusedResultIndex.value;
  }

  if (
    hoveredResultIndex.value !== null &&
    hoveredResultIndex.value >= 0 &&
    filteredTexts.value[hoveredResultIndex.value]
  ) {
    return hoveredResultIndex.value;
  }

  if (reviewItems.value.length) {
    return reviewItems.value[0]._filteredIndex;
  }

  if (filteredTexts.value.length) {
    return 0;
  }

  return -1;
}

function applyReviewStatusByShortcut(status) {
  const targetFilteredIndex = getActiveTargetFilteredIndex();
  if (targetFilteredIndex < 0) return;

  const targetItem = filteredTexts.value[targetFilteredIndex];
  if (!targetItem) return;

  focusedResultIndex.value = targetFilteredIndex;
  setReviewStatus(targetItem._textIndex, status);
  focusResult(targetFilteredIndex, { scrollCanvas: true, scrollTable: true });
}

function applyBulkReviewStatus(status) {
  const targets = effectiveBulkItems.value;
  if (!targets.length) return;

  const nextMap = { ...reviewStatusMap.value };

  targets.forEach(item => {
    nextMap[item._textIndex] = status;
  });

  reviewStatusMap.value = nextMap;

  const statusLabel =
    status === "checked"
      ? "已检查"
      : status === "needsReview"
      ? "需复核"
      : "未检查";

  const targetLabel = selectedReviewItems.value.length
    ? `选中的 ${selectedReviewItems.value.length}`
    : `当前筛选结果 ${reviewItems.value.length}`;

  addLog(`已将${targetLabel} 条记录批量标记为“${statusLabel}”。`);
}

function shouldIgnoreShortcut(event) {
  const el = event.target;
  if (!el) return false;

  const tagName = el.tagName?.toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select" ||
    el.isContentEditable
  );
}

function handleKeydown(event) {
  const key = event.key.toLowerCase();

  if (showHelpModal.value) {
    if (key === "escape") {
      event.preventDefault();
      closeHelpModal();
    }
    return;
  }

  if (loading.value) return;
  if (shouldIgnoreShortcut(event)) return;

  switch (key) {
    case "a":
      event.preventDefault();
      focusPrevAll();
      break;
    case "d":
      event.preventDefault();
      focusNextAll();
      break;
    case "z":
      event.preventDefault();
      focusPrevLowConfidence();
      break;
    case "c":
      event.preventDefault();
      focusNextLowConfidence();
      break;
    case "j":
      event.preventDefault();
      focusPrevNeedsReview();
      break;
    case "l":
      event.preventDefault();
      focusNextNeedsReview();
      break;
    case "1":
      event.preventDefault();
      applyReviewStatusByShortcut("unchecked");
      break;
    case "2":
      event.preventDefault();
      applyReviewStatusByShortcut("checked");
      break;
    case "3":
      event.preventDefault();
      applyReviewStatusByShortcut("needsReview");
      break;
    case "q":
      event.preventDefault();
      reviewFilterMode.value = "all";
      break;
    case "f":
      event.preventDefault();
      reviewFilterMode.value = "low";
      break;
    case "t":
      event.preventDefault();
      reviewFilterMode.value = "high";
      break;
    case "w":
      event.preventDefault();
      reviewFilterMode.value = "unchecked";
      break;
    case "e":
      event.preventDefault();
      reviewFilterMode.value = "needsReview";
      break;
    case "r":
      event.preventDefault();
      if (visUrl.value) resetZoom("vis");
      break;
    default:
      break;
  }
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

function showZoomToast(kind) {
  const isSrc = kind === "src";
  const toastRef = isSrc ? srcZoomToast : visZoomToast;

  toastRef.value = true;

  if (isSrc) {
    if (srcZoomToastTimer) clearTimeout(srcZoomToastTimer);
    srcZoomToastTimer = setTimeout(() => {
      srcZoomToast.value = false;
    }, 800);
  } else {
    if (visZoomToastTimer) clearTimeout(visZoomToastTimer);
    visZoomToastTimer = setTimeout(() => {
      visZoomToast.value = false;
    }, 800);
  }
}

function changeZoom(kind, delta) {
  if (kind === "src" && !imagePreview.value) return;
  if (kind === "vis" && !visUrl.value) return;

  const { shell, meta, zoomRef } = getShellAndMeta(kind);
  const img = kind === "src" ? srcImgRef.value : visImgRef.value;

  const prevZoom = zoomRef.value;
  const nextZoom = clampZoom(prevZoom + delta);

  if (nextZoom === prevZoom) return;

  if (!shell || !meta.baseWidth || !meta.baseHeight || !img) {
    return;
  }

  const shellRect = shell.getBoundingClientRect();
  const imgRect = img.getBoundingClientRect();

  const focusClientX = shellRect.left + shell.clientWidth / 2;
  const focusClientY = shellRect.top + shell.clientHeight / 2;

  const rawRatioX = imgRect.width
    ? (focusClientX - imgRect.left) / imgRect.width
    : 0.5;
  const rawRatioY = imgRect.height
    ? (focusClientY - imgRect.top) / imgRect.height
    : 0.5;

  const ratioX = Math.min(1, Math.max(0, rawRatioX));
  const ratioY = Math.min(1, Math.max(0, rawRatioY));

  zoomRef.value = nextZoom;
  showZoomToast(kind);

  nextTick(() => {
    const newImg = kind === "src" ? srcImgRef.value : visImgRef.value;
    if (!shell || !newImg) return;

    const newImgRect = newImg.getBoundingClientRect();

    const newPointClientX = newImgRect.left + newImgRect.width * ratioX;
    const newPointClientY = newImgRect.top + newImgRect.height * ratioY;

    shell.scrollLeft += newPointClientX - focusClientX;
    shell.scrollTop += newPointClientY - focusClientY;
  });
}

function resetZoom(kind) {
  const { zoomRef } = getShellAndMeta(kind);
  zoomRef.value = 1;
  showZoomToast(kind);

  nextTick(() => {
    centerStage(kind);
  });
}

function clampZoom(value) {
  return Math.min(4, Math.max(0.3, Number(value.toFixed(2))));
}

function handleWheelZoom(kind, event) {
  if (kind === "src" && !imagePreview.value) return;
  if (kind === "vis" && !visUrl.value) return;

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
  window.addEventListener("keydown", handleKeydown);

  fetchCurrentModelInfo();
  modelInfoTimer = window.setInterval(() => {
    fetchCurrentModelInfo();
  }, MODEL_INFO_REFRESH_MS);

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
  window.removeEventListener("keydown", handleKeydown);

  if (srcZoomToastTimer) clearTimeout(srcZoomToastTimer);
  if (visZoomToastTimer) clearTimeout(visZoomToastTimer);
  if (modelInfoTimer) clearInterval(modelInfoTimer);

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

.glass-lite {
  background: rgba(255, 255, 255, 0.54);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 6px 16px rgba(31, 38, 135, 0.08);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
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
  overflow: visible;
  z-index: 200;
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
  overflow: visible;
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
  z-index: 400;
}

.file-btn:hover:not(.disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 26px rgba(37, 99, 235, 0.16);
  background: rgba(255, 255, 255, 0.92);
}

.file-btn:hover,
.file-btn:focus-within {
  z-index: 5000;
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

.file-hover-name {
  position: absolute;
  left: 0;
  top: calc(100% + 10px);
  min-width: max-content;
  max-width: 560px;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.96);
  color: #fff;
  font-size: 13px;
  line-height: 1.45;
  white-space: normal;
  overflow-wrap: anywhere;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.22);
  z-index: 99999;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: opacity 0.16s ease, transform 0.16s ease, visibility 0.16s ease;
}

.file-hover-name::before {
  content: "";
  position: absolute;
  left: 18px;
  top: -6px;
  width: 12px;
  height: 12px;
  background: rgba(15, 23, 42, 0.96);
  transform: rotate(45deg);
}

.file-btn:hover .file-hover-name {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
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

.canvas-frame {
  position: relative;
  width: 100%;
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

.zoom-toast {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  padding: 12px 18px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.86);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.22);
  z-index: 5000;
  pointer-events: none;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
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
  border-radius: 26px;
  padding: 22px;
  overflow: visible;
  background: linear-gradient(180deg, #eef5ff 0%, #edf4fb 100%);
  border: 1px solid rgba(214, 226, 245, 0.95);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 8px 24px rgba(148, 163, 184, 0.08);
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

.summary-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.summary-chip {
  padding: 10px 12px;
  border-radius: 14px;
}

.summary-chip-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.summary-chip strong {
  font-size: 16px;
  color: #1e293b;
}

.review-filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(
    180deg,
    rgba(245, 248, 255, 0.92),
    rgba(238, 243, 255, 0.82)
  );
  border: 1px solid rgba(191, 219, 254, 0.55);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.mini-filter-btn {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(191, 219, 254, 0.75);
  color: #52607a;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.08);
}

.mini-filter-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(147, 197, 253, 0.95);
  color: #334155;
}

.mini-filter-btn.active {
  background: linear-gradient(135deg, #3148a2, #b79cff);
  color: #ffffff;
  border-color: rgba(139, 92, 246, 0.18);
  box-shadow: 0 6px 14px rgba(99, 102, 241, 0.16);
}

.tab-btn.active {
  background: linear-gradient(135deg, #315efb, #7c3aed);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.24);
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
  max-height: 280px;
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
  .mini-stats-row,
  .summary-strip {
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

.review-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.review-badge.unchecked {
  background: rgba(241, 245, 249, 0.95);
  color: #475569;
}

.review-badge.checked {
  background: rgba(240, 253, 244, 0.95);
  color: #15803d;
}

.review-badge.needs-review {
  background: rgba(254, 226, 226, 0.95);
  color: #dc2626;
}

.review-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.raw-text-cell {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  color: #0f172a;
}

.edit-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.review-edit-input {
  width: 100%;
  min-height: 82px;
  resize: vertical;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(191, 219, 254, 0.9);
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-size: 13px;
  line-height: 1.6;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.review-edit-input:focus {
  border-color: rgba(37, 99, 235, 0.9);
  box-shadow: 0 0 0 3px rgba(191, 219, 254, 0.55);
}

.edit-cell-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.edit-indicator {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.edit-indicator.edited {
  color: #2563eb;
}

.inline-link-btn {
  padding: 0;
  border: none;
  background: transparent;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.inline-link-btn:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.status-action-btn {
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.9);
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.status-action-btn.active {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.16);
}

.shortcut-tip {
  width: 100%;
  margin-top: 4px;
  font-size: 12px;
  color: #6b7a90;
  line-height: 1.7;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.52);
  border: 1px dashed rgba(191, 219, 254, 0.7);
}

.help-trigger-btn {
  color: #0f766e;
  border-color: rgba(94, 234, 212, 0.9);
}

.help-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 24px;
}

.help-modal {
  width: min(920px, 100%);
  max-height: min(82vh, 860px);
  border-radius: 24px;
  padding: 20px 20px 18px;
  overflow: auto;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.2);
}

.help-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.help-modal-header h3 {
  margin: 0;
  font-size: 24px;
  color: #1e293b;
}

.help-modal-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
}

.help-close-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 12px;
  font-size: 22px;
  line-height: 1;
  color: #475569;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.9);
}

.help-modal-body {
  display: grid;
  gap: 14px;
}

.help-section {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.72);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.help-section h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #1e293b;
}

.help-kbd-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px 14px;
}

.help-kbd-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.help-kbd-item span {
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
}

.help-kbd-item kbd {
  min-width: 34px;
  padding: 4px 8px;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.16);
}

.help-list {
  margin: 0;
  padding-left: 18px;
  color: #475569;
}

.help-list li {
  margin-bottom: 8px;
  line-height: 1.8;
}

.help-list li:last-child {
  margin-bottom: 0;
}

.batch-review-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-radius: 14px;
  margin-bottom: 12px;
}

.batch-review-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.batch-review-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.batch-review-desc {
  font-size: 12px;
  color: #64748b;
}

.batch-review-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.batch-action-btn {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(191, 219, 254, 0.9);
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.batch-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.danger-batch {
  color: #dc2626;
  border-color: rgba(252, 165, 165, 0.9);
}

.table-wrap tbody tr.selected {
  background: rgba(99, 102, 241, 0.10);
}

.table-wrap tbody tr.selected td {
  background: rgba(99, 102, 241, 0.06);
}

.table-wrap tbody tr.selected td:first-child {
  box-shadow: inset 4px 0 0 rgba(99, 102, 241, 0.95);
}

.table-wrap tbody tr.selected.active {
  background: rgba(37, 99, 235, 0.18);
}

.table-wrap tbody tr.selected.active td {
  background: rgba(37, 99, 235, 0.10);
}

.selectable-box.selected {
  box-shadow:
    0 0 0 2px rgba(99, 102, 241, 0.45),
    0 4px 12px rgba(99, 102, 241, 0.14);
}

.selectable-box.selected.active {
  box-shadow:
    0 0 0 2px rgba(37, 99, 235, 0.7),
    0 6px 16px rgba(37, 99, 235, 0.18);
}
</style>
