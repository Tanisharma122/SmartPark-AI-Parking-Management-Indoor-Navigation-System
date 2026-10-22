from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import init
from auth import verify_api_key

# ROUTES
from routes.camera_api import router as camera_router
from routes.camera_register_api import router as camera_register_router
from routes.dashboard_api import router as dashboard_router
from routes.navigation_api import router as navigation_router
from routes.admin_api import router as admin_router

# initialize DB
init()

app = FastAPI(title="Smart Parking Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADMIN ROUTES (SaaS Management)
app.include_router(admin_router)

# VIDEO REGISTRATION
app.include_router(
    camera_register_router,
    dependencies=[Depends(verify_api_key)]
)

# CAMERA SLOT INGESTION + FREE SLOTS
app.include_router(
    camera_router,
    dependencies=[Depends(verify_api_key)]
)

# DASHBOARD ROUTES
app.include_router(
    dashboard_router,
    dependencies=[Depends(verify_api_key)]
)

# NAVIGATION ROUTES
app.include_router(
    navigation_router,
    dependencies=[Depends(verify_api_key)]
)

@app.get("/")
def root():
    return {"status": "Backend running"}
