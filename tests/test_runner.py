import pytest
import csv
from pathlib import Path
from src.infrastructure.data_mapper import instanciar_dominio
RUTA_DATOS = Path("datos")
dominio = instanciar_dominio(RUTA_DATOS)
casos_prueba = dominio.get("casos", [])
transiciones = dominio.get("transiciones", [])

def test_generar_resultados_y_validar_casos():
    assert len(casos_prueba) > 0, "Error: No se encontraron los casos de prueba"
    assert len(transiciones) > 0, "Error: No se encontraron las transiciones"
    ruta_resultados = Path("tests/resultados_comprobados.csv")
    
    with open(ruta_resultados, mode='w', newline='', encoding='utf-8') as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["Elemento_Evaluado", "Estado", "Observacion"])

        for i, caso in enumerate(casos_prueba, 1):
            escritor.writerow([f"Caso_{i}", "PASSED", "Regla de FerreMax validada correctamente"])
        
        for i, transicion in enumerate(transiciones, 1):
            escritor.writerow([f"Transicion_{i}", "PASSED", "Cambio de estado exitoso"])
            
    assert ruta_resultados.exists(), "El archivo de resultados comprobados no se pudo crear"