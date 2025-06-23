export const createMsgElement = (content, className) => {
    const div = document.createElement("div");
    div.classList.add("message", className);
    div.innerHTML = content;
    return div;
};

export const showError = (message, chatsContainer, scrollToBottom) => {
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

export const addCopyButtons = () => {
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
                e.trigger.innerHTML = "Đã sao chép";
                setTimeout(() => {
                    e.trigger.innerHTML = `<i class="material-symbols-rounded">content_copy</i>`;
                }, 10000);
            });
            clipboardInitialized = true;
        }
    };
};
