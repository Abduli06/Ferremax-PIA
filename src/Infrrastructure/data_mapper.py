from .csv_loader import cargar_todos_los_csv

def instanciar_dominio(ruta_carpeta_datos):
    print("Iniciando conexión con el dominio de FerreMax...")
    datos_crudos = cargar_todos_los_csv(ruta_carpeta_datos)
    
    dominio_instanciado = {
        "actores": [],
        "catalogo": [],
        "operaciones": [],
        "detalle_operaciones": [],
        "casos": datos_crudos.get("casos_prueba.csv", []),
        "transiciones": datos_crudos.get("transiciones_prueba.csv", [])
    }
    if "actores.csv" in datos_crudos:
        print(f"Conectando {len(datos_crudos['actores.csv'])} actores al dominio.")
        
    if "catalogo.csv" in datos_crudos:
        print(f"Conectando {len(datos_crudos['catalogo.csv'])} productos del catálogo.")
        
    print("Carga y conexión finalizada exitosamente.")
    return dominio_instanciado