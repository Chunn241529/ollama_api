import { createMsgElement, showError, addCopyButtons } from './utils/ui_utils.js';
import { generateResponse, savePartialResponse } from './utils/api_utils.js';
import { handleFormSubmit, processImageInput } from './utils/input_handlers.js';
import { addStyles } from './utils/styles.js';

const container = document.querySelector(".container");
const chatsContainer = document.querySelector(".chats-container");
const promptForm = document.querySelector(".prompt-form");
const promptInput = promptForm.querySelector(".prompt-input");
const suggestions = document.querySelector(".suggestions");
const appHeader = document.querySelector(".app-header");
const searchToggle = document.getElementById("search-toggle");
const deepThinkToggle = document.getElementById("deep-think-toggle");
const stopResponseBtn = document.getElementById("stop-response-btn");
const sendPromptBtn = document.getElementById("send-prompt-btn");
const closeIframe = document.getElementById("close-iframe");
const moveSelectionRight = document.getElementById("move_selection_right");
const moveSelectionLeft = document.getElementById("move_selection_left");
const rightContainer = document.querySelector(".right-container");
const rightElement = document.querySelector(".right");
const searchOutput = document.querySelector(".search-output");
const outputIframe = document.getElementById("output");
const uploadBtn = document.getElementById("upload-btn");
const uploadDropdown = document.getElementById("upload-dropdown");
const attachBtn = document.getElementById("attach-file-btn");
const fileInput = document.getElementById("file-input");
const filePreviewList = document.querySelector(".file-preview-list");

let controller = new AbortController();
let userMessage = "";
let messages = [];
let autoScroll = true;
let toggle_deepthink = false;
let toggle_search = false;
let model_current;
let lastResultText = "";
let lastResultThinking = "";
let attachedFiles = [];

const SCROLL_THRESHOLD = 30;
const INDICATOR_SHOW_OFFSET = 120;

// Hàm cuộn xuống đáy
const scrollToBottom = (force = false) => {
    if (!autoScroll && !force) {
        return;
    }

    requestAnimationFrame(() => {
        const targetScroll = container.scrollHeight - container.clientHeight;
        const currentScroll = container.scrollTop;

        if (Math.abs(targetScroll - currentScroll) < 2) {
            container.scrollTop = targetScroll;
            return;
        }

        container.scrollTo({
            top: targetScroll,
            behavior: currentScroll < targetScroll - 1000 ? 'auto' : 'smooth'
        });
    });
};

// Tạo nút scroll indicator
const scrollIndicator = document.createElement('button');
scrollIndicator.className = 'scroll-indicator';
scrollIndicator.innerHTML = '⬇ Tin nhắn mới';
scrollIndicator.style.cssText = `
    position: fixed;
    bottom: 220px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--primary-color);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    border: none;
    cursor: pointer;
    display: none;
    z-index: 1000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: opacity 0.3s ease;
`;
document.body.appendChild(scrollIndicator);

// Xử lý sự kiện cuộn
container.addEventListener("scroll", () => {
    const scrollPosition = container.scrollTop + container.clientHeight;
    const atBottom = container.scrollHeight - scrollPosition <= SCROLL_THRESHOLD + 5;
    if (atBottom) {
        autoScroll = true;
        scrollIndicator.style.display = 'none';
    } else {
        autoScroll = false;
        // Chỉ hiện scrollIndicator khi cuộn lên trên một đoạn lớn
        if (container.scrollTop < container.scrollHeight - container.clientHeight - INDICATOR_SHOW_OFFSET) {
            scrollIndicator.style.display = 'block';
        } else {
            scrollIndicator.style.display = 'none';
        }
    }
}, { passive: true });

scrollIndicator.addEventListener('click', () => {
    scrollToBottom(true);
    scrollIndicator.style.display = 'none';
    autoScroll = true;
});

addStyles();

suggestions?.addEventListener("wheel", (event) => {
    event.preventDefault();
    event.currentTarget.scrollBy({ left: event.deltaY < 0 ? -30 : 30 });
});

promptInput.addEventListener("input", () => {
    promptInput.style.height = "auto";
    promptInput.style.height = `${promptInput.scrollHeight}px`;
});

searchToggle.addEventListener("click", () => {
    searchToggle.classList.toggle("active");
    toggle_search = searchToggle.classList.contains("active");
    console.log(`Chế độ tìm kiếm ${toggle_search ? "được kích hoạt" : "bị tắt"}`);
});

deepThinkToggle.addEventListener("click", () => {
    deepThinkToggle.classList.toggle("active");
    toggle_deepthink = deepThinkToggle.classList.contains("active");
    console.log(`Chế độ deep think ${toggle_deepthink ? "được kích hoạt" : "bị tắt"}`);
});

uploadBtn.addEventListener("click", () => {
    uploadDropdown.classList.toggle("active");
});

document.addEventListener("click", (e) => {
    if (!uploadBtn.contains(e.target) && !uploadDropdown.contains(e.target)) {
        uploadDropdown.classList.remove("active");
    }
});

const formSubmitParams = {
    userMessage,
    messages,
    toggle_search,
    toggle_deepthink,
    chatsContainer,
    promptInput,
    stopResponseBtn,
    sendPromptBtn,
    autoScroll,
    scrollToBottom,
    createMsgElement,
    showError,
    addCopyButtons,
    generateResponse,
    processImageInput,
    suggestions,
    appHeader,
    closeIframe,
    rightContainer,
    controller,
    lastResultText,
    lastResultThinking,
    searchOutput,
    moveSelectionRight,
    moveSelectionLeft,
    outputIframe,
    rightElement
};

promptForm.addEventListener("submit", (e) => {
    controller = new AbortController();
    formSubmitParams.controller = controller;
    formSubmitParams.toggle_deepthink = deepThinkToggle.classList.contains("active");
    formSubmitParams.toggle_search = searchToggle.classList.contains("active");
    autoScroll = true;
    formSubmitParams.autoScroll = autoScroll;
    scrollIndicator.style.display = 'none';
    handleFormSubmit(e, formSubmitParams);
    scrollToBottom(true);
});

promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        if (e.shiftKey) {
            e.preventDefault();
            const cursorPos = promptInput.selectionStart;
            const textBefore = promptInput.value.substring(0, cursorPos);
            const textAfter = promptInput.value.substring(cursorPos);
            promptInput.value = textBefore + "\n" + textAfter;
            promptInput.selectionStart = promptInput.selectionEnd = cursorPos + 1;
        } else {
            e.preventDefault();
            controller = new AbortController();
            formSubmitParams.controller = controller;
            formSubmitParams.toggle_deepthink = deepThinkToggle.classList.contains("active");
            formSubmitParams.toggle_search = searchToggle.classList.contains("active");
            autoScroll = true;
            formSubmitParams.autoScroll = autoScroll;
            scrollIndicator.style.display = 'none';
            handleFormSubmit(e, formSubmitParams);
            scrollToBottom(true);
        }
    }
});

suggestions?.addEventListener("click", (e) => {
    const item = e.target.closest(".suggestions-item");
    if (item) {
        const text = item.querySelector(".text").textContent;
        promptInput.value = "";
        let i = 0;
        const interval = setInterval(() => {
            promptInput.value += text[i];
            i++;
            if (i >= text.length) {
                clearInterval(interval);
            }
        }, 10);
    }
});

document.addEventListener("click", ({ target }) => {
    const wrapper = document.querySelector(".prompt-wrapper");
    const shouldHide = target.classList.contains("prompt-input") ||
        (wrapper.classList.contains("hide-controls") &&
        (target.id === "upload-btn" || target.id === "stop-response-btn"));
    wrapper.classList.toggle("hide-controls", shouldHide);
});

stopResponseBtn.addEventListener("click", async () => {
    controller?.abort();
    stopResponseBtn.style.display = "none";
    sendPromptBtn.style.display = "block";
    if (lastResultThinking.trim()) {
        await savePartialResponse(lastResultThinking, true);
    }
    if (lastResultText.trim()) {
        await savePartialResponse(lastResultText, false);
    }
});

closeIframe.addEventListener("click", () => {
    closeIframe.style.display = "none";
    rightContainer.classList.remove("active");
});

moveSelectionRight.addEventListener("click", () => {
    rightElement.classList.remove("fullscreen");
});

moveSelectionLeft.addEventListener("click", () => {
    rightElement.classList.add("fullscreen");
});

document.addEventListener("DOMContentLoaded", function() {
    const attachBtn = document.getElementById("attach-file-btn");
    const fileInput = document.getElementById("file-input");
    const filePreviewList = document.querySelector(".file-preview-list");
    let attachedFiles = [];

    if (attachBtn && fileInput && filePreviewList) {
        attachBtn.addEventListener("click", () => fileInput.click());

        fileInput.addEventListener("change", (e) => {
            for (const file of e.target.files) {
                attachedFiles.push(file);
            }
            renderFilePreview();
            fileInput.value = ""; // reset input
        });
    }

    function renderFilePreview() {
        filePreviewList.innerHTML = "";
        attachedFiles.forEach((file, idx) => {
            const item = document.createElement("div");
            item.className = "file-preview-item";
            item.innerHTML = `
                <span class="file-icon">📄</span>
                <span class="file-name">${file.name}</span>
                <button class="remove-file-btn" title="Xóa file" data-idx="${idx}">&times;</button>
            `;
            filePreviewList.appendChild(item);
        });
        // Xử lý xóa file
        filePreviewList.querySelectorAll(".remove-file-btn").forEach(btn => {
            btn.onclick = (e) => {
                const idx = +btn.dataset.idx;
                attachedFiles.splice(idx, 1);
                renderFilePreview();
            };
        });
    }

    // --- Gửi chat kèm file upload nếu có ---
    promptForm.addEventListener("submit", async (e) => {
        controller = new AbortController();
        formSubmitParams.controller = controller;
        formSubmitParams.toggle_deepthink = deepThinkToggle.classList.contains("active");
        formSubmitParams.toggle_search = searchToggle.classList.contains("active");
        autoScroll = true;
        formSubmitParams.autoScroll = autoScroll;
        scrollIndicator.style.display = 'none';

        // Nếu có file đính kèm, upload trước rồi gửi chat
        if (attachedFiles.length > 0) {
            const uploadedFileInfos = [];
            for (const file of attachedFiles) {
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const response = await fetch('/chat/upload_image', {
                        method: 'POST',
                        body: formData
                    });
                    if (!response.ok) throw new Error('Không thể tải lên file');
                    const data = await response.json();
                    uploadedFileInfos.push(data.file_path);
                } catch (error) {
                    showError(error.message, chatsContainer, () => scrollToBottom(true));
                    e.preventDefault();
                    return;
                }
            }
            // Gửi chat kèm thông tin file (tuỳ backend xử lý)
            formSubmitParams.attachedFiles = uploadedFileInfos;
        } else {
            formSubmitParams.attachedFiles = [];
        }
        handleFormSubmit(e, formSubmitParams);
        scrollToBottom(true);
        // Sau khi gửi, reset file preview
        attachedFiles = [];
        renderFilePreview();
    });
});
