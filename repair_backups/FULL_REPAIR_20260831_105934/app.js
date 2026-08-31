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
                            message
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
                    "/api/upload",
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

            addMessage(
                "assistant",
                "Uploaded: " +
                data.filename
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
                "/api/chess/start",
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
                "/api/chess/move",
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
            const data=await mediaRequest("/api/autonomous/image",prompt.trim());
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
            const data=await mediaRequest("/api/autonomous/video",prompt.trim());
            for(let i=0;i<120;i++){
                await new Promise(resolve=>setTimeout(resolve,5000));
                const response=await fetch(
                    "/api/autonomous/video/status/"+
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


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   ADA FINAL CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    /*
     * This controller intentionally lives at the end of app.js
     * so it becomes the final authority if older code contains
     * duplicate handlers.
     */

    const chat =
        document.getElementById("chat");

    const sidebar =
        document.getElementById("sidebar");


    /* ========================================================
       CHAT AUTO-SCROLL
       ======================================================== */

    function scrollChatToBottom() {

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    /*
     * Make auto-scroll available to older code too.
     */
    window.scrollBottom =
        scrollChatToBottom;


    /*
     * Observe streamed messages and new messages.
     */
    if (chat) {

        const observer =
            new MutationObserver(
                function () {
                    scrollChatToBottom();
                }
            );

        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        window.addEventListener(
            "load",
            scrollChatToBottom
        );


        window.addEventListener(
            "resize",
            scrollChatToBottom
        );


        setTimeout(
            scrollChatToBottom,
            50
        );

        setTimeout(
            scrollChatToBottom,
            250
        );

        setTimeout(
            scrollChatToBottom,
            1000
        );
    }


    /*
     * Whenever the user sends a message, force the chat
     * to the bottom shortly afterward.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const text =
                (
                    button.textContent
                    ||
                    ""
                )
                .toLowerCase();

            if (
                text.includes("send")
                ||
                button.id === "sendBtn"
                ||
                button.id === "send"
            ) {

                setTimeout(
                    scrollChatToBottom,
                    20
                );

                setTimeout(
                    scrollChatToBottom,
                    250
                );
            }

        }
    );


    /* ========================================================
       SIDEBAR
       ======================================================== */

    window.toggleSidebar =
        function () {

            if (!sidebar) {
                return;
            }


            /*
             * Never turn the sidebar into a full-screen overlay.
             */
            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "hidden-mobile"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


    /* ========================================================
       CHESS
       ======================================================== */

    const PIECES = {

        p: "\u265F",
        r: "\u265C",
        n: "\u265E",
        b: "\u265D",
        q: "\u265B",
        k: "\u265A",

        P: "\u2659",
        R: "\u2656",
        N: "\u2658",
        B: "\u2657",
        Q: "\u2655",
        K: "\u2654"
    };


    let chessGameId = null;

    let chessFen = null;

    let chessColor = "white";

    let chessSelected = null;

    let chessLegal = [];


    function chessBoard() {

        return document.getElementById(
            "chessBoard"
        );
    }


    function chessStatus() {

        return document.getElementById(
            "chessStatus"
        );
    }


    function chessSetup() {

        return document.getElementById(
            "chessSetup"
        );
    }


    function chessGame() {

        return document.getElementById(
            "chessGame"
        );
    }


    function chessModal() {

        return document.getElementById(
            "chessModal"
        );
    }


    function parseFen(fen) {

        const rows =
            String(fen || "")
            .split(" ")[0]
            .split("/");


        return rows.map(
            function (row) {

                const output = [];


                for (
                    const character of row
                ) {

                    if (
                        character >= "1"
                        &&
                        character <= "8"
                    ) {

                        const count =
                            Number(
                                character
                            );


                        for (
                            let i = 0;
                            i < count;
                            i++
                        ) {

                            output.push("");
                        }

                    } else {

                        output.push(
                            character
                        );
                    }
                }


                while (
                    output.length < 8
                ) {

                    output.push("");
                }


                return output;
            }
        );
    }


    function squareName(
        row,
        column
    ) {

        return (
            String.fromCharCode(
                97 + column
            )
            +
            String(
                8 - row
            )
        );
    }


    function ownPiece(piece) {

        if (!piece) {
            return false;
        }


        const white =
            piece ===
            piece.toUpperCase();


        return chessColor === "white"
            ? white
            : !white;
    }


    function renderChess() {

        const boardElement =
            chessBoard();


        if (
            !boardElement
            ||
            !chessFen
        ) {

            return;
        }


        const board =
            parseFen(
                chessFen
            );


        const reverse =
            chessColor === "black";


        boardElement.innerHTML = "";


        for (
            let visualRow = 0;
            visualRow < 8;
            visualRow++
        ) {

            for (
                let visualColumn = 0;
                visualColumn < 8;
                visualColumn++
            ) {

                const row =
                    reverse
                    ? 7 - visualRow
                    : visualRow;


                const column =
                    reverse
                    ? 7 - visualColumn
                    : visualColumn;


                const square =
                    squareName(
                        row,
                        column
                    );


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.className =
                    "chess-square "
                    +
                    (
                        (
                            visualRow
                            +
                            visualColumn
                        ) % 2 === 0
                        ? "chess-light"
                        : "chess-dark"
                    );


                if (
                    chessSelected ===
                    square
                ) {

                    button.classList.add(
                        "chess-selected"
                    );
                }


                if (
                    chessLegal.includes(
                        square
                    )
                ) {

                    button.classList.add(
                        "ada-legal"
                    );
                }


                const piece =
                    board[row][column];


                if (piece) {

                    button.textContent =
                        PIECES[piece]
                        ||
                        piece;
                }


                button.addEventListener(
                    "click",
                    function () {

                        handleChessClick(
                            row,
                            column,
                            board
                        );

                    }
                );


                boardElement.appendChild(
                    button
                );
            }
        }
    }


    async function legalMoves(
        square
    ) {

        const response =
            await fetch(
                "/api/autonomous/chess/legal-moves"
                +
                "?game_id="
                +
                encodeURIComponent(
                    chessGameId
                )
                +
                "&square="
                +
                encodeURIComponent(
                    square
                ),
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
                ||
                "Unable to get legal moves."
            );
        }


        return Array.isArray(
            data.legal_moves
        )
            ? data.legal_moves
            : [];
    }


    async function handleChessClick(
        row,
        column,
        board
    ) {

        const clicked =
            squareName(
                row,
                column
            );


        const piece =
            board[row][column];


        try {

            /*
             * First click selects a piece.
             */
            if (!chessSelected) {

                if (
                    !ownPiece(piece)
                ) {

                    return;
                }


                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Clicking the selected piece again deselects.
             */
            if (
                clicked ===
                chessSelected
            ) {

                chessSelected = null;
                chessLegal = [];

                renderChess();

                return;
            }


            /*
             * Clicking another own piece changes selection.
             */
            if (
                ownPiece(piece)
                &&
                !chessLegal.includes(
                    clicked
                )
            ) {

                chessSelected =
                    clicked;


                chessLegal =
                    await legalMoves(
                        clicked
                    );


                renderChess();

                return;
            }


            /*
             * Reject illegal destination.
             */
            if (
                !chessLegal.includes(
                    clicked
                )
            ) {

                const status =
                    chessStatus();


                if (status) {

                    status.textContent =
                        "Choose a highlighted legal square.";
                }


                return;
            }


            const from =
                chessSelected;


            const fromRow =
                8 -
                parseInt(
                    from[1],
                    10
                );


            const fromColumn =
                from.charCodeAt(0)
                -
                97;


            const movingPiece =
                board[fromRow][fromColumn];


            let move =
                from +
                clicked;


            /*
             * Automatically promote to queen.
             */
            if (
                movingPiece
                &&
                movingPiece.toLowerCase()
                    ===
                    "p"
                &&
                (
                    row === 0
                    ||
                    row === 7
                )
            ) {

                move += "q";
            }


            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Thinking...";
            }


            const response =
                await fetch(
                    "/api/autonomous/chess/move",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({
                                game_id:
                                    chessGameId,

                                move:
                                    move
                            })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail
                    ||
                    "Chess move failed."
                );
            }


            chessFen =
                data.fen;


            renderChess();


            if (status) {

                if (
                    data.game_over
                ) {

                    status.textContent =
                        "Game over: "
                        +
                        (
                            data.result
                            ||
                            "Finished"
                        );

                } else {

                    status.textContent =
                        "Your move";
                }
            }


        } catch (error) {

            console.error(
                "Chess error:",
                error
            );


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Chess error: "
                    +
                    error.message;
            }
        }
    }


    /*
     * Public function used by the existing UI.
     */
    window.openChess =
        function () {

            const modal =
                chessModal();


            if (modal) {

                modal.classList.remove(
                    "hidden"
                );
            }


            const setup =
                chessSetup();


            if (setup) {

                setup.classList.remove(
                    "hidden"
                );
            }


            const game =
                chessGame();


            if (game) {

                game.classList.add(
                    "hidden"
                );
            }


            chessGameId = null;
            chessFen = null;
            chessSelected = null;
            chessLegal = [];


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Choose your side and difficulty.";
            }
        };


    /*
     * Public function used by the existing UI.
     */
    window.startChess =
        async function () {

            const colorElement =
                document.getElementById(
                    "chessColor"
                );


            const difficultyElement =
                document.getElementById(
                    "chessDifficulty"
                );


            chessColor =
                colorElement
                ? colorElement.value
                : "white";


            const difficulty =
                difficultyElement
                ? difficultyElement.value
                : "Medium";


            const status =
                chessStatus();


            if (status) {

                status.textContent =
                    "Starting chess...";
            }


            try {

                const response =
                    await fetch(
                        "/api/autonomous/chess/start",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({
                                    color:
                                        chessColor,

                                    difficulty:
                                        difficulty
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail
                        ||
                        "Could not start chess."
                    );
                }


                chessGameId =
                    data.game_id;


                chessFen =
                    data.fen;


                chessColor =
                    data.color
                    ||
                    chessColor;


                chessSelected = null;
                chessLegal = [];


                const setup =
                    chessSetup();


                if (setup) {

                    setup.classList.add(
                        "hidden"
                    );
                }


                const game =
                    chessGame();


                if (game) {

                    game.classList.remove(
                        "hidden"
                    );
                }


                renderChess();


                if (status) {

                    status.textContent =
                        "Your move";
                }


                /*
                 * If backend provides an automatic first
                 * move for Black, refresh board state.
                 */
                if (
                    data.ai_moved
                    &&
                    data.fen
                ) {

                    chessFen =
                        data.fen;

                    renderChess();
                }


            } catch (error) {

                console.error(
                    "Chess start error:",
                    error
                );


                if (status) {

                    status.textContent =
                        "Chess error: "
                        +
                        error.message;
                }
            }
        };


})();


/* ============================================================
   AUTONOMOUS DESKTOP AGENT - FINAL CHAT CONTROLLER
   ============================================================ */

(function () {

    "use strict";

    function findChat() {

        const candidates = [
            document.getElementById("chat"),
            document.querySelector(".chat"),
            document.querySelector(".chat-messages"),
            document.querySelector(".messages"),
            document.querySelector(".message-list")
        ];

        for (const element of candidates) {

            if (element) {
                return element;
            }
        }

        return null;
    }


    function scrollChatToBottom() {

        const chat = findChat();

        if (!chat) {
            return;
        }

        requestAnimationFrame(function () {

            chat.scrollTop =
                chat.scrollHeight;

        });
    }


    window.scrollChatToBottom =
        scrollChatToBottom;


    /*
     * Watch for new assistant/user messages.
     */
    function installObserver() {

        const chat = findChat();

        if (!chat) {
            return false;
        }

        if (chat.dataset.adaObserverInstalled === "1") {
            return true;
        }

        chat.dataset.adaObserverInstalled = "1";


        const observer =
            new MutationObserver(function () {

                scrollChatToBottom();

            });


        observer.observe(
            chat,
            {
                childList: true,
                subtree: true,
                characterData: true
            }
        );


        scrollChatToBottom();

        return true;
    }


    /*
     * The app may create the chat element after startup,
     * therefore retry several times.
     */
    let attempts = 0;

    const timer =
        setInterval(function () {

            attempts += 1;

            if (installObserver()) {

                clearInterval(timer);

            }

            if (attempts > 40) {

                clearInterval(timer);
            }

        }, 250);


    window.addEventListener(
        "load",
        function () {

            setTimeout(
                scrollChatToBottom,
                100
            );

            setTimeout(
                scrollChatToBottom,
                500
            );

            setTimeout(
                scrollChatToBottom,
                1200
            );

        }
    );


    window.addEventListener(
        "resize",
        function () {

            setTimeout(
                scrollChatToBottom,
                100
            );

        }
    );


    /*
     * Catch send buttons without replacing existing handlers.
     */
    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "button"
                );

            if (!button) {
                return;
            }

            const id =
                String(
                    button.id || ""
                ).toLowerCase();


            const text =
                String(
                    button.textContent || ""
                ).toLowerCase();


            if (
                id.includes("send")
                ||
                text.includes("send")
            ) {

                setTimeout(
                    scrollChatToBottom,
                    50
                );

                setTimeout(
                    scrollChatToBottom,
                    300
                );

                setTimeout(
                    scrollChatToBottom,
                    1000
                );
            }

        },
        true
    );


    /*
     * Sidebar handling.
     *
     * We do not replace the existing sidebar button.
     * We provide a safe public function for buttons that
     * call window.toggleSidebar().
     */
    window.adaToggleSidebar =
        function () {

            const sidebar =
                document.querySelector(
                    ".sidebar"
                );

            if (!sidebar) {
                return;
            }


            if (
                window.innerWidth <= 900
            ) {

                sidebar.classList.toggle(
                    "collapsed"
                );

            } else {

                sidebar.classList.toggle(
                    "collapsed"
                );
            }


            setTimeout(
                scrollChatToBottom,
                250
            );
        };


})();

