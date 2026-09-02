window.ADA = window.ADA || {};

ADA.restart = function () {
    window.location.reload();
};

ADA.download = function () {
    window.open(
        "https://github.com/atlworkchatgpt-boop/AUTONOMOUS_DESKTOP_AGENT",
        "_blank"
    );
};

ADA.generateImage = async function () {

    const prompt = window.prompt(
        "Describe the image ADA should create:"
    );

    if (!prompt) return;

    const response = await fetch(
        "/api/media/image",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                prompt: prompt
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {
        alert(data.detail || "Image generation failed.");
        return;
    }

    if (data.url) {
        window.open(data.url, "_blank");
    }
};

ADA.generateVideo = async function () {

    const prompt = window.prompt(
        "Describe the video ADA should create:"
    );

    if (!prompt) return;

    const response = await fetch(
        "/api/media/video",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                prompt: prompt
            })
        }
    );

    const data = await response.json();

    alert(
        data.message ||
        "Video generation is not configured."
    );
};

ADA.chess = {
    restart: () =>
        fetch("/api/chess/restart", {
            method: "POST"
        }),

    resign: () =>
        fetch("/api/chess/resign", {
            method: "POST"
        }),

    draw: () =>
        fetch("/api/chess/draw", {
            method: "POST"
        }),

    analysis: () =>
        fetch("/api/chess/analysis", {
            method: "POST"
        })
};
