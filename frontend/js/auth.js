const API = "http://localhost:8000";
let isLoginMode = true;

function switchMode() {
  isLoginMode = !isLoginMode;
  const formTitle = document.getElementById("form-title");
  const authBtn = document.getElementById("auth-btn");
  const switchText = document.getElementById("switch-text");
  const switchLink = document.getElementById("switch-link");
  const msgDiv = document.getElementById("msg");

  if (isLoginMode) {
    formTitle.textContent = "Login";
    authBtn.textContent = "Login";
    switchText.textContent = "Don't have an account?";
    switchLink.textContent = "Register now";
  } else {
    formTitle.textContent = "Register";
    authBtn.textContent = "Register";
    switchText.textContent = "Already have an account?";
    switchLink.textContent = "Login now";
  }

  msgDiv.textContent = "";
  document.getElementById("username").value = "";
  document.getElementById("password").value = "";
}

async function handleAuth() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const msgDiv = document.getElementById("msg");

  // Validation
  if (!username || !password) {
    msgDiv.textContent = "Please enter all required fields";
    msgDiv.className = "message error";
    return;
  }

  if (username.length < 3) {
    msgDiv.textContent = "Username must be at least 3 characters";
    msgDiv.className = "message error";
    return;
  }

  if (username.length > 50) {
    msgDiv.textContent = "Username cannot exceed 50 characters";
    msgDiv.className = "message error";
    return;
  }

  if (password.length < 4) {
    msgDiv.textContent = "Password must be at least 4 characters";
    msgDiv.className = "message error";
    return;
  }

  if (password.length > 72) {
    msgDiv.textContent = "Password cannot exceed 72 characters";
    msgDiv.className = "message error";
    return;
  }

  if (isLoginMode) {
    await login(username, password);
  } else {
    await register(username, password);
  }
}

async function register(username, password) {
  const msgDiv = document.getElementById("msg");

  try {
    const res = await fetch(API + "/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const errorData = await res.json();
      msgDiv.textContent = errorData.detail || "Registration failed";
      msgDiv.className = "message error";
      return;
    }

    const data = await res.json();
    msgDiv.textContent = "Registration successful! Switching to login...";
    msgDiv.className = "message success";

    // Auto switch to login mode after 2 seconds
    setTimeout(() => {
      switchMode();
      msgDiv.textContent = "Please login with your new account";
      msgDiv.className = "message info";
    }, 2000);

  } catch (error) {
    msgDiv.textContent = "Connection error: " + error.message;
    msgDiv.className = "message error";
  }
}

async function login(username, password) {
  const msgDiv = document.getElementById("msg");

  try {
    const res = await fetch(API + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const errorData = await res.json();
      msgDiv.textContent = errorData.detail || "Login failed";
      msgDiv.className = "message error";
      return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    msgDiv.textContent = "Login successful! Redirecting...";
    msgDiv.className = "message success";

    setTimeout(() => {
      window.location.href = "/dashboard.html";
    }, 1000);

  } catch (error) {
    msgDiv.textContent = "Connection error: " + error.message;
    msgDiv.className = "message error";
  }
}

window.onload = function () {
  const token = localStorage.getItem("token");
  if (token) {
    window.location.href = "/dashboard.html";
  }
}