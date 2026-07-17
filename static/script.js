const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const username = email.split('@')[0];

        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username, password}),
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem("token", data.data.token);
            localStorage.setItem("user_id", data.data.user_id);
            window.location.href = "/dashboard/";
        } else {
            alert("Login failed: " + JSON.stringify(data.data));
        }
    });
}

const signupForm = document.getElementById("signupForm");
if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("name").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const username = email.split('@')[0];

        const response = await fetch(`${API_BASE_URL}/auth/signup/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username, email, password, name}),
        });

        const data = await response.json();
        if (response.ok) {
            alert("Signup successful!");
            window.location.href = "/login/";
        } else {
            alert("Signup failed: " + JSON.stringify(data));
        }
    });
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    window.location.href = "/login/";
}