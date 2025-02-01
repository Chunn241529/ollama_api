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

searchToggle.addEventListener('click', () => {
    searchToggle.classList.toggle('active');
    if (searchToggle.classList.contains('active')) {
        deepThinkToggle.classList.remove('active');
        console.log('Chế độ tìm kiếm được kích hoạt');
    } else {
        console.log('Chế độ tìm kiếm bị tắt');
    }
});

deepThinkToggle.addEventListener('click', () => {
    deepThinkToggle.classList.toggle('active');
    if (deepThinkToggle.classList.contains('active')) {
        searchToggle.classList.remove('active');
        console.log('Chế độ deep think được kích hoạt');
    } else {
        console.log('Chế độ deep think bị tắt');
    }
});


const chatsContainer = document.querySelector(".chats-container");
const promptForm = document.querySelector(".prompt-form");
const promptInput = promptForm.querySelector(".prompt-input");

let userMessage = "";

const createMsgElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
}

function addCopyButtons() {
    document.querySelectorAll('pre code').forEach((block, index) => {
        const pre = block.parentElement;

        // Nếu nút copy đã tồn tại thì bỏ qua
        if (pre.querySelector('.copy-btn')) return;

        // Tạo nút copy
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        // Sử dụng icon copy của Material Icons (đảm bảo đã thêm font Material Icons vào trang)
        copyBtn.innerHTML = `<i class="material-symbols-rounded">content_copy</i>`;

        // Tạo id cho code block nếu chưa có
        if (!block.id) {
            block.id = `code-block-${index}`;
        }
        // Gán thuộc tính data-clipboard-target cho nút copy
        copyBtn.setAttribute('data-clipboard-target', `#${block.id}`);

        // Đặt vị trí cho nút copy (ví dụ: góc trên bên phải của khối code)
        pre.style.position = 'relative';
        copyBtn.style.position = 'absolute';
        copyBtn.style.top = '5px';
        copyBtn.style.right = '5px';
        copyBtn.style.cursor = 'pointer';
        copyBtn.style.border = 'none';
        copyBtn.style.background = 'transparent'; // Nút trong suốt
        copyBtn.style.padding = '4px';
        copyBtn.style.display = 'flex';
        copyBtn.style.alignItems = 'center';
        copyBtn.style.justifyContent = 'center';
        copyBtn.style.color = '#aaa'; // Màu icon ban đầu

        // Thêm nút copy vào thẻ pre
        pre.appendChild(copyBtn);
    });

    // Khởi tạo Clipboard.js cho các nút copy
    new ClipboardJS('.copy-btn');
}


// Hàm render nội dung Markdown streaming
const generateResponse = async (BotMsgDiv) => {
    const textElement = BotMsgDiv.querySelector(".message-text");

    const response = await fetch("http://127.0.0.1:2401/chat/test", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: userMessage,
            model: "qwen2.5-coder:7b",
            chat_ai_id: 0,
            is_deep_think: false,
            is_search: false,
        }),
    });

    if (!response.ok) {
        console.error("Failed to fetch response from API");
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let result = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        result += decoder.decode(value, { stream: true });
        // Parse Markdown và render HTML
        textElement.innerHTML = marked.parse(result);

        // Apply highlight cho code blocks
        hljs.highlightAll();

        // Chèn nút copy cho mỗi code block
        addCopyButtons();
    }

    result += decoder.decode(new Uint8Array(), { stream: false });
    textElement.innerHTML = marked.parse(result);
    hljs.highlightAll();
    addCopyButtons();
};



const handleFormSubmit = (e) => {
    e.preventDefault();
    userMessage = promptInput.value.trim();
    if (!userMessage) return;

    const userMsgHTML = `<p class="message-text"></p>`;
    const userMsgDiv = createMsgElement(userMsgHTML, "user-message")
    userMsgDiv.querySelector(".message-text").textContent = userMessage;
    chatsContainer.appendChild(userMsgDiv);

    promptInput.value = ""; // Clear the input value after submitting

    setTimeout(() => {
        const BotMsgHTML = `<img src="\\storage\\assets\\img\\1.jpg" alt="" class="avatar"><p class="message-text">Just a sex...</p>`;
        const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message")
        chatsContainer.appendChild(BotMsgDiv);
        generateResponse(BotMsgDiv);
    }, 600)
}

promptForm.addEventListener("submit", handleFormSubmit);

// Add event listener for Enter key press
promptInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        handleFormSubmit(e);
    }
});