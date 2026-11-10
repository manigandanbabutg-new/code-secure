const input = document.getElementById("videoInput");
const chooseBtn = document.getElementById("chooseBtn");
const scanBtn = document.getElementById("scanBtn");
const fileInfo = document.getElementById("fileInfo");
const dropArea = document.getElementById("dropArea");
const resultBox = document.getElementById("result");
const progressWrap = document.getElementById("progressWrap");

let selectedFile = null;

chooseBtn.addEventListener("click", () => input.click());
input.addEventListener("change", () => selectFile(input.files[0]));

function selectFile(file) {
    if (!file) return;
    resultBox.hidden = true;

    if (!file.name.toLowerCase().endsWith(".mp4")) {
        selectedFile = null;
        scanBtn.disabled = true;
        fileInfo.textContent = "Please select an MP4 file.";
        return;
    }

    if (file.size > 100 * 1024 * 1024) {
        selectedFile = null;
        scanBtn.disabled = true;
        fileInfo.textContent = "File is larger than 100 MB.";
        return;
    }

    selectedFile = file;
    scanBtn.disabled = false;
    fileInfo.textContent = `${file.name} · ${(file.size / (1024 * 1024)).toFixed(2)} MB`;
}

["dragenter", "dragover"].forEach(eventName => {
    dropArea.addEventListener(eventName, event => {
        event.preventDefault();
        dropArea.classList.add("dragover");
    });
});
["dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, event => {
        event.preventDefault();
        dropArea.classList.remove("dragover");
    });
});
dropArea.addEventListener("drop", event => selectFile(event.dataTransfer.files[0]));

scanBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("video", selectedFile);

    scanBtn.disabled = true;
    progressWrap.hidden = false;
    resultBox.hidden = true;

    try {
        const response = await fetch("/api/scan", { method: "POST", body: formData });
        const data = await response.json();

        if (!response.ok || !data.success) {
            showResult("error", "Could not scan file", data.error || "An unknown error occurred.");
        } else if (data.scan_status === "clean") {
            showResult("clean", "✓ No known malware detected", data.message);
        } else if (data.scan_status === "infected") {
            showResult("infected", "⚠ Threat detected", data.message);
        } else {
            showResult("error", "Scan unavailable", data.message);
        }
    } catch (error) {
        showResult("error", "Connection error", "Could not contact the scanner. Please try again.");
    } finally {
        progressWrap.hidden = true;
        scanBtn.disabled = !selectedFile;
    }
});

function showResult(type, title, message) {
    resultBox.className = `result ${type}`;
    resultBox.innerHTML = "";
    const heading = document.createElement("strong");
    const detail = document.createElement("span");
    heading.textContent = title;
    detail.textContent = message;
    resultBox.append(heading, detail);
    resultBox.hidden = false;
}
