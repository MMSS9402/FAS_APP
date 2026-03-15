const state = {
  images: [],
  models: [],
  selectedModels: new Set(),
  lastResponse: null,
  running: false,
};

const elements = {
  fileInput: document.getElementById("file-input"),
  dropzone: document.getElementById("dropzone"),
  imageMeta: document.getElementById("image-meta"),
  imageList: document.getElementById("image-list"),
  modelList: document.getElementById("model-list"),
  statusText: document.getElementById("status-text"),
  responseNotes: document.getElementById("response-notes"),
  resultsGallery: document.getElementById("results-gallery"),
  resultsTableBody: document.getElementById("results-table-body"),
  summaryImageCount: document.getElementById("summary-image-count"),
  summaryModelCount: document.getElementById("summary-model-count"),
  summaryRunCount: document.getElementById("summary-run-count"),
  summaryLatency: document.getElementById("summary-latency"),
  runSelected: document.getElementById("run-selected"),
  runAll: document.getElementById("run-all"),
  selectReady: document.getElementById("select-ready"),
  clearModels: document.getElementById("clear-models"),
  clearImages: document.getElementById("clear-images"),
  resetState: document.getElementById("reset-state"),
  exportCsv: document.getElementById("export-csv"),
};

async function init() {
  bindEvents();
  await loadModels();
  renderImages();
  renderSummary();
}

function bindEvents() {
  elements.fileInput.addEventListener("change", (event) => {
    addFiles(event.target.files);
    event.target.value = "";
  });

  elements.dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    elements.dropzone.classList.add("dragging");
  });

  elements.dropzone.addEventListener("dragleave", () => {
    elements.dropzone.classList.remove("dragging");
  });

  elements.dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    elements.dropzone.classList.remove("dragging");
    addFiles(event.dataTransfer.files);
  });

  elements.selectReady.addEventListener("click", () => {
    state.selectedModels = new Set(
      state.models.filter((model) => model.ready_status === "ready").map((model) => model.model_id),
    );
    renderModels();
  });

  elements.clearModels.addEventListener("click", () => {
    state.selectedModels.clear();
    renderModels();
  });

  elements.clearImages.addEventListener("click", () => {
    state.images.forEach((image) => URL.revokeObjectURL(image.previewUrl));
    state.images = [];
    state.lastResponse = null;
    renderImages();
    renderResults();
    renderSummary();
  });

  elements.resetState.addEventListener("click", () => {
    state.selectedModels.clear();
    state.images.forEach((image) => URL.revokeObjectURL(image.previewUrl));
    state.images = [];
    state.lastResponse = null;
    renderModels();
    renderImages();
    renderResults();
    renderSummary();
    setStatus("초기화되었습니다.");
  });

  elements.runSelected.addEventListener("click", () => runInference(false));
  elements.runAll.addEventListener("click", () => runInference(true));
  elements.exportCsv.addEventListener("click", exportCsv);
}

async function loadModels() {
  const response = await fetch("/api/models");
  const models = await response.json();
  state.models = models;
  renderModels();
}

function addFiles(fileList) {
  const accepted = Array.from(fileList).filter((file) => file.type.startsWith("image/"));
  const nextImages = accepted.map((file, index) => ({
    id: `${file.name}-${file.size}-${file.lastModified}-${index}`,
    file,
    previewUrl: URL.createObjectURL(file),
  }));
  state.images = [...state.images, ...nextImages];
  renderImages();
  renderSummary();
}

function renderImages() {
  if (!state.images.length) {
    elements.imageMeta.textContent = "선택된 이미지가 없습니다.";
    elements.imageList.innerHTML = "";
    return;
  }

  elements.imageMeta.textContent = `${state.images.length}개의 이미지가 선택되었습니다.`;
  elements.imageList.innerHTML = state.images
    .map(
      (image) => `
        <article class="image-card">
          <img class="image-preview" src="${image.previewUrl}" alt="${escapeHtml(image.file.name)}" />
          <div class="image-card-body">
            <div class="image-card-actions">
              <div>
                <strong>${escapeHtml(image.file.name)}</strong>
                <div class="meta-row">${formatBytes(image.file.size)}</div>
              </div>
              <button class="ghost-button" type="button" data-remove-image="${image.id}">삭제</button>
            </div>
          </div>
        </article>
      `,
    )
    .join("");

  elements.imageList.querySelectorAll("[data-remove-image]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.removeImage;
      const target = state.images.find((image) => image.id === targetId);
      if (target) {
        URL.revokeObjectURL(target.previewUrl);
      }
      state.images = state.images.filter((image) => image.id !== targetId);
      renderImages();
      renderSummary();
    });
  });
}

function renderModels() {
  const readyModels = state.models.filter((model) => model.ready_status === "ready");
  const nonReadyModels = state.models.filter((model) => model.ready_status !== "ready");
  const sections = [
    ["즉시 실행 가능", readyModels],
    ["연구/비디오 전용", nonReadyModels],
  ];

  elements.modelList.innerHTML = sections
    .map(([title, models]) => {
      if (!models.length) {
        return "";
      }

      return `
        <section>
          <h3>${title}</h3>
          <div class="model-list">
            ${models.map(renderModelCard).join("")}
          </div>
        </section>
      `;
    })
    .join("");

  elements.modelList.querySelectorAll("input[type=checkbox]").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const modelId = checkbox.value;
      if (checkbox.checked) {
        state.selectedModels.add(modelId);
      } else {
        state.selectedModels.delete(modelId);
      }
    });
  });
}

function renderModelCard(model) {
  const checked = state.selectedModels.has(model.model_id) ? "checked" : "";
  const disabled = model.ready_status !== "ready" ? "disabled" : "";
  const disabledClass = model.ready_status !== "ready" ? "disabled" : "";

  return `
    <article class="model-card ${disabledClass}">
      <label>
        <div>
          <input type="checkbox" value="${model.model_id}" ${checked} ${disabled} />
          <strong>${escapeHtml(model.display_name)}</strong>
        </div>
        <div class="model-meta">
          <span class="pill ${model.ready_status}">${escapeHtml(model.ready_status_label || formatReadyStatus(model.ready_status))}</span>
          <span class="pill ${model.implementation_status || "unknown"}">${escapeHtml(model.implementation_status_label || formatImplementationStatus(model.implementation_status))}</span>
          <span class="pill track">${escapeHtml(model.track_label || formatAttackTrack(model.attack_track))}</span>
          <span class="pill">${escapeHtml(formatInputType(model.input_type))}</span>
          <span class="pill">${escapeHtml(String(model.paper_year))}</span>
        </div>
        <div>${escapeHtml(model.paper_title)}</div>
        <div class="meta-row">${escapeHtml(model.repository_url)}</div>
      </label>
    </article>
  `;
}

async function runInference(useAllModels) {
  if (state.running) {
    return;
  }

  if (!state.images.length) {
    setStatus("이미지를 먼저 업로드하세요.");
    return;
  }

  const selectedModels = useAllModels
    ? state.models.filter((model) => model.ready_status === "ready").map((model) => model.model_id)
    : Array.from(state.selectedModels);

  if (!selectedModels.length) {
    setStatus("실행할 모델을 선택하세요.");
    return;
  }

  state.running = true;
  updateRunButtons();
  setStatus("추론을 실행 중입니다...");

  const formData = new FormData();
  state.images.forEach((image) => formData.append("files", image.file));
  formData.append("selected_models", JSON.stringify(selectedModels));
  formData.append("use_all_models", String(useAllModels));

  try {
    const response = await fetch("/api/infer", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "추론 요청에 실패했습니다.");
    }

    state.lastResponse = payload;
    renderResults();
    renderSummary();
    setStatus(`완료: ${payload.summary.successful_runs}건 성공, ${payload.summary.failed_runs}건 실패`);
  } catch (error) {
    setStatus(error.message);
  } finally {
    state.running = false;
    updateRunButtons();
  }
}

function renderResults() {
  const response = state.lastResponse;
  if (!response) {
    elements.responseNotes.className = "response-notes empty-state";
    elements.responseNotes.textContent = "실행 메모가 없습니다.";
    elements.resultsGallery.className = "results-gallery empty-state";
    elements.resultsGallery.textContent = "아직 실행 결과가 없습니다.";
    elements.resultsTableBody.innerHTML = '<tr><td colspan="14" class="table-empty">실행 결과가 없습니다.</td></tr>';
    return;
  }

  renderResponseNotes(response.notes || []);
  elements.resultsGallery.className = "results-gallery";
  elements.resultsGallery.innerHTML = response.images
    .map((imageResult) => {
      const preview = state.images.find((image) => image.file.name === imageResult.image_name)?.previewUrl ?? "";
      const badges = imageResult.results
        .map((result) => {
          const labelClass = (result.prediction_label || "").toLowerCase();
          const scoreText =
            typeof result.normalized_spoof_score === "number"
              ? result.normalized_spoof_score.toFixed(4)
              : "-";
          return `
            <div class="result-chip ${labelClass}">
              <div class="result-chip-main">
                <span>${escapeHtml(result.display_name)}</span>
                <span>${escapeHtml(result.prediction_label || result.status)} / ${scoreText}</span>
              </div>
              <div class="result-chip-sub">
                <span>${escapeHtml(result.track_label || formatAttackTrack(result.attack_track))}</span>
                <span>${escapeHtml(result.implementation_status_label || formatImplementationStatus(result.implementation_status))}</span>
              </div>
            </div>
          `;
        })
        .join("");

      return `
        <article class="result-card">
          <img class="result-preview" src="${preview}" alt="${escapeHtml(imageResult.image_name)}" />
          <div class="overlay-badges">${badges}</div>
        </article>
      `;
    })
    .join("");

  const rows = response.images.flatMap((imageResult) =>
    imageResult.results.map(
      (result) => `
        <tr>
          <td>${escapeHtml(imageResult.image_name)}</td>
          <td>${escapeHtml(result.display_name)}</td>
          <td>${escapeHtml(result.track_label || formatAttackTrack(result.attack_track))}</td>
          <td>${escapeHtml(result.implementation_status_label || formatImplementationStatus(result.implementation_status))}</td>
          <td>${escapeHtml(result.paper_title)}</td>
          <td>${escapeHtml(String(result.paper_year))}</td>
          <td>${escapeHtml(result.prediction_label || "-")}</td>
          <td class="mono">${formatNullableNumber(result.raw_score)}</td>
          <td class="mono">${formatNullableNumber(result.normalized_spoof_score)}</td>
          <td class="mono">${formatNullableNumber(result.threshold)}</td>
          <td>${escapeHtml(String(result.inference_time_ms))} ms</td>
          <td>${escapeHtml(result.status)}</td>
          <td>${escapeHtml(buildDecisionGuide(result))}</td>
          <td>${escapeHtml(result.preprocessing_note || "-")}</td>
        </tr>
      `,
    ),
  );

  elements.resultsTableBody.innerHTML = rows.join("");
}

function renderSummary() {
  const response = state.lastResponse;
  if (!response) {
    elements.summaryImageCount.textContent = String(state.images.length);
    elements.summaryModelCount.textContent = String(state.selectedModels.size);
    elements.summaryRunCount.textContent = "0 / 0";
    elements.summaryLatency.textContent = "0 ms";
    return;
  }

  elements.summaryImageCount.textContent = String(response.summary.image_count);
  elements.summaryModelCount.textContent = String(response.summary.model_count);
  elements.summaryRunCount.textContent = `${response.summary.successful_runs} / ${response.summary.failed_runs}`;
  elements.summaryLatency.textContent = `${response.summary.average_inference_time_ms} ms`;
}

function exportCsv() {
  if (!state.lastResponse) {
    setStatus("먼저 추론을 실행하세요.");
    return;
  }

  const lines = [
    [
      "image_name",
      "model_name",
      "track_label",
      "runtime_label",
      "paper_title",
      "paper_year",
      "prediction_label",
      "raw_score",
      "normalized_spoof_score",
      "threshold",
      "inference_time_ms",
      "status",
      "decision_guide",
      "preprocessing_note",
    ].join(","),
  ];

  state.lastResponse.images.forEach((imageResult) => {
    imageResult.results.forEach((result) => {
      lines.push(
        [
          imageResult.image_name,
          result.display_name,
          result.track_label || formatAttackTrack(result.attack_track),
          result.implementation_status_label || formatImplementationStatus(result.implementation_status),
          result.paper_title,
          result.paper_year,
          result.prediction_label || "",
          result.raw_score ?? "",
          result.normalized_spoof_score ?? "",
          result.threshold ?? "",
          result.inference_time_ms ?? "",
          result.status,
          buildDecisionGuide(result),
          result.preprocessing_note || "",
        ]
          .map(csvEscape)
          .join(","),
      );
    });
  });

  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "fas_app_results.csv";
  link.click();
  URL.revokeObjectURL(url);
}

function updateRunButtons() {
  elements.runSelected.disabled = state.running;
  elements.runAll.disabled = state.running;
}

function setStatus(message) {
  elements.statusText.textContent = message;
}

function renderResponseNotes(notes) {
  if (!notes.length) {
    elements.responseNotes.className = "response-notes empty-state";
    elements.responseNotes.textContent = "실행 메모가 없습니다.";
    return;
  }

  elements.responseNotes.className = "response-notes";
  elements.responseNotes.innerHTML = `
    <strong>실행 메모</strong>
    <ul>
      ${notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}
    </ul>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function csvEscape(value) {
  const normalized = String(value ?? "");
  return `"${normalized.replaceAll('"', '""')}"`;
}

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatNullableNumber(value) {
  return typeof value === "number" ? value.toFixed(4) : "-";
}

function buildDecisionGuide(result) {
  const parts = [result.raw_score_meaning, result.normalized_score_meaning, result.threshold_rule].filter(Boolean);
  return parts.join(" ");
}

function formatAttackTrack(value) {
  if (value === "3d_specialized") {
    return "3D 마스크 특화 FAS";
  }
  if (value === "general_physical_digital_fas") {
    return "일반 FAS (물리·디지털 공격)";
  }
  return value || "-";
}

function formatReadyStatus(value) {
  if (value === "ready") {
    return "즉시 실행 가능";
  }
  if (value === "research_only") {
    return "연구용";
  }
  if (value === "video_only") {
    return "비디오 전용";
  }
  return value || "-";
}

function formatImplementationStatus(value) {
  if (value === "actual") {
    return "실제 체크포인트";
  }
  if (value === "mock") {
    return "모의 결과";
  }
  if (value === "planned") {
    return "미연동";
  }
  return value || "-";
}

function formatInputType(value) {
  if (value === "image") {
    return "이미지";
  }
  if (value === "video") {
    return "비디오";
  }
  return value || "-";
}

init();
