import unittest
from logic import validar_fecha

class TestLogic(unittest.TestCase):
    def test_fechas_correctas(self):
        self.assertTrue(validar_fecha("30/04/2026"))
        self.assertTrue(validar_fecha("01/01/2024"))

    def test_fechas_incorrectas(self):
        self.assertFalse(validar_fecha("32/01/2024"))
        self.assertFalse(validar_fecha("ab/cd/efgh"))
        self.assertFalse(validar_fecha("2026-04-30"))

if __name__ == "__main__":
    unittest.main()