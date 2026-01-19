from fastapi import FastAPI
from routers import stt,feedback

app = FastAPI()

app.include_router(stt.router, prefix="/api/v1", tags=["stt"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])

@app.get("/")
async def root():
    return {"message": "Hello World"}