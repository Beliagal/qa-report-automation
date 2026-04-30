# test_integration.py
import unittest
import os
from models import ReportData
from services import PDFService

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        self.data = ReportData()
        self.service = PDFService()
        self.test_filename = "test_output_report.pdf"

    def test_creacion_pdf_con_datos(self):
        # 1. Simular datos cargados
        self.data.metadata["Tester:"] = "Sistema de Test"
        self.data.pruebas.append({
            "input": "Prueba de integración",
            "esp": "PDF generado",
            "obt": "PDF generado",
            "estado": "Pass",
            "img": ""
        })

        # 2. Ejecutar servicio
        self.service.generate_report(self.data, self.test_filename)

        # 3. Verificar que el archivo existe y tiene contenido
        self.assertTrue(os.path.exists(self.test_filename))
        self.assertGreater(os.path.getsize(self.test_filename), 0)

    def tearDown(self):
        # Limpiar el archivo de prueba después del test
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

if __name__ == "__main__":
    unittest.main()