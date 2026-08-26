from fastapi import FastAPI

app = FastAPI(title="Career TimeMachine API")

@app.get("/health")
def health():
    return {"status": "ok"}