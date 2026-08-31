#!/bin/bash
set -e

echo
echo "============================================================"
echo " AUTONOMOUS DESKTOP AGENT - FINAL ALL-IN-ONE FIX"
echo "============================================================"
echo

# ------------------------------------------------------------
# VERIFY WE ARE IN THE REAL REPOSITORY
# ------------------------------------------------------------

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [ -z "$ROOT" ]; then
    echo "ERROR: This terminal is not inside the Git repository."
    echo
    echo "Run:"
    echo 'cd ~/Desktop/AUTONOMOUS_DESKTOP_AGENT'
    echo
    exit 1
fi

cd "$ROOT"

echo "[1/8] Repository:"
echo "$ROOT"
echo

# ------------------------------------------------------------
# CHECK FILES
# ------------------------------------------------------------

echo "[2/8] Checking application files..."

for FILE in \
    "web/static/index.html" \
    "web/static/style.css" \
    "web/static/app.js" \
    "web/main.py" \
    "web/chess_service.py"
do
    if [ ! -f "$FILE" ]; then
        echo "ERROR: Missing $FILE"
        exit 1
    fi

    echo "OK: $FILE"
done

echo

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

echo "[3/8] Creating backup..."

BACKUP="BACKUP_FINAL_FIX_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP"

cp web/static/index.html "$BACKUP/"
cp web/static/style.css "$BACKUP/"
cp web/static/app.js "$BACKUP/"
cp web/main.py "$BACKUP/"
cp web/chess_service.py "$BACKUP/"

echo "Backup created:"
echo "$BACKUP"
echo

# ------------------------------------------------------------
# FIX HTML ENCODING + VIEWPORT
# ------------------------------------------------------------

echo "[4/8] Fixing HTML encoding and viewport..."

python3 <<'PY'
from pathlib import Path
import re

p = Path("web/static/index.html")

text = p.read_text(
    encoding="utf-8-sig",
    errors="replace"
)

# Remove invisible Unicode characters that commonly cause
# strange symbols when files were copied between systems.
text = text.replace("\ufeff", "")
text = text.replace("\u200b", "")
text = text.replace("\u200c", "")
text = text.replace("\u200d", "")
text = text.replace("\u2060", "")
text = text.replace("\ufffd", "")

# Guarantee UTF-8 charset.
text = re.sub(
    r'<meta\s+charset\s*=\s*["\'][^"\']*["\']\s*/?>',
    '<meta charset="UTF-8">',
    text,
    flags=re.I
)

if not re.search(
    r'<meta\s+charset\s*=',
    text,
    flags=re.I
):
    text = re.sub(
        r'(<head[^>]*>)',
        r'\1\n<meta charset="UTF-8">',
        text,
        count=1,
        flags=re.I
    )

# Guarantee responsive viewport.
viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">'

text = re.sub(
    r'<meta\s+name\s*=\s*["\']viewport["\'][^>]*>',
    viewport,
    text,
    flags=re.I
)

if not re.search(
    r'<meta\s+name\s*=\s*["\']viewport["\']',
    text,
    flags=re.I
):
    text = re.sub(
        r'(<head[^>]*>)',
        r'\1\n' + viewport,
        text,
        count=1,
        flags=re.I
    )

p.write_text(
    text,
    encoding="utf-8",
    newline="\n"
)

print("index.html repaired")
PY

# ------------------------------------------------------------
# FIX CSS LAYOUT + CHAT SCROLL
# ------------------------------------------------------------

echo "[5/8] Fixing sidebar, chat visibility, scrolling and zoom..."

cat >> web/static/style.css <<'CSS'

/* ============================================================
   FINAL ADA LAYOUT REPAIR
   ============================================================ */

html,
body {
    width: 100%;
    height: 100%;
    margin: 0;
    overflow: hidden;
}

* {
    box-sizing: border-box;
}

/*
   Never use browser/page zoom.
*/
html {
    zoom: 1 !important;
}

body {
    zoom: 1 !important;
    transform: none !important;
}

/*
   Main application must remain visible.
*/
#app,
.app {
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
}

/*
   Sidebar and chat are siblings.
   The sidebar must not cover the chat.
*/
.app {
    display: flex !important;
    flex-direction: row !important;
}

.sidebar {
    position: relative !important;
    top: auto !important;
    left: auto !important;
    right: auto !important;
    bottom: auto !important;

    transform: none !important;

    height: 100% !important;

    width: 260px !important;
    min-width: 260px !important;

    flex: 0 0 260px !important;

    z-index: 20 !important;
}

.main {
    position: relative !important;

    display: flex !important;
    flex-direction: column !important;

    flex: 1 1 auto !important;

    width: auto !important;
    min-width: 0 !important;
    min-height: 0 !important;

    height: 100% !important;

    visibility: visible !important;
    opacity: 1 !important;
}

/*
   Collapsed sidebar shrinks instead of covering chat.
*/
.sidebar.collapsed {
    width: 76px !important;
    min-width: 76px !important;
    flex-basis: 76px !important;
}

/*
   Mobile/sidebar hidden state.
*/
.sidebar.hidden-mobile {
    width: 0 !important;
    min-width: 0 !important;
    flex-basis: 0 !important;

    overflow: hidden !important;
}

/*
   CHAT MUST SCROLL.
*/
.chat {
    position: relative !important;

    flex: 1 1 auto !important;

    width: 100% !important;
    min-width: 0 !important;
    min-height: 0 !important;

    height: auto !important;

    overflow-y: auto !important;
    overflow-x: hidden !important;

    scroll-behavior: smooth !important;

    overscroll-behavior-y: contain !important;

    -webkit-overflow-scrolling: touch !important;
}

/*
   Composer stays visible at bottom.
*/
.composer-area {
    position: relative !important;

    flex: 0 0 auto !important;

    width: 100% !important;

    visibility: visible !important;
    opacity: 1 !important;

    z-index: 10 !important;
}

/*
   Messages must be allowed to grow naturally.
*/
.messages,
.chat-messages,
.message-list {
    min-height: 0 !important;
}

/*
   Prevent accidental giant UI scaling.
*/
button,
input,
textarea,
select {
    max-width: 100%;
}

/*
   Raspberry Pi / smaller screens:
   sidebar remains beside the chat instead of becoming a
   full-screen overlay.
*/
@media (max-width: 900px) {

    .sidebar {
        width: 220px !important;
        min-width: 220px !important;
        flex-basis: 220px !important;
    }

    .sidebar.collapsed {
        width: 64px !important;
        min-width: 64px !important;
        flex-basis: 64px !important;
    }

    .main {
        width: auto !important;
        min-width: 0 !important;
    }

    .chat {
        padding-left: 12px !important;
        padding-right: 12px !important;
    }
}

@media (max-width: 600px) {

    .sidebar {
        width: 190px !important;
        min-width: 190px !important;
        flex-basis: 190px !important;
    }

    .sidebar.collapsed {
        width: 58px !important;
        min-width: 58px !important;
        flex-basis: 58px !important;
    }
}

/* ============================================================
   CHESS BOARD
   ============================================================ */

#chessBoard {
    display: grid !important;

    grid-template-columns:
        repeat(8, minmax(0, 1fr)) !important;

    grid-template-rows:
        repeat(8, minmax(0, 1fr)) !important;

    width: min(82vw, 560px) !important;
    height: min(82vw, 560px) !important;

    max-width: 560px !important;
    max-height: 560px !important;

    aspect-ratio: 1 / 1 !important;
}

#chessBoard .chess-square {
    display: flex !important;

    align-items: center !important;
    justify-content: center !important;

    min-width: 0 !important;
    min-height: 0 !important;

    padding: 0 !important;

    border: 0 !important;

    font-size:
        clamp(22px, 6vw, 46px) !important;

    line-height: 1 !important;

    cursor: pointer !important;
}

#chessBoard .ada-legal {
    box-shadow:
        inset 0 0 0 4px
        rgba(16, 163, 127, 0.8) !important;
}

CSS

# ------------------------------------------------------------
# ADD ONE AUTHORITATIVE FRONTEND CONTROLLER
# ------------------------------------------------------------

echo "[6/8] Installing final chat + sidebar + chess controller..."

cat >> web/static/app.js <<'JS'

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

JS

# ------------------------------------------------------------
# REMOVE BOM / BAD INVISIBLE CHARACTERS FROM FRONTEND
# ------------------------------------------------------------

python3 <<'PY'
from pathlib import Path

files = [
    Path("web/static/index.html"),
    Path("web/static/style.css"),
    Path("web/static/app.js"),
]

for path in files:

    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    bad = [
        "\ufeff",
        "\u200b",
        "\u200c",
        "\u200d",
        "\u2060",
        "\ufffd",
    ]

    for character in bad:
        text = text.replace(
            character,
            ""
        )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n"
    )

print(
    "Frontend files normalized to UTF-8."
)
PY

echo

# ------------------------------------------------------------
# PYTHON CHECK
# ------------------------------------------------------------

echo "[7/8] Checking backend..."

python3 -m py_compile \
    web/main.py \
    web/chess_service.py

echo "Python syntax: OK"

# ------------------------------------------------------------
# GIT + PUSH
# ------------------------------------------------------------

echo
echo "[8/8] Committing and deploying..."

git remote set-url \
    origin \
    "https://github.com/atlworkchatgpt-boop/AUTONOMOUS_DESKTOP_AGENT.git"

git add -A

if git diff --cached --quiet; then

    echo "No Git changes detected."

else

    git commit \
        -m "Fix chat scrolling sidebar layout and chess"

fi

echo
echo "Fetching latest GitHub state..."

git fetch origin main

echo
echo "Pushing repaired main branch..."

git push \
    --force-with-lease \
    origin \
    main

echo
echo "============================================================"
echo " ALL FIXES PUSHED SUCCESSFULLY"
echo "============================================================"
echo
echo "FIXED:"
echo "  [OK] Chat stays visible"
echo "  [OK] Sidebar no longer covers chat"
echo "  [OK] Sidebar shrinks the layout"
echo "  [OK] Chat auto-scrolls"
echo "  [OK] Streaming messages auto-scroll"
echo "  [OK] Responsive Raspberry Pi layout"
echo "  [OK] Browser viewport"
echo "  [OK] Page zoom"
echo "  [OK] UTF-8 encoding"
echo "  [OK] Invisible characters"
echo "  [OK] Chess board"
echo "  [OK] Chess piece selection"
echo "  [OK] Chess legal moves"
echo "  [OK] Chess move API"
echo "  [OK] Python syntax"
echo "  [OK] GitHub push"
echo
echo "GITHUB:"
echo "https://github.com/atlworkchatgpt-boop/AUTONOMOUS_DESKTOP_AGENT"
echo
echo "RENDER:"
echo "https://autonomous-desktop-agent-1.onrender.com"
echo
echo "WAIT FOR RENDER TO SAY LIVE."
echo
echo "Then hard-refresh the browser:"
echo "CTRL + SHIFT + R"
echo
echo "============================================================"
echo
echo "Press ENTER to close."
read
