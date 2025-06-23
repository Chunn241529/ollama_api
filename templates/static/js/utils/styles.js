export const addStyles = () => {
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
        .thinking-container {
            margin: 10px 0;
            padding: 10px;
            background: var(--secondary-color);
            border-radius: 5px;
            position: relative;
            max-width: 90%;
        }
        .thinking-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding-bottom: 5px;
        }
        .thinking-title {
            font-size: 16px;
            color: var(--text-color);
            font-weight: bold;
        }
        .toggle-thinking {
            background: transparent;
            border: none;
            color: var(--text-color);
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        .toggle-thinking i {
            font-size: 20px;
        }
        .thinking-output {
            margin-top: 10px;
            color: var(--text-color);
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
            padding: 10px 0;
        }
        .thinking-output.collapsed {
            max-height: 0;
            padding: 0;
        }
        .lds-dual-ring {
            display: none;
            margin-top: 10px;
        }
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
    document.head.appendChild(style);
};
