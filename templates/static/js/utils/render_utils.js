export const renderCodeHtml = async (extract, rightContainer, outputIframe) => {
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

export const renderSearch = async (search_results, outputIframe) => {
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
                <htmlContent>
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

export const addImageClickHandler = (container, imageSrc, mimeType) => {
    const fileExt = mimeType.split("/")[1];
    container.querySelector(".message-image")?.addEventListener("click", () => {
        const imageIframeHTML = `
            <html>
                <head>
                    <style>
                        :root {
                            --text-color: #edf3ff;
                            --secondary-color: #2d2d2d;
                            --secondary-hover-color: #3a3a3a;
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
                            width: 100vw;
                            height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }
                        img {
                            max-width: 90vw;
                            max-height: 90vh;
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
