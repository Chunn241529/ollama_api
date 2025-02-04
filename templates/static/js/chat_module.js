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


const container = document.querySelector(".container")
const chatsContainer = document.querySelector(".chats-container");
const promptForm = document.querySelector(".prompt-form");
const promptInput = promptForm.querySelector(".prompt-input");

let controller;
let userMessage = "";

const createMsgElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
}

const scrollToBottom = () => container.scrollTo({ top: container.scrollHeight, behavior: "smooth" })

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

    fetch('http://127.0.0.1:2401/chat/get_models_test')
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
                    if (index === 2) {
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
    // Lấy phần tử hiển thị nội dung text và thinking
    const textElement = BotMsgDiv.querySelector(".message-text");
    const thinkingOutput = BotMsgDiv.querySelector(".thinking-output");
    const modelName = BotMsgDiv.querySelector('.modelName');

    modelName.textContent = model_current;


    controller = new AbortController();

    if (is_deep_think) {
        const loadingBars = BotMsgDiv.querySelectorAll('.loading-bars');
        loadingBars.forEach(lb => lb.style.display = 'none');
    } else {
        thinkingOutput.style.borderLeft = 'none';
    }

    // Khởi tạo biến riêng cho mỗi loại kết quả
    let resultThinking = "";
    let resultText = "";

    const response = await fetch("http://127.0.0.1:2401/chat/test", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: userMessage,
            model: model_current,
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

                // Xử lý riêng theo type của message
                if (jsonData.type === "thinking") {
                    resultThinking += content;
                    // Cập nhật nội dung thinking
                    thinkingOutput.innerHTML = marked.parse(resultThinking);
                } else if (jsonData.type === "text") {
                    resultText += content;
                    // Cập nhật nội dung text
                    textElement.innerHTML = marked.parse(resultText);
                    // thinkContainer.style.display = `none`;
                }
            } catch (e) {
                console.error("JSON parse error:", e);
            }
        }

        hljs.highlightAll();
        addCopyButtons();
        scrollToBottom();
    }

    // Nếu có dữ liệu còn lại trong buffer sau khi đọc xong
    if (buffer.trim()) {
        try {
            const jsonData = JSON.parse(buffer);
            let content = (jsonData.message && jsonData.message.content) ? jsonData.message.content : "";

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
    scrollToBottom();

    // Khi hoàn thành việc generate response, thay đổi trạng thái nút
    const btn_stop = document.querySelector("#stop-response-btn");
    const btn_send = document.querySelector("#send-prompt-btn");
    btn_stop.style.display = "none";  // Ẩn nút stop
    btn_send.style.display = "block"; // Hiển thị nút send
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

const handleFormSubmit = (e, is_deep_think, is_search) => {
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
    textarea.style.height = `70px`;
    btn_stop.style.display = `block`;
    btn_send.style.display = `none`;

    setTimeout(() => {
        const BotMsgHTML = `
            <img src="templates/static/assets/img/1.jpg" alt="" class="avatar"><p class="modelName"></p>
            <div class="thinking-container">
                <p class="thinking-output"></p>
            </div>
            <p class="message-text">
                <span class="loading-bars">
                    <span></span><span></span><span></span>
                </span>
                <span class="loading-bars">
                    <span></span><span></span>
                </span>
                <span class="loading-bars" style="width: 410px;">
                    <span></span>
                </span>
            </p>
        `;

        const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message");
        chatsContainer.appendChild(BotMsgDiv);

        if (toggle_search && toggle_deepthink) {
            generateResponse(BotMsgDiv, true, true);
        } else if (toggle_search) {
            generateResponse(BotMsgDiv, false, true);
        } else if (toggle_deepthink) {
            generateResponse(BotMsgDiv, true, false);
        } else {
            generateResponse(BotMsgDiv, false, false);
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