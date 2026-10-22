from fastapi import FastAPI
from database import init
from routes.camera_api import router as camera_router
from routes.dashboard_api import router as dashboard_router

init()

app = FastAPI(title="Smart Parking Backend")

app.include_router(camera_router)
app.include_router(dashboard_router)

@app.get("/")
def root():
    return {"status": "Backend running"}
