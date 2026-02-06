# 🔐 Authentication Flow Explained

This document explains exactly how the login and signup systems work in your chatbot application.

---

## 1. The Frontend Layer (React/Next.js)

### **Login Page (`frontend/src/app/login/page.tsx`)**
This is the user interface.

*   **Action:** When a user clicks "Login".
*   **Code:** `handleLogin` function.
*   **What it does:**
    1.  Collects email and password.
    2.  Sends a POST request to the backend.
    3.  **Crucial Setting:** `credentials: 'include'`
        *   This tells the browser: "If the server sends back a cookie, accept it. And send this cookie back with future requests."

```typescript
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // <--- VERY IMPORTANT
  body: JSON.stringify({ email, password }),
});
```

*   **On Success:**
    1.  Frontend receives purely informational data (username, role).
    2.  It saves this to `localStorage` just to update the UI (like showing your name in the navbar).
    3.  Redirects to `/chat`.

---

## 2. The Backend Layer (FastAPI)

### **Auth Routes (`backend/app/api/routes/auth.py`)**
This is the logic center.

*   **Endpoint:** `/auth/login`
*   **Input:** Receives Email & Password.
*   **Logic:**
    1.  Queries the database (`users` table).
    2.  Checks if password matches.
    3.  If valid, generates a **JWT (JSON Web Token)**.

### **The Token (`backend/app/core/security.py`)**
This is the key to the castle.

We don't just create a random string. We create a structured token that Hasura understands.

**What's inside the token?**
```json
{
  "sub": "user_uuid",
  "name": "User Name",
  "https://hasura.io/jwt/claims": {
    "x-hasura-allowed-roles": ["user", "admin"],
    "x-hasura-default-role": "admin",
    "x-hasura-user-id": "user_uuid"
  }
}
```
*   **Hasura Claims:** These specific fields tell Hasura exactly who this user is and what role they have.

### **The Cookie Handoff**
This is the security best practice.

Instead of sending the token back in the JSON body (where you'd have to store it in JS, making it vulnerable to XSS attacks), we send it as a **Cookie**.

```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,  # JavaScript cannot read this cookie!
    secure=False,   # (True in production)
    samesite="lax"
)
```

---

## 3. The Database Layer (Postgres)

*   **Users Table:** Stores `email`, `password`, `role` ('admin' or 'user').
*   **Relationship:** When JWT is generated, the `id` from this table becomes the `x-hasura-user-id`.

---

## 4. How It Works After Login (Authorization)

When you navigate to a protected page (e.g., Workflow):

### **Frontend Check (UI Security)**
*   The page (`workflow/page.tsx`) checks `localStorage` user info.
*   If `role !== 'admin'`, it redirects you to `/chat` immediately.
*   *Note: This is just for UX. A hacker could change localStorage.*

### **Backend Check (Real Security)**
*   The frontend makes an API call to fetch workflows.
*   The **Browser automatically includes the `access_token` cookie**.
*   **Hasura/Backend:**
    1.  intercepts the request.
    2.  Verifies the Token's signature (using `SECRET_KEY`).
    3.  Reads the `x-hasura-role`.
    4.  **Enforces Permissions:**
        *   If the token says 'user', and you try to DELETE a workflow, Hasura blocks it because of the permissions we configured.

---

## Summary

1.  **User** enters credentials.
2.  **Backend** validates and creates a signed **JWT** with **Hasura Claims**.
3.  **Backend** puts JWT in an **HTTP-Only Cookie**.
4.  **Browser** automatically sends this cookie for every future request.
5.  **Hasura** trust the token and allows access based on the Role inside it.
