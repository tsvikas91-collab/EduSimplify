const fileInput = document.getElementById("file");
const fileName = document.getElementById("file-name");
const submitBtn = document.getElementById("submit-btn");
const emptyState = document.getElementById("empty-state");
const loading = document.getElementById("loading");
const resultBox = document.getElementById("result");
const errorBox = document.getElementById("error");
const resultFooter = document.getElementById("result-footer");
const modeBadge = document.getElementById("mode-badge");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files.length ? fileInput.files[0].name : "No file selected";
});

async function checkStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    modeBadge.textContent = data.granite_configured ? "IBM Granite connected" : "Demo mode";
    modeBadge.classList.toggle("connected", data.granite_configured);
  } catch {
    modeBadge.textContent = "Status unavailable";
  }
}
checkStatus();

submitBtn.addEventListener("click", async () => {
  const text = document.getElementById("course-text").value.trim();
  const file = fileInput.files[0];
  if (!text && !file) {
    showError("Please upload a PDF, PPTX or TXT file, or paste your course content.");
    return;
  }

  const formData = new FormData();
  if (file) formData.append("file", file);
  formData.append("text", text);
  formData.append("level", document.getElementById("level").value);
  formData.append("task", document.getElementById("task").value);

  emptyState.classList.add("hidden");
  resultBox.classList.add("hidden");
  resultFooter.classList.add("hidden");
  errorBox.classList.add("hidden");
  loading.classList.remove("hidden");
  submitBtn.disabled = true;

  try {
    const response = await fetch("/api/simplify", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    resultBox.textContent = data.result;
    resultBox.classList.remove("hidden");
    resultFooter.classList.remove("hidden");
    document.getElementById("source-label").textContent =
      `${data.filename} · ${data.mode}${data.truncated ? " · Input shortened to fit the demo limit" : ""}`;
    modeBadge.textContent = data.mode === "IBM Granite" ? "IBM Granite connected" : "Demo mode";
    modeBadge.classList.toggle("connected", data.mode === "IBM Granite");
  } catch (error) {
    showError(error.message);
  } finally {
    loading.classList.add("hidden");
    submitBtn.disabled = false;
  }
});

function showError(message) {
  loading.classList.add("hidden");
  emptyState.classList.add("hidden");
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

document.getElementById("copy-btn").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(resultBox.textContent);
    document.getElementById("copy-btn").textContent = "Copied!";
    setTimeout(() => document.getElementById("copy-btn").textContent = "Copy result", 1600);
  } catch {
    document.getElementById("copy-btn").textContent = "Copy unavailable";
  }
});
