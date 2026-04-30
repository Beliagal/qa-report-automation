import re
from datetime import datetime

def validar_fecha(fecha_str):
    
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", fecha_str):
        return False
    try:
        datetime.strptime(fecha_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def obtener_color_estado(estado):
    
    if estado == "Pass":
        return (46, 204, 113)
    return (231, 76, 60)