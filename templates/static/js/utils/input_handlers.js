import { createMsgElement, showError, addCopyButtons } from './ui_utils.js';
import { generateResponse } from './api_utils.js';

export const processImageInput = async (text) => {
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

export const handleFormSubmit = async (e, {
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
}) => {
    e.preventDefault();
    if (suggestions) suggestions.style.display = "none";
    if (appHeader) appHeader.style.display = "none";
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
                    <div class="thinking-header">
                        <span class="thinking-title">Quá trình suy nghĩ</span>
                        <button class="toggle-thinking">
                            <i class="material-symbols-rounded">expand_less</i>
                        </button>
                    </div>
                    <p class="thinking-output"></p>
                </div>
                <p class="message-text">
                    <span class="loading-bars"><span></span><span></span><span></span></span>
                </p>
            `;
            const BotMsgDiv = createMsgElement(BotMsgHTML, "bot-message");
            chatsContainer.appendChild(BotMsgDiv);

            const toggleButton = BotMsgDiv.querySelector(".toggle-thinking");
            const thinkingOutput = BotMsgDiv.querySelector(".thinking-output");
            toggleButton.addEventListener("click", () => {
                thinkingOutput.classList.toggle("collapsed");
                const icon = toggleButton.querySelector("i");
                icon.textContent = thinkingOutput.classList.contains("collapsed") ? "expand_more" : "expand_less";
            });

            document.getElementById("search").addEventListener("click", () => {
                if (closeIframe && rightContainer) {
                    closeIframe.style.display = "block";
                    rightContainer.classList.add("active");
                }
            });

            messages.length = 0; // Reset messages array

            if (imageResult.isImage) {
                messages.push({
                    role: "user",
                    content: imageResult.description,
                    image_url: imageResult.image_url
                });
                generateResponse(
                    BotMsgDiv,
                    false,
                    false,
                    true,
                    userMessage,
                    messages,
                    controller,
                    searchOutput,
                    moveSelectionRight,
                    moveSelectionLeft,
                    closeIframe,
                    rightContainer,
                    rightElement,
                    outputIframe,
                    autoScroll,
                    chatsContainer,
                    stopResponseBtn,
                    sendPromptBtn,
                    lastResultText,
                    lastResultThinking,
                    scrollToBottom
                );
            } else {
                messages.push({
                    role: "user",
                    content: userMessage
                });

                if (toggle_search && toggle_deepthink) {
                    generateResponse(
                        BotMsgDiv,
                        true,
                        true,
                        false,
                        userMessage,
                        messages,
                        controller,
                        searchOutput,
                        moveSelectionRight,
                        moveSelectionLeft,
                        closeIframe,
                        rightContainer,
                        rightElement,
                        outputIframe,
                        autoScroll,
                        chatsContainer,
                        stopResponseBtn,
                        sendPromptBtn,
                        lastResultText,
                        lastResultThinking,
                        scrollToBottom
                    );
                } else if (toggle_search) {
                    generateResponse(
                        BotMsgDiv,
                        false,
                        true,
                        false,
                        userMessage,
                        messages,
                        controller,
                        searchOutput,
                        moveSelectionRight,
                        moveSelectionLeft,
                        closeIframe,
                        rightContainer,
                        rightElement,
                        outputIframe,
                        autoScroll,
                        chatsContainer,
                        stopResponseBtn,
                        sendPromptBtn,
                        lastResultText,
                        lastResultThinking,
                        scrollToBottom
                    );
                } else if (toggle_deepthink) {
                    generateResponse(
                        BotMsgDiv,
                        true,
                        false,
                        false,
                        userMessage,
                        messages,
                        controller,
                        searchOutput,
                        moveSelectionRight,
                        moveSelectionLeft,
                        closeIframe,
                        rightContainer,
                        rightElement,
                        outputIframe,
                        autoScroll,
                        chatsContainer,
                        stopResponseBtn,
                        sendPromptBtn,
                        lastResultText,
                        lastResultThinking,
                        scrollToBottom
                    );
                } else {
                    generateResponse(
                        BotMsgDiv,
                        false,
                        false,
                        false,
                        userMessage,
                        messages,
                        controller,
                        searchOutput,
                        moveSelectionRight,
                        moveSelectionLeft,
                        closeIframe,
                        rightContainer,
                        rightElement,
                        outputIframe,
                        autoScroll,
                        chatsContainer,
                        stopResponseBtn,
                        sendPromptBtn,
                        lastResultText,
                        lastResultThinking,
                        scrollToBottom
                    );
                }
            }

            autoScroll = true;
            scrollToBottom(true);
        }, 600);
    } catch (error) {
        showError(error.message, chatsContainer, () => scrollToBottom(true));
    }
};
