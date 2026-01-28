import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)


# cloudflared tunnel --url http://localhost:8000
# cloudflared tunnel --url http://localhost:3000
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload