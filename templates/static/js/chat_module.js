const container = document.querySelector(".container")
const chatsContainer = document.querySelector(".chats-container");
const promptForm = document.querySelector(".prompt-form");
const promptInput = promptForm.querySelector(".prompt-input");

let controller;
let userMessage = "";

let autoScroll = true; // Ban đầu cho phép tự động scroll


container.addEventListener("scroll", () => {
    const atBottom = Math.abs(container.scrollTop + container.clientHeight - container.scrollHeight) < 10; // Kiểm tra có gần cuối hay không
    autoScroll = atBottom;
});

const scrollToBottom = () => {
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
};


document.querySelector('.suggestions').addEventListener('wheel', (event) => {
    event.preventDefault();
    event.currentTarget.scrollBy({
        left: event.deltaY < 0 ? -30 : 30,
    });
});
const textarea = document.querySelector('.prompt-input');

textarea.addEventListener('input', () => {
    textarea.style.height = 'auto'; // Reset chiều cao
    textarea.style.height = `${textarea.scrollHeight}px`; // Đặt chiều cao dựa trên nội dung
});
const searchToggle = document.getElementById('search-toggle');
const deepThinkToggle = document.getElementById('deep-think-toggle');

let toggle_deepthink = false;
let toggle_search = false;

searchToggle.addEventListener('click', () => {
    searchToggle.classList.toggle('active');
    if (searchToggle.classList.contains('active')) {
        toggle_search = true;
        console.log('Chế độ tìm kiếm được kích hoạt');
    } else {
        toggle_search = false;
        console.log('Chế độ tìm kiếm bị tắt');
    }
});

deepThinkToggle.addEventListener('click', () => {
    deepThinkToggle.classList.toggle('active');
    if (deepThinkToggle.classList.contains('active')) {
        toggle_deepthink = true;
        console.log('Chế độ deep think được kích hoạt');
    } else {
        toggle_deepthink = false;
        console.log('Chế độ deep think bị tắt');
    }
});

const createMsgElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
}

function addCopyButtons() {
    const blocks = document.querySelectorAll('pre code');
    if (blocks.length === 0) return;

    blocks.forEach((block, index) => {
        const pre = block.parentElement;

        // Nếu đã có nút copy thì bỏ qua
        if (pre.querySelector('.copy-btn')) return;

        // Tạo nút copy
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = `<i class="material-symbols-rounded">content_copy</i>`;

        // Đặt ID cho block nếu chưa có
        if (!block.id) {
            block.id = `code-block-${index}`;
        }
        copyBtn.setAttribute('data-clipboard-target', `#${block.id}`);

        // Định dạng nút copy bằng CSS inline
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

        pre.style.position = 'relative';
        pre.appendChild(copyBtn);
    });

    // Khởi tạo ClipboardJS một lần cho tất cả nút copy
    if (document.querySelectorAll('.copy-btn').length > 0) {
        const clipboard = new ClipboardJS('.copy-btn');

        clipboard.on('success', function (e) {
            // Xóa lựa chọn (highlight) code sau khi copy
            e.clearSelection();
            // Thay đổi nội dung của nút copy thành "Đã lưu"
            e.trigger.innerHTML = "Đã lưu";
            setTimeout(() => {
                e.trigger.innerHTML = `<i class="material-symbols-rounded">content_copy</i>`;
            }, 3000);
        });
    }
}

let model_current;

document.addEventListener('DOMContentLoaded', function () {

    fetch('http://localhost:2401/chat/get_models_test')
        .then(response => response.json())
        .then(data => {
            if (data.models && Array.isArray(data.models)) {
                const dropdown = document.getElementById('deep-think-options');

                data.models.forEach((model, index) => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    dropdown.appendChild(option);

                    // Chọn giá trị đầu tiên nếu chưa có model_current
                    if (index === 0) {
                        model_current = model;
                        dropdown.value = model; // Hiển thị giá trị mặc định trên dropdown
                    }
                });

                console.log('Default model selected:', model_current);

                // Cập nhật model khi thay đổi dropdown
                dropdown.addEventListener('change', (event) => {
                    model_current = event.target.value;
                    console.log('Model selected:', model_current);
                });
            } else {
                console.error('Invalid data format:', data);
            }
        })
        .catch(error => console.error('Error fetching data:', error));
});


const generateResponse = async (BotMsgDiv, is_deep_think = false, is_search = false) => {
    const textElement = BotMsgDiv.querySelector(".message-text");
    const thinkingOutput = BotMsgDiv.querySelector(".thinking-output");
    const modelName = BotMsgDiv.querySelector('.modelName');
    const searchOutput = document.querySelector(".search-output");

    controller = new AbortController();

    modelName.textContent = "chun-gpt";

    if (is_deep_think) {
        const loadingBars = BotMsgDiv.querySelectorAll('.message-text .loading-bars');
        loadingBars.forEach(lb => lb.style.display = 'none');
    } else {
        document.querySelector(".lds-dual-ring").style.display = "none";
    }

    if (is_search || is_search && is_deep_think) {
        searchOutput.style.display = "block";
        document.getElementById("move_selection_right").style.display = "none";
        document.getElementById("move_selection_left").style.display = "none";
    }

    // Khởi tạo biến riêng cho mỗi loại kết quả
    let resultThinking = "";
    let resultText = "";

    const response = await fetch("http://localhost:2401/chat/test", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: userMessage,
            // model: model_current,
            chat_ai_id: 0,
            is_deep_think: is_deep_think,
            is_search: is_search,
        }),
        signal: controller.signal
    });

    if (!response.ok) {
        console.error("Failed to fetch response from API");
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let num_search = "";
    let search_results = "";

    // Reset các biến khi bắt đầu response mới
    document.querySelector('.right-container').classList.remove('active');
    document.querySelector('.right').classList.remove('fullscreen');
    document.getElementById("close-iframe").style.display = "none";


    let lastRenderedHTML = "";
    let lastRenderedCSS = "";
    let lastRenderedJS = "";
    let lastRenderedSearch = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split("\n");
        buffer = lines.pop();

        for (let line of lines) {
            if (!line.trim()) continue;

            try {
                const jsonData = JSON.parse(line);
                let content = (jsonData.message && jsonData.message.content) ? jsonData.message.content : "";

                if (jsonData.num_results) {
                    num_search = jsonData.num_results;
                    search_results = jsonData.search_results;

                    if (search_results !== lastRenderedSearch) {
                        lastRenderedSearch = search_results;
                        await renderSearch(search_results);
                    }
                }

                // Chỉ cập nhật nếu có giá trị `num_search`
                if (num_search) {
                    searchOutput.textContent = `Tìm được ${num_search} kết quả`;
                }


                if (jsonData.type === "thinking") {
                    thinkingOutput.style.borderLeft = '2px solid var(--think-color)';
                    resultThinking += content;
                    thinkingOutput.innerHTML = marked.parse(resultThinking);
                } else if (jsonData.type === "text") {
                    document.querySelector(".lds-dual-ring").style.display = "none";
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

        // Kiểm tra từng loại nội dung, nếu có sự thay đổi thì cập nhật
        if (htmlContent !== lastRenderedHTML) {
            lastRenderedHTML = htmlContent;
            document.getElementById("close-iframe").style.display = "block";
            document.querySelector('.right-container').classList.add('active');
            await renderCodeHtml(resultText);
        }

        if (cssContent !== lastRenderedCSS) {
            lastRenderedCSS = cssContent;
            await renderCodeHtml(resultText);
        }

        if (jsContent !== lastRenderedJS) {
            lastRenderedJS = jsContent;
            await renderCodeHtml(resultText);

            // Chỉ thêm fullscreen khi thực sự có JS content
            const rightElement = document.querySelector('.right');
            if (jsContent.trim().length > 0) {
                rightElement.classList.add('fullscreen');
            } else {
                rightElement.classList.remove('fullscreen'); // Xóa class nếu không có JS
            }
        }


        // Các xử lý bổ sung
        hljs.highlightAll();
        addCopyButtons();

        if (autoScroll) {
            scrollToBottom();
        }
    }

    // Nếu có dữ liệu còn lại trong buffer sau khi đọc xong
    if (buffer.trim()) {
        try {
            const jsonData = JSON.parse(buffer);
            let content = (jsonData.message && jsonData.message.content) ? jsonData.message.content : "";
            // Chỉ cập nhật `num_search` nếu nó tồn tại
            if (jsonData.num_results) {
                num_search = jsonData.num_results;
            }

            // Chỉ cập nhật nếu có giá trị `num_search`
            if (num_search) {
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

    if (autoScroll) {
        scrollToBottom();
    }

    // Khi hoàn thành việc generate response, thay đổi trạng thái nút
    document.querySelector("#stop-response-btn").style.display = "none";
    document.querySelector("#send-prompt-btn").style.display = "block";

};

// Ngừng xử lý nếu người dùng nhấn nút Stop
document.querySelector("#stop-response-btn").addEventListener("click", () => {
    controller?.abort();
    const btn_stop = document.querySelector("#stop-response-btn");
    const btn_send = document.querySelector("#send-prompt-btn");
    btn_stop.style.display = "none";  // Ẩn nút stop
    btn_send.style.display = "block"; // Hiển thị nút send
});


const hideSuggestion = (e, suggestion = `none`, header = `none`) => {
    const suggestions = document.querySelector(".suggestions");
    const app_header = document.querySelector(".app-header");

    suggestions.style.display = suggestion;
    app_header.style.display = header;
}

const handleFormSubmit = (e) => {
    e.preventDefault();
    const btn_stop = document.querySelector("#stop-response-btn");
    const btn_send = document.querySelector("#send-prompt-btn");
    hideSuggestion(e);


    userMessage = promptInput.value.trim();
    if (!userMessage) return;

    const userMsgHTML = `<p class="message-text"></p>`;
    const userMsgDiv = createMsgElement(userMsgHTML, "user-message");
    userMsgDiv.querySelector(".message-text").textContent = userMessage;
    chatsContainer.appendChild(userMsgDiv);

    promptInput.value = ""; // Clear the input value after submitting
    textarea.style.height = `77px`;
    btn_stop.style.display = `block`;
    btn_send.style.display = `none`;

    setTimeout(() => {
        const BotMsgHTML = `
            <img src="templates/static/assets/img/1.jpg" alt="" class="avatar"><p class="modelName"></p>
            <button type="button" class="search-output" id="search">
                <svg class="search-icon" viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 0 0 1.48-5.34c-.47-2.78-2.79-5-5.59-5.34a6.505 6.505 0 0 0-7.27 7.27c.34 2.8 2.56 5.12 5.34 5.59a6.5 6.5 0 0 0 5.34-1.48l.27.28v.79l4.25 4.25c.41.41 1.08.41 1.49 0 .41-.41.41-1.08 0-1.49L15.5 14zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
            </button>
            
            <div class="thinking-container">
                <p class="thinking-output">
                </p>
                <span class="lds-dual-ring"></span>
            </div>
     
            <p class="message-text">
                <span class="loading-bars">
                    <span></span><span></span><span></span>
                </span>
                <span class="loading-bars">
                    <span></span><span></span>
                </span>
            </p>
        `;

        const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message");
        chatsContainer.appendChild(BotMsgDiv);

        const searchElement = document.getElementById("search");
        searchElement.addEventListener("click", async function () {
            document.getElementById("close-iframe").style.display = "block";
            document.querySelector('.right-container').classList.add('active');
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
        if (autoScroll) {
            scrollToBottom();
        }
    }, 600);
};



promptForm.addEventListener("submit", handleFormSubmit);

promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        if (e.shiftKey) {
            // Nếu giữ Shift + Enter, chèn xuống dòng
            e.preventDefault(); // Ngăn chặn gửi form
            const cursorPos = promptInput.selectionStart;
            const textBefore = promptInput.value.substring(0, cursorPos);
            const textAfter = promptInput.value.substring(cursorPos);
            promptInput.value = textBefore + "\n" + textAfter;
            promptInput.selectionStart = promptInput.selectionEnd = cursorPos + 1; // Đặt con trỏ sau dòng mới
        } else {
            // Nếu chỉ nhấn Enter, gửi form
            e.preventDefault();
            handleFormSubmit(e);
            autoScroll = true;
            if (autoScroll) {
                scrollToBottom();
            }
        }
    }
});



document.querySelectorAll(".suggestions-item").forEach(item => {
    item.addEventListener("click", () => {
        promptInput.value = item.querySelector(".text").textContent;
        promptForm.dispatchEvent(new Event("submit"));
    })
})

document.addEventListener("click", ({ target }) => {
    const wrapper = document.querySelector(".prompt-wrapper");
    const shouldHide = target.classList.contains(".prompt-input") || (wrapper.classList.contains("hide-controls") && (target.id === "add-file-btn") || (target.id === "stop-response-btn"));
    wrapper.classList.toggle("hide-controls", shouldHide);
})


// 🔹 Hàm trích xuất code block
function extractHTML(response) {
    let match = response.match(/```html\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
}

function extractCSS(response) {
    let match = response.match(/```css\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
}

function extractJavaScript(response) {
    let match = response.match(/```javascript\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
}

function extractPython(response) {
    let match = response.match(/```python\n([\s\S]*?)```/);
    return match ? match[1].trim() : "";
}


// 🔹 Render HTML vào iframe
async function renderCodeHtml(extract) {
    document.querySelector(".right-container").style.background = "#fff";
    const htmlContent = extractHTML(extract);
    const cssContent = extractCSS(extract);
    const jsContent = extractJavaScript(extract);
    if (!htmlContent) return;

    // Tạo Blob URL từ HTML và CSS
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
                    <\/script>
                </body>
            </html>
        `;
    const blob = new Blob([fullHTML], { type: "text/html" });
    const blobURL = URL.createObjectURL(blob);

    // Gán vào iframe
    document.getElementById("output").src = blobURL;
}

async function renderSearch(search_results) {

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
            background:rgba(68, 75, 90, 0.87);
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

    const htmlContent = search_results.map(result => `
        <a href="${result.href}" target="_blank">
            <div class="search-box">
                <h2 class="search-title">${result.title}</h2>
                <p class="search-description">${result.body}</p>
            </div>
        </a>
        
    `).join('');

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
                <\/script>
            </body>
        </html>
    `;

    const blob = new Blob([fullHTML], { type: "text/html" });
    const blobURL = URL.createObjectURL(blob);

    document.getElementById("output").src = blobURL;
}


// Trình run code python trên trình duyệt
// async function loadPyodideInstance() {
//     window.pyodide = await loadPyodide();
//     console.log("✅ Pyodide đã tải xong!");
// }
// loadPyodideInstance();

// function isPyodideReady() {
//     return window.pyodide && typeof window.pyodide.runPythonAsync === "function";
// }

// async function renderPythonCode(extract) {
//     const pythonCode = extractPython(extract);
//     if (!pythonCode) return alert("Không tìm thấy code Python!");

//     // Chờ Pyodide tải hoàn tất
//     if (!isPyodideReady()) {
//         alert("Pyodide chưa sẵn sàng! Vui lòng đợi...");
//         return;
//     }

//     try {
//         const result = await window.pyodide.runPythonAsync(pythonCode); // ✅ Đã có `await`
//         alert(result);

//     } catch (error) {
//         alert("Lỗi khi chạy code: " + error);
//     }
// }

document.getElementById("close-iframe").addEventListener("click", function () {
    document.getElementById("close-iframe").style.display = "none";
    document.querySelector('.right-container').classList.remove('active');
});

document.getElementById("move_selection_right").addEventListener("click", function () {
    document.querySelector('.right').classList.remove('fullscreen');
});

document.getElementById("move_selection_left").addEventListener("click", function () {
    document.querySelector('.right').classList.add('fullscreen');
});
