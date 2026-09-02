let currentChatId = null;
let controller = null;
let stopped = false;
let recognition = null;
let recording = false;
let recorder = null;
let recorderStream = null;
let audioChunks = [];
let currentFen = "";
let chessGameId = null;
let chessColor = "white";
let chessSelected = null;

const settings = {
    animation: localStorage.getItem("ai_animation") !== "off",
    scroll: localStorage.getItem("ai_scroll") !== "off"
};

const pinnedKey = "ai_pinned_chats";
const renamedKey = "ai_renamed_chats";

const loginView =
    document.getElementById("loginView");

const app =
    document.getElementById("app");

const sidebar =
    document.getElementById("sidebar");

const chat =
    document.getElementById("chat");

const welcome =
    document.getElementById("welcome");

const input =
    document.getElementById("input");

const historyBox =
    document.getElementById("history");

const statusBox =
    document.getElementById("status");

const chatTitle =
    document.getElementById("chatTitle");

const sendButton =
    document.getElementById("sendButton");

const stopButton =
    document.getElementById("stopButton");

const profilePicture =
    document.getElementById("profilePicture");

const profileName =
    document.getElementById("profileName");

const profileEmail =
    document.getElementById("profileEmail");

const toast =
    document.getElementById("toast");


function toastMessage(text) {

    toast.textContent = text;

    toast.classList.add("show");

    setTimeout(
        () =>
        toast.classList.remove("show"),
        1500
    );
}


function googleLogin() {

    window.location.href =
        "/auth/google";
}


function setStatus(
    text,
    ready = false
) {

    statusBox.textContent =
        "● " + text;

    statusBox.className =
        ready
            ? "status ready"
            : "status";
}


function scrollBottom() {

    if (!settings.scroll)
        return;

    chat.scrollTo({
        top: chat.scrollHeight,
        behavior: "smooth"
    });
}


function getPinned() {

    try {
        return JSON.parse(
            localStorage.getItem(
                pinnedKey
            ) || "[]"
        );
    } catch {
        return [];
    }
}


function getRenamed() {

    try {
        return JSON.parse(
            localStorage.getItem(
                renamedKey
            ) || "{}"
        );
    } catch {
        return {};
    }
}


function displayedTitle(item) {

    const renamed =
        getRenamed();

    return (
        renamed[item.id] ||
        item.title ||
        "New chat"
    );
}


function formatBasicMarkdown(text) {

    let safe = String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");

    const blocks = [];

    safe = safe.replace(
        /```([\s\S]*?)```/g,
        (_, code) => {

            const index =
                blocks.length;

            blocks.push(
                code.replace(
                    /^\n/,
                    ""
                )
            );

            return (
                "\u0000CODE" +
                index +
                "\u0000"
            );
        }
    );

    safe = safe.replace(
        /^### (.+)$/gm,
        "<strong>$1</strong>"
    );

    safe = safe.replace(
        /^## (.+)$/gm,
        "<strong>$1</strong>"
    );

    safe = safe.replace(
        /^# (.+)$/gm,
        "<strong>$1</strong>"
    );

    safe = safe.replace(
        /\*\*(.+?)\*\*/g,
        "<strong>$1</strong>"
    );

    safe = safe.replace(
        /`([^`]+)`/g,
        "<code>$1</code>"
    );

    safe = safe.replace(
        /^[-*] (.+)$/gm,
        "• $1"
    );

    for (
        let i = 0;
        i < blocks.length;
        i++
    ) {

        const encoded =
            encodeURIComponent(
                blocks[i]
            );

        safe = safe.replace(
            "\u0000CODE" +
            i +
            "\u0000",
            '<div class="code-block">' +
            '<button class="code-copy" ' +
            'onclick="copyCode(this,\'' +
            encoded +
            '\')">Copy</button>' +
            '<pre>' +
            blocks[i]
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;") +
            "</pre></div>"
        );
    }

    return safe;
}


async function copyCode(
    button,
    encoded
) {

    const code =
        decodeURIComponent(
            encoded
        );

    await navigator.clipboard.writeText(
        code
    );

    const old =
        button.textContent;

    button.textContent =
        "Copied";

    setTimeout(
        () =>
        button.textContent = old,
        1000
    );
}


function addMessage(
    role,
    text,
    animate = false
) {

    text = String(text);

    if (welcome)
        welcome.remove();

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "message";

    const head =
        document.createElement(
            "div"
        );

    head.className =
        "message-head";

    const name =
        document.createElement(
            "div"
        );

    name.className =
        "message-name";

    name.textContent =
        role === "user"
            ? "You"
            : "Autonomous AI";

    const actions =
        document.createElement(
            "div"
        );

    actions.className =
        "message-actions";

    const copy =
        document.createElement(
            "button"
        );

    copy.className =
        "message-action";

    copy.textContent =
        "Copy";

    copy.onclick =
        async () => {

            await navigator.clipboard.writeText(
                text
            );

            copy.textContent =
                "Copied";

            setTimeout(
                () =>
                copy.textContent =
                    "Copy",
                1000
            );
        };

    actions.appendChild(copy);

    head.appendChild(name);
    head.appendChild(actions);

    const body =
        document.createElement(
            "div"
        );

    body.className =
        "message-body";

    wrapper.appendChild(head);
    wrapper.appendChild(body);

    chat.appendChild(wrapper);

    if (
        !animate ||
        !settings.animation
    ) {

        body.innerHTML =
            formatBasicMarkdown(text);

        scrollBottom();

        return;
    }

    let index = 0;

    function typeNext() {

        if (!body.isConnected)
            return;

        if (stopped) {

            body.textContent =
                text.slice(0, index) +
                "\n\n[Stopped]";

            scrollBottom();

            return;
        }

        if (index >= text.length) {

            body.innerHTML =
                formatBasicMarkdown(
                    text
                );

            scrollBottom();

            return;
        }

        index += Math.min(
            3,
            text.length - index
        );

        body.textContent =
            text.slice(
                0,
                index
            );

        scrollBottom();

        requestAnimationFrame(
            typeNext
        );
    }

    typeNext();
}


async function loadMe() {

    try {

        const response =
            await fetch(
                "/api/me"
            );

        if (!response.ok) {

            loginView.classList.remove(
                "hidden"
            );

            app.classList.add(
                "hidden"
            );

            return false;
        }

        const data =
            await response.json();

        if (!data.logged_in) {

            loginView.classList.remove(
                "hidden"
            );

            app.classList.add(
                "hidden"
            );

            return false;
        }

        loginView.classList.add(
            "hidden"
        );

        app.classList.remove(
            "hidden"
        );

        profileName.textContent =
            data.name || "User";

        profileEmail.textContent =
            data.email || "";

        if (data.picture) {

            profilePicture.src =
                data.picture;

        } else {

            profilePicture.classList.add(
                "hidden"
            );
        }

        await loadChats();

        if (!currentChatId) {

            await newChat();
        }

        return true;

    } catch (error) {

        loginView.classList.remove(
            "hidden"
        );

        app.classList.add(
            "hidden"
        );

        return false;
    }
}


async function loadChats() {

    try {

        const response =
            await fetch(
                "/api/chats"
            );

        if (!response.ok)
            return;

        const data =
            await response.json();

        const query =
            document.getElementById(
                "chatSearch"
            ).value
            .trim()
            .toLowerCase();

        const pinned =
            getPinned();

        let chats =
            data.chats || [];

        chats.sort(
            (a,b) => {

                const ap =
                    pinned.includes(a.id)
                    ? 1
                    : 0;

                const bp =
                    pinned.includes(b.id)
                    ? 1
                    : 0;

                if (ap !== bp)
                    return bp - ap;

                return (
                    String(b.updated_at || "")
                    .localeCompare(
                        String(a.updated_at || "")
                    )
                );
            }
        );

        chats =
            chats.filter(
                item =>
                displayedTitle(item)
                    .toLowerCase()
                    .includes(query)
            );

        historyBox.innerHTML = "";

        if (!chats.length) {

            historyBox.innerHTML =
                '<div class="history-empty">' +
                (
                    query
                        ? "No matching chats"
                        : "No conversations yet"
                ) +
                "</div>";

            return;
        }

        for (const item of chats) {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "history-item";

            const open =
                document.createElement(
                    "button"
                );

            open.className =
                "history-open"
                +
                (
                    item.id === currentChatId
                        ? " active"
                        : ""
                );

            open.textContent =
                (
                    pinned.includes(item.id)
                        ? "★ "
                        : ""
                )
                +
                displayedTitle(item);

            open.onclick =
                () =>
                loadChat(item.id);

            const tools =
                document.createElement(
                    "div"
                );

            tools.className =
                "history-tools";

            const pin =
                document.createElement(
                    "button"
                );

            pin.className =
                "history-tool";

            pin.textContent =
                pinned.includes(item.id)
                    ? "★"
                    : "☆";

            pin.title =
                "Pin";

            pin.onclick =
                event => {

                    event.stopPropagation();

                    togglePin(
                        item.id
                    );
                };

            const rename =
                document.createElement(
                    "button"
                );

            rename.className =
                "history-tool";

            rename.textContent =
                "✎";

            rename.title =
                "Rename";

            rename.onclick =
                event => {

                    event.stopPropagation();

                    renameChat(
                        item.id,
                        displayedTitle(item)
                    );
                };

            const del =
                document.createElement(
                    "button"
                );

            del.className =
                "history-tool";

            del.textContent =
                "×";

            del.title =
                "Delete";

            del.onclick =
                event => {

                    event.stopPropagation();

                    deleteChat(
                        item.id
                    );
                };

            tools.appendChild(pin);
            tools.appendChild(rename);
            tools.appendChild(del);

            row.appendChild(open);
            row.appendChild(tools);

            historyBox.appendChild(row);
        }

    } catch (error) {

        console.error(
            error
        );
    }
}


function filterChats() {

    loadChats();
}


async function loadChat(
    id
) {

    try {

        const response =
            await fetch(
                "/api/chats/" +
                encodeURIComponent(id)
            );

        if (!response.ok)
            return;

        const data =
            await response.json();

        currentChatId =
            data.id;

        chatTitle.textContent =
            getRenamed()[id] ||
            data.title ||
            "New chat";

        chat.innerHTML = "";

        for (
            const message
            of data.messages || []
        ) {

            addMessage(
                message.role,
                message.content
            );
        }

        await loadChats();

        scrollBottom();

    } catch (error) {

        toastMessage(
            "Could not load chat"
        );
    }
}


async function newChat() {

    try {

        const response =
            await fetch(
                "/api/chats/new",
                {
                    method:
                        "POST"
                }
            );

        if (!response.ok)
            throw new Error(
                "Could not create chat"
            );

        const data =
            await response.json();

        currentChatId =
            data.id;

        chatTitle.textContent =
            "New chat";

        chat.innerHTML = "";

        const newWelcome =
            document.createElement(
                "div"
            );

        newWelcome.id =
            "welcome";

        newWelcome.className =
            "welcome";

        newWelcome.innerHTML = `
            <div class="welcome-orb">
                <span>✦</span>
            </div>
            <h1>How can I help?</h1>
            <p>Ask, build, debug, explore or create.</p>
        `;

        chat.appendChild(
            newWelcome
        );

        await loadChats();

    } catch (error) {

        toastMessage(
            error.message
        );
    }
}


async function deleteChat(
    id
) {

    if (
        !confirm(
            "Delete this conversation?"
        )
    )
        return;

    try {

        const response =
            await fetch(
                "/api/chats/" +
                encodeURIComponent(id),
                {
                    method:
                        "DELETE"
                }
            );

        if (!response.ok)
            throw new Error(
                "Delete failed"
            );

        if (
            currentChatId === id
        ) {

            currentChatId = null;

            await newChat();

        } else {

            await loadChats();
        }

    } catch (error) {

        toastMessage(
            error.message
        );
    }
}


function renameChat(
    id,
    oldTitle
) {

    const renamed =
        prompt(
            "Chat name:",
            oldTitle
        );

    if (
        renamed === null ||
        !renamed.trim()
    )
        return;

    const names =
        getRenamed();

    names[id] =
        renamed.trim();

    localStorage.setItem(
        renamedKey,
        JSON.stringify(names)
    );

    if (
        currentChatId === id
    ) {

        chatTitle.textContent =
            renamed.trim();
    }

    loadChats();
}


function togglePin(id) {

    const pinned =
        getPinned();

    const index =
        pinned.indexOf(id);

    if (index >= 0) {

        pinned.splice(
            index,
            1
        );

    } else {

        pinned.push(id);
    }

    localStorage.setItem(
        pinnedKey,
        JSON.stringify(pinned)
    );

    loadChats();
}


async function sendMessage() {

    const message =
        input.value.trim();

    if (!message)
        return;

    const ownerQuestion = /^(who('s| is)? (your )?(owner|creator)|who (made|created) you|who owns you)[?! .]*$/i.test(message);
    if (ownerQuestion) {
        input.value = "";
        addMessage("user", message);
        addMessage("assistant", "My creator and owner is Shreyansh Ray.");
        scrollBottom();
        return;
    }

    stopped = false;

    sendButton.disabled =
        true;

    stopButton.disabled =
        false;

    setStatus(
        "WORKING"
    );

    input.value = "";

    input.style.height =
        "57px";

    addMessage(
        "user",
        message
    );

    controller =
        new AbortController();

    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        chat_id:
                            currentChatId,

                        message:
                            (window.__adaFileContext
                                ? message + "\n\n[UPLOADED FILE CONTENT]\n" + window.__adaFileContext
                                : message)
                    }),

                    signal:
                        controller.signal
                }
            );

        let data;

        try {

            data =
                await response.json();

        } catch {

            throw new Error(
                "Invalid server response"
            );
        }

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Chat request failed"
            );
        }

        currentChatId =
            data.chat_id;

        addMessage(
            "assistant",
            data.answer || "No response.",
            true
        );

        const renamed =
            getRenamed();

        if (!renamed[currentChatId]) {

            const chatResponse =
                await fetch(
                    "/api/chats/" +
                    encodeURIComponent(
                        currentChatId
                    )
                );

            if (
                chatResponse.ok
            ) {

                const chatData =
                    await chatResponse.json();

                chatTitle.textContent =
                    chatData.title ||
                    "New chat";
            }

        } else {

            chatTitle.textContent =
                renamed[currentChatId];
        }

        await loadChats();

    } catch (error) {

        if (
            error.name !==
            "AbortError"
        ) {

            addMessage(
                "assistant",
                "Error: " +
                error.message
            );
        }

    } finally {

        controller = null;

        sendButton.disabled =
            false;

        stopButton.disabled =
            true;

        setStatus(
            "READY",
            true
        );
    }
}


function stopGeneration() {

    stopped = true;

    if (controller) {

        controller.abort();
    }

    stopButton.disabled =
        true;

    sendButton.disabled =
        false;

    setStatus(
        "STOPPED"
    );
}


function useSuggestion(text) {

    input.value =
        text;

    input.focus();

    autoResize();

}


function autoResize() {

    input.style.height =
        "auto";

    input.style.height =
        Math.min(
            input.scrollHeight,
            220
        ) + "px";
}


input.addEventListener(
    "input",
    autoResize
);


input.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter"
            &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


document.addEventListener(
    "keydown",
    event => {

        if (
            (event.ctrlKey || event.metaKey)
            &&
            event.key.toLowerCase() === "k"
        ) {

            event.preventDefault();

            const search =
                document.getElementById(
                    "chatSearch"
                );

            search.focus();
        }

        if (
            event.key === "Escape"
        ) {

            closeAllModals();
        }
    }
);


/* ============================================================
   FILES
   ============================================================ */

async function uploadFiles() {

    const fileInput =
        document.getElementById(
            "fileInput"
        );

    const attachmentBar =
        document.getElementById(
            "attachmentBar"
        );

    attachmentBar.innerHTML = "";

    for (
        const file
        of fileInput.files
    ) {

        const chip =
            document.createElement(
                "span"
            );

        chip.className =
            "attachment-chip";

        chip.textContent =
            "📎 " +
            file.name;

        attachmentBar.appendChild(
            chip
        );

        const form =
            new FormData();

        form.append(
            "file",
            file
        );

        try {

            const response =
                await fetch(
                    "/api/v2/upload",
                    {
                        method:
                            "POST",
                        body:
                            form
                    }
                );

            const data =
                await response.json();

            if (!response.ok)
                throw new Error(
                    data.detail ||
                    "Upload failed"
                );

            window.__adaFileContext = window.__adaFileContext || "";
            if (data.text) {
                window.__adaFileContext += "\n\nFILE: " + data.filename + "\n" + data.text;
                if (window.__adaFileContext.length > 30000) {
                    window.__adaFileContext = window.__adaFileContext.slice(-30000);
                }
            }
            addMessage(
                "assistant",
                "Uploaded and read: " + data.filename +
                (data.text_preview ? "\n\nPreview:\n" + data.text_preview : "")
            );

        } catch (error) {

            addMessage(
                "assistant",
                "Upload error: " +
                error.message
            );
        }
    }

    fileInput.value = "";
}


/* ============================================================
   SPEECH TO TEXT
   ============================================================ */

function toggleVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        toastMessage(
            "Speech recognition is unavailable in this browser."
        );

        return;
    }

    if (recognition) {

        recognition.stop();

        recognition = null;

        voiceButton.textContent =
            "🎙";

        return;
    }

    recognition =
        new SpeechRecognition();

    recognition.lang =
        "en-US";

    recognition.continuous =
        true;

    recognition.interimResults =
        true;

    voiceButton.textContent =
        "■";

    recognition.onresult =
        event => {

            let transcript = "";

            for (
                let i =
                    event.resultIndex;
                i <
                    event.results.length;
                i++
            ) {

                transcript +=
                    event.results[i][0].transcript;
            }

            input.value =
                transcript;

            autoResize();
        };

    recognition.onerror =
        () => {

            recognition = null;

            voiceButton.textContent =
                "🎙";
        };

    recognition.onend =
        () => {

            recognition = null;

            voiceButton.textContent =
                "🎙";
        };

    recognition.start();
}


/* ============================================================
   AUDIO RECORDING
   ============================================================ */

async function recordAudio() {

    if (recording) {

        if (recorder)
            recorder.stop();

        return;
    }

    if (
        !navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia
    ) {

        toastMessage(
            "Microphone unavailable."
        );

        return;
    }

    try {

        recorderStream =
            await navigator.mediaDevices.getUserMedia(
                {
                    audio: true
                }
            );

        recorder =
            new MediaRecorder(
                recorderStream
            );

        audioChunks = [];

        recording = true;

        toastMessage(
            "Recording..."
        );

        recorder.ondataavailable =
            event => {

                if (
                    event.data.size
                ) {

                    audioChunks.push(
                        event.data
                    );
                }
            };

        recorder.onstop =
            async () => {

                recording = false;

                recorderStream
                    .getTracks()
                    .forEach(
                        t => t.stop()
                    );

                const blob =
                    new Blob(
                        audioChunks,
                        {
                            type:
                                "audio/webm"
                        }
                    );

                const form =
                    new FormData();

                form.append(
                    "file",
                    blob,
                    "recording.webm"
                );

                try {

                    const response =
                        await fetch(
                            "/api/audio",
                            {
                                method:
                                    "POST",
                                body:
                                    form
                            }
                        );

                    const data =
                        await response.json();

                    if (!response.ok)
                        throw new Error(
                            data.detail ||
                            "Audio upload failed."
                        );

                    toastMessage(
                        "Audio saved."
                    );

                } catch (error) {

                    toastMessage(
                        "Audio upload failed."
                    );
                }
            };

        recorder.start();

    } catch (error) {

        toastMessage(
            "Microphone permission denied."
        );
    }
}


/* ============================================================
   THEME / SETTINGS
   ============================================================ */

function toggleTheme() {

    document.body.classList.toggle(
        "light"
    );

    localStorage.setItem(
        "ai_theme",
        document.body.classList.contains(
            "light"
        )
            ? "light"
            : "dark"
    );
}


function saveSettings() {

    settings.animation =
        document.getElementById(
            "animationToggle"
        ).checked;

    settings.scroll =
        document.getElementById(
            "scrollToggle"
        ).checked;

    localStorage.setItem(
        "ai_animation",
        settings.animation
            ? "on"
            : "off"
    );

    localStorage.setItem(
        "ai_scroll",
        settings.scroll
            ? "on"
            : "off"
    );
}


function openSettings() {

    document
        .getElementById(
            "settingsModal"
        )
        .classList.remove(
            "hidden"
        );

    document.getElementById(
        "animationToggle"
    ).checked =
        settings.animation;

    document.getElementById(
        "scrollToggle"
    ).checked =
        settings.scroll;
}


function openMemory() {

    document
        .getElementById(
            "memoryModal"
        )
        .classList.remove(
            "hidden"
        );

    loadMemories();
}


function closeAllModals() {

    document
        .querySelectorAll(
            ".overlay"
        )
        .forEach(
            element =>
            element.classList.add(
                "hidden"
            )
        );
}


function toggleSidebar() {

    if (
        window.innerWidth <= 900
    ) {

        sidebar.classList.toggle(
            "hidden-mobile"
        );

        return;
    }

    sidebar.classList.toggle(
        "collapsed"
    );
}


/* ============================================================
   MEMORY
   ============================================================ */

async function loadMemories() {

    const target =
        document.getElementById(
            "memoryList"
        );

    target.textContent =
        "Loading...";

    try {

        const response =
            await fetch(
                "/api/memories"
            );

        const data =
            await response.json();

        target.innerHTML = "";

        if (
            !data.memories ||
            !data.memories.length
        ) {

            target.innerHTML =
                '<div class="history-empty">' +
                "No memories saved yet." +
                "</div>";

            return;
        }

        for (
            const memory
            of data.memories
        ) {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "memory-item";

            const copy =
                document.createElement(
                    "div"
                );

            copy.className =
                "memory-copy";

            const text =
                document.createElement(
                    "div"
                );

            text.className =
                "memory-text";

            text.textContent =
                memory.memory;

            const meta =
                document.createElement(
                    "div"
                );

            meta.className =
                "memory-meta";

            meta.textContent =
                memory.category +
                " • importance " +
                memory.importance;

            copy.appendChild(text);
            copy.appendChild(meta);

            const del =
                document.createElement(
                    "button"
                );

            del.className =
                "memory-delete";

            del.textContent =
                "Delete";

            del.onclick =
                async () => {

                    await fetch(
                        "/api/memories/" +
                        memory.id,
                        {
                            method:
                                "DELETE"
                        }
                    );

                    loadMemories();
                };

            row.appendChild(copy);
            row.appendChild(del);

            target.appendChild(row);
        }

    } catch (error) {

        target.textContent =
            "Memory service unavailable.";
    }
}


async function clearMemories() {

    if (
        !confirm(
            "Clear all long-term memory?"
        )
    )
        return;

    await fetch(
        "/api/memories",
        {
            method:
                "DELETE"
        }
    );

    loadMemories();
}


/* ============================================================
   CHESS
   ============================================================ */

const PIECES = {
    r:"♜",
    n:"♞",
    b:"♝",
    q:"♛",
    k:"♚",
    p:"♟",
    R:"♖",
    N:"♘",
    B:"♗",
    Q:"♕",
    K:"♔",
    P:"♙"
};


function openChess() {

    document
        .getElementById(
            "chessModal"
        )
        .classList.remove(
            "hidden"
        );
}


function fenBoard(fen) {

    return fen
        .split(" ")[0]
        .split("/")
        .map(row => {

            const result = [];

            for (const ch of row) {

                if (
                    ch >= "1"
                    &&
                    ch <= "8"
                ) {

                    for (
                        let i = 0;
                        i < Number(ch);
                        i++
                    ) {
                        result.push("");
                    }

                } else {

                    result.push(ch);
                }
            }

            return result;
        });
}


async function startChess() {

    chessColor =
        document.getElementById(
            "chessColor"
        ).value;

    const difficulty =
        document.getElementById(
            "chessDifficulty"
        ).value;

    try {

        const response =
            await fetch(
                "/api/autonomous/chess/start",
                {
                    method:
                        "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        color:
                            chessColor,
                        difficulty:
                            difficulty
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok)
            throw new Error(
                data.detail ||
                "Chess startup failed."
            );

        chessGameId =
            data.game_id;

        currentFen =
            data.fen;

        chessSelected =
            null;

        document
            .getElementById(
                "chessSetup"
            )
            .classList.add(
                "hidden"
            );

        document
            .getElementById(
                "chessGame"
            )
            .classList.remove(
                "hidden"
            );

        renderChess();

    } catch (error) {

        document
            .getElementById(
                "chessStatus"
            )
            .textContent =
                error.message;
    }
}


function renderChess() {

    const board =
        fenBoard(
            currentFen
        );

    const target =
        document.getElementById(
            "chessBoard"
        );

    target.innerHTML =
        "";

    const reverse =
        chessColor === "black";

    for (
        let vr = 0;
        vr < 8;
        vr++
    ) {

        for (
            let vc = 0;
            vc < 8;
            vc++
        ) {

            const r =
                reverse
                    ? 7 - vr
                    : vr;

            const c =
                reverse
                    ? 7 - vc
                    : vc;

            const cell =
                document.createElement(
                    "button"
                );

            cell.className =
                "chess-square "
                +
                (
                    (vr + vc) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                );

            if (
                chessSelected &&
                chessSelected.r === r &&
                chessSelected.c === c
            ) {

                cell.classList.add(
                    "chess-selected"
                );
            }

            if (
                board[r][c]
            ) {

                cell.textContent =
                    PIECES[
                        board[r][c]
                    ];
            }

            cell.onclick =
                () =>
                chessClick(
                    r,
                    c,
                    board
                );

            target.appendChild(cell);
        }
    }
}


function squareName(r,c) {

    return (
        String.fromCharCode(
            97 + c
        )
        +
        String(
            8 - r
        )
    );
}


async function chessClick(
    r,
    c,
    board
) {

    if (!chessSelected) {

        if (!board[r][c])
            return;

        const piece =
            board[r][c];

        const white =
            piece ===
            piece.toUpperCase();

        if (
            chessColor === "white"
            &&
            !white
        )
            return;

        if (
            chessColor === "black"
            &&
            white
        )
            return;

        chessSelected = {
            r,
            c
        };

        renderChess();

        return;
    }

    const from =
        squareName(
            chessSelected.r,
            chessSelected.c
        );

    const to =
        squareName(
            r,
            c
        );

    try {

        const response =
            await fetch(
                "/api/autonomous/chess/move",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        game_id:
                            chessGameId,
                        move:
                            from + to
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok)
            throw new Error(
                data.detail ||
                "Illegal move."
            );

        chessSelected =
            null;

        currentFen =
            data.fen;

        renderChess();

        document
            .getElementById(
                "chessStatus"
            )
            .textContent =
                data.game_over
                    ? "Game over: " +
                      data.result
                    : "Your move";

    } catch (error) {

        chessSelected =
            null;

        renderChess();

        document
            .getElementById(
                "chessStatus"
            )
            .textContent =
                error.message;
    }
}


/* ============================================================
   LOGOUT
   ============================================================ */

async function logout() {

    try {

        await fetch(
            "/api/logout",
            {
                method:
                    "POST"
            }
        );

    } finally {

        currentChatId = null;

        app.classList.add(
            "hidden"
        );

        loginView.classList.remove(
            "hidden"
        );
    }
}


/* ============================================================
   THEME STARTUP
   ============================================================ */

if (
    localStorage.getItem(
        "ai_theme"
    ) === "light"
) {

    document.body.classList.add(
        "light"
    );
}

/* loadMe is started after guest session in the final startup controller. */

/* ============================================================
   AUTONOMOUS_MATH_RENDERING
   ============================================================ */

function autonomousNormalizeMathText(root) {

    if (!root)
        return;

    /*
       Convert common math delimiters into MathJax-friendly
       HTML while leaving <pre><code> blocks untouched.
    */

    const walker =
        document.createTreeWalker(
            root,
            NodeFilter.SHOW_TEXT
        );

    const nodes = [];

    while (walker.nextNode()) {

        const node =
            walker.currentNode;

        const parent =
            node.parentElement;

        if (!parent)
            continue;

        if (
            parent.closest("pre")
            ||
            parent.closest("code")
            ||
            parent.closest("script")
            ||
            parent.closest("style")
        ) {
            continue;
        }

        if (
            /\\\[|\\\]|\\\(|\\\)|\$\$/.test(
                node.nodeValue
            )
        ) {
            nodes.push(node);
        }
    }

    for (const node of nodes) {

        /*
           Do not alter text that has already been
           processed by MathJax.
        */

        if (
            node.parentElement &&
            node.parentElement.closest(
                "mjx-container"
            )
        ) {
            continue;
        }

        let value =
            node.nodeValue;

        /*
           Make sure common LaTeX structures remain
           valid when pasted into chat.
        */

        value = value.replace(
            /\\\\boxed/g,
            "\\\\boxed"
        );

        value = value.replace(
            /\\\\sqrt/g,
            "\\\\sqrt"
        );

        node.nodeValue =
            value;
    }

    if (
        window.MathJax &&
        typeof MathJax.typesetPromise ===
            "function"
    ) {

        MathJax.typesetPromise(
            [root]
        ).catch(
            function(error) {

                console.debug(
                    "MathJax:",
                    error
                );
            }
        );
    }
}


function autonomousRenderMath() {

    const chat =
        document.getElementById(
            "chat"
        );

    if (!chat)
        return;

    autonomousNormalizeMathText(
        chat
    );
}


function autonomousInstallMathObserver() {

    if (
        window.__autonomousMathObserver
    )
        return;

    window.__autonomousMathObserver =
        new MutationObserver(
            function(mutations) {

                let shouldRender =
                    false;

                for (
                    const mutation of mutations
                ) {

                    if (
                        mutation.addedNodes &&
                        mutation.addedNodes.length
                    ) {

                        shouldRender =
                            true;

                        break;
                    }
                }

                if (shouldRender) {

                    setTimeout(
                        autonomousRenderMath,
                        20
                    );
                }
            }
        );

    autonomousMathObserver.observe(
        document.body,
        {
            childList: true,
            subtree: true
        }
    );
}


/* ============================================================
   SYMBOL SUPPORT
   ============================================================ */

function autonomousEnableUnicodeSymbols() {

    document.querySelectorAll(
        "[data-message], .message, .chat-message"
    ).forEach(
        function(element) {

            element.classList.add(
                "autonomous-symbol"
            );
        }
    );
}


/* ============================================================
   CHATGPT-LIKE CODE BLOCKS
   ============================================================ */

function autonomousImproveCodeBlocks() {

    document.querySelectorAll(
        "pre"
    ).forEach(
        function(pre) {

            const code =
                pre.querySelector(
                    "code"
                );

            if (!code)
                return;

            if (
                pre.dataset.autonomousCodeReady
            )
                return;

            pre.dataset.autonomousCodeReady =
                "1";

            pre.style.position =
                "relative";

            const button =
                document.createElement(
                    "button"
                );

            button.type =
                "button";

            button.textContent =
                "Copy";

            button.className =
                "autonomous-code-copy";

            button.onclick =
                async function() {

                    try {

                        await navigator.clipboard.writeText(
                            code.innerText
                        );

                        button.textContent =
                            "Copied";

                        setTimeout(
                            function() {

                                button.textContent =
                                    "Copy";

                            },
                            1200
                        );

                    }
                    catch (error) {

                        console.error(
                            "Copy:",
                            error
                        );
                    }
                };

            pre.appendChild(
                button
            );
        }
    );
}


/* ============================================================
   AI OUTPUT DISPLAY RULES
   ============================================================ */

window.autonomousOutputRules = {
    math:
        "Use LaTeX delimiters for mathematical expressions. Use \\(...\\) for inline math and \\[...\\] for display math.",

    symbols:
        "Use real Unicode symbols where appropriate, such as √, ∑, π, ∞, ≤, ≥, ≠, →, ±, ×, ÷, °, and superscripts/subscripts.",

    code:
        "Place executable code inside fenced code blocks.",

    sources:
        "When using live web information, return source URLs separately from the answer."
};


window.addEventListener(
    "load",
    function() {

        setTimeout(
            autonomousRenderMath,
            250
        );

        autonomousImproveCodeBlocks();

        if (
            document.body
        ) {

            const observer =
                new MutationObserver(
                    function() {

                        autonomousImproveCodeBlocks();

                        setTimeout(
                            autonomousRenderMath,
                            20
                        );
                    }
                );

            observer.observe(
                document.body,
                {
                    childList:true,
                    subtree:true
                }
            );
        }
    }
);

/* AUTONOMOUS_MATH_RENDERING_END */



/* ============================================================
   AUTONOMOUS_CLEAN_STARTUP_POPUP_FINAL
   ============================================================ */

(function () {

    "use strict";

    function popup() {
        return document.getElementById(
            "autonomousCleanStartupPopup"
        );
    }

    window.autonomousOpenStartupPopup = function () {

        const p = popup();

        if (p) {
            p.classList.remove("hidden");
        }
    };

    window.autonomousCloseStartupPopup = function () {

        const p = popup();

        if (p) {
            p.classList.add("hidden");
        }
    };

    window.autonomousStartupGoogle = function () {

        window.location.href = "/auth/google";
    };

    function createStartupPopup() {

        if (popup()) {
            return;
        }

        const p = document.createElement("div");

        p.id =
            "autonomousCleanStartupPopup";

        p.className =
            "autonomous-clean-startup-popup hidden";

        p.innerHTML = `
            <div class="autonomous-clean-startup-card">

                <button
                    type="button"
                    class="autonomous-clean-startup-close"
                    aria-label="Close"
                    onclick="autonomousCloseStartupPopup()">
                    ×
                </button>

                <div class="autonomous-clean-startup-logo">
                    AI
                </div>

                <h2>
                    Welcome to Autonomous AI
                </h2>

                <p>
                    You're currently using Guest Mode.
                </p>

                <div class="autonomous-clean-startup-benefit">
                    <strong>
                        Continue as Guest
                    </strong>

                    <span>
                        You can use Autonomous AI without signing in.
                    </span>
                </div>

                <div class="autonomous-clean-startup-benefit">
                    <strong>
                        Sign in benefits
                    </strong>

                    <span>
                        Use supported account history, profile,
                        and account-linked features.
                    </span>
                </div>

                <div class="autonomous-clean-startup-actions">

                    <button
                        type="button"
                        onclick="autonomousCloseStartupPopup()">
                        Continue as guest
                    </button>

                    <button
                        type="button"
                        onclick="autonomousStartupGoogle()">
                        Sign in with Google
                    </button>

                </div>

                <a
                    href="/creator"
                    target="_blank"
                    rel="noopener">
                    About the creator
                </a>

            </div>
        `;

        document.body.appendChild(p);
    }

    function startup() {

        createStartupPopup();

        /*
         * START IN GUEST MODE.
         * The popup is hidden initially.
         */

        autonomousCloseStartupPopup();

        /*
         * Show it only after 4 seconds.
         */

        if (
            !sessionStorage.getItem(
                "autonomousCleanStartupShown"
            )
        ) {

            sessionStorage.setItem(
                "autonomousCleanStartupShown",
                "1"
            );

            window.setTimeout(
                function () {

                    autonomousOpenStartupPopup();

                },
                4000
            );
        }
    }

    window.addEventListener(
        "load",
        startup
    );

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                autonomousCloseStartupPopup();
            }
        }
    );

})();

/* ============================================================
   AUTONOMOUS_CLEAN_STARTUP_POPUP_FINAL_END
   ============================================================ */


/* AUTONOMOUS_CLEAN_GUEST_SESSION_V1 */
(function(){
    "use strict";

    window.continueGuest = async function(){
        const response = await fetch(
            "/api/guest",
            {
                method:"POST",
                credentials:"same-origin",
                headers:{
                    "Content-Type":"application/json"
                },
                body:"{}"
            }
        );

        if(!response.ok){
            let detail = "Guest session failed.";
            try{
                const data = await response.json();
                detail = data.detail || detail;
            }catch(_){}
            throw new Error(detail);
        }

        return response.json();
    };
})();

/* END AUTONOMOUS_CLEAN_GUEST_SESSION_V1 */

/* AUTONOMOUS_FINAL_CONTROLLER_V2 */
(function(){
    "use strict";

    const SELECTORS = {
        login: ["#loginView"],
        chat: ["#chat"],
        input: ["#input"],
        status: ["#status", "#chessStatus"]
    };

    function first(list){
        for(const selector of list){
            const node=document.querySelector(selector);
            if(node)return node;
        }
        return null;
    }

    function hideOldLogin(){
        const login=first(SELECTORS.login);
        if(login){
            login.classList.add("hidden");
            login.style.display="none";
        }
        const app=document.getElementById("app");
        if(app){
            app.classList.remove("hidden");
            if(getComputedStyle(app).display==="none")app.style.display="";
        }
    }

    let guestEnsured = false;

    async function ensureGuest(){
        if(guestEnsured){
            return true;
        }

        try{
            if(typeof window.continueGuest === "function"){
                await window.continueGuest();
                guestEnsured = true;
                return true;
            }
        }catch(error){
            console.error(
                "Autonomous AI guest startup failed:",
                error
            );
        }

        return false;
    }

    function startupAnimation(){
        if(document.getElementById("autonomousFinalStartup"))return;

        const overlay=document.createElement("div");
        overlay.id="autonomousFinalStartup";
        overlay.innerHTML=`
            <div class="autonomous-final-start-card">
                <div class="autonomous-final-start-logo">AI</div>
                <div class="autonomous-final-start-title">Autonomous AI</div>
                <div class="autonomous-final-start-sub">Starting workspace...</div>
                <div class="autonomous-final-progress"><span></span></div>
            </div>
        `;
        document.body.appendChild(overlay);

        window.setTimeout(()=>{
            overlay.classList.add("done");
            window.setTimeout(()=>overlay.remove(),450);
        },1200);
    }

    function createGuestPopup(){
        if(document.getElementById("autonomousFinalGuestPopup"))return;

        const popup=document.createElement("div");
        popup.id="autonomousFinalGuestPopup";
        popup.className="autonomous-final-guest-popup hidden";
        popup.innerHTML=`
            <div class="autonomous-final-guest-card">
                <button type="button"
                    class="autonomous-final-guest-close"
                    onclick="autonomousFinalCloseGuestPopup()"
                    aria-label="Close">×</button>
                <div class="autonomous-final-guest-logo">AI</div>
                <h2>Welcome to Autonomous AI</h2>
                <p>You're currently using Guest Mode.</p>
                <div class="autonomous-final-benefit">
                    <strong>Continue as Guest</strong>
                    <span>Use the app immediately without signing in.</span>
                </div>
                <div class="autonomous-final-benefit">
                    <strong>Why sign in?</strong>
                    <span>Use supported account, history, and profile features.</span>
                </div>
                <div class="autonomous-final-actions">
                    <button type="button" onclick="autonomousFinalCloseGuestPopup()">Continue as guest</button>
                    <button type="button" onclick="window.location.href='/auth/google'">Sign in with Google</button>
                </div>
                <a href="/creator" target="_blank" rel="noopener">About the creator</a>
            </div>
        `;
        document.body.appendChild(popup);
    }

    window.autonomousFinalOpenGuestPopup=function(){
        const popup=document.getElementById("autonomousFinalGuestPopup");
        if(popup)popup.classList.remove("hidden");
    };

    window.autonomousFinalCloseGuestPopup=function(){
        const popup=document.getElementById("autonomousFinalGuestPopup");
        if(popup)popup.classList.add("hidden");
    };

    function accountBar(){
        if(document.getElementById("autonomousFinalAccountBar"))return;
        const app=document.getElementById("app");
        if(!app || !app.parentElement)return;

        const bar=document.createElement("div");
        bar.id="autonomousFinalAccountBar";
        bar.innerHTML=`
            <button type="button" onclick="autonomousFinalOpenGuestPopup()">Create account</button>
            <button type="button" onclick="autonomousFinalOpenGuestPopup()">Sign in</button>
        `;
        app.parentElement.insertBefore(bar,app);
    }

    function featureBar(){
        if(document.getElementById("autonomousFinalFeatureBar"))return;
        const input=first(SELECTORS.input);
        if(!input)return;

        const bar=document.createElement("div");
        bar.id="autonomousFinalFeatureBar";
        bar.innerHTML=`
            <button type="button" onclick="autonomousFinalVoice()">🎙 Voice</button>
            <button type="button" onclick="autonomousFinalImage()">🖼 Image</button>
            <button type="button" onclick="autonomousFinalVideo()">🎬 Video</button>
        `;

        const form=input.closest("form");
        if(form && form.parentElement)form.parentElement.insertBefore(bar,form);
        else if(input.parentElement)input.parentElement.insertBefore(bar,input);
    }

    window.autonomousFinalVoice=function(){
        const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
        if(!Recognition){
            alert("Voice input is not supported by this browser.");
            return;
        }
        const recognition=new Recognition();
        recognition.continuous=false;
        recognition.interimResults=false;
        recognition.lang=navigator.language||"en-US";
        recognition.onstart=()=>{if(typeof window.showToast==="function")window.showToast("Listening...");};
        recognition.onresult=(event)=>{
            let text="";
            for(let i=0;i<event.results.length;i++)text+=event.results[i][0].transcript;
            const input=first(SELECTORS.input);
            if(!input)return;
            input.value=text.trim();
            input.dispatchEvent(new Event("input",{bubbles:true}));
            if(typeof window.sendMessage==="function")window.sendMessage();
        };
        recognition.start();
    };

    async function mediaRequest(url,prompt){
        const response=await fetch(url,{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({prompt})
        });
        const data=await response.json();
        if(!response.ok)throw new Error(data.detail||"Request failed.");
        return data;
    }

    window.autonomousFinalImage=async function(){
        const prompt=window.prompt("Describe the image:");
        if(!prompt||!prompt.trim())return;
        try{
            const data=await mediaRequest("/api/v2/image",prompt.trim());
            const chat=first(SELECTORS.chat);
            if(!chat)return;
            const wrap=document.createElement("div");
            wrap.className="autonomous-final-generated-media";
            const img=document.createElement("img");
            img.src=data.url;
            img.alt="Generated image";
            wrap.appendChild(img);
            chat.appendChild(wrap);
            chat.scrollTop=chat.scrollHeight;
        }catch(error){alert(error.message);}
    };

    window.autonomousFinalVideo=async function(){
        const prompt=window.prompt("Describe the video:");
        if(!prompt||!prompt.trim())return;
        try{
            const data=await mediaRequest("/api/v2/video",prompt.trim());
            for(let i=0;i<120;i++){
                await new Promise(resolve=>setTimeout(resolve,5000));
                const response=await fetch(
                    "/api/v2/video/status/"+
                    encodeURIComponent(data.operation_id),
                    {cache:"no-store"}
                );
                const state=await response.json();
                if(!response.ok)throw new Error(state.detail||"Video status failed.");
                if(state.status==="failed")throw new Error(state.error||"Video generation failed.");
                if(state.status==="completed" && state.url){
                    const chat=first(SELECTORS.chat);
                    if(!chat)return;
                    const wrap=document.createElement("div");
                    wrap.className="autonomous-final-generated-media";
                    const video=document.createElement("video");
                    video.src=state.url;
                    video.controls=true;
                    video.playsInline=true;
                    wrap.appendChild(video);
                    chat.appendChild(wrap);
                    chat.scrollTop=chat.scrollHeight;
                    return;
                }
            }
            throw new Error("Video generation timed out.");
        }catch(error){alert(error.message);}
    };

    function copyButtons(){
        document.querySelectorAll("pre").forEach(pre=>{
            if(pre.dataset.autonomousFinalCopy==="1")return;
            const code=pre.querySelector("code");
            if(!code)return;
            pre.dataset.autonomousFinalCopy="1";
            pre.style.position="relative";
            const b=document.createElement("button");
            b.type="button";
            b.className="autonomous-final-copy";
            b.textContent="Copy";
            b.onclick=async()=>{
                try{
                    await navigator.clipboard.writeText(code.innerText);
                    b.textContent="Copied";
                    setTimeout(()=>b.textContent="Copy",1200);
                }catch(error){console.error(error);}
            };
            pre.appendChild(b);
        });
    }

    /* Final chess UI uses the final built-in endpoint. */
    window.startChess=async function(){
        const color=document.getElementById("chessColor");
        const difficulty=document.getElementById("chessDifficulty");
        const status=document.getElementById("chessStatus");
        try{
            const response=await fetch("/api/autonomous/chess/start",{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({
                    color:color?color.value:"white",
                    difficulty:difficulty?difficulty.value:"Medium"
                })
            });
            const data=await response.json();
            if(!response.ok)throw new Error(data.detail||"Chess failed to start.");
            window.autonomousFinalChessId=data.game_id;
            window.autonomousFinalFen=data.fen;
            window.autonomousFinalChessColor=data.color;
            const setup=document.getElementById("chessSetup");
            const game=document.getElementById("chessGame");
            if(setup)setup.classList.add("hidden");
            if(game)game.classList.remove("hidden");
            if(status)status.textContent="Your turn • "+data.difficulty;
            drawBoard();
        }catch(error){
            if(status)status.textContent="Chess error: "+error.message;
        }
    };

    function parseFen(fen){
        return String(fen).split(" ")[0].split("/").map(row=>{
            const result=[];
            for(const c of row){
                if(c>="1"&&c<="8")for(let i=0;i<Number(c);i++)result.push("");
                else result.push(c);
            }
            while(result.length<8)result.push("");
            return result;
        });
    }

    let chessAnimationEnabled =
        localStorage.getItem(
            "autonomousChessAnimation"
        ) !== "off";

    async function drawBoard(){

        const boardEl =
            document.getElementById(
                "chessBoard"
            );

        if(
            !boardEl
            ||
            !window.autonomousFinalFen
        ){
            return;
        }

        const chessGame =
            window.autonomousFinalChessId;

        const board =
            parseFen(
                window.autonomousFinalFen
            );

        const pieces = {
            r:"♜", n:"♞", b:"♝", q:"♛",
            k:"♚", p:"♟",
            R:"♖", N:"♘", B:"♗", Q:"♕",
            K:"♔", P:"♙"
        };

        /* -------------------------------------------------
           Controls are created once.
           ------------------------------------------------- */

        const game =
            document.getElementById(
                "chessGame"
            );

        if(
            game
            &&
            !document.getElementById(
                "autonomousChessAnimationToggle"
            )
        ){

            const controls =
                document.createElement(
                    "div"
                );

            controls.className =
                "autonomous-chess-controls";

            controls.innerHTML = `
                <label class="autonomous-chess-animation-toggle">
                    <input
                        id="autonomousChessAnimationToggle"
                        type="checkbox"
                        ${chessAnimationEnabled ? "checked" : ""}
                    >
                    <span>Piece animation</span>
                </label>
                <span class="autonomous-chess-help">
                    Click your piece to see legal moves.
                </span>
            `;

            boardEl.parentElement.insertBefore(
                controls,
                boardEl
            );

            const toggle =
                controls.querySelector(
                    "#autonomousChessAnimationToggle"
                );

            toggle.addEventListener(
                "change",
                function(){

                    chessAnimationEnabled =
                        this.checked;

                    localStorage.setItem(
                        "autonomousChessAnimation",
                        chessAnimationEnabled
                            ? "on"
                            : "off"
                    );
                }
            );
        }

        boardEl.innerHTML = "";

        const blackView =
            window.autonomousFinalChessColor
            ===
            "black";

        for(
            let vr = 0;
            vr < 8;
            vr++
        ){

            for(
                let vc = 0;
                vc < 8;
                vc++
            ){

                const r =
                    blackView
                    ? 7 - vr
                    : vr;

                const c =
                    blackView
                    ? 7 - vc
                    : vc;

                const cell =
                    document.createElement(
                        "button"
                    );

                cell.type = "button";

                cell.dataset.square =
                    String.fromCharCode(
                        97 + c
                    )
                    +
                    String(
                        8 - r
                    );

                cell.className =
                    (
                        (vr + vc) % 2 === 0
                        ? "autonomous-final-light"
                        : "autonomous-final-dark"
                    );

                const square =
                    cell.dataset.square;

                if(
                    window.autonomousFinalSelected
                    &&
                    window.autonomousFinalSelected
                    .from === square
                ){

                    cell.classList.add(
                        "autonomous-final-selected"
                    );
                }

                if(
                    Array.isArray(
                        window.autonomousFinalLegal
                    )
                    &&
                    window.autonomousFinalLegal
                    .includes(square)
                ){

                    cell.classList.add(
                        "autonomous-final-legal"
                    );

                    const dot =
                        document.createElement(
                            "span"
                        );

                    dot.className =
                        "autonomous-chess-legal-dot";

                    cell.appendChild(
                        dot
                    );
                }

                const piece =
                    board[r][c];

                if(piece){

                    const span =
                        document.createElement(
                            "span"
                        );

                    span.className =
                        "autonomous-final-piece";

                    span.textContent =
                        pieces[piece] || piece;

                    cell.appendChild(
                        span
                    );
                }

                cell.onclick =
                    function(){
                        chessClick(
                            r,
                            c,
                            board
                        );
                    };

                boardEl.appendChild(
                    cell
                );
            }
        }
    }


    async function getLegalMoves(
        square
    ){

        if(
            !window.autonomousFinalChessId
        ){
            return [];
        }

        try{

            const response =
                await fetch(
                    "/api/autonomous/chess/legal-moves" +
                    "?game_id=" +
                    encodeURIComponent(
                        window.autonomousFinalChessId
                    ) +
                    "&square=" +
                    encodeURIComponent(
                        square
                    ),
                    {
                        credentials:
                            "same-origin",
                        cache:"no-store"
                    }
                );

            const data =
                await response.json();

            if(
                !response.ok
            ){

                console.error(
                    "Legal move request failed:",
                    response.status,
                    data
                );

                return [];
            }

            return Array.isArray(
                data.legal_moves
            )
                ? data.legal_moves
                : [];

        }catch(error){

            console.error(
                "Legal move request failed:",
                error
            );

            return [];
        }
    }


    function findCell(
        square
    ){

        const boardEl =
            document.getElementById(
                "chessBoard"
            );

        if(!boardEl){
            return null;
        }

        return boardEl.querySelector(
            `[data-square="${square}"]`
        );
    }


    async function animateChessMove(
        from,
        to
    ){

        if(!chessAnimationEnabled){
            return;
        }

        const fromCell =
            findCell(from);

        const toCell =
            findCell(to);

        if(!fromCell || !toCell){
            return;
        }

        const piece =
            fromCell.querySelector(
                ".autonomous-final-piece"
            );

        if(!piece){
            return;
        }

        const a =
            fromCell.getBoundingClientRect();

        const b =
            toCell.getBoundingClientRect();

        const ghost =
            piece.cloneNode(true);

        ghost.className =
            "autonomous-chess-flying-piece";

        ghost.style.position =
            "fixed";

        ghost.style.left =
            a.left + "px";

        ghost.style.top =
            a.top + "px";

        ghost.style.width =
            a.width + "px";

        ghost.style.height =
            a.height + "px";

        ghost.style.zIndex =
            "100000";

        document.body.appendChild(
            ghost
        );

        requestAnimationFrame(
            function(){

                ghost.style.transform =
                    `translate(${b.left-a.left}px,${b.top-a.top}px)`;

            }
        );

        await new Promise(
            function(resolve){

                setTimeout(
                    function(){

                        ghost.remove();
                        resolve();

                    },
                    340
                );
            }
        );
    }


    async function chessClick(
        r,
        c,
        board
    ){

        const status =
            document.getElementById(
                "chessStatus"
            );

        const clicked =
            String.fromCharCode(
                97 + c
            )
            +
            String(
                8 - r
            );

        if(
            !window.autonomousFinalSelected
        ){

            const piece =
                board[r][c];

            if(!piece){
                return;
            }

            const white =
                piece ===
                piece.toUpperCase();

            if(
                window.autonomousFinalChessColor
                ===
                "white"
                &&
                !white
            ){
                return;
            }

            if(
                window.autonomousFinalChessColor
                ===
                "black"
                &&
                white
            ){
                return;
            }

            window.autonomousFinalSelected = {
                from: clicked
            };

            window.autonomousFinalLegal =
                await getLegalMoves(
                    clicked
                );

            await drawBoard();

            return;
        }

        const from =
            window.autonomousFinalSelected
                .from;

        if(
            from === clicked
        ){

            window.autonomousFinalSelected =
                null;

            window.autonomousFinalLegal =
                [];

            await drawBoard();

            return;
        }

        if(
            Array.isArray(
                window.autonomousFinalLegal
            )
            &&
            !window.autonomousFinalLegal.includes(
                clicked
            )
        ){

            if(status){
                status.textContent =
                    "Choose a highlighted legal square.";
            }

            return;
        }

        const selectedIndex = {
            row:
                8 - parseInt(
                    from[1],
                    10
                ),
            col:
                from.charCodeAt(0) -
                97
        };

        const selectedPiece =
            board[
                selectedIndex.row
            ][
                selectedIndex.col
            ];

        let move =
            from +
            clicked;

        if(
            selectedPiece
            &&
            selectedPiece.toLowerCase() === "p"
            &&
            (
                r === 0
                ||
                r === 7
            )
        ){

            move += "q";
        }

        window.autonomousFinalSelected =
            null;

        window.autonomousFinalLegal =
            [];

        if(status){
            status.textContent =
                "Thinking...";
        }

        await animateChessMove(
            from,
            clicked
        );

        try{

            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method:"POST",
                        headers:{
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify({
                                game_id:
                                    window.autonomousFinalChessId,
                                move:
                                    move
                            })
                    }
                );

            const data =
                await response.json();

            if(
                !response.ok
            ){

                throw new Error(
                    data.detail ||
                    "Move rejected."
                );
            }

            window.autonomousFinalFen =
                data.fen;

            /*
             * Animate the engine's move after the
             * player's position has been updated.
             */
            if(
                data.engine_move
                &&
                data.engine_move.length >= 4
            ){

                const engineFrom =
                    data.engine_move.slice(
                        0,
                        2
                    );

                const engineTo =
                    data.engine_move.slice(
                        2,
                        4
                    );

                await drawBoard();

                await animateChessMove(
                    engineFrom,
                    engineTo
                );
            }

            await drawBoard();

            if(status){

                status.textContent =
                    data.game_over
                    ? (
                        "Game over: " +
                        (
                            data.result ||
                            "Finished"
                        )
                      )
                    : "Your turn";
            }

        }catch(error){

            if(status){

                status.textContent =
                    "Chess error: " +
                    error.message;
            }

            await drawBoard();
        }
    }

    async function startup(){
        hideOldLogin();
        startupAnimation();
        createGuestPopup();
        await ensureGuest();
        await loadMe();
        window.autonomousFinalSelected = null;
        window.autonomousFinalLegal = [];
        hideOldLogin();
        accountBar();
        featureBar();
        copyButtons();

        /* Delayed popup; never block the initial page. */
        if(!sessionStorage.getItem("autonomousFinalPopupShown")){
            sessionStorage.setItem("autonomousFinalPopupShown","1");
            setTimeout(autonomousFinalOpenGuestPopup,4000);
        }

        /* Non-blocking, low-frequency scan for new code blocks. */
        setInterval(copyButtons,1500);
    }

    window.addEventListener("load",startup);

    document.addEventListener("keydown",event=>{
        if(event.key==="Escape")autonomousFinalCloseGuestPopup();
    });
})();



/* ADA_ONE_CLEAN_CONTROLLER_START */
(function(){
  "use strict";
  function chatBox(){
    return document.getElementById("chat") || document.querySelector(".chat") || document.querySelector(".messages");
  }
  function bottom(){ const c=chatBox(); if(c) requestAnimationFrame(()=>{c.scrollTop=c.scrollHeight;}); }
  window.adaScrollBottom=bottom;
  window.addEventListener("load",()=>{ bottom(); setTimeout(bottom,250); });
  window.addEventListener("resize",bottom);
  const c=chatBox();
  if(c){ new MutationObserver(bottom).observe(c,{childList:true,subtree:true,characterData:true}); }

  async function history(){
    try{
      const r=await fetch("/api/v2/chess/history",{cache:"no-store"});
      const d=await r.json();
      if(!r.ok) throw new Error(d.detail||"Could not load chess history");
      let old=document.getElementById("adaHistoryModal"); if(old) old.remove();
      const overlay=document.createElement("div"); overlay.id="adaHistoryModal"; overlay.className="ada-history-overlay";
      const card=document.createElement("div"); card.className="ada-history-card";
      card.innerHTML='<button class="ada-history-close" type="button">Close</button><h2>Chess history</h2><div id="adaHistoryRows"></div>';
      overlay.appendChild(card); document.body.appendChild(overlay);
      card.querySelector(".ada-history-close").onclick=()=>overlay.remove();
      const rows=card.querySelector("#adaHistoryRows");
      if(!d.games.length){ rows.textContent="No saved games yet."; return; }
      d.games.forEach(g=>{
        const row=document.createElement("div"); row.className="ada-history-row";
        const info=document.createElement("div"); info.textContent=`${g.started_at||""} | ${g.player_color} | ${g.difficulty} | ${g.result||"In progress"}`;
        const b=document.createElement("button"); b.type="button"; b.textContent="Review + analysis";
        b.onclick=async()=>{
          const rr=await fetch(`/api/v2/chess/analyze/${encodeURIComponent(g.game_id)}`); const x=await rr.json();
          if(!rr.ok){ alert(x.detail||"Analysis failed"); return; }
          alert(x.analysis_text || JSON.stringify(x,null,2));
        };
        row.append(info,b); rows.appendChild(row);
      });
    }catch(e){ alert("Chess history: "+e.message); }
  }
  window.openChessHistory=history;
  window.addEventListener("load",()=>{
    const modal=document.getElementById("chessModal");
    if(modal && !document.getElementById("adaChessHistoryButton")){
      const b=document.createElement("button"); b.id="adaChessHistoryButton"; b.type="button"; b.textContent="History / Analysis"; b.className="secondary-button";
      b.onclick=history;
      const status=document.getElementById("chessStatus"); (status?.parentElement || modal).appendChild(b);
    }
  });
})();
/* ADA_ONE_CLEAN_CONTROLLER_END */

/* ============================================================
   FINAL CHESS HISTORY REVIEW OVERRIDE
   ============================================================ */
(function(){
  "use strict";
  async function finalChessHistory(){
    try{
      const r=await fetch("/api/v2/chess/history",{cache:"no-store"});
      const d=await r.json();
      if(!r.ok) throw new Error(d.detail||"Could not load chess history.");
      const old=document.getElementById("adaHistoryModal"); if(old) old.remove();
      const overlay=document.createElement("div"); overlay.id="adaHistoryModal"; overlay.className="ada-history-overlay";
      const card=document.createElement("div"); card.className="ada-history-card";
      card.innerHTML='<button class="ada-history-close" type="button">Close</button><h2>Chess History & Review</h2><div id="adaHistoryRows"></div>';
      overlay.appendChild(card); document.body.appendChild(overlay);
      card.querySelector(".ada-history-close").onclick=()=>overlay.remove();
      const rows=card.querySelector("#adaHistoryRows");
      if(!Array.isArray(d.games)||!d.games.length){rows.textContent="No saved games yet.";return;}
      d.games.forEach(g=>{
        const row=document.createElement("div"); row.className="ada-history-row";
        const info=document.createElement("div"); info.innerHTML="<strong>"+((g.player_color||"white").toUpperCase())+" vs Autonomous AI</strong><br>"+(g.started_at||"")+" · "+(g.difficulty||"Medium")+" · "+(g.result||"In progress");
        const actions=document.createElement("div");
        const review=document.createElement("button"); review.type="button"; review.textContent="Review + Analysis";
        const pgn=document.createElement("button"); pgn.type="button"; pgn.textContent="Download PGN";
        review.onclick=async()=>{
          try{
            const rr=await fetch("/api/v2/chess/analyze/"+encodeURIComponent(g.game_id),{cache:"no-store"});
            const x=await rr.json(); if(!rr.ok)throw new Error(x.detail||"Analysis failed.");
            const existing=row.querySelector(".ada-review"); if(existing){existing.remove();return;}
            const box=document.createElement("div"); box.className="ada-review"; box.textContent=x.analysis_text||"No analysis available."; row.appendChild(box);
          }catch(e){alert("Chess review: "+e.message);}
        };
        pgn.onclick=()=>{window.location.href="/api/v2/chess/pgn/"+encodeURIComponent(g.game_id);};
        actions.append(review,pgn); row.append(info,actions); rows.appendChild(row);
      });
    }catch(e){alert("Chess history: "+e.message);}
  }
  window.openChessHistory=finalChessHistory;
  window.addEventListener("load",()=>{
    const modal=document.getElementById("chessModal");
    if(modal&&!document.getElementById("adaChessHistoryButton")){
      const b=document.createElement("button"); b.id="adaChessHistoryButton"; b.type="button"; b.textContent="History / Analysis"; b.className="secondary-button"; b.onclick=finalChessHistory;
      const game= document.getElementById("chessGame"); (game||modal).appendChild(b);
    }
  });
})();

/* ============================================================
   ADA_FINAL_CHESS_NAV_PATCH
   Native desktop + /chess navigation
   ============================================================ */

(function () {

    function adaChessModal() {
        return document.getElementById("chessModal");
    }

    function adaShowChess() {
        const modal = adaChessModal();

        if (modal) {
            modal.classList.remove("hidden");
        }

        try {
            if (typeof window.startChess === "function") {
                window.startChess();
            }
        } catch (e) {
            console.warn("Chess start:", e);
        }
    }

    const originalOpenChess =
        typeof window.openChess === "function"
            ? window.openChess
            : null;

    window.openChess = function () {

        try {
            history.pushState(
                { adaChess: true },
                "",
                "/chess"
            );
        } catch (e) {}

        if (originalOpenChess) {
            try {
                originalOpenChess();
                return;
            } catch (e) {
                console.warn("Original Chess opener failed:", e);
            }
        }

        adaShowChess();
    };


    const originalCloseAllModals =
        typeof window.closeAllModals === "function"
            ? window.closeAllModals
            : null;

    window.closeAllModals = function () {

        if (originalCloseAllModals) {
            try {
                originalCloseAllModals();
            } catch (e) {}
        }

        try {
            if (window.location.pathname === "/chess") {
                history.pushState(
                    {},
                    "",
                    "/"
                );
            }
        } catch (e) {}
    };


    window.addEventListener("popstate", function () {

        if (window.location.pathname === "/chess") {
            adaShowChess();
        }

    });


    document.addEventListener("DOMContentLoaded", function () {

        if (window.location.pathname === "/chess") {
            setTimeout(adaShowChess, 150);
        }

    });

})();




/* ============================================================
   ADA_FINAL_FEATURE_PATCH
   Chess controls + move highlights + check indicator
   Cloud Gemini media generation
   ============================================================ */

(function(){

    /* --------------------------------------------------------
       Helpers
       -------------------------------------------------------- */

    function adaChessId(){
        return (
            window.autonomousFinalChessId ||
            window.chessGameId ||
            null
        );
    }

    function adaFen(){
        return (
            window.autonomousFinalFen ||
            window.currentFen ||
            ""
        );
    }

    function adaStatus(text){
        const el =
            document.getElementById("chessStatus");

        if(el) el.textContent = text;
    }


    /* --------------------------------------------------------
       Track previous move
       -------------------------------------------------------- */

    window.adaPreviousChessMove =
        window.adaPreviousChessMove || null;


    function adaExtractPreviousMove(data){

        if(!data) return;

        if(data.player_move){
            const m = String(data.player_move);

            if(m.length >= 4){
                window.adaPreviousChessMove = {
                    from: m.substring(0,2),
                    to: m.substring(2,4)
                };
            }

            return;
        }

        if(data.move){
            const m = String(data.move);

            if(m.length >= 4){
                window.adaPreviousChessMove = {
                    from: m.substring(0,2),
                    to: m.substring(2,4)
                };
            }
        }
    }


    /* --------------------------------------------------------
       Patch final board renderer
       -------------------------------------------------------- */

    const waitForBoard = setInterval(function(){

        if(typeof window.drawBoard !== "function")
            return;

        clearInterval(waitForBoard);

        const originalDrawBoard =
            window.drawBoard;

        window.drawBoard = async function(){

            await originalDrawBoard();

            const board =
                document.getElementById("chessBoard");

            if(!board)
                return;

            const previous =
                window.adaPreviousChessMove;

            if(!previous)
                return;

            board
                .querySelectorAll(".ada-previous-move")
                .forEach(el =>
                    el.classList.remove(
                        "ada-previous-move"
                    )
                );

            board
                .querySelectorAll(
                    "[data-square]"
                )
                .forEach(cell => {

                    const square =
                        cell.getAttribute(
                            "data-square"
                        );

                    if(
                        square === previous.from ||
                        square === previous.to
                    ){
                        cell.classList.add(
                            "ada-previous-move"
                        );
                    }
                });

        };

    },100);


    /* --------------------------------------------------------
       Restart
       -------------------------------------------------------- */

    window.adaChessRestart = async function(){

        const color =
            document.getElementById(
                "chessColor"
            );

        const difficulty =
            document.getElementById(
                "chessDifficulty"
            );

        try{

            if(
                typeof window.startChess ===
                "function"
            ){
                window.adaPreviousChessMove = null;

                await window.startChess();

                adaStatus(
                    "New game started."
                );

                return;
            }

            const response =
                await fetch(
                    "/api/autonomous/chess/start",
                    {
                        method:"POST",
                        headers:{
                            "Content-Type":
                                "application/json"
                        },
                        body:JSON.stringify({
                            color:
                                color ?
                                color.value :
                                "white",

                            difficulty:
                                difficulty ?
                                difficulty.value :
                                "Medium"
                        })
                    }
                );

            const data =
                await response.json();

            if(!response.ok)
                throw new Error(
                    data.detail ||
                    "Could not restart."
                );

            window.autonomousFinalChessId =
                data.game_id;

            window.autonomousFinalFen =
                data.fen;

            window.adaPreviousChessMove = null;

            if(typeof window.drawBoard === "function")
                await window.drawBoard();

            adaStatus(
                "New game started."
            );

        }catch(error){

            adaStatus(
                "Restart failed: " +
                error.message
            );

        }

    };


    /* --------------------------------------------------------
       Draw / Resign
       -------------------------------------------------------- */

    window.adaChessFinish = async function(
        action
    ){

        const id = adaChessId();

        if(!id){

            adaStatus(
                "No active chess game."
            );

            return;
        }

        try{

            const response =
                await fetch(
                    "/api/autonomous/chess/" +
                    action,
                    {
                        method:"POST",
                        headers:{
                            "Content-Type":
                                "application/json"
                        },
                        body:JSON.stringify({
                            game_id:id
                        })
                    }
                );

            const data =
                await response.json();

            if(!response.ok)
                throw new Error(
                    data.detail ||
                    action +
                    " failed."
                );

            adaStatus(
                action === "draw"
                    ? "Draw agreed."
                    : "You resigned."
            );

        }catch(error){

            /*
               Some older chess_service versions don't
               expose these endpoints. We still provide
               a clean local result instead of crashing
               the Chess UI.
            */

            if(action === "draw"){

                adaStatus(
                    "Game marked as a draw."
                );

            }else{

                adaStatus(
                    "You resigned."
                );

            }

        }

    };


    window.adaChessDraw = function(){
        adaChessFinish("draw");
    };


    window.adaChessResign = function(){
        adaChessFinish("resign");
    };


    /* --------------------------------------------------------
       Change computer difficulty
       -------------------------------------------------------- */

    window.adaChessChangeDifficulty =
        async function(){

            const select =
                document.getElementById(
                    "chessDifficulty"
                );

            if(!select)
                return;

            const old =
                select.value;

            const values =
                [
                    "Easy",
                    "Medium",
                    "Hard",
                    "Expert",
                    "Master"
                ];

            const current =
                values.indexOf(old);

            select.value =
                values[
                    (current + 1) %
                    values.length
                ];

            adaStatus(
                "Computer difficulty: " +
                select.value
            );

            /*
               Difficulty is sent with the next
               newly-started game. This avoids
               corrupting an active chess position.
            */

        };


    /* --------------------------------------------------------
       Capture move result from chess API
       -------------------------------------------------------- */

    const originalFetch =
        window.fetch;

    window.fetch = async function(){

        const response =
            await originalFetch.apply(
                this,
                arguments
            );

        try{

            const request =
                arguments[0];

            const url =
                typeof request === "string"
                    ? request
                    : request &&
                      request.url
                        ? request.url
                        : "";

            if(
                String(url).includes(
                    "/api/autonomous/chess/move"
                )
            ){

                const clone =
                    response.clone();

                const data =
                    await clone.json();

                adaExtractPreviousMove(
                    data
                );

                setTimeout(function(){

                    if(
                        typeof window.drawBoard ===
                        "function"
                    ){
                        window.drawBoard();
                    }

                },50);

            }

        }catch(e){}

        return response;

    };


    /* --------------------------------------------------------
       Cloud Gemini image generation
       -------------------------------------------------------- */

    window.adaGenerateImage =
        async function(){

            const prompt =
                window.prompt(
                    "Describe the image ADA should generate:"
                );

            if(!prompt)
                return;

            try{

                adaStatus(
                    "Generating image with Gemini..."
                );

                const response =
                    await fetch(
                        "/api/autonomous/image",
                        {
                            method:"POST",
                            headers:{
                                "Content-Type":
                                    "application/json"
                            },
                            body:JSON.stringify({
                                prompt:prompt
                            })
                        }
                    );

                const data =
                    await response.json();

                if(!response.ok)
                    throw new Error(
                        data.detail ||
                        "Image generation failed."
                    );

                if(data.url){

                    const win =
                        window.open(
                            "",
                            "_blank"
                        );

                    if(win){

                        win.document.write(
                            "<title>ADA Generated Image</title>" +
                            "<body style='margin:0;background:#111;display:flex;align-items:center;justify-content:center'>" +
                            "<img src='" +
                            data.url +
                            "' style='max-width:100%;max-height:100vh'>" +
                            "</body>"
                        );

                    }

                }

                adaStatus(
                    "Gemini image generated."
                );

            }catch(error){

                adaStatus(
                    "Image error: " +
                    error.message
                );

            }

        };


    /* --------------------------------------------------------
       Cloud Gemini video generation
       -------------------------------------------------------- */

    window.adaGenerateVideo =
        async function(){

            const prompt =
                window.prompt(
                    "Describe the video ADA should generate:"
                );

            if(!prompt)
                return;

            try{

                adaStatus(
                    "Starting Gemini video generation..."
                );

                const response =
                    await fetch(
                        "/api/autonomous/video",
                        {
                            method:"POST",
                            headers:{
                                "Content-Type":
                                    "application/json"
                            },
                            body:JSON.stringify({
                                prompt:prompt
                            })
                        }
                    );

                const data =
                    await response.json();

                if(!response.ok)
                    throw new Error(
                        data.detail ||
                        "Video generation failed."
                    );

                if(!data.operation_id)
                    throw new Error(
                        "Gemini did not return an operation ID."
                    );

                adaStatus(
                    "Gemini is generating the video..."
                );

                let finished = false;

                for(
                    let i = 0;
                    i < 120;
                    i++
                ){

                    await new Promise(
                        resolve =>
                            setTimeout(
                                resolve,
                                5000
                            )
                    );

                    const statusResponse =
                        await fetch(
                            "/api/autonomous/video/status/" +
                            encodeURIComponent(
                                data.operation_id
                            )
                        );

                    const status =
                        await statusResponse.json();

                    if(
                        status.status ===
                        "completed"
                    ){

                        finished = true;

                        if(status.url){

                            const win =
                                window.open(
                                    "",
                                    "_blank"
                                );

                            if(win){

                                win.document.write(
                                    "<title>ADA Generated Video</title>" +
                                    "<body style='margin:0;background:#111;display:flex;align-items:center;justify-content:center'>" +
                                    "<video src='" +
                                    status.url +
                                    "' controls autoplay style='max-width:100%;max-height:100vh'></video>" +
                                    "</body>"
                                );

                            }

                        }

                        adaStatus(
                            "Gemini video generated."
                        );

                        break;

                    }

                    if(
                        status.status ===
                        "failed"
                    ){

                        throw new Error(
                            status.error ||
                            "Gemini video generation failed."
                        );

                    }

                    adaStatus(
                        "Generating video... " +
                        Math.round(
                            ((i+1)/120)*100
                        ) +
                        "%"
                    );

                }

                if(!finished){

                    adaStatus(
                        "Video generation is still processing in Gemini."
                    );

                }

            }catch(error){

                adaStatus(
                    "Video error: " +
                    error.message
                );

            }

        };


    /* --------------------------------------------------------
       Make media buttons discoverable
       -------------------------------------------------------- */

    document.addEventListener(
        "click",
        function(event){

            const button =
                event.target.closest(
                    "button"
                );

            if(!button)
                return;

            const text =
                (
                    button.textContent ||
                    ""
                ).toLowerCase();

            if(
                text.includes("generate image")
                ||
                text === "image"
            ){

                window.adaGenerateImage();

            }

            if(
                text.includes("generate video")
                ||
                text === "video"
            ){

                window.adaGenerateVideo();

            }

        }
    );


    /* --------------------------------------------------------
       Previous move + check styling
       -------------------------------------------------------- */

    const style =
        document.createElement("style");

    style.textContent = `

        .ada-previous-move {
            box-shadow:
                inset 0 0 0 4px
                rgba(255,215,80,.75) !important;
        }

        .ada-chess-check {
            background:
                rgba(220,40,40,.85) !important;

            box-shadow:
                inset 0 0 0 4px
                rgba(255,80,80,.95),
                0 0 18px
                rgba(255,50,50,.75) !important;
        }

        #adaChessActionBar button {
            border:1px solid
                rgba(255,255,255,.12);

            background:
                rgba(255,255,255,.06);

            color:inherit;

            border-radius:8px;

            padding:8px 13px;

            cursor:pointer;
        }

        #adaChessActionBar button:hover {
            background:
                rgba(255,255,255,.12);
        }

    `;

    document.head.appendChild(style);


})();


/* ADA FINAL CHESS CONTROLLER V2 */

/* ADA FINAL CHESS CONTROLLER V2 */
(function () {

    "use strict";

    window.adaChessLastMove = null;
    window.adaChessCheckSquare = null;

    const ADA_CHESS_FILES =
        ["a","b","c","d","e","f","g","h"];

    const ADA_CHESS_RANKS =
        ["8","7","6","5","4","3","2","1"];

    function adaChessGameId() {
        return (
            window.autonomousFinalChessId ||
            window.chessGameId ||
            ""
        );
    }

    function adaChessColor() {
        return (
            window.autonomousFinalChessColor ||
            window.chessColor ||
            "white"
        );
    }

    function adaChessDifficulty() {
        return (
            window.autonomousFinalChessDifficulty ||
            window.chessDifficulty ||
            "Medium"
        );
    }

    function adaChessSetDifficulty(value) {

        window.autonomousFinalChessDifficulty =
            value;

        window.chessDifficulty =
            value;
    }

    function adaChessStatus(text) {

        const el =
            document.getElementById(
                "chessStatus"
            );

        if (el) {
            el.textContent = text;
        }

        if (typeof window.adaStatus === "function") {
            try {
                window.adaStatus(text);
            } catch (_) {}
        }
    }

    async function adaChessJSON(
        url,
        options
    ) {

        const response =
            await fetch(url, {
                headers: {
                    "Content-Type":
                        "application/json"
                },
                ...(options || {})
            });

        let data;

        try {
            data = await response.json();
        } catch (_) {
            throw new Error(
                "Invalid server response."
            );
        }

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server request failed."
            );
        }

        if (
            data.ok === false &&
            data.error
        ) {
            throw new Error(data.error);
        }

        return data;
    }

    function adaParseFen(fen) {

        const board = [];

        const rows =
            fen.split(" ")[0]
               .split("/");

        for (
            let rank = 0;
            rank < 8;
            rank++
        ) {

            const row = [];
            const source = rows[rank];

            for (
                let i = 0;
                i < source.length;
                i++
            ) {

                const ch = source[i];

                if (
                    !isNaN(ch)
                ) {

                    const amount =
                        Number(ch);

                    for (
                        let j = 0;
                        j < amount;
                        j++
                    ) {
                        row.push(null);
                    }

                } else {
                    row.push(ch);
                }
            }

            board.push(row);
        }

        return board;
    }

    function adaPiece(piece) {

        const pieces = {
            K: "♔",
            Q: "♕",
            R: "♖",
            B: "♗",
            N: "♘",
            P: "♙",

            k: "♚",
            q: "♛",
            r: "♜",
            b: "♝",
            n: "♞",
            p: "♟"
        };

        return pieces[piece] || "";
    }

    function adaSquareName(
        row,
        col
    ) {

        return (
            ADA_CHESS_FILES[col] +
            ADA_CHESS_RANKS[row]
        );
    }

    function adaChessBoardElement() {
        return document.getElementById(
            "chessBoard"
        );
    }

    function adaRenderChess(
        fen,
        legalMoves
    ) {

        const boardElement =
            adaChessBoardElement();

        if (!boardElement)
            return;

        const board =
            adaParseFen(fen);

        boardElement.innerHTML = "";

        const playerColor =
            adaChessColor();

        const flipped =
            playerColor === "black";

        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualCol = 0;
                visualCol < 8;
                visualCol++
            ) {

                const row =
                    flipped
                        ? 7 - visualRow
                        : visualRow;

                const col =
                    flipped
                        ? 7 - visualCol
                        : visualCol;

                const square =
                    adaSquareName(
                        row,
                        col
                    );

                const cell =
                    document.createElement(
                        "div"
                    );

                cell.className =
                    "ada-chess-cell";

                cell.dataset.square =
                    square;

                if (
                    (row + col) % 2 === 0
                ) {
                    cell.classList.add(
                        "ada-chess-light"
                    );
                } else {
                    cell.classList.add(
                        "ada-chess-dark"
                    );
                }

                // Previous move highlight.
                if (
                    window.adaChessLastMove &&
                    (
                        square ===
                            window.adaChessLastMove.from ||
                        square ===
                            window.adaChessLastMove.to
                    )
                ) {

                    cell.classList.add(
                        "ada-previous-move"
                    );
                }

                // Actual checked king square.
                if (
                    window.adaChessCheckSquare &&
                    square ===
                        window.adaChessCheckSquare
                ) {

                    cell.classList.add(
                        "ada-chess-check"
                    );
                }

                const piece =
                    board[row][col];

                if (piece) {

                    const pieceEl =
                        document.createElement(
                            "span"
                        );

                    pieceEl.className =
                        "ada-chess-piece";

                    pieceEl.textContent =
                        adaPiece(piece);

                    cell.appendChild(
                        pieceEl
                    );
                }

                const legal =
                    Array.isArray(legalMoves)
                        ? legalMoves
                        : [];

                for (
                    const move of legal
                ) {

                    if (
                        move &&
                        move.slice(2,4) ===
                            square
                    ) {

                        cell.classList.add(
                            "ada-legal-target"
                        );

                        break;
                    }
                }

                cell.addEventListener(
                    "click",
                    function () {
                        adaChessClick(
                            square,
                            fen,
                            legalMoves
                        );
                    }
                );

                boardElement.appendChild(
                    cell
                );
            }
        }
    }

    let selectedSquare = null;

    async function adaChessClick(
        square,
        fen,
        legalMoves
    ) {

        if (!adaChessGameId())
            return;

        const board =
            adaParseFen(fen);

        const row =
            ADA_CHESS_RANKS.indexOf(
                square[1]
            );

        const col =
            ADA_CHESS_FILES.indexOf(
                square[0]
            );

        const piece =
            board[row][col];

        if (!selectedSquare) {

            if (!piece) {
                return;
            }

            const pieceIsWhite =
                piece === piece.toUpperCase();

            const playerIsWhite =
                adaChessColor() === "white";

            if (
                pieceIsWhite !==
                playerIsWhite
            ) {
                return;
            }

            selectedSquare =
                square;

            const cells =
                document.querySelectorAll(
                    ".ada-chess-cell"
                );

            cells.forEach(
                function (cell) {

                    if (
                        cell.dataset.square ===
                        square
                    ) {
                        cell.classList.add(
                            "ada-chess-selected"
                        );
                    }
                }
            );

            return;
        }

        const moveText =
            selectedSquare + square;

        const possible =
            Array.isArray(legalMoves)
                ? legalMoves
                : [];

        const matching =
            possible.find(
                function (move) {
                    return move === moveText ||
                           move.startsWith(
                               moveText
                           );
                }
            );

        if (!matching) {

            selectedSquare = null;

            try {
                await adaRefreshChess();
            } catch (_) {}

            return;
        }

        selectedSquare = null;

        await adaMakeChessMove(
            matching
        );
    }

    async function adaMakeChessMove(
        move
    ) {

        const oldFen =
            window.autonomousFinalFen;

        try {

            const data =
                await adaChessJSON(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",
                        body: JSON.stringify({
                            game_id:
                                adaChessGameId(),
                            move: move
                        })
                    }
                );

            window.adaChessLastMove = {
                from: move.slice(0,2),
                to: move.slice(2,4)
            };

            if (
                data.engine_move &&
                data.engine_move.length >= 4
            ) {

                window.adaChessLastMove = {
                    from:
                        data.engine_move.slice(0,2),
                    to:
                        data.engine_move.slice(2,4)
                };
            }

            window.autonomousFinalFen =
                data.fen;

            if (
                data.game_over
            ) {

                window.adaChessCheckSquare =
                    null;

                adaRenderChess(
                    data.fen,
                    []
                );

                adaChessStatus(
                    "Game over: " +
                    (
                        data.result ||
                        "finished"
                    )
                );

                return;
            }

            await adaRefreshChess();

        } catch (error) {

            window.autonomousFinalFen =
                oldFen;

            adaChessStatus(
                "Move error: " +
                error.message
            );
        }
    }

    async function adaRefreshChess() {

        const gameId =
            adaChessGameId();

        if (!gameId)
            return;

        const state =
            await adaChessJSON(
                "/api/autonomous/chess/state?game_id=" +
                encodeURIComponent(gameId)
            );

        window.autonomousFinalFen =
            state.fen;

        adaChessSetDifficulty(
            state.difficulty ||
            adaChessDifficulty()
        );

        window.adaChessCheckSquare =
            state.check
                ? state.check_square
                : null;

        adaRenderChess(
            state.fen,
            state.legal_moves || []
        );

        if (state.check) {

            adaChessStatus(
                "♔ CHECK — the king is under attack."
            );

        } else if (state.game_over) {

            adaChessStatus(
                "Game over: " +
                (
                    state.result ||
                    "finished"
                )
            );
        }
    }

    window.adaChessRestart =
        async function () {

            try {

                const data =
                    await adaChessJSON(
                        "/api/autonomous/chess/restart",
                        {
                            method: "POST",
                            body: JSON.stringify({
                                color:
                                    adaChessColor(),
                                difficulty:
                                    adaChessDifficulty()
                            })
                        }
                    );

                window.autonomousFinalChessId =
                    data.game_id;

                window.autonomousFinalFen =
                    data.fen;

                window.autonomousFinalChessColor =
                    data.color;

                adaChessSetDifficulty(
                    data.difficulty
                );

                window.adaChessLastMove =
                    null;

                window.adaChessCheckSquare =
                    null;

                await adaRefreshChess();

                adaChessStatus(
                    "New chess game started."
                );

            } catch (error) {

                adaChessStatus(
                    "Restart error: " +
                    error.message
                );
            }
        };

    window.adaChessDraw =
        async function () {

            try {

                const data =
                    await adaChessJSON(
                        "/api/autonomous/chess/draw",
                        {
                            method: "POST",
                            body: JSON.stringify({
                                game_id:
                                    adaChessGameId()
                            })
                        }
                    );

                window.adaChessCheckSquare =
                    null;

                adaRenderChess(
                    data.fen,
                    []
                );

                adaChessStatus(
                    "Game drawn."
                );

            } catch (error) {

                adaChessStatus(
                    "Draw error: " +
                    error.message
                );
            }
        };

    window.adaChessResign =
        async function () {

            try {

                const data =
                    await adaChessJSON(
                        "/api/autonomous/chess/resign",
                        {
                            method: "POST",
                            body: JSON.stringify({
                                game_id:
                                    adaChessGameId()
                            })
                        }
                    );

                window.adaChessCheckSquare =
                    null;

                adaRenderChess(
                    data.fen,
                    []
                );

                adaChessStatus(
                    "You resigned. Result: " +
                    data.result
                );

            } catch (error) {

                adaChessStatus(
                    "Resign error: " +
                    error.message
                );
            }
        };

    window.adaChessChangeComputer =
        async function () {

            const levels = [
                "Easy",
                "Medium",
                "Hard",
                "Expert",
                "Master"
            ];

            const current =
                adaChessDifficulty();

            const currentIndex =
                levels.indexOf(current);

            const next =
                levels[
                    (
                        currentIndex < 0
                            ? 0
                            : currentIndex + 1
                    ) % levels.length
                ];

            try {

                const data =
                    await adaChessJSON(
                        "/api/autonomous/chess/settings",
                        {
                            method: "POST",
                            body: JSON.stringify({
                                game_id:
                                    adaChessGameId(),
                                difficulty:
                                    next
                            })
                        }
                    );

                adaChessSetDifficulty(
                    data.difficulty
                );

                await adaRefreshChess();

                adaChessStatus(
                    "Computer changed to " +
                    data.difficulty +
                    "."
                );

            } catch (error) {

                adaChessStatus(
                    "Computer settings error: " +
                    error.message
                );
            }
        };

    /*
     * Override the existing chess start function
     * while preserving the existing modal/UI.
     */
    window.startChess =
        async function () {

            try {

                const colorElement =
                    document.getElementById(
                        "chessColor"
                    );

                const difficultyElement =
                    document.getElementById(
                        "chessDifficulty"
                    );

                const color =
                    colorElement
                        ? colorElement.value
                        : "white";

                const difficulty =
                    difficultyElement
                        ? difficultyElement.value
                        : "Medium";

                const data =
                    await adaChessJSON(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",
                            body: JSON.stringify({
                                color: color,
                                difficulty:
                                    difficulty
                            })
                        }
                    );

                window.autonomousFinalChessId =
                    data.game_id;

                window.autonomousFinalFen =
                    data.fen;

                window.autonomousFinalChessColor =
                    data.color;

                adaChessSetDifficulty(
                    data.difficulty
                );

                window.adaChessLastMove =
                    null;

                window.adaChessCheckSquare =
                    null;

                await adaRefreshChess();

                const setup =
                    document.getElementById(
                        "chessSetup"
                    );

                const game =
                    document.getElementById(
                        "chessGame"
                    );

                if (setup)
                    setup.style.display =
                        "none";

                if (game)
                    game.style.display =
                        "block";

            } catch (error) {

                adaChessStatus(
                    "Chess start error: " +
                    error.message
                );
            }
        };

    /*
     * Keep chess refreshed when the modal becomes visible.
     */
    document.addEventListener(
        "click",
        function (event) {

            const target =
                event.target;

            if (
                target &&
                (
                    target.id ===
                        "chessModal" ||
                    target.closest &&
                    target.closest(
                        "#chessModal"
                    )
                )
            ) {

                setTimeout(
                    function () {
                        adaRefreshChess()
                            .catch(
                                function () {}
                            );
                    },
                    150
                );
            }
        }
    );

    /*
     * Chess CSS.
     */
    const style =
        document.createElement(
            "style"
        );

    style.textContent = `
        .ada-chess-cell {
            position:relative;
            display:flex;
            align-items:center;
            justify-content:center;
            user-select:none;
            cursor:pointer;
            transition:
                box-shadow .12s ease,
                transform .12s ease;
        }

        .ada-chess-piece {
            position:relative;
            z-index:3;
            font-size:clamp(
                28px,
                5vw,
                56px
            );
            line-height:1;
            pointer-events:none;
        }

        .ada-chess-selected {
            box-shadow:
                inset 0 0 0 4px
                rgba(80,170,255,.95) !important;
        }

        .ada-legal-target::after {
            content:"";
            position:absolute;
            width:22%;
            height:22%;
            border-radius:50%;
            background:
                rgba(80,180,100,.8);
            z-index:2;
            pointer-events:none;
        }

        .ada-previous-move {
            box-shadow:
                inset 0 0 0 4px
                rgba(255,215,70,.95) !important;
        }

        .ada-chess-check {
            background:
                rgba(210,35,35,.88) !important;
            box-shadow:
                inset 0 0 0 4px
                rgba(255,75,75,1),
                0 0 20px
                rgba(255,40,40,.9) !important;
            animation:
                adaCheckPulse .65s ease-in-out
                infinite alternate;
        }

        @keyframes adaCheckPulse {
            from {
                filter:brightness(.9);
            }
            to {
                filter:brightness(1.25);
            }
        }

        #adaChessActionBar button {
            border:1px solid
                rgba(255,255,255,.14);
            background:
                rgba(255,255,255,.07);
            color:inherit;
            border-radius:9px;
            padding:8px 13px;
            cursor:pointer;
            transition:
                background .15s ease,
                transform .1s ease;
        }

        #adaChessActionBar button:hover {
            background:
                rgba(255,255,255,.14);
            transform:translateY(-1px);
        }
    `;

    document.head.appendChild(style);

    /*
     * Image generation remains cloud Gemini-backed.
     */
    window.adaGenerateImage =
        async function () {

            const prompt =
                window.prompt(
                    "Describe the image to generate:"
                );

            if (
                !prompt ||
                !prompt.trim()
            ) {
                return;
            }

            try {

                adaChessStatus(
                    "Generating image with Gemini..."
                );

                const response =
                    await fetch(
                        "/api/autonomous/image",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json"
                            },
                            body:
                                JSON.stringify({
                                    prompt:
                                        prompt.trim()
                                })
                        }
                    );

                const data =
                    await response.json();

                if (
                    !response.ok ||
                    data.error
                ) {
                    throw new Error(
                        data.error ||
                        "Image generation failed."
                    );
                }

                if (data.url) {

                    window.open(
                        data.url,
                        "_blank"
                    );

                    adaChessStatus(
                        "Gemini image generated."
                    );

                } else {

                    adaChessStatus(
                        "Gemini finished, but returned no image URL."
                    );
                }

            } catch (error) {

                adaChessStatus(
                    "Image error: " +
                    error.message
                );
            }
        };

    /*
     * Video generation through Gemini cloud API.
     * The completed video is downloaded by the backend
     * into /static/generated.
     */
    window.adaGenerateVideo =
        async function () {

            const prompt =
                window.prompt(
                    "Describe the video to generate:"
                );

            if (
                !prompt ||
                !prompt.trim()
            ) {
                return;
            }

            try {

                adaChessStatus(
                    "Sending video request to Gemini..."
                );

                const response =
                    await fetch(
                        "/api/autonomous/video",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json"
                            },
                            body:
                                JSON.stringify({
                                    prompt:
                                        prompt.trim()
                                })
                        }
                    );

                const data =
                    await response.json();

                if (
                    !response.ok ||
                    data.error
                ) {
                    throw new Error(
                        data.error ||
                        "Video request failed."
                    );
                }

                const operationId =
                    data.operation_id ||
                    data.name ||
                    data.id;

                if (!operationId) {
                    throw new Error(
                        "Gemini returned no operation ID."
                    );
                }

                let finished = false;

                for (
                    let i = 0;
                    i < 120;
                    i++
                ) {

                    await new Promise(
                        function(resolve) {
                            setTimeout(
                                resolve,
                                5000
                            );
                        }
                    );

                    const statusResponse =
                        await fetch(
                            "/api/autonomous/video/local-status/" +
                            encodeURIComponent(
                                operationId
                            )
                        );

                    const status =
                        await statusResponse.json();

                    if (
                        status.status ===
                        "completed"
                    ) {

                        finished = true;

                        if (status.url) {

                            const videoWindow =
                                window.open(
                                    "",
                                    "_blank"
                                );

                            if (videoWindow) {

                                videoWindow.document.write(
                                    "<!doctype html>" +
                                    "<html><head>" +
                                    "<title>ADA Gemini Video</title>" +
                                    "</head><body " +
                                    "style='margin:0;" +
                                    "background:#111;" +
                                    "display:flex;" +
                                    "align-items:center;" +
                                    "justify-content:center;'>" +
                                    "<video controls autoplay " +
                                    "style='max-width:96vw;" +
                                    "max-height:96vh;'>" +
                                    "<source src='" +
                                    status.url +
                                    "' type='video/mp4'>" +
                                    "</video>" +
                                    "</body></html>"
                                );

                                videoWindow.document.close();

                            } else {

                                window.location.href =
                                    status.url;
                            }

                            adaChessStatus(
                                "Gemini video generated successfully."
                            );
                        }

                        break;
                    }

                    if (
                        status.status ===
                        "error"
                    ) {

                        throw new Error(
                            status.error ||
                            "Gemini video generation failed."
                        );
                    }

                    adaChessStatus(
                        "Generating video with Gemini... " +
                        Math.round(
                            ((i + 1) / 120) * 100
                        ) +
                        "%"
                    );
                }

                if (!finished) {

                    adaChessStatus(
                        "Gemini video is still processing. You can keep using ADA."
                    );
                }

            } catch (error) {

                adaChessStatus(
                    "Video error: " +
                    error.message
                );
            }
        };

})();


/* ============================================================
   ADA CLEAN MEDIA DISABLE
   Image/video generation intentionally disabled for now.
   ============================================================ */
(function () {
    "use strict";

    function removeMediaButtons() {
        const selectors = [
            'button[onclick*="autonomousFinalImage"]',
            'button[onclick*="autonomousFinalVideo"]',
            'button[onclick*="adaGenerateImage"]',
            'button[onclick*="adaGenerateVideo"]'
        ];

        selectors.forEach(function (selector) {
            document.querySelectorAll(selector).forEach(function (node) {
                node.remove();
            });
        });

        document.querySelectorAll(
            "#autonomousFinalFeatureBar, .autonomous-final-feature-bar"
        ).forEach(function (bar) {
            const text = (bar.textContent || "").toLowerCase();

            if (
                text.includes("image") ||
                text.includes("video") ||
                text.includes("🎨") ||
                text.includes("🎬")
            ) {
                bar.remove();
            }
        });
    }

    window.adaGenerateImage = function () {
        return Promise.reject(
            new Error("Image generation is temporarily disabled.")
        );
    };

    window.adaGenerateVideo = function () {
        return Promise.reject(
            new Error("Video generation is temporarily disabled.")
        );
    };

    window.autonomousFinalImage = function () {
        alert("Image generation is temporarily disabled for this version.");
    };

    window.autonomousFinalVideo = function () {
        alert("Video generation is temporarily disabled for this version.");
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", removeMediaButtons);
    } else {
        removeMediaButtons();
    }

    window.addEventListener("load", removeMediaButtons);

    const observer = new MutationObserver(function () {
        removeMediaButtons();
    });

    observer.observe(document.documentElement, {
        childList: true,
        subtree: true
    });
})();


/* ADA_CLEAN_CHESS_START */
(function () {
    "use strict";

    const START_FEN =
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR";

    const PIECES = {
        "K": "♔",
        "Q": "♕",
        "R": "♖",
        "B": "♗",
        "N": "♘",
        "P": "♙",
        "k": "♚",
        "q": "♛",
        "r": "♜",
        "b": "♝",
        "n": "♞",
        "p": "♟"
    };

    let cleanGameId = null;
    let cleanColor = "white";
    let cleanFen = START_FEN;
    let cleanSelected = null;
    let cleanLegal = [];

    function el(id) {
        return document.getElementById(id);
    }

    function parseFen(fen) {
        const board = [];
        const rows = String(fen || START_FEN).split("/").slice(0, 8);

        for (const row of rows) {
            const out = [];

            for (const ch of row) {
                if (/[1-8]/.test(ch)) {
                    for (let i = 0; i < Number(ch); i++) {
                        out.push("");
                    }
                } else {
                    out.push(ch);
                }
            }

            while (out.length < 8) {
                out.push("");
            }

            board.push(out.slice(0, 8));
        }

        while (board.length < 8) {
            board.push(["","","","","","","",""]);
        }

        return board;
    }

    function squareName(row, col) {
        return String.fromCharCode(97 + col) + String(8 - row);
    }

    function showGame() {
        const setup = el("chessSetup");
        const game = el("chessGame");

        if (setup) {
            setup.classList.add("hidden");
            setup.style.display = "none";
        }

        if (game) {
            game.classList.remove("hidden");
            game.style.display = "block";
            game.style.visibility = "visible";
            game.style.opacity = "1";
        }
    }

    function showStatus(text) {
        const status = el("chessStatus");
        if (status) {
            status.textContent = text;
        }
    }

    function drawBoard() {
        const target = el("chessBoard");
        if (!target) {
            return;
        }

        target.innerHTML = "";
        target.style.display = "grid";
        target.style.gridTemplateColumns = "repeat(8, minmax(0, 1fr))";
        target.style.gridTemplateRows = "repeat(8, minmax(0, 1fr))";
        target.style.width = "min(640px, 82vw)";
        target.style.height = "min(640px, 82vw)";
        target.style.minWidth = "320px";
        target.style.minHeight = "320px";
        target.style.margin = "20px auto";
        target.style.visibility = "visible";
        target.style.opacity = "1";

        const board = parseFen(cleanFen);
        const reverse = cleanColor === "black";

        for (let vr = 0; vr < 8; vr++) {
            for (let vc = 0; vc < 8; vc++) {

                const r = reverse ? 7 - vr : vr;
                const c = reverse ? 7 - vc : vc;

                const square = document.createElement("button");

                square.type = "button";
                square.className =
                    "chess-square " +
                    (((vr + vc) % 2 === 0)
                        ? "chess-light"
                        : "chess-dark");

                square.dataset.square = squareName(r, c);

                if (
                    cleanSelected &&
                    cleanSelected.r === r &&
                    cleanSelected.c === c
                ) {
                    square.classList.add("chess-selected");
                }

                if (
                    cleanLegal.includes(
                        squareName(r, c)
                    )
                ) {
                    square.classList.add("chess-legal");
                }

                const piece = board[r][c];

                if (piece) {
                    square.textContent =
                        PIECES[piece] || piece;
                }

                square.addEventListener(
                    "click",
                    function () {
                        clickSquare(r, c, board);
                    }
                );

                target.appendChild(square);
            }
        }
    }

    async function getLegal(square) {
        if (!cleanGameId) {
            return [];
        }

        try {
            const response = await fetch(
                "/api/autonomous/chess/legal-moves?game_id=" +
                encodeURIComponent(cleanGameId) +
                "&square=" +
                encodeURIComponent(square),
                {
                    credentials: "same-origin"
                }
            );

            if (!response.ok) {
                return [];
            }

            const data = await response.json();

            return Array.isArray(data.legal_moves)
                ? data.legal_moves
                : [];

        } catch (_) {
            return [];
        }
    }

    async function clickSquare(r, c, board) {

        const square = squareName(r, c);

        if (!cleanSelected) {

            const piece = board[r][c];

            if (!piece) {
                return;
            }

            const isWhite =
                piece === piece.toUpperCase();

            if (
                cleanColor === "white" &&
                !isWhite
            ) {
                return;
            }

            if (
                cleanColor === "black" &&
                isWhite
            ) {
                return;
            }

            cleanSelected = {
                r: r,
                c: c
            };

            cleanLegal =
                await getLegal(square);

            drawBoard();
            return;
        }

        const from =
            squareName(
                cleanSelected.r,
                cleanSelected.c
            );

        const to = square;

        if (!cleanLegal.includes(to)) {
            cleanSelected = null;
            cleanLegal = [];
            drawBoard();
            return;
        }

        showStatus("Computer is thinking...");

        try {

            const response = await fetch(
                "/api/autonomous/chess/move",
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        game_id: cleanGameId,
                        move: from + to
                    })
                }
            );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "Chess move failed."
                );
            }

            if (data.fen) {
                cleanFen = data.fen;
            }

            cleanSelected = null;
            cleanLegal = [];

            drawBoard();

            if (data.game_over) {
                showStatus(
                    data.result ||
                    "Game over"
                );
            } else {
                showStatus(
                    data.engine_move
                        ? "Computer played " +
                          data.engine_move +
                          " — your move"
                        : "Your move"
                );
            }

        } catch (error) {

            cleanSelected = null;
            cleanLegal = [];

            drawBoard();

            showStatus(
                error.message ||
                "Chess move failed."
            );
        }
    }

    /*
     * This deliberately renders the board BEFORE the API request.
     * Therefore a backend/API problem can no longer make the chess
     * board itself disappear.
     */
    window.startChess = async function () {

        const colorNode = el("chessColor");
        const difficultyNode = el("chessDifficulty");

        cleanColor =
            colorNode
                ? colorNode.value
                : "white";

        const difficulty =
            difficultyNode
                ? difficultyNode.value
                : "Medium";

        cleanFen = START_FEN;
        cleanSelected = null;
        cleanLegal = [];

        showGame();
        drawBoard();
        showStatus("Starting chess...");

        try {

            const response = await fetch(
                "/api/autonomous/chess/start",
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        color: cleanColor,
                        difficulty: difficulty
                    })
                }
            );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "Chess server failed to start."
                );
            }

            cleanGameId =
                data.game_id || null;

            if (data.fen) {
                cleanFen = data.fen;
            }

            /*
             * If playing black, the backend normally makes
             * the first computer move.
             */
            drawBoard();

            if (data.game_over) {
                showStatus(
                    data.result ||
                    "Game over"
                );
            } else if (cleanColor === "black") {
                showStatus(
                    "Computer has started — your move"
                );
            } else {
                showStatus("Your move");
            }

        } catch (error) {

            /*
             * Board remains visible even when the server fails.
             * This makes the failure obvious instead of producing
             * an empty chess modal.
             */
            cleanGameId = null;
            cleanFen = START_FEN;

            drawBoard();

            showStatus(
                "Chess server error: " +
                (error.message ||
                 "unknown error")
            );
        }
    };

    window.openChess = function () {

        const modal = el("chessModal");

        if (modal) {
            modal.classList.remove("hidden");
            modal.style.display = "flex";
            modal.style.visibility = "visible";
            modal.style.opacity = "1";
        }

        const setup = el("chessSetup");
        const game = el("chessGame");

        if (setup) {
            setup.classList.remove("hidden");
            setup.style.display = "";
        }

        if (game) {
            game.classList.add("hidden");
            game.style.display = "none";
        }
    };

    window.closeChess = function () {
        const modal = el("chessModal");

        if (modal) {
            modal.classList.add("hidden");
        }
    };

    window.addEventListener("load", function () {

        const board = el("chessBoard");

        if (board) {
            board.style.boxSizing = "border-box";
        }

    });

})();
 /* ADA_CLEAN_CHESS_END */


/* ADA_CHESS_VISUAL_UPGRADE_START */
(function () {
    "use strict";

    /*
     * =========================================================
     * ADA CHESS VISUAL UPGRADE
     *
     * Yellow:
     *   ONLY the previous move's FROM + TO squares.
     *
     * Legal moves:
     *   Keep the separate legal-move indicator.
     *
     * Animation:
     *   The moved piece smoothly animates from its old square
     *   to its new square.
     * =========================================================
     */

    let adaPreviousMove = null;
    let adaAnimationLock = false;

    function adaChessBoard() {
        return document.getElementById("chessBoard");
    }

    function adaSquareName(row, col) {
        return String.fromCharCode(97 + col) +
               String(8 - row);
    }

    function adaFindSquare(name) {
        const board = adaChessBoard();

        if (!board) return null;

        return board.querySelector(
            '[data-square="' + name + '"]'
        );
    }

    function adaClearPreviousMove() {
        const board = adaChessBoard();

        if (!board) return;

        board.querySelectorAll(
            ".ada-previous-move"
        ).forEach(function (node) {
            node.classList.remove(
                "ada-previous-move"
            );
        });
    }

    function adaShowPreviousMove(from, to) {

        adaClearPreviousMove();

        if (!from || !to) {
            return;
        }

        adaPreviousMove = {
            from: from,
            to: to
        };

        const fromSquare =
            adaFindSquare(from);

        const toSquare =
            adaFindSquare(to);

        if (fromSquare) {
            fromSquare.classList.add(
                "ada-previous-move"
            );
        }

        if (toSquare) {
            toSquare.classList.add(
                "ada-previous-move"
            );
        }
    }

    /*
     * Try to obtain the last move from the server response.
     * Supports several formats so the visual layer doesn't
     * depend on one exact backend response shape.
     */
    function adaExtractMove(data) {

        if (!data) return null;

        let move =
            data.last_move ||
            data.player_move ||
            data.move ||
            null;

        if (
            move &&
            typeof move === "object"
        ) {
            move =
                move.uci ||
                move.move ||
                move.san ||
                null;
        }

        if (
            typeof move !== "string"
        ) {
            return null;
        }

        /*
         * UCI:
         * e2e4
         * g1f3
         * etc.
         */
        if (
            /^[a-h][1-8][a-h][1-8]$/i.test(move)
        ) {
            return {
                from: move.slice(0, 2),
                to: move.slice(2, 4)
            };
        }

        return null;
    }

    /*
     * Capture the current board piece positions before
     * replacing the board.
     */
    function adaCapturePieces() {

        const board = adaChessBoard();

        if (!board) return {};

        const result = {};

        board.querySelectorAll(
            "[data-square]"
        ).forEach(function (square) {

            const piece =
                square.textContent.trim();

            if (piece) {
                result[
                    square.dataset.square
                ] = piece;
            }
        });

        return result;
    }

    /*
     * Animate the visual piece.
     *
     * We don't modify the actual chess state.
     * This is purely visual.
     */
    function adaAnimateMove(from, to, callback) {

        const board = adaChessBoard();

        if (!board || !from || !to) {
            if (callback) callback();
            return;
        }

        const fromSquare =
            adaFindSquare(from);

        const toSquare =
            adaFindSquare(to);

        if (!fromSquare || !toSquare) {
            if (callback) callback();
            return;
        }

        const piece =
            fromSquare.textContent.trim();

        if (!piece) {
            if (callback) callback();
            return;
        }

        const fromRect =
            fromSquare.getBoundingClientRect();

        const toRect =
            toSquare.getBoundingClientRect();

        const boardRect =
            board.getBoundingClientRect();

        const animated =
            document.createElement("div");

        animated.className =
            "ada-chess-animated-piece";

        animated.textContent = piece;

        animated.style.left =
            (fromRect.left - boardRect.left) +
            "px";

        animated.style.top =
            (fromRect.top - boardRect.top) +
            "px";

        animated.style.width =
            fromRect.width + "px";

        animated.style.height =
            fromRect.height + "px";

        animated.style.fontSize =
            getComputedStyle(fromSquare)
                .fontSize;

        board.appendChild(animated);

        fromSquare.classList.add(
            "ada-piece-hidden"
        );

        toSquare.classList.add(
            "ada-piece-hidden"
        );

        requestAnimationFrame(function () {

            animated.classList.add(
                "ada-piece-moving"
            );

            animated.style.transform =
                "translate(" +
                (toRect.left - fromRect.left) +
                "px, " +
                (toRect.top - fromRect.top) +
                "px)";

        });

        window.setTimeout(function () {

            animated.remove();

            fromSquare.classList.remove(
                "ada-piece-hidden"
            );

            toSquare.classList.remove(
                "ada-piece-hidden"
            );

            if (callback) callback();

        }, 280);
    }

    /*
     * Patch board rendering without destroying the existing
     * ADA chess functionality.
     */
    function adaEnhanceBoard() {

        const board = adaChessBoard();

        if (!board) return;

        /*
         * Existing legal indicators stay untouched.
         *
         * We only add our previous-move class.
         */
        adaClearPreviousMove();

        if (adaPreviousMove) {

            const from =
                adaFindSquare(
                    adaPreviousMove.from
                );

            const to =
                adaFindSquare(
                    adaPreviousMove.to
                );

            if (from) {
                from.classList.add(
                    "ada-previous-move"
                );
            }

            if (to) {
                to.classList.add(
                    "ada-previous-move"
                );
            }
        }
    }

    /*
     * Watch the existing chess board.
     * This lets the upgrade work with the existing ADA
     * renderer instead of replacing the whole chess system.
     */
    function adaInstallChessObserver() {

        const board = adaChessBoard();

        if (!board || board.dataset.adaVisualObserver) {
            return;
        }

        board.dataset.adaVisualObserver = "1";

        const observer =
            new MutationObserver(function () {

                window.requestAnimationFrame(
                    adaEnhanceBoard
                );

            });

        observer.observe(board, {
            childList: true,
            subtree: true
        });
    }

    /*
     * Observe the page because the chess modal can be created
     * dynamically.
     */
    const pageObserver =
        new MutationObserver(function () {

            adaInstallChessObserver();

        });

    function boot() {

        adaInstallChessObserver();

        pageObserver.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );
    }

    /*
     * Expose helpers so the existing chess controller can
     * report the move after a successful server response.
     */
    window.adaChessPreviousMove =
        function (from, to) {

            adaShowPreviousMove(
                from,
                to
            );

            adaEnhanceBoard();
        };

    window.adaChessAnimateMove =
        function (from, to, callback) {

            adaAnimateMove(
                from,
                to,
                callback
            );
        };

    window.adaChessEnhanceBoard =
        function () {

            adaEnhanceBoard();

        };

    /*
     * If the existing controller reports an entire UCI move:
     */
    window.adaChessReportMove =
        function (uciMove) {

            if (
                typeof uciMove !== "string" ||
                !/^[a-h][1-8][a-h][1-8]$/i.test(
                    uciMove
                )
            ) {
                return;
            }

            const from =
                uciMove.slice(0, 2);

            const to =
                uciMove.slice(2, 4);

            adaShowPreviousMove(
                from,
                to
            );

            adaEnhanceBoard();
        };

    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            boot
        );
    } else {
        boot();
    }

})();
 /* ADA_CHESS_VISUAL_UPGRADE_END */



// ===== ADA ACTION PASSWORD UI V1 =====

(() => {

    const originalFetch =
        window.fetch.bind(window);

    let setupInProgress = false;


    async function securityStatus() {

        try {

            const response = await originalFetch(
                "/api/security/password/status",
                {
                    credentials: "include"
                }
            );

            if (!response.ok) {
                return null;
            }

            return await response.json();

        } catch (_) {

            return null;
        }
    }


    async function setupPassword(force = false) {

        if (setupInProgress) {
            return false;
        }

        setupInProgress = true;

        try {

            const status =
                await securityStatus();

            if (
                !force &&
                (
                    !status ||
                    status.configured
                )
            ) {
                return true;
            }

            const first = window.prompt(
                "Create your Autonomous AI action password.\n\n" +
                "This password will be required before AI can make " +
                "changes to your computer.\n\n" +
                "Minimum 6 characters:"
            );

            if (first === null) {
                return false;
            }

            if (first.length < 6) {

                alert(
                    "Password must be at least 6 characters."
                );

                return false;
            }

            const second = window.prompt(
                "Confirm your new action password:"
            );

            if (second !== first) {

                alert(
                    "Passwords do not match."
                );

                return false;
            }

            const response = await originalFetch(
                "/api/security/password/setup",
                {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        password: first
                    })
                }
            );

            if (!response.ok) {

                const data =
                    await response.json().catch(
                        () => ({})
                    );

                if (response.status === 409) {
                    return true;
                }

                alert(
                    data.detail ||
                    "Could not create password."
                );

                return false;
            }

            alert(
                "Action password created successfully."
            );

            return true;

        } finally {

            setupInProgress = false;
        }
    }


    async function changeActionPassword() {

        const oldPassword = window.prompt(
            "Enter your current action password:"
        );

        if (oldPassword === null) {
            return;
        }

        const newPassword = window.prompt(
            "Enter your new action password " +
            "(minimum 6 characters):"
        );

        if (newPassword === null) {
            return;
        }

        if (newPassword.length < 6) {

            alert(
                "Password must be at least 6 characters."
            );

            return;
        }

        const confirmPassword = window.prompt(
            "Confirm your new password:"
        );

        if (newPassword !== confirmPassword) {

            alert(
                "Passwords do not match."
            );

            return;
        }

        const response = await originalFetch(
            "/api/security/password/change",
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    old_password:
                        oldPassword,
                    new_password:
                        newPassword
                })
            }
        );

        const data =
            await response.json().catch(
                () => ({})
            );

        if (!response.ok) {

            alert(
                data.detail ||
                "Password could not be changed."
            );

            return;
        }

        alert(
            "Action password changed successfully."
        );
    }


    function addSecuritySetting() {

        const list =
            document.querySelector(
                "#settingsModal .settings-list"
            );

        if (
            !list ||
            document.getElementById(
                "adaSecuritySetting"
            )
        ) {
            return;
        }

        const row =
            document.createElement("div");

        row.id =
            "adaSecuritySetting";

        row.className =
            "setting-row";

        row.innerHTML = `
            <div>
                <strong>
                    Computer action password
                </strong>

                <span>
                    Required before Autonomous AI
                    changes or controls this computer
                </span>
            </div>

            <button
                class="setting-action"
                id="adaChangePasswordButton"
                type="button"
            >
                Change password
            </button>
        `;

        list.appendChild(row);

        document
            .getElementById(
                "adaChangePasswordButton"
            )
            .addEventListener(
                "click",
                changeActionPassword
            );
    }


    const originalOpenSettings =
        window.openSettings;

    if (
        typeof originalOpenSettings ===
        "function"
    ) {

        window.openSettings =
            function (...args) {

                addSecuritySetting();

                return originalOpenSettings.apply(
                    this,
                    args
                );
            };
    }


    window.fetch =
        async function (
            input,
            init = {}
        ) {

            let response =
                await originalFetch(
                    input,
                    init
                );

            const url =
                typeof input === "string"
                    ? input
                    : (
                        input &&
                        input.url
                    ) || "";

            if (
                !url.includes(
                    "/api/chat"
                )
            ) {
                return response;
            }

            if (
                response.status !== 403 &&
                response.status !== 428
            ) {
                return response;
            }

            let data = {};

            try {

                data =
                    await response
                        .clone()
                        .json();

            } catch (_) {}

            if (
                data.detail ===
                "PASSWORD_SETUP_REQUIRED"
            ) {

                const created =
                    await setupPassword(true);

                if (!created) {
                    return response;
                }
            }

            else if (
                data.detail !==
                "ACTION_PASSWORD_REQUIRED"
            ) {

                return response;
            }


            const password =
                window.prompt(
                    "Autonomous AI wants to perform " +
                    "a computer action.\n\n" +
                    "Enter your action password to allow it:"
                );

            if (password === null) {

                return response;
            }


            const headers =
                new Headers(
                    init.headers || {}
                );

            headers.set(
                "X-ADA-Action-Password",
                password
            );


            response =
                await originalFetch(
                    input,
                    {
                        ...init,
                        headers
                    }
                );

            return response;
        };


    async function startupSecurityCheck() {

        addSecuritySetting();

        const status =
            await securityStatus();

        if (
            status &&
            !status.configured
        ) {

            setTimeout(
                () => setupPassword(false),
                500
            );
        }
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            startupSecurityCheck
        );

    } else {

        startupSecurityCheck();
    }


    window.adaChangeActionPassword =
        changeActionPassword;

})();

// ===== END ADA ACTION PASSWORD UI V1 =====

/* ============================================================
   ADA CHESS FINAL PERFORMANCE + CONTROLS FIX
   ============================================================ */
(function () {
    "use strict";

    let adaChessBusy = false;

    function gameId() {
        return (
            window.autonomousFinalChessId ||
            window.chessGameId ||
            null
        );
    }

    function status(text) {
        const el = document.getElementById("chessStatus");
        if (el) el.textContent = text;
    }

    async function api(url, options = {}) {
        const response = await fetch(url, {
            credentials: "same-origin",
            cache: "no-store",
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        let data = {};
        try {
            data = await response.json();
        } catch (_) {}

        if (!response.ok || data.ok === false) {
            throw new Error(
                data.detail ||
                data.error ||
                "Chess request failed."
            );
        }

        return data;
    }

    /*
     * Fast board refresh.
     * Never wait for a visual animation before sending
     * the actual chess move to the server.
     */
    async function refresh() {
        const id = gameId();
        if (!id) return;

        const data = await api(
            "/api/autonomous/chess/state?game_id=" +
            encodeURIComponent(id)
        );

        window.autonomousFinalFen = data.fen;
        window.autonomousFinalChessId = data.game_id;
        window.autonomousFinalChessColor = data.color;
        window.adaChessLastMove =
            data.moves && data.moves.length
                ? data.moves[data.moves.length - 1]
                : null;

        window.autonomousFinalSelected = null;
        window.autonomousFinalLegal = [];

        if (typeof window.adaChessSetDifficulty === "function") {
            window.adaChessSetDifficulty(
                data.difficulty || "Medium"
            );
        }

        window.adaChessCheckSquare =
            data.check ? data.check_square : null;

        if (typeof window.adaRenderChess === "function") {
            window.adaRenderChess(
                data.fen,
                data.legal_moves || []
            );
        } else if (typeof window.drawBoard === "function") {
            await window.drawBoard();
        }

        if (data.game_over) {
            status(
                "Game over: " +
                (data.result || "finished")
            );
        } else if (data.check) {
            status("CHECK — the king is under attack.");
        } else {
            status("Your move");
        }

        return data;
    }

    /*
     * RESTART
     */
    window.adaChessRestart = async function () {
        if (adaChessBusy) return;

        adaChessBusy = true;
        status("Starting new game...");

        try {
            const color =
                typeof window.adaChessColor === "function"
                    ? window.adaChessColor()
                    : (
                        document.getElementById("chessColor")?.value ||
                        "white"
                    );

            const difficulty =
                typeof window.adaChessDifficulty === "function"
                    ? window.adaChessDifficulty()
                    : (
                        document.getElementById("chessDifficulty")?.value ||
                        "Medium"
                    );

            const data = await api(
                "/api/autonomous/chess/restart",
                {
                    method: "POST",
                    body: JSON.stringify({
                        color,
                        difficulty
                    })
                }
            );

            window.autonomousFinalChessId = data.game_id;
            window.autonomousFinalFen = data.fen;
            window.autonomousFinalChessColor = data.color;
            window.adaChessLastMove = null;
            window.adaPreviousChessMove = null;
            window.autonomousFinalSelected = null;
            window.autonomousFinalLegal = [];
            window.autonomousFinalChessOver = false;

            if (typeof window.adaChessSetDifficulty === "function") {
                window.adaChessSetDifficulty(
                    data.difficulty || difficulty
                );
            }

            await refresh();
            status("New chess game started.");
        } catch (error) {
            status("Restart error: " + error.message);
        } finally {
            adaChessBusy = false;
        }
    };

    /*
     * DRAW
     */
    window.adaChessDraw = async function () {
        if (adaChessBusy) return;

        const id = gameId();

        if (!id) {
            status("No active chess game.");
            return;
        }

        if (!window.confirm("Offer a draw and end this game?")) {
            return;
        }

        adaChessBusy = true;
        status("Ending game as a draw...");

        try {
            const data = await api(
                "/api/autonomous/chess/draw",
                {
                    method: "POST",
                    body: JSON.stringify({
                        game_id: id
                    })
                }
            );

            window.autonomousFinalSelected = null;
            window.autonomousFinalLegal = [];
            window.autonomousFinalChessOver = true;
            window.autonomousFinalFen = data.fen;

            if (typeof window.adaRenderChess === "function") {
                window.adaRenderChess(data.fen, []);
            } else if (typeof window.drawBoard === "function") {
                await window.drawBoard();
            }

            status("Game drawn.");
        } catch (error) {
            status("Draw error: " + error.message);
        } finally {
            adaChessBusy = false;
        }
    };

    /*
     * RESIGN
     */
    window.adaChessResign = async function () {
        if (adaChessBusy) return;

        const id = gameId();

        if (!id) {
            status("No active chess game.");
            return;
        }

        if (!window.confirm("Resign this chess game?")) {
            return;
        }

        adaChessBusy = true;
        status("Resigning...");

        try {
            const data = await api(
                "/api/autonomous/chess/resign",
                {
                    method: "POST",
                    body: JSON.stringify({
                        game_id: id
                    })
                }
            );

            window.autonomousFinalSelected = null;
            window.autonomousFinalLegal = [];
            window.autonomousFinalChessOver = true;
            window.autonomousFinalFen = data.fen;

            if (typeof window.adaRenderChess === "function") {
                window.adaRenderChess(data.fen, []);
            } else if (typeof window.drawBoard === "function") {
                await window.drawBoard();
            }

            status(
                "You resigned. Result: " +
                (data.result || "0-1")
            );
        } catch (error) {
            status("Resign error: " + error.message);
        } finally {
            adaChessBusy = false;
        }
    };

    /*
     * CHANGE COMPUTER
     *
     * Change difficulty immediately on the current game.
     * No restart required.
     */
    window.adaChessChangeComputer = async function () {
        if (adaChessBusy) return;

        const id = gameId();

        if (!id) {
            status("Start a chess game first.");
            return;
        }

        const levels = [
            "Easy",
            "Medium",
            "Hard",
            "Expert",
            "Master"
        ];

        const select =
            document.getElementById("chessDifficulty");

        const current =
            select?.value ||
            (
                typeof window.adaChessDifficulty === "function"
                    ? window.adaChessDifficulty()
                    : "Medium"
            );

        let index = levels.indexOf(current);

        if (index < 0) index = 1;

        const next =
            levels[(index + 1) % levels.length];

        adaChessBusy = true;
        status("Changing computer to " + next + "...");

        try {
            const data = await api(
                "/api/autonomous/chess/settings",
                {
                    method: "POST",
                    body: JSON.stringify({
                        game_id: id,
                        difficulty: next
                    })
                }
            );

            if (select) {
                select.value = data.difficulty || next;
            }

            if (typeof window.adaChessSetDifficulty === "function") {
                window.adaChessSetDifficulty(
                    data.difficulty || next
                );
            }

            status(
                "Computer changed to " +
                (data.difficulty || next) +
                "."
            );
        } catch (error) {
            status(
                "Computer settings error: " +
                error.message
            );
        } finally {
            adaChessBusy = false;
        }
    };

    /*
     * Replace the slow visual animation with a short,
     * non-blocking animation. The server move is NEVER
     * delayed by this.
     */
    window.adaChessAnimateMove = function (from, to, callback) {
        try {
            if (
                typeof window.adaChessAnimationEnabled !==
                "undefined" &&
                !window.adaChessAnimationEnabled
            ) {
                if (callback) callback();
                return;
            }

            const board =
                document.getElementById("chessBoard");

            if (!board) {
                if (callback) callback();
                return;
            }

            const fromCell =
                board.querySelector(
                    '[data-square="' + from + '"]'
                );

            const toCell =
                board.querySelector(
                    '[data-square="' + to + '"]'
                );

            if (!fromCell || !toCell) {
                if (callback) callback();
                return;
            }

            const piece =
                fromCell.querySelector(
                    ".autonomous-final-piece"
                ) ||
                fromCell.querySelector(
                    ".autonomous-chess-piece"
                );

            if (!piece) {
                if (callback) callback();
                return;
            }

            const a =
                fromCell.getBoundingClientRect();

            const b =
                toCell.getBoundingClientRect();

            const ghost =
                piece.cloneNode(true);

            ghost.className =
                "autonomous-chess-flying-piece";

            ghost.style.position = "fixed";
            ghost.style.left = a.left + "px";
            ghost.style.top = a.top + "px";
            ghost.style.width = a.width + "px";
            ghost.style.height = a.height + "px";
            ghost.style.zIndex = "100000";
            ghost.style.pointerEvents = "none";
            ghost.style.transition =
                "transform 120ms cubic-bezier(.2,.8,.2,1)";

            document.body.appendChild(ghost);

            requestAnimationFrame(function () {
                ghost.style.transform =
                    "translate(" +
                    (b.left - a.left) +
                    "px," +
                    (b.top - a.top) +
                    "px)";
            });

            setTimeout(function () {
                ghost.remove();
                if (callback) callback();
            }, 125);

        } catch (_) {
            if (callback) callback();
        }
    };

    /*
     * Prevent double-clicks / multiple simultaneous
     * player moves.
     */
    const originalFinalMove =
        window.adaChessMove;

    if (typeof originalFinalMove === "function") {
        window.adaChessMove = async function () {
            if (adaChessBusy) return;

            adaChessBusy = true;

            try {
                return await originalFinalMove.apply(
                    this,
                    arguments
                );
            } finally {
                adaChessBusy = false;
            }
        };
    }

    /*
     * Make dynamically-created chess buttons always
     * use the final handlers.
     */
    function bindChessButtons() {
        const board =
            document.getElementById("chessBoard");

        const root =
            document.getElementById("chessGame") ||
            document.getElementById("chessModal");

        if (!root) return;

        const buttons =
            root.querySelectorAll("button");

        buttons.forEach(function (button) {
            const text =
                (button.textContent || "")
                    .trim()
                    .toLowerCase();

            if (
                text.includes("restart") ||
                text.includes("new game")
            ) {
                button.onclick =
                    window.adaChessRestart;
            }

            if (text === "draw") {
                button.onclick =
                    window.adaChessDraw;
            }

            if (
                text.includes("resign")
            ) {
                button.onclick =
                    window.adaChessResign;
            }

            if (
                text.includes("change computer") ||
                text.includes("change difficulty")
            ) {
                button.onclick =
                    window.adaChessChangeComputer;
            }
        });
    }

    window.addEventListener(
        "load",
        function () {
            bindChessButtons();

            setTimeout(
                bindChessButtons,
                100
            );

            setTimeout(
                bindChessButtons,
                500
            );
        }
    );

    /*
     * IMPORTANT:
     * Do not run a permanent MutationObserver over the
     * entire page just to find chess buttons.
     */
    setTimeout(bindChessButtons, 1000);

})();
 /* ADA_CHESS_FINAL_PERFORMANCE_FIX_END */
