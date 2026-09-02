(function () {

    "use strict";

    window.ADA = window.ADA || {};

    // --------------------------------------------------------
    // DOWNLOAD
    // --------------------------------------------------------

    ADA.download = function () {

        window.open(
            "https://github.com/atlworkchatgpt-boop/AUTONOMOUS_DESKTOP_AGENT",
            "_blank"
        );

    };


    // --------------------------------------------------------
    // RESTART DASHBOARD
    // --------------------------------------------------------

    ADA.restart = function () {

        window.location.reload();

    };


    // --------------------------------------------------------
    // POLICY
    // --------------------------------------------------------

    ADA.openPolicy = function () {

        window.location.href =
            "/static/privacy.html";

    };


    // --------------------------------------------------------
    // TERMS
    // --------------------------------------------------------

    ADA.openTerms = function () {

        window.location.href =
            "/static/terms.html";

    };


    // --------------------------------------------------------
    // WEATHER
    // --------------------------------------------------------

    ADA.weather = async function () {

        const city =
            window.prompt(
                "Which city should I check the weather for?"
            );

        if (!city)
            return;

        const status =
            document.querySelector(
                "#weatherStatus"
            );

        if (status)
            status.textContent =
                "Getting live weather...";

        try {

            /*
             * Ask ADA's existing web/weather system.
             * No WeatherStack API key is required here.
             */

            const response =
                await fetch(
                    "/api/weather",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify({
                                city: city
                            })
                    }
                );

            const data =
                await response.json();

            if (!response.ok)
                throw new Error(
                    data.detail ||
                    "Weather request failed."
                );

            if (status) {

                status.textContent =
                    data.answer ||
                    data.message ||
                    JSON.stringify(data);

            }

        }
        catch (error) {

            if (status)
                status.textContent =
                    "Weather: " +
                    error.message;

            else
                alert(
                    "Weather error: " +
                    error.message
                );

        }

    };


    // --------------------------------------------------------
    // CHESS
    // --------------------------------------------------------

    ADA.chess = ADA.chess || {};


    ADA.chess.restart =
        async function () {

            const response =
                await fetch(
                    "/api/chess/restart",
                    {
                        method: "POST"
                    }
                );

            if (!response.ok)
                throw new Error(
                    "Chess restart failed."
                );

            return response.json();

        };


    ADA.chess.resign =
        async function () {

            const response =
                await fetch(
                    "/api/chess/resign",
                    {
                        method: "POST"
                    }
                );

            if (!response.ok)
                throw new Error(
                    "Resign failed."
                );

            return response.json();

        };


    ADA.chess.draw =
        async function () {

            /*
             * The server-side chess implementation is responsible
             * for Stockfish analysis before accepting/declining.
             */

            const response =
                await fetch(
                    "/api/chess/draw",
                    {
                        method: "POST"
                    }
                );

            const data =
                await response.json();

            if (!response.ok)
                throw new Error(
                    data.detail ||
                    "Draw request failed."
                );

            return data;

        };


    // --------------------------------------------------------
    // MOVE HIGHLIGHTING
    // --------------------------------------------------------

    ADA.chess.highlightMove =
        function (
            from,
            to
        ) {

            document
                .querySelectorAll(
                    ".chess-last-move"
                )
                .forEach(
                    function (element) {

                        element.classList.remove(
                            "chess-last-move"
                        );

                    }
                );

            const squares =
                document.querySelectorAll(
                    "[data-square]"
                );

            squares.forEach(
                function (square) {

                    const name =
                        square.getAttribute(
                            "data-square"
                        );

                    if (
                        name === from ||
                        name === to
                    ) {

                        square.classList.add(
                            "chess-last-move"
                        );

                    }

                }
            );

        };


    // --------------------------------------------------------
    // MENU HELPERS
    // --------------------------------------------------------

    function addMenuLink(
        text,
        onclick
    ) {

        const existing =
            Array.from(
                document.querySelectorAll(
                    "a,button"
                )
            ).find(
                function (element) {

                    return (
                        element.textContent
                            .trim()
                            .toLowerCase()
                            ===
                        text
                            .trim()
                            .toLowerCase()
                    );

                }
            );

        if (existing)
            return;

        const menus =
            document.querySelectorAll(
                "nav, aside, .sidebar, .menu"
            );

        if (!menus.length)
            return;

        const parent =
            menus[0];

        const button =
            document.createElement(
                "button"
            );

        button.type =
            "button";

        button.textContent =
            text;

        button.className =
            "ada-local-menu-button";

        button.onclick =
            onclick;

        parent.appendChild(
            button
        );

    }


    function addFeatures() {

        addMenuLink(
            "Policy",
            ADA.openPolicy
        );

        addMenuLink(
            "Terms",
            ADA.openTerms
        );

        addMenuLink(
            "Download",
            ADA.download
        );

        addMenuLink(
            "Weather",
            ADA.weather
        );

    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            addFeatures
        );

    }
    else {

        addFeatures();

    }

})();
