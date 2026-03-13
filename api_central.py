import requests
import pandas as pd
import urllib3
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter()


@router.get("/deudas/{cuit}")
def get_deudas(cuit: str):
    res = requests.get(
        f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{cuit}",
        verify=False,
        timeout=30
    )

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Error al consultar la API del BCRA")

    response_data = res.json()

    if 'results' in response_data:
        return response_data['results']
    return response_data

@router.get("/deudashistorico/{cuit}")
def get_deudas_historica(cuit:str):
    res = requests.get(
        f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/Historicas/{cuit}",
        verify=False,
        timeout=30
    )

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Error al consultar la API del BCRA")

    response_data = res.json()

    if 'results' in response_data:
        return response_data['results']
    return response_data


