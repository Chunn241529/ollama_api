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

let togggle_deepthink = false;
let togggle_search = false;

searchToggle.addEventListener('click', () => {
    searchToggle.classList.toggle('active');
    if (searchToggle.classList.contains('active')) {
        deepThinkToggle.classList.remove('active');
        togggle_search = true;
        console.log('Chế độ tìm kiếm được kích hoạt');
    } else {
        togggle_search = false;
        console.log('Chế độ tìm kiếm bị tắt');
    }
});

deepThinkToggle.addEventListener('click', () => {
    deepThinkToggle.classList.toggle('active');
    if (deepThinkToggle.classList.contains('active')) {
        searchToggle.classList.remove('active');
        togggle_deepthink = true;
        console.log('Chế độ deep think được kích hoạt');
    } else {
        togggle_deepthink = false;
        console.log('Chế độ deep think bị tắt');
    }
});


const container = document.querySelector(".container")
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

const scrollToBottom = () => container.scrollTo({ top: container.scrollHeight, behavior: "smooth" })

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



const generateResponse = async (BotMsgDiv, is_deep_think = false, is_search = false) => {
    const textElement = BotMsgDiv.querySelector(".message-text");

    const response = await fetch("http://127.0.0.1:2401/chat/test", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: userMessage,
            model: "llama3.2:3b",
            chat_ai_id: 0,
            is_deep_think: is_deep_think,
            is_search: is_search,
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

        // In log kiểm tra xem thẻ <think> có bị mất không
        console.log("Streaming content:", result);

        // Parse Markdown nhưng giữ nguyên thẻ HTML
        let parsedResult = marked.parse(result);

        // Thay thế thẻ <think> thành <span> để đổi màu
        parsedResult = parsedResult.replace(/&lt;think&gt;(.*?)&lt;\/think&gt;/g, '<span style="color: black;">$1</span>');


        textElement.innerHTML = parsedResult;

        hljs.highlightAll();
        addCopyButtons();
        scrollToBottom();
    }

    // Xử lý lần cuối sau khi toàn bộ dữ liệu đã nhận xong
    result += decoder.decode(new Uint8Array(), { stream: false });

    // Log nội dung cuối cùng
    console.log("Final content:", result);

    let parsedResult = marked.parse(result);
    parsedResult = parsedResult.replace(/&lt;think&gt;(.*?)&lt;\/think&gt;/g, '<span style="color: black;">$1</span>');

    textElement.innerHTML = parsedResult;

    hljs.highlightAll();
    addCopyButtons();
    scrollToBottom();
};



const handleFormSubmit = (e, is_deep_think, is_search) => {
    e.preventDefault();
    userMessage = promptInput.value.trim();
    if (!userMessage) return;

    const userMsgHTML = `<p class="message-text"></p>`;
    const userMsgDiv = createMsgElement(userMsgHTML, "user-message")
    userMsgDiv.querySelector(".message-text").textContent = userMessage;
    chatsContainer.appendChild(userMsgDiv);

    promptInput.value = ""; // Clear the input value after submitting

    setTimeout(() => {
        const BotMsgHTML = `<img src="/storage/assets/img/1.jpg" alt="" class="avatar"><p class="message-text">Just a sec...</p>`;
        const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message")
        chatsContainer.appendChild(BotMsgDiv);
        scrollToBottom();
        if (togggle_search) {
            generateResponse(BotMsgDiv, is_deep_think = false, is_search = true);
            scrollToBottom();
        } else if (togggle_deepthink) {
            generateResponse(BotMsgDiv, is_deep_think = true, is_search = false);
            scrollToBottom();
        } else {
            generateResponse(BotMsgDiv, is_deep_think = false, is_search = false);
            scrollToBottom();
        }

    }, 600)
}

promptForm.addEventListener("submit", handleFormSubmit);

// Add event listener for Enter key press
promptInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        handleFormSubmit(e);
    }
});