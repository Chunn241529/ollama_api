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
const fileInput = document.getElementById("file-input");

let controller;
let userMessage = "";
let messages = [];
let autoScroll = true;
let toggle_deepthink = false;
let toggle_search = false;
let model_current;
let lastResultText = ""; // Lưu nội dung text/image_description mới nhất
let lastResultThinking = ""; // Lưu nội dung thinking mới nhất

// Dropdown toggle
uploadBtn.addEventListener("click", () => {
    uploadDropdown.classList.toggle("active");
});

// Check if input contains image URL or path
const isImageInput = (text) => {
    const urlPattern = /(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp))/i;
    return urlPattern.test(text);
};

// File input handling for image uploads
fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/chat/upload_image', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Không thể tải lên ảnh');
            }

            const data = await response.json();
            userMessage = promptInput.value.trim() || "Mô tả từng chi tiết của hình ảnh.";
            messages = [{
                role: "user",
                content: userMessage,
                image_url: data.image_url
            }];
            promptForm.dispatchEvent(new Event("submit"));
        } catch (error) {
            console.error('Lỗi khi tải lên ảnh:', error);
            showError(error.message);
        }
    }
    uploadDropdown.classList.remove("active");
});

// Click outside to close dropdown
document.addEventListener("click", (e) => {
    if (!uploadBtn.contains(e.target) && !uploadDropdown.contains(e.target)) {
        uploadDropdown.classList.remove("active");
    }
});

// Scroll event to toggle autoScroll
container.addEventListener("scroll", () => {
    const atBottom = Math.abs(container.scrollTop + container.clientHeight - container.scrollHeight) < 5;
    autoScroll = atBottom;
});

// Scroll to bottom
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

// Create scroll indicator
const scrollIndicator = document.createElement('button');
scrollIndicator.className = 'scroll-indicator';
scrollIndicator.innerHTML = '⬇ New messages';
scrollIndicator.style.cssText = `
    position: fixed;
    bottom: 210px;
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

// Scroll handling utilities
let isScrolling = false;
let scrollTimeout = null;
const SCROLL_THRESHOLD = 100;
const SCROLL_CHECK_DELAY = 150;

const handleScroll = () => {
    if (!isScrolling) {
        isScrolling = true;
        window.requestAnimationFrame(() => {
            const scrollPosition = container.scrollTop + container.clientHeight;
            const nearBottom = container.scrollHeight - scrollPosition <= SCROLL_THRESHOLD;

            autoScroll = nearBottom;
            scrollIndicator.style.display = autoScroll ? 'none' : 'block';
            isScrolling = false;
        });
    }

    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
    }
    scrollTimeout = setTimeout(() => {
        isScrolling = false;
    }, SCROLL_CHECK_DELAY);
};

container.addEventListener("scroll", handleScroll, { passive: true });

scrollIndicator.addEventListener('click', () => {
    scrollToBottom(true);
    scrollIndicator.style.display = 'none';
    autoScroll = true;
});

// Horizontal scroll for suggestions
suggestions.addEventListener("wheel", (event) => {
    event.preventDefault();
    event.currentTarget.scrollBy({ left: event.deltaY < 0 ? -30 : 30 });
});

// Auto-resize textarea
promptInput.addEventListener("input", () => {
    promptInput.style.height = "auto";
    promptInput.style.height = `${promptInput.scrollHeight}px`;
});

// Toggle search mode
searchToggle.addEventListener("click", () => {
    searchToggle.classList.toggle("active");
    toggle_search = searchToggle.classList.contains("active");
    console.log(`Chế độ tìm kiếm ${toggle_search ? "được kích hoạt" : "bị tắt"}`);
});

// Toggle deep think mode
deepThinkToggle.addEventListener("click", () => {
    deepThinkToggle.classList.toggle("active");
    toggle_deepthink = deepThinkToggle.classList.contains("active");
    console.log(`Chế độ deep think ${toggle_deepthink ? "được kích hoạt" : "bị tắt"}`);
});

// Create message element
const createMsgElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
};

// Show error message
const showError = (message) => {
    const errorDiv = document.createElement("div");
    errorDiv.className = "error-message";
    errorDiv.style.cssText = `
        background: #ff4d4d;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        text-align: center;
    `;
    errorDiv.textContent = message;
    chatsContainer.appendChild(errorDiv);
    scrollToBottom();
};

// Add copy buttons to code blocks
const addCopyButtons = (() => {
    let clipboardInitialized = false;
    return () => {
        const blocks = document.querySelectorAll("pre code");
        if (blocks.length === 0) return;

        blocks.forEach((block, index) => {
            const pre = block.parentElement;
            if (pre.querySelector(".copy-btn")) return;

            const copyBtn = document.createElement("button");
            copyBtn.className = "copy-btn";
            copyBtn.innerHTML = `<i class="material-symbols-rounded">content_copy</i>`;
            copyBtn.style.cssText = `
                position: absolute;
                top: 5px;
                right: 5px;
                cursor: pointer;
                border: none;
                background: transparent;
                padding: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #aaa;
            `;
            if (!block.id) block.id = `code-block-${index}`;
            copyBtn.setAttribute("data-clipboard-target", `#${block.id}`);
            pre.style.position = "relative";
            pre.appendChild(copyBtn);
        });

        if (!clipboardInitialized && document.querySelectorAll(".copy-btn").length > 0) {
            const clipboard = new ClipboardJS(".copy-btn");
            clipboard.on("success", (e) => {
                e.clearSelection();
                e.trigger.innerHTML = "Đã lưu";
                setTimeout(() => {
                    e.trigger.innerHTML = `<i class="material-symbols-rounded">content_copy</i>`;
                }, 3000);
            });
            clipboardInitialized = true;
        }
    };
})();

// Save partial response to backend
const savePartialResponse = async (content, isThinking = false) => {
    if (!content.trim()) {
        console.log("No partial content to save");
        return;
    }
    try {
        const response = await fetch("http://localhost:2401/chat/save_partial", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                content: content,
                chat_ai_id: 0,
                is_thinking: isThinking
            })
        });
        if (!response.ok) {
            throw new Error("Không thể lưu phản hồi dở dang");
        }
        console.log(`Saved partial ${isThinking ? "thinking" : "text"} response:`, content.slice(0, 50) + "...");
    } catch (error) {
        console.error("Error saving partial response:", error);
        showError("Không thể lưu phản hồi dở dang");
    }
};

// Generate response from API
const generateResponse = async (BotMsgDiv, is_deep_think = false, is_search = false, is_image = false) => {
    const textElement = BotMsgDiv.querySelector(".message-text");
    const thinkingOutput = BotMsgDiv.querySelector(".thinking-output");
    const modelName = BotMsgDiv.querySelector(".modelName");
    const ldsDualRing = BotMsgDiv.querySelector(".lds-dual-ring");
    controller = new AbortController();
    modelName.textContent = "4T AI";

    ldsDualRing.style.display = "none";

    const userText = userMessage.toLowerCase();
    const searchKeywords = ["tìm kiếm", "tra cứu", "nghiên cứu", "search"];
    is_search = is_search || searchKeywords.some((keyword) => userText.includes(keyword));

    const isGeneratingImage = userText.includes("tạo ảnh") || userText.includes("tạo hình ảnh");
    is_image = is_image || isImageInput(userText);

    textElement.innerHTML = `<span class="loading-bars"><span></span><span></span><span></span></span>`;
    if (is_deep_think) {
        BotMsgDiv.querySelectorAll(".message-text .loading-bars").forEach((lb) => (lb.style.display = "none"));
        ldsDualRing.style.display = "block";
    } else if (is_search) {
        searchOutput.style.display = "block";
        moveSelectionRight.style.display = "none";
        moveSelectionLeft.style.display = "none";
    } else {
        ldsDualRing.style.display = "none";
    }

    lastResultThinking = "";
    lastResultText = "";
    let lastRenderedHTML = "";
    let lastRenderedCSS = "";
    let lastRenderedJS = "";
    let lastRenderedSearch = "";
    let num_search = "";
    let search_results = "";

    try {
        const response = await fetch("http://localhost:2401/chat/test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: userMessage,
                messages: messages,
                chat_ai_id: 0,
                is_deep_think,
                is_search,
                is_image,
                is_generate_image: isGeneratingImage
            }),
            signal: controller.signal,
        });

        if (!response.ok) {
            throw new Error("Không thể kết nối với API chat.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const jsonData = JSON.parse(line);
                    if (jsonData.type === "thinking") {
                        lastResultThinking += jsonData.message?.content || "";
                        thinkingOutput.style.borderLeft = "2px solid var(--think-color)";
                        thinkingOutput.innerHTML = marked.parse(lastResultThinking);
                    } else if (jsonData.type === "text" || jsonData.type === "image_description") {
                        lastResultText += jsonData.message?.content || "";
                        textElement.innerHTML = marked.parse(lastResultText);
                    } else if (jsonData.type === "image") {
                        const imageBase64 = jsonData.image_base64;
                        const mimeType = jsonData.mime_type || "image/png";
                        const imageSrc = `data:${mimeType};base64,${imageBase64}`;

                        console.log("Image chunk received:", { imageBase64: imageBase64.slice(0, 50) + "...", mimeType });

                        textElement.innerHTML = `
                            <div class="image-message">
                                <img src="${imageSrc}" class="message-image" alt="Ảnh được tạo" style="max-width: 100%; height: auto; cursor: pointer;">
                            </div>
                        `;

                        addImageClickHandler(textElement, imageSrc, mimeType);
                    } else if (jsonData.type === "error") {
                        console.error("API error:", jsonData.error || jsonData.message);
                        showError(jsonData.error || jsonData.message || "Failed to process the request.");
                    }
                } catch (e) {
                    console.error("JSON parse error:", e);
                }

                const htmlContent = extractHTML(lastResultText);
                const cssContent = extractCSS(lastResultText);
                const jsContent = extractJavaScript(lastResultText);

                if (htmlContent !== lastRenderedHTML || cssContent !== lastRenderedCSS || jsContent !== lastRenderedJS) {
                    lastRenderedHTML = htmlContent;
                    lastRenderedCSS = cssContent;
                    lastRenderedJS = jsContent;
                    closeIframe.style.display = "block";
                    rightContainer.classList.add("active");
                    await renderCodeHtml(lastResultText);
                    rightElement.classList.toggle("fullscreen", jsContent.trim().length > 0);
                }

                hljs.highlightAll();
                addCopyButtons();
                if (autoScroll) scrollToBottom();
            }
        }

        if (buffer.trim()) {
            try {
                const jsonData = JSON.parse(buffer);
                if (jsonData.type === "thinking") {
                    lastResultThinking += jsonData.message?.content || "";
                    thinkingOutput.innerHTML = marked.parse(lastResultThinking);
                } else if (jsonData.type === "text" || jsonData.type === "image_description") {
                    lastResultText += jsonData.message?.content || "";
                    textElement.innerHTML = marked.parse(lastResultText);
                } else if (jsonData.type === "image") {
                    const imageBase64 = jsonData.image_base64;
                    const mimeType = jsonData.mime_type || "image/png";
                    const imageSrc = `data:${mimeType};base64,${imageBase64}`;

                    textElement.innerHTML = `
                        <div class="image-message">
                            <img src="${imageSrc}" class="message-image" alt="Ảnh được tạo" style="max-width: 100%; height: auto; cursor: pointer;">
                        </div>
                    `;

                    addImageClickHandler(textElement, imageSrc, mimeType);
                } else if (jsonData.type === "error") {
                    showError(jsonData.error || jsonData.message || "Failed to process the request.");
                }
            } catch (e) {
                console.error("JSON parse error on final buffer:", e);
            }
        }

        hljs.highlightAll();
        addCopyButtons();
        if (autoScroll) scrollToBottom();
    } catch (error) {
        if (error.name === "AbortError") {
            console.log("Response aborted by user");
            // Lưu phản hồi dở dang
            if (lastResultThinking.trim()) {
                await savePartialResponse(lastResultThinking, true);
            }
            if (lastResultText.trim()) {
                await savePartialResponse(lastResultText, false);
            }
        } else {
            console.error("Error in generateResponse:", error);
            showError(error.message);
        }
    } finally {
        stopResponseBtn.style.display = "none";
        sendPromptBtn.style.display = "block";
    }
};

// Stop response
stopResponseBtn.addEventListener("click", async () => {
    controller?.abort();
    stopResponseBtn.style.display = "none";
    sendPromptBtn.style.display = "block";
    // Lưu phản hồi dở dang ngay khi nhấn Stop
    if (lastResultThinking.trim()) {
        await savePartialResponse(lastResultThinking, true);
    }
    if (lastResultText.trim()) {
        await savePartialResponse(lastResultText, false);
    }
});

// Hide suggestions and header
const hideSuggestion = (e, suggestion = "none", header = "none") => {
    suggestions.style.display = suggestion;
    appHeader.style.display = header;
};

// Handle form submission
const handleFormSubmit = async (e) => {
    e.preventDefault();
    hideSuggestion(e);
    userMessage = promptInput.value.trim();
    if (!userMessage) return;

    try {
        const imageResult = await processImageInput(userMessage);

        const userMsgHTML = `<div class="message-text"></div>`;
        const userMsgDiv = createMsgElement(userMsgHTML, "user-message");
        userMsgDiv.querySelector(".message-text").innerHTML = marked.parse(userMessage);

        userMsgDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        chatsContainer.appendChild(userMsgDiv);

        promptInput.value = "";
        promptInput.style.height = "77px";
        stopResponseBtn.style.display = "block";
        sendPromptBtn.style.display = "none";

        setTimeout(() => {
            const BotMsgHTML = `
                <img src="templates/static/assets/img/1.jpg" alt="" class="avatar"><p class="modelName"></p>
                <button type="button" class="search-output" id="search">
                    <svg class="search-icon" viewBox="0 0 24 24" width="24" height="24">
                        <path fill="currentColor" d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 0 0 1.48-5.34c-.47-2.78-2.79-5-5.59-5.34a6.505 6.505 0 0 0-7.27 7.27c.34 2.8 2.56 5.12 5.34 5.59a6.5 6.5 0 0 0 5.34-1.48l.27.28v.79l4.25 4.25c.41.41 1.08.41 1.49 0 .41-.41.41-1.08 0-1.49L15.5 14zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                    </svg>
                </button>
                <div class="thinking-container">
                    <p class="thinking-output"></p>
                    <span class="lds-dual-ring"></span>
                </div>
                <p class="message-text">
                    <span class="loading-bars"><span></span><span></span><span></span></span>
                </p>
            `;
            const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message");
            chatsContainer.appendChild(BotMsgDiv);

            document.getElementById("search").addEventListener("click", () => {
                closeIframe.style.display = "block";
                rightContainer.classList.add("active");
            });

            messages = [];

            if (imageResult.isImage) {
                messages.push({
                    role: "user",
                    content: imageResult.description,
                    image_url: imageResult.image_url
                });
                generateResponse(BotMsgDiv, false, false, true);
            } else {
                messages.push({
                    role: "user",
                    content: userMessage
                });

                if (toggle_search && toggle_deepthink) {
                    generateResponse(BotMsgDiv, true, true);
                } else if (toggle_search) {
                    generateResponse(BotMsgDiv, false, true);
                } else if (toggle_deepthink) {
                    generateResponse(BotMsgDiv, true, false);
                } else {
                    generateResponse(BotMsgDiv, false, false);
                }
            }

            autoScroll = true;
            if (autoScroll) scrollToBottom();
        }, 600);
    } catch (error) {
        showError(error.message);
    }
};

// Form submission and keydown handling
promptForm.addEventListener("submit", handleFormSubmit);
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
            handleFormSubmit(e);
            autoScroll = true;
            if (autoScroll) scrollToBottom();
        }
    }
});

// Event delegation for suggestions
suggestions.addEventListener("click", (e) => {
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

// Toggle prompt wrapper controls
document.addEventListener("click", ({ target }) => {
    const wrapper = document.querySelector(".prompt-wrapper");
    const shouldHide = target.classList.contains("prompt-input") ||
        (wrapper.classList.contains("hide-controls") &&
        (target.id === "upload-btn" || target.id === "stop-response-btn"));
    wrapper.classList.toggle("hide-controls", shouldHide);
});

// Add CSS for dropdown
const style = document.createElement("style");
style.textContent = `
    .dropdown {
        position: relative;
        display: inline-block;
    }
    .dropdown-toggle {
        background: transparent;
        border: none;
        color: var(--text-color);
        padding: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
    }
    .dropdown-menu {
        display: none;
        position: absolute;
        background: var(--secondary-color);
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        min-width: 120px;
        top: 100%;
        left: 0;
    }
    .dropdown-menu.active {
        display: block;
    }
    .dropdown-item {
        display: block;
        padding: 8px 12px;
        color: var(--text-color);
        text-decoration: none;
        cursor: pointer;
    }
    .dropdown-item:hover {
        background: var(--secondary-hover-color);
    }
`;
document.head.appendChild(style);

// Check if input contains image URL and process it
const processImageInput = async (text) => {
    const urlPattern = /(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp))/i;
    const match = text.match(urlPattern);

    if (match) {
        try {
            const imageUrl = match[0];
            const description = text.replace(imageUrl, "").trim() || "Mô tả từng chi tiết của hình ảnh.";
            return {
                isImage: true,
                image_url: imageUrl,
                description: description
            };
        } catch (error) {
            console.error("Error processing image URL:", error);
            throw new Error("Không thể tải ảnh từ URL này. Vui lòng thử URL khác hoặc tải ảnh trực tiếp.");
        }
    }

    const filePattern = /file:\/\/[^\s]+/i;
    const fileMatch = text.match(filePattern);
    if (fileMatch) {
        const filePath = fileMatch[0];
        const description = text.replace(filePath, "").trim() || "Mô tả từng chi tiết của hình ảnh.";
        return {
            isImage: true,
            image_url: filePath,
            description: description
        };
    }

    return { isImage: false };
};

// Code extraction functions
const extractHTML = (response) => {
    const match = response.match(/```html\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
};

const extractCSS = (response) => {
    const match = response.match(/```css\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
};

const extractJavaScript = (response) => {
    const match = response.match(/```javascript\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
};

const extractPython = (response) => {
    const match = response.match(/```python\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
};

// Render HTML/CSS/JS to iframe
const renderCodeHtml = async (extract) => {
    rightContainer.style.background = "#fff";
    const htmlContent = extractHTML(extract);
    const cssContent = extractCSS(extract);
    const jsContent = extractJavaScript(extract);
    if (!htmlContent) return;

    const fullHTML = `
        <html>
            <head>
                <style>
                    ${cssContent}
                </style>
            </head>
            <body>
                ${htmlContent}
                <script type="module">
                    ${jsContent}
                </script>
            </body>
        </html>
    `;
    const blob = new Blob([fullHTML], { type: "text/html" });
    const blobURL = URL.createObjectURL(blob);
    outputIframe.src = blobURL;
};

// Render search results
const renderSearch = async (search_results) => {
    const cssContent = `
        @import url('https://fonts.googleapis.com/css2?family=Itim&display=swap');
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Itim", serif;
        }
        :root {
            --text-color: #edf3ff;
            --think-color: #aaaaaad8;
            --subheading-color: #97a7ca;
            --placeholder-color: #c3cdde;
            --primary-color: #101623;
            --secondary-color: #283045;
            --secondary-hover-color: #333e58;
            --scrollbar-color: #626a7f;
        }
        .search-box {
            padding: 10px;
            box-shadow: 0 4px 8px rgba(3, 3, 3, 0.8);
            border-radius: 10px;
            margin: 20px;
            background: #333e58;
            color: var(--text-color);
            word-wrap: break-word;
            font-family: "Source Code Pro", serif;
            border: none;
        }
        .search-box:hover {
            background: rgba(68, 75, 90, 0.87);
        }
        .search-title {
            font-size: 18px;
            margin: 10px 0;
        }
        .search-description {
            font-size: 14px;
            margin: 5px 0;
        }
        a {
            text-decoration: none;
            color: inherit;
        }
    `;
    const htmlContent = search_results.map(
        (result) => `
        <a href="${result.href}" target="_blank">
            <div class="search-box">
                <h2 class="search-title">${result.title}</h2>
                <p class="search-description">${result.body}</p>
            </div>
        </a>
    `
    ).join("");
    const jsContent = "";
    const fullHTML = `
        <html>
            <head>
                <style>
                    ${cssContent}
                </style>
            </head>
            <body>
                ${htmlContent}
                <script type="module">
                    ${jsContent}
                </script>
            </body>
        </html>
    `;
    const blob = new Blob([fullHTML], { type: "text/html" });
    const blobURL = URL.createObjectURL(blob);
    outputIframe.src = blobURL;
};

// Iframe controls
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

// Handle image click to view in full screen
const addImageClickHandler = (container, imageSrc, mimeType) => {
    const fileExt = mimeType.split("/")[1];
    container.querySelector(".message-image")?.addEventListener("click", () => {
        const imageIframeHTML = `
            <html>
                <head>
                    <style>
                        :root {
                            --text-color: #edf3ff;
                            --secondary-color: #283045;
                            --secondary-hover-color: #333e58;
                        }
                        body {
                            margin: 0;
                            padding: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            background: rgba(0, 0, 0, 0.7);
                            backdrop-filter: blur(5px);
                        }
                        .image-container {
                            position: relative;
                            max-width: 90%;
                            max-height: 90%;
                        }
                        img {
                            max-width: 100%;
                            max-height: 100%;
                            object-fit: contain;
                        }
                        .download-btn {
                            position: absolute;
                            top: 10px;
                            right: 10px;
                            background: var(--secondary-hover-color);
                            color: var(--text-color);
                            border: none;
                            padding: 8px 16px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-family: 'Itim', sans-serif;
                        }
                        .download-btn:hover {
                            background: var(--secondary-color);
                        }
                    </style>
                </head>
                <body>
                    <div class="image-container">
                        <img src="${imageSrc}" alt="Ảnh được tạo/xử lý">
                        <a href="${imageSrc}" download="generated_image.${fileExt}" class="download-btn">Tải ảnh</a>
                    </div>
                </body>
            </html>
        `;
        const blob = new Blob([imageIframeHTML], { type: "text/html" });
        const blobURL = URL.createObjectURL(blob);
        const imageIframe = document.createElement("iframe");
        imageIframe.id = "imageIframe";
        imageIframe.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
            z-index: 1000;
        `;
        document.body.appendChild(imageIframe);
        imageIframe.src = blobURL;

        const closeImageIframe = document.createElement("button");
        closeImageIframe.innerHTML = `<i class="material-symbols-rounded">close</i>`;
        closeImageIframe.style.cssText = `
            position: fixed;
            top: 10px;
            left: 10px;
            background: var(--secondary-hover-color);
            color: var(--text-color);
            border: none;
            padding: 8px;
            border-radius: 5px;
            cursor: pointer;
            z-index: 1001;
        `;
        document.body.appendChild(closeImageIframe);
        closeImageIframe.addEventListener("click", () => {
            document.body.removeChild(imageIframe);
            document.body.removeChild(closeImageIframe);
            URL.revokeObjectURL(blobURL);
        });
    });
};

const imageStyles = document.createElement("style");
imageStyles.textContent = `
    .image-message {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        max-width: 100%;
        gap: 8px;
    }
    .image-message img {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .image-message img:hover {
        transform: scale(1.02);
    }
`;
document.head.appendChild(imageStyles);
