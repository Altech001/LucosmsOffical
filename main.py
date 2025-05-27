import asyncio
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import httpx
from rate_limiter.rate_limiter import setup_limiter

from sqlalchemy.orm import Session
from database import get_db

from database import Base, engine
from routes.auth import auth_router, get_current_user
from routes.lucouser import user_router
from routes.lucosms import sms_router

from routes.lucoapi import router
from routes.clientsms import luco_router

from controllers.autodelete import auto_delete_router
import logging
import os
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


Base.metadata.create_all(bind=engine)


APP_URL = os.environ.get("APP_URL", "https://lucosms-api.onrender.com")


PING_INTERVAL = 600

Base.metadata.create_all(bind=engine)


async def keep_alive():
    """Task that pings the app URL periodically to keep it alive."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                logger.info(f"Sending keep-alive ping to {APP_URL}/health")
                response = await client.get(f"{APP_URL}/health")
                logger.info(f"Keep-alive response: {response.status_code}")
            except Exception as e:
                logger.error(f"Keep-alive ping failed: {str(e)}")
            
            
            await asyncio.sleep(PING_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    task = asyncio.create_task(keep_alive())
    yield
    
    task.cancel()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_limiter(app)


@app.get("/")
def root(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {
        "message":"Welcome to the Luco SMS API",
        "version":"1.1.0",
        "author":"Abaasa Albert",
        "status":"online",
        "documentation":"https://lucosms.com/docs",
        }

@app.get("/health")
async def health_check():
    return {"status": "ok"}



app.include_router(router=auth_router, prefix="/auth", tags=["Auth"])
app.include_router(router=user_router, prefix="/user")
app.include_router(router=sms_router)

app.include_router(router=router)
app.include_router(router=luco_router)
app.include_router(router=auto_delete_router)
