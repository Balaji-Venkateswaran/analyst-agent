const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("fileElem");
const uploadBtn = document.getElementById("uploadBtn");
const output = document.getElementById("output");

let filesToUpload = [];

["dragenter", "dragover"].forEach(eventName => {
  dropArea.addEventListener(eventName, e => {
    e.preventDefault();
    dropArea.classList.add("highlight");
  }, false);
});

["dragleave", "drop"].forEach(eventName => {
  dropArea.addEventListener(eventName, e => {
    e.preventDefault();
    dropArea.classList.remove("highlight");
  }, false);
});

dropArea.addEventListener("drop", e => {
  filesToUpload = [...e.dataTransfer.files];
  showFiles();
}, false);

fileInput.addEventListener("change", e => {
  filesToUpload = [...e.target.files];
  showFiles();
});

function showFiles() {
  output.textContent = "Selected Files:\n" + filesToUpload.map(f => f.name).join("\n");
}

uploadBtn.addEventListener("click", async () => {
  if (filesToUpload.length === 0) {
    alert("Please select or drag files first.");
    return;
  }

  const formData = new FormData();
  filesToUpload.forEach(file => formData.append("files", file));

  output.textContent = "⏳ Uploading...";

  try {
    // const res = await fetch("http://localhost:8000/api/", {
     const res = await fetch("https://analyst-agent.onrender.com/api/", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    const data = await res.json();
    output.textContent = "Response:\n" + JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = "Error: " + err.message;
  }
});
