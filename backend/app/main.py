from fastapi import FastAPI
from backend.app.routes import analyzer_controller

app = FastAPI(title="AI Codebase Review System", version="1.0.0")

# Include routers
app.include_router(analyzer_controller.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "AI Codebase Review System API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
