from fastapi import FastAPI, Depends
from database import init
from routes.camera_api import router as camera_router
from routes.dashboard_api import router as dashboard_router
from routes.navigation_api import router as navigation_router
from auth import verify_api_key

init()

app = FastAPI(title="Smart Parking Backend")

# Secure camera ingestion
app.include_router(
    camera_router,
    dependencies=[Depends(verify_api_key)]
)

# Dashboard routes (secured)
app.include_router(
    dashboard_router,
    dependencies=[Depends(verify_api_key)]
)

# Navigation routes (secured)
app.include_router(
    navigation_router,
    dependencies=[Depends(verify_api_key)]
)

@app.get("/")
def root():
    return {"status": "Backend running"}
