import datetime
from typing import List, Dict

class ReportData:
    def __init__(self):
        self.reset_data()

    def reset_data(self):
        self.metadata = {
            "Aplicación:": "Valoraclick",
            "Tester:": "",
            "Fecha:": datetime.datetime.now().strftime('%d/%m/%Y'),
            "Historia de Usuario:": "",
            "Requisitos:": "",
            "Versión:": "",
            "dep": "",
            "resumen": ""
        }
        self.pruebas: List[Dict] = []