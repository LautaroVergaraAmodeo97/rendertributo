import asyncio
import aiohttp
import pandas as pd
import urllib3
from fastapi import APIRouter, HTTPException

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter(prefix="/analisis", tags=["Análisis de Deudas"])

situacion_map = {
    1: 'Situación Normal',
    2: 'Situación con seguimiento especial o riesgo bajo',
    3: 'Con problemas o riesgo medio',
    4: 'Alto riesgo de insolvencia o riesgo alto',
    5: 'Irrecuperable',
    0: 'Sin información'
}

#CSV_PATH = "C:\\Users\\lauta\\OneDrive\\Desktop\\Tributo Simple\\datos_externos\\backend\\cuits.csv"
CSV_PATH = "backend\cuits.csv"
_cache = {"deudas_df": None}


async def fetch_cuit(session, cuit):
    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{cuit}"
    try:
        async with session.get(url, ssl=False, timeout=aiohttp.ClientTimeout(total=10)) as res:
            response_data = await res.json()
            if 'results' in response_data:
                return response_data['results']
            return response_data
    except Exception as e:
        return {"cuit": cuit, "error": str(e)}


async def fetch_todos_los_cuits(lista_cuits, chunk_size=10):
    respuestas = []
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(lista_cuits), chunk_size):
            chunk = lista_cuits[i:i + chunk_size]
           # print(f" Procesando chunk {i//chunk_size + 1} de {-(-len(lista_cuits)//chunk_size)}...")
            tareas = [fetch_cuit(session, cuit) for cuit in chunk]
            resultados = await asyncio.gather(*tareas)
            respuestas.extend(resultados)
    return respuestas


def procesar_respuestas(respuestas):
    deudas = []
    for response in respuestas:
        if 'errorMessages' in response or 'error' in response:
            deudas.append({
                'identificacion': response.get('cuit', 'N/A'),
                'denominacion': 'Error', 'periodo': None,
                'entidad': None, 'situacion': None,
                'monto': None, 'error_message': response.get('error', response.get('errorMessages'))
            })
        elif 'identificacion' in response and 'periodos' in response:
            for periodo_data in response['periodos']:
                for entidad_data in periodo_data['entidades']:
                    deudas.append({
                        'identificacion': response['identificacion'],
                        'denominacion': response['denominacion'],
                        'periodo': periodo_data['periodo'],
                        'entidad': entidad_data['entidad'],
                        'situacion': entidad_data['situacion'],
                        'monto': entidad_data['monto'],
                        'error_message': None
                    })
        else:
            deudas.append({
                'identificacion': response.get('identificacion', 'N/A'),
                'denominacion': 'Formato inesperado', 'periodo': None,
                'entidad': None, 'situacion': None, 'monto': None,
                'error_message': "Estructura desconocida"
            })

    deudas_df = pd.DataFrame(deudas)
    deudas_df = deudas_df[deudas_df['error_message'].isnull()].copy()
    deudas_df['situacion_descripcion'] = deudas_df['situacion'].map(situacion_map).fillna('Desconocida')
    return deudas_df


async def cargar_deudas():
    df = pd.read_csv(CSV_PATH)
    lista_cuits = df['cuit'].tolist()
    print(f"🔍 Consultando {len(lista_cuits)} CUITs en chunks de 10...")
    respuestas = await fetch_todos_los_cuits(lista_cuits)
    _cache["deudas_df"] = procesar_respuestas(respuestas)
    print(f"✅ Cache cargado: {len(_cache['deudas_df'])} registros.")


def get_df():
    if _cache["deudas_df"] is None:
        raise HTTPException(status_code=503, detail="Datos aún no cargados, reintentá en unos segundos.")
    return _cache["deudas_df"]


@router.get("/resumen")
def get_resumen():
    deudas_df = get_df()
    return {
        "total_registros": len(deudas_df),
        "cuits_unicos": int(deudas_df['identificacion'].nunique()),
        "distribucion_situaciones": deudas_df['situacion_descripcion'].value_counts().to_dict(),
        "monto_por_situacion": deudas_df.groupby('situacion_descripcion')['monto'].sum().to_dict(),
    }


@router.get("/top-entidades")
def get_top_entidades(top: int = 5):
    deudas_df = get_df()
    return (
        deudas_df.groupby('entidad')['monto']
        .sum().nlargest(top).reset_index()
        .rename(columns={'monto': 'monto_total'})
        .to_dict(orient='records')
    )


@router.get("/deudas")
def get_todas_las_deudas():
    return get_df().to_dict(orient='records')