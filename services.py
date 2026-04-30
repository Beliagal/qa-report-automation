import os
import csv
import datetime
import win32com.client
from fpdf import FPDF
from fpdf.enums import XPos, YPos

class PDFService:
    def generate_report(self, data, output_path):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, 'INFORME DE TESTING', align='C', 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, " INFORMACIÓN GENERAL", border=1, fill=True, 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", "", 9)
        m = data.metadata
        pdf.cell(95, 7, f" Aplicación: {m.get('Aplicación:', '')}", border=1)
        pdf.cell(95, 7, f" Tester: {m.get('Tester:', '')}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(95, 7, f" Fecha: {m.get('Fecha:', '')}", border=1)
        pdf.cell(95, 7, f" Versión: {m.get('Versión:', '')}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.multi_cell(0, 7, f" Resumen: {m.get('resumen', '')}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        if hasattr(data, 'pruebas') and data.pruebas:
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 8, " PASOS DE EJECUCIÓN", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(80, 7, " Acción / Entrada", border=1)
            pdf.cell(40, 7, " Esperado", border=1)
            pdf.cell(40, 7, " Obtenido", border=1)
            pdf.cell(30, 7, " Estado", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font("helvetica", "", 8)
            for p in data.pruebas:
                pdf.set_text_color(0, 128, 0) if p['estado'] == "Pass" else pdf.set_text_color(255, 0, 0)

                x_start, y_start = pdf.get_x(), pdf.get_y()
                
                pdf.multi_cell(80, 7, p['input'], border=1)
                h_fila = pdf.get_y() - y_start
                
                pdf.set_xy(x_start + 80, y_start)
                pdf.multi_cell(40, h_fila, p['esp'], border=1)
                pdf.set_xy(x_start + 120, y_start)
                pdf.multi_cell(40, h_fila, p['obt'], border=1)
                pdf.set_xy(x_start + 160, y_start)
                pdf.cell(30, h_fila, p['estado'], border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                pdf.set_text_color(0, 0, 0)

                if p.get('img') and os.path.exists(p['img']):
                    pdf.ln(2)
                    pdf.image(p['img'], x=pdf.get_x() + 10, w=100)
                    pdf.ln(5)

        pdf.output(output_path)

class CSVService:
    def __init__(self):
        self.shortcut_path = r"G:\Mi unidad\Informes.lnk"
        self.fallback_path = r"G:\Mi unidad"

    def _resolve_shortcut(self, path):
        try:
            if os.path.exists(path):
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(path)
                return shortcut.Targetpath
        except Exception: return None
        return None

    def export(self, data):
        target_dir = self._resolve_shortcut(self.shortcut_path) or self.fallback_path
        if not os.path.exists(target_dir): os.makedirs(target_dir, exist_ok=True)

        ahora = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        tester = data.metadata.get("Tester:", "SinNombre").replace(" ", "_")
        full_path = os.path.join(target_dir, f"backup_{ahora}_{tester}.csv")

        try:
            with open(full_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["Campo", "Valor"])
                for k, v in data.metadata.items(): writer.writerow([k, v])
                if hasattr(data, 'pruebas') and data.pruebas:
                    writer.writerow([]); writer.writerow(["Acción", "Esperado", "Obtenido", "Estado", "Ruta Imagen"])
                    for p in data.pruebas:
                        writer.writerow([p['input'], p['esp'], p['obt'], p['estado'], p.get('img', '')])
            return True, full_path
        except Exception as e: return False, str(e)