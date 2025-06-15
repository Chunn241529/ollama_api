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

let controller;
let userMessage = "";
let autoScroll = true;
let toggle_deepthink = false;
let toggle_search = false;
let model_current;

// Scroll event to toggle autoScroll
container.addEventListener("scroll", () => {
    const atBottom = Math.abs(container.scrollTop + container.clientHeight - container.scrollHeight) < 5;
    autoScroll = atBottom;
});

// Scroll to bottom
const scrollToBottom = () => {
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
};

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

// Fetch models on DOM load

// document.addEventListener("DOMContentLoaded", () => {
//     fetch("http://localhost:2401/chat/get_models_test")
//         .then((response) => response.json())
//         .then((data) => {
//             if (data.models && Array.isArray(data.models)) {
//                 const dropdown = document.getElementById("deep-think-options");
//                 data.models.forEach((model, index) => {
//                     const option = document.createElement("option");
//                     option.value = model;
//                     option.textContent = model;
//                     dropdown.appendChild(option);
//                     if (index === 0) {
//                         model_current = model;
//                         dropdown.value = model;
//                     }
//                 });
//                 console.log("Default model selected:", model_current);
//                 dropdown.addEventListener("change", (event) => {
//                     model_current = event.target.value;
//                     console.log("Model selected:", model_current);
//                 });
//             } else {
//                 console.error("Invalid data format:", data);
//             }
//         })
//         .catch((error) => console.error("Error fetching data:", error));
// });

// Generate response from API
const generateResponse = async (BotMsgDiv, is_deep_think = false, is_search = false) => {
    const textElement = BotMsgDiv.querySelector(".message-text");
    const thinkingOutput = BotMsgDiv.querySelector(".thinking-output");
    const modelName = BotMsgDiv.querySelector(".modelName");
    const ldsDualRing = BotMsgDiv.querySelector(".lds-dual-ring");
    controller = new AbortController();
    modelName.textContent = "4T AI";

    const userText = textElement.textContent.toLowerCase();
    const searchKeywords = ["tìm kiếm", "tra cứu", "nghiên cứu", "search"];
    is_search = is_search || searchKeywords.some((keyword) => userText.includes(keyword));

    // Hide loading indicators for the current message
    if (is_deep_think) {
        BotMsgDiv.querySelectorAll(".message-text .loading-bars").forEach((lb) => (lb.style.display = "none"));
    }
    ldsDualRing.style.display = "none"; // Always hide lds-dual-ring for this message

    if (is_search) {
        searchOutput.style.display = "block";
        moveSelectionRight.style.display = "none";
        moveSelectionLeft.style.display = "none";
    }

    let resultThinking = "";
    let resultText = "";
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
                chat_ai_id: 0,
                is_deep_think,
                is_search,
            }),
            signal: controller.signal,
        });

        if (!response.ok) {
            console.error("Failed to fetch response from API");
            return;
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
                    const content = jsonData.message?.content || "";

                    if (jsonData.num_results) {
                        num_search = jsonData.num_results;
                        search_results = jsonData.search_results;
                        if (search_results !== lastRenderedSearch) {
                            lastRenderedSearch = search_results;
                            await renderSearch(search_results);
                        }
                        searchOutput.textContent = `Tìm được ${num_search} kết quả`;
                    }

                    if (jsonData.type === "thinking") {
                        resultThinking += content;
                        thinkingOutput.style.borderLeft = "2px solid var(--think-color)";
                        thinkingOutput.innerHTML = marked.parse(resultThinking);
                    } else if (jsonData.type === "text") {
                        resultText += content;
                        textElement.innerHTML = marked.parse(resultText);
                    }
                } catch (e) {
                    console.error("JSON parse error:", e);
                }
            }

            const htmlContent = extractHTML(resultText);
            const cssContent = extractCSS(resultText);
            const jsContent = extractJavaScript(resultText);

            if (htmlContent !== lastRenderedHTML || cssContent !== lastRenderedCSS || jsContent !== lastRenderedJS) {
                lastRenderedHTML = htmlContent;
                lastRenderedCSS = cssContent;
                lastRenderedJS = jsContent;
                closeIframe.style.display = "block";
                rightContainer.classList.add("active");
                await renderCodeHtml(resultText);
                rightElement.classList.toggle("fullscreen", jsContent.trim().length > 0);
            }

            hljs.highlightAll();
            addCopyButtons();
            if (autoScroll) scrollToBottom();
        }

        if (buffer.trim()) {
            try {
                const jsonData = JSON.parse(buffer);
                const content = jsonData.message?.content || "";
                if (jsonData.num_results) {
                    num_search = jsonData.num_results;
                    searchOutput.textContent = `Tìm được ${num_search} kết quả`;
                }
                if (jsonData.type === "thinking") {
                    resultThinking += content;
                    thinkingOutput.innerHTML = marked.parse(resultThinking);
                } else if (jsonData.type === "text") {
                    resultText += content;
                    textElement.innerHTML = marked.parse(resultText);
                }
            } catch (e) {
                console.error("JSON parse error on final buffer:", e);
            }
        }

        hljs.highlightAll();
        addCopyButtons();
        if (autoScroll) scrollToBottom();
    } finally {
        stopResponseBtn.style.display = "none";
        sendPromptBtn.style.display = "block";
    }
};

// Stop response
stopResponseBtn.addEventListener("click", () => {
    controller?.abort();
    stopResponseBtn.style.display = "none";
    sendPromptBtn.style.display = "block";
});

// Hide suggestions and header
const hideSuggestion = (e, suggestion = "none", header = "none") => {
    suggestions.style.display = suggestion;
    appHeader.style.display = header;
};

// Handle form submission
const handleFormSubmit = (e) => {
    e.preventDefault();
    hideSuggestion(e);
    userMessage = promptInput.value.trim();
    if (!userMessage) return;

    const userMsgHTML = `<p class="message-text"></p>`;
    const userMsgDiv = createMsgElement(userMsgHTML, "user-message");
    userMsgDiv.querySelector(".message-text").textContent = userMessage;
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
                <span class="loading-bars"><span></span><span></span></span>
            </p>
        `;
        const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message");
        chatsContainer.appendChild(BotMsgDiv);

        document.getElementById("search").addEventListener("click", () => {
            closeIframe.style.display = "block";
            rightContainer.classList.add("active");
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
        autoScroll = true;
        if (autoScroll) scrollToBottom();
    }, 600);
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
        promptInput.value = item.querySelector(".text").textContent;
        promptForm.dispatchEvent(new Event("submit"));
    }
});

// Toggle prompt wrapper controls
document.addEventListener("click", ({ target }) => {
    const wrapper = document.querySelector(".prompt-wrapper");
    const shouldHide = target.classList.contains("prompt-input") ||
        (wrapper.classList.contains("hide-controls") &&
        (target.id === "add-file-btn" || target.id === "stop-response-btn"));
    wrapper.classList.toggle("hide-controls", shouldHide);
});

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
