import requests
import urllib3
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException
from playwright.sync_api import sync_playwright

router = APIRouter()

@router.get("/codem/{cuil}")
def consultar_codem(cuil: str):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://servicioswww.anses.gob.ar/ooss2/")

        # completar CUIL
        page.fill("#txtCuil", cuil)

        print("Resolver captcha manualmente en el navegador...")

        input("Presiona ENTER cuando el captcha esté resuelto")

        # enviar consulta
        page.click("#btnConsultar")

        page.wait_for_timeout(3000)

        html = page.content()

        browser.close()

        return {"html": html}
