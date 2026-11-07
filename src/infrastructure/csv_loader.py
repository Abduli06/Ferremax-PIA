import csv
from pathlib import Path

def cargar_todos_los_csv(ruta_carpeta_datos):
    ruta = Path(ruta_carpeta_datos)
    datos = {}
    
    nombres_archivos = [
        "actores.csv",
        "casos_prueba.csv",
        "catalogo.csv",
        "detalle_operaciones.csv",
        "operaciones.csv",
        "transiciones_prueba.csv"
    ]
    
    for nombre in nombres_archivos:
        archivo_csv = ruta / nombre
        datos_archivo = []
        
        if archivo_csv.exists():
            with open(archivo_csv, mode='r', encoding='utf-8-sig') as f:
                lector = csv.DictReader(f)
                for fila in lector:
                    datos_archivo.append(fila)
            datos[nombre] = datos_archivo
            
    return datos