function getNextUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("next") || "/";
}

document.getElementById("loginForm").addEventListener("submit", async function (e) {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const notification = document.getElementById("notification");
    notification.style.display = "none";

    try {
        const response = await fetch("/api/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const data = await response.json();
            notification.textContent = data.detail || "登入失敗，請再試一次";
            notification.style.display = "block";
        } else {
            window.location.href = getNextUrl();
        }
    } catch (error) {
        notification.textContent = "伺服器錯誤，請稍後再試";
        notification.style.display = "block";
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}