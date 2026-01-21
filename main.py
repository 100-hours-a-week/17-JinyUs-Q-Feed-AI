from fastapi import FastAPI
from routers import stt,feedback

app = FastAPI()

app.include_router(stt.router, prefix="/ai", tags=["stt"])
app.include_router(feedback.router, prefix="/ai", tags=["feedback"])

@app.get("/ai")
async def root():
    return {"message": "FastAPI is running"}