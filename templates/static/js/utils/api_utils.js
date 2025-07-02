import { addCopyButtons, showError } from './ui_utils.js';
import { renderCodeHtml, addImageClickHandler } from './render_utils.js';

export const savePartialResponse = async (content, isThinking = false) => {
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
        showError("Không thể lưu phản hồi dở dang", null, () => {});
    }
};

export const generateResponse = async (
    BotMsgDiv,
    is_deep_think = false,
    is_search = false,
    is_image = false,
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
    scrollToBottom // Thêm tham số scrollToBottom
) => {
    const textElement = BotMsgDiv.querySelector(".message-text");
    const thinkingOutput = BotMsgDiv.querySelector(".thinking-output");
    const modelName = BotMsgDiv.querySelector(".modelName");

    modelName.textContent = "4T AI";

    const userText = userMessage.toLowerCase();
    const searchKeywords = ["tìm kiếm", "tra cứu", "nghiên cứu", "search"];
    is_search = is_search || searchKeywords.some((keyword) => userText.includes(keyword));

    textElement.innerHTML = `<span class="loading-bars"><span></span><span></span><span></span></span>`;
    if (is_deep_think) {
        BotMsgDiv.querySelectorAll(".message-text .loading-bars").forEach((lb) => (lb.style.display = "none"));
        thinkingOutput.style.display = "block";
        // Hiển thị loading trong quá trình chờ dữ liệu
        thinkingOutput.innerHTML = `<span class="loading-bars"><span></span><span></span><span></span></span>`;
        BotMsgDiv.querySelector(".thinking-container").style.display = "block";
    } else {
        thinkingOutput.style.display = "none";
        BotMsgDiv.querySelector(".thinking-container").style.display = "none";
    }

    if (is_search) {
        searchOutput.style.display = "block";
        moveSelectionRight.style.display = "none";
        moveSelectionLeft.style.display = "none";
    }
    // else {
    //     searchOutput.style.display = "none";
    // }

    let localLastResultThinking = lastResultThinking || "";
    let localLastResultText = lastResultText || "";
    let lastRenderedHTML = "";
    let lastRenderedCSS = "";
    let lastRenderedJS = "";
    let lastRenderedSearch = "";
    let num_search = "";
    let search_results = [];

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
                // Không còn truyền is_generate_image từ frontend
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
                        // Xóa loading khi có dữ liệu thực sự
                        if (thinkingOutput.innerHTML.includes("loading-bars")) thinkingOutput.innerHTML = "";
                        localLastResultThinking += jsonData.message?.content || "";
                        thinkingOutput.innerHTML = marked.parse(localLastResultThinking);
                        thinkingOutput.style.display = "block";
                        BotMsgDiv.querySelector(".thinking-container").style.display = "block";
                    } else if (jsonData.type === "text" || jsonData.type === "image_description") {
                        localLastResultText += jsonData.message?.content || "";
                        textElement.innerHTML = marked.parse(localLastResultText);
                        hljs.highlightAll();
                        addCopyButtons()();
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
                        showError(jsonData.error || jsonData.message || "Failed to process the request.", chatsContainer, () => scrollToBottom(true));
                    }
                } catch (e) {
                    console.error("JSON parse error:", e);
                }

                const htmlContent = extractHTML(localLastResultText);
                const cssContent = extractCSS(localLastResultText);
                const jsContent = extractJavaScript(localLastResultText);

                if (htmlContent !== lastRenderedHTML || cssContent !== lastRenderedCSS || jsContent !== lastRenderedJS) {
                    lastRenderedHTML = htmlContent;
                    lastRenderedCSS = cssContent;
                    lastRenderedJS = jsContent;
                    closeIframe.style.display = "block";
                    rightContainer.classList.add("active");
                    await renderCodeHtml(localLastResultText, rightContainer, outputIframe);
                    rightElement.classList.toggle("fullscreen", jsContent.trim().length > 0);
                }

                if (autoScroll) scrollToBottom(false);
            }
        }

        if (buffer.trim()) {
            try {
                const jsonData = JSON.parse(buffer);
                if (jsonData.type === "thinking") {
                    if (thinkingOutput.innerHTML.includes("loading-bars")) thinkingOutput.innerHTML = "";
                    localLastResultThinking += jsonData.message?.content || "";
                    thinkingOutput.innerHTML = marked.parse(localLastResultThinking);
                    thinkingOutput.style.display = "block";
                    BotMsgDiv.querySelector(".thinking-container").style.display = "block";
                } else if (jsonData.type === "text" || jsonData.type === "image_description") {
                    localLastResultText += jsonData.message?.content || "";
                    textElement.innerHTML = marked.parse(localLastResultText);
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
                    showError(jsonData.error || jsonData.message || "Failed to process the request.", chatsContainer, () => scrollToBottom(true));
                }
            } catch (e) {
                console.error("JSON parse error on final buffer:", e);
            }
        }

        hljs.highlightAll();
        addCopyButtons()();
        if (autoScroll) scrollToBottom(false);

        lastResultText = localLastResultText;
        lastResultThinking = localLastResultThinking;
    } catch (error) {
        if (error.name === "AbortError") {
            console.log("Response aborted by user");
            if (localLastResultThinking.trim()) {
                await savePartialResponse(localLastResultThinking, true);
            }
            if (localLastResultText.trim()) {
                await savePartialResponse(localLastResultText, false);
            }
            lastResultThinking = localLastResultThinking;
            lastResultText = localLastResultText;
        } else {
            console.error("Error in generateResponse:", error);
            showError(error.message, chatsContainer, () => scrollToBottom(true));
        }
    } finally {
        stopResponseBtn.style.display = "none";
        sendPromptBtn.style.display = "block";
    }
};

const isImageInput = (text) => {
    const urlPattern = /(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp))/i;
    return urlPattern.test(text);
};

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
