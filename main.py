from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_central import router as api_central_router
from datos_tributosimple import router as api_analisis_router, cargar_deudas
#from codem import router as codem_router
#Todavía está de prueba from codem import router as codem_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await cargar_deudas()  
    yield
   

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_central_router)
app.include_router(api_analisis_router)
#app.include_router(codem_router) 

@app.get("/health")
def health():
    return {"status": "ok", "servicio": "API BCRA", "version": "2.0.0"}