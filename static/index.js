document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const workspace = document.getElementById("workspace");
    const processingState = document.getElementById("processing-state");
    const resultsState = document.getElementById("results-state");
    
    // File Details
    const selectedFileName = document.getElementById("selected-file-name");
    const selectedFileSize = document.getElementById("selected-file-size");
    const changeFileBtn = document.getElementById("change-file-btn");
    
    // Sliders & Toggles
    const qualitySlider = document.getElementById("quality-slider");
    const qualityVal = document.getElementById("quality-val");
    const scaleSlider = document.getElementById("scale-slider");
    const scaleVal = document.getElementById("scale-val");
    const grayscaleToggle = document.getElementById("grayscale-toggle");
    const metadataToggle = document.getElementById("metadata-toggle");
    
    // Presets
    const presetLossless = document.getElementById("preset-lossless");
    const presetBalanced = document.getElementById("preset-balanced");
    const presetMax = document.getElementById("preset-max");
    const presetButtons = [presetLossless, presetBalanced, presetMax];
    
    // Actions
    const compressBtn = document.getElementById("compress-btn");
    const downloadBtn = document.getElementById("download-btn");
    const resetBtn = document.getElementById("reset-btn");
    
    // Result Display fields
    const statOriginal = document.getElementById("stat-original");
    const statCompressed = document.getElementById("stat-compressed");
    const statPercent = document.getElementById("stat-percent");
    const statSaved = document.getElementById("stat-saved");
    const detailFilename = document.getElementById("detail-filename");
    const detailImages = document.getElementById("detail-images");
    const detailMetadata = document.getElementById("detail-metadata");
    
    // State variables
    let selectedFile = null;
    
    // -------------------------------------------------------------
    // 1. Drag and Drop handlers
    // -------------------------------------------------------------
    
    // Highlight drop area when item is dragged over it
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        }, false);
    });
    
    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        }, false);
    });
    
    // Handle dropped files
    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    // Click on drop zone triggers file input click
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            alert("Apenas arquivos PDF são aceitos!");
            return;
        }
        
        selectedFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = formatBytes(file.size);
        
        // Switch view
        dropZone.classList.add("hidden");
        workspace.classList.remove("hidden");
        resultsState.classList.add("hidden");
    }
    
    // Change file button action
    changeFileBtn.addEventListener("click", () => {
        resetApp();
    });
    
    // -------------------------------------------------------------
    // 2. Settings Panel Sliders & Presets
    // -------------------------------------------------------------
    
    // Update slider indicators dynamically
    qualitySlider.addEventListener("input", (e) => {
        qualityVal.textContent = `${e.target.value}%`;
        clearPresetHighlights();
    });
    
    scaleSlider.addEventListener("input", (e) => {
        scaleVal.textContent = `${e.target.value}%`;
        clearPresetHighlights();
    });
    
    [grayscaleToggle, metadataToggle].forEach(toggle => {
        toggle.addEventListener("change", () => {
            clearPresetHighlights();
        });
    });
    
    // Preset actions
    presetButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            presetButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            const presetType = btn.getAttribute("data-preset");
            applyPreset(presetType);
        });
    });
    
    function applyPreset(type) {
        if (type === "lossless") {
            qualitySlider.value = 90;
            scaleSlider.value = 100;
            grayscaleToggle.checked = false;
            metadataToggle.checked = false;
        } else if (type === "balanced") {
            qualitySlider.value = 70;
            scaleSlider.value = 70;
            grayscaleToggle.checked = false;
            metadataToggle.checked = true;
        } else if (type === "max") {
            qualitySlider.value = 45;
            scaleSlider.value = 50;
            grayscaleToggle.checked = true;
            metadataToggle.checked = true;
        }
        
        // Update display values
        qualityVal.textContent = `${qualitySlider.value}%`;
        scaleVal.textContent = `${scaleSlider.value}%`;
    }
    
    function clearPresetHighlights() {
        // If sliders are manually altered, we clear the active preset button highlight
        // because the config is now custom
        presetButtons.forEach(b => b.classList.remove("active"));
    }
    
    // -------------------------------------------------------------
    // 3. API Compression Request
    // -------------------------------------------------------------
    
    compressBtn.addEventListener("click", async () => {
        if (!selectedFile) return;
        
        // Transition to processing state
        workspace.classList.add("hidden");
        processingState.classList.remove("hidden");
        
        // Progress steps initialization
        const stepUpload = document.getElementById("step-upload");
        const stepProcess = document.getElementById("step-process");
        const stepFinalize = document.getElementById("step-finalize");
        
        resetSteps([stepUpload, stepProcess, stepFinalize]);
        
        // Step 1: Uploading
        setStepActive(stepUpload);
        
        // Prepare Form Data
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("quality", qualitySlider.value);
        // Scale slider is 10-100, backend wants 0.1-1.0
        formData.append("scale", (scaleSlider.value / 100).toFixed(2));
        formData.append("grayscale", grayscaleToggle.checked);
        formData.append("remove_metadata", metadataToggle.checked);
        
        try {
            // Give a small delay to visually show the initial upload state
            await delay(400);
            
            // Post compression request
            const response = await fetch("/api/compress", {
                method: "POST",
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Erro ao iniciar compactação");
            }
            
            const startData = await response.json();
            const taskId = startData.task_id;
            
            setStepDone(stepUpload);
            setStepActive(stepProcess);
            
            // Poll task status
            let isCompleted = false;
            let resultData = null;
            
            while (!isCompleted) {
                await delay(400); // Poll interval
                
                const statusRes = await fetch(`/api/status/${taskId}`);
                if (!statusRes.ok) {
                    throw new Error("Erro ao consultar status da compactação");
                }
                
                const statusData = await statusRes.json();
                const progress = statusData.progress;
                const message = statusData.message;
                
                // Update UI with progress and messages
                document.getElementById("processing-title").textContent = `Compactando seu arquivo... (${progress}%)`;
                document.getElementById("processing-subtitle").textContent = message;
                
                // Handle progress step transitions
                if (progress >= 15 && progress < 85) {
                    setStepDone(stepUpload);
                    setStepActive(stepProcess);
                } else if (progress >= 85 && progress < 100) {
                    setStepDone(stepProcess);
                    setStepActive(stepFinalize);
                }
                
                if (statusData.status === "completed") {
                    isCompleted = true;
                    resultData = statusData;
                } else if (statusData.status === "failed") {
                    throw new Error(statusData.error || "A compactação falhou no servidor.");
                }
            }
            
            // Reset titles back to default for next usage
            document.getElementById("processing-title").textContent = "Compactando seu arquivo...";
            document.getElementById("processing-subtitle").textContent = "Isso pode levar alguns segundos dependendo do tamanho das imagens.";
            
            setStepDone(stepFinalize);
            await delay(300);
            
            // Show Results
            displayResults(resultData);
            
        } catch (err) {
            console.error("Compression failed:", err);
            alert(`Falha na compactação: ${err.message}`);
            // Reset titles and restore workspace
            document.getElementById("processing-title").textContent = "Compactando seu arquivo...";
            document.getElementById("processing-subtitle").textContent = "Isso pode levar alguns segundos dependendo do tamanho das imagens.";
            processingState.classList.add("hidden");
            workspace.classList.remove("hidden");
        }
    });
    
    function displayResults(data) {
        const stats = data.stats;
        
        // Update stats dashboard
        statOriginal.textContent = formatBytes(stats.original_size);
        statCompressed.textContent = formatBytes(stats.compressed_size);
        statPercent.textContent = `-${stats.percentage_saved.toFixed(1)}%`;
        statSaved.textContent = formatBytes(stats.bytes_saved);
        
        // Update breakdown list
        detailFilename.textContent = stats.filename;
        detailImages.textContent = `${stats.optimized_images} de ${stats.total_images} (Pular: ${stats.skipped_images})`;
        detailMetadata.textContent = metadataToggle.checked ? "Removidos" : "Mantidos";
        
        // Setup download button link
        downloadBtn.setAttribute("href", data.download_url);
        downloadBtn.setAttribute("download", `comprimido_${selectedFile.name}`);
        
        // Switch Views
        processingState.classList.add("hidden");
        resultsState.classList.remove("hidden");
        
        // Refresh icons just in case
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
    
    // Reset/Compress another action
    resetBtn.addEventListener("click", () => {
        resetApp();
    });
    
    // Helper function to reset app state
    function resetApp() {
        selectedFile = null;
        fileInput.value = "";
        
        // Reset inputs to default balanced preset
        presetButtons.forEach(b => b.classList.remove("active"));
        presetBalanced.classList.add("active");
        applyPreset("balanced");
        
        // View swap
        resultsState.classList.add("hidden");
        workspace.classList.add("hidden");
        processingState.classList.add("hidden");
        dropZone.classList.remove("hidden");
    }
    
    // -------------------------------------------------------------
    // Helper functions
    // -------------------------------------------------------------
    
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
    }
    
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    function resetSteps(steps) {
        steps.forEach(step => {
            step.className = "step";
            const icon = step.querySelector("i");
            if (icon) icon.setAttribute("data-lucide", "circle");
        });
    }
    
    function setStepActive(step) {
        step.classList.add("active");
        const icon = step.querySelector("i");
        if (icon) icon.setAttribute("data-lucide", "loader-2");
        // trigger lucide update for dynamic icon change
        if (window.lucide) window.lucide.createIcons();
        
        // Add spin animation to loading icon
        const iconElement = step.querySelector(".lucide-loader-2");
        if (iconElement) {
            iconElement.style.animation = "spin 1s linear infinite";
        }
    }
    
    function setStepDone(step) {
        step.classList.remove("active");
        step.classList.add("done");
        const icon = step.querySelector("i");
        if (icon) icon.setAttribute("data-lucide", "check-circle-2");
        if (window.lucide) window.lucide.createIcons();
    }
});
