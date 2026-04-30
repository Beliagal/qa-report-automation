import customtkinter as ctk
from tkinter import messagebox, filedialog
import datetime
import json
import os
import re
import logging
from fpdf import FPDF
from PIL import Image
from typing import List, Dict, Optional

# ==========================================
# CONFIGURACIÓN DE LOGGING
# ==========================================
logging.basicConfig(
    filename="qa_tool.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==========================================
# CAPA DE MODELO Y LÓGICA (Business Logic)
# ==========================================

class ReportData:
    """Clase para encapsular los datos del informe, separándolos de la UI."""
    def __init__(self):
        self.metadata = {
            "app": "Valoraclick",
            "tester": "",
            "fecha": datetime.datetime.now().strftime('%d/%m/%Y'),
            "hu": "",
            "req": "",
            "ver": "",
            "dep": "",
            "resumen": ""
        }
        self.pruebas: List[Dict] = []

class PDFService(FPDF):
    """Servicio especializado en la generación de documentos PDF."""
    
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'INFORME DE TESTING - VALORACLICK', 0, 1, 'C')
        self.ln(5)

    def generate_report(self, data: ReportData, output_path: str):
        self.add_page()
        self._build_metadata_section(data.metadata)
        self._build_summary_section(data.metadata["resumen"])
        self._build_results_table(data.pruebas)
        self._build_evidence_annex(data.pruebas)
        self.output(output_path)

    def _build_metadata_section(self, meta: Dict):
        self.set_fill_color(240, 240, 240)
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, " INFORMACIÓN GENERAL", 1, 1, 'L', 1)
        self.set_font("Arial", "", 9)
        
        # Grid de metadatos 3x2
        self.cell(63, 7, f"Aplicación: {meta['app']}", 1)
        self.cell(63, 7, f"Tester: {meta['tester']}", 1)
        self.cell(64, 7, f"Fecha: {meta['fecha']}", 1, 1)
        self.cell(63, 7, f"Historia de Usuario: {meta['hu']}", 1)
        self.cell(63, 7, f"Requisitos: {meta['req']}", 1)
        self.cell(64, 7, f"Versión: {meta['ver']}", 1, 1)
        self.cell(0, 7, f"Dependencias: {meta['dep']}", 1, 1)
        self.ln(5)

    def _build_summary_section(self, resumen: str):
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, " RESUMEN DE RESULTADOS", 1, 1, 'L', 1)
        self.set_font("Arial", "", 9)
        self.multi_cell(0, 7, resumen if resumen else "Sin resumen proporcionado.", border=1)
        self.ln(5)

    def _build_results_table(self, pruebas: List[Dict]):
        self.set_font("Arial", "B", 10)
        self.cell(0, 8, " DETALLES DE LOS RESULTADOS", 1, 1, 'L', 1)
        
        headers = ["Input usuario", "Resultado esperado", "Resultado obtenido", "Pass/Fail"]
        widths = [50, 50, 60, 30]
        
        self.set_font("Arial", "B", 8)
        for i, h in enumerate(headers):
            self.cell(widths[i], 8, h, 1, 0, 'C')
        self.ln()

        self.set_font("Arial", "", 8)
        for p in pruebas:
            y_start = self.get_y()
            self.multi_cell(50, 6, p['input'], border=1)
            h_row = self.get_y() - y_start
            
            self.set_xy(60, y_start)
            self.multi_cell(50, 6, p['esp'], border=1)
            self.set_xy(110, y_start)
            self.multi_cell(60, 6, p['obt'], border=1)
            self.set_xy(170, y_start)
            
            color = (0, 128, 0) if p['estado'] == "Pass" else (255, 0, 0)
            self.set_text_color(*color)
            self.cell(30, h_row, p['estado'], border=1, ln=1, align='C')
            self.set_text_color(0, 0, 0)

    def _build_evidence_annex(self, pruebas: List[Dict]):
        evidencias = [p for p in pruebas if p['img'] and os.path.exists(p['img'])]
        if not evidencias: return

        self.add_page()
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "ANEXO DE EVIDENCIAS VISUALES", 0, 1, 'L')
        
        for i, e in enumerate(evidencias, 1):
            self.set_font("Arial", "I", 9)
            self.cell(0, 8, f"Evidencia #{i} - Ref: {e['input'][:40]}", 0, 1)
            try:
                with Image.open(e['img']) as img:
                    img.thumbnail((800, 800))
                    self.image(e['img'], x=20, w=170)
            except Exception as ex:
                self.cell(0, 8, f"[Error al cargar imagen: {ex}]", 0, 1)
            self.ln(5)

# ==========================================
# CAPA DE VISTA (UI - CustomTkinter)
# ==========================================

class TestingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.report_manager = ReportData()
        self.pdf_service = PDFService()
        self.archivo_sesion = "sesion_testing.json"
        
        self._configure_window()
        self._setup_ui()
        self._load_existing_session()

    def _configure_window(self):
        self.title("Valoraclick QA Tool - Clean Architecture")
        self.geometry("1150x900")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

    def _setup_ui(self):
        """Inicializa los componentes de la interfaz de forma modular."""
        # Botón de acción principal fijo
        self.btn_export = ctk.CTkButton(
            self, text="FINALIZAR Y GENERAR PDF", 
            command=self._handle_export, 
            fg_color="#27ae60", height=50, font=("Arial", 14, "bold")
        )
        self.btn_export.place(relx=0.5, rely=0.93, anchor="center", relwidth=0.95)

        self.scroll_container = ctk.CTkScrollableFrame(self, label_text="Panel de Control QA")
        self.scroll_container.pack(fill="both", expand=True, padx=10, pady=(10, 80))

        self._create_metadata_form()
        self._create_summary_field()
        self._create_test_step_form()
        self._create_log_viewer()

    def _create_metadata_form(self):
        frame = ctk.CTkFrame(self.scroll_container)
        frame.pack(fill="x", padx=10, pady=10)
        
        # Grid Layout para Metadatos
        labels = ["Aplicación:", "Tester:", "Fecha:", "Historia de Usuario:", "Requisitos:", "Versión:"]
        self.meta_entries = {}
        
        for i, label in enumerate(labels):
            row, col = divmod(i, 3)
            ctk.CTkLabel(frame, text=label).grid(row=row, column=col*2, padx=5, pady=5, sticky="e")
            entry = ctk.CTkEntry(frame, width=150)
            entry.grid(row=row, column=col*2+1, padx=5, pady=5, sticky="w")
            self.meta_entries[label] = entry

        # Campo especial para Dependencias
        ctk.CTkLabel(frame, text="Dependencias:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.ent_dep = ctk.CTkEntry(frame)
        self.ent_dep.grid(row=2, column=1, columnspan=5, sticky="ew", padx=5, pady=5)
        
        # Valores por defecto
        self.meta_entries["Aplicación:"].insert(0, "Valoraclick")
        self.meta_entries["Fecha:"].insert(0, datetime.datetime.now().strftime('%d/%m/%Y'))

    def _create_summary_field(self):
        frame = ctk.CTkFrame(self.scroll_container)
        frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame, text="Resumen Ejecutivo:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        self.txt_summary = ctk.CTkTextbox(frame, height=80)
        self.txt_summary.pack(fill="x", padx=10, pady=5)

    def _create_test_step_form(self):
        frame = ctk.CTkFrame(self.scroll_container)
        frame.pack(fill="x", padx=10, pady=10)
        
        self.ent_input = ctk.CTkEntry(frame, placeholder_text="Paso realizado / Input", height=35)
        self.ent_input.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.ent_esp = ctk.CTkEntry(frame, placeholder_text="Esperado")
        self.ent_esp.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.ent_obt = ctk.CTkEntry(frame, placeholder_text="Obtenido")
        self.ent_obt.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.btn_img = ctk.CTkButton(frame, text="📸 Evidencia", command=self._handle_attachment)
        self.btn_img.grid(row=2, column=0, padx=10, pady=10)

        self.cmb_status = ctk.CTkComboBox(frame, values=["Pass", "Fail"])
        self.cmb_status.grid(row=2, column=1, padx=10, pady=10)

        ctk.CTkButton(frame, text="Añadir Registro", command=self._handle_add_test, fg_color="#2c3e50").grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def _create_log_viewer(self):
        self.txt_log = ctk.CTkTextbox(self.scroll_container, height=150)
        self.txt_log.pack(fill="x", padx=10, pady=10)

    # ==========================================
    # MANEJADORES DE EVENTOS (Handlers)
    # ==========================================

    def _handle_attachment(self):
        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if path and os.path.getsize(path) <= 10 * 1024 * 1024:
            self.current_img_path = path
            self.btn_img.configure(text="✅ Imagen Cargada", fg_color="#1a252f")
        else:
            messagebox.showerror("Error", "Archivo no válido o demasiado grande (>10MB)")

    def _handle_add_test(self):
        if not self.ent_input.get(): return
        
        test_step = {
            "input": self.ent_input.get(),
            "esp": self.ent_esp.get(),
            "obt": self.ent_obt.get(),
            "estado": self.cmb_status.get(),
            "img": getattr(self, 'current_img_path', "")
        }
        
        self.report_manager.pruebas.append(test_step)
        self._update_ui_log()
        self._clear_step_fields()
        self._save_session_state()

    def _handle_export(self):
        if not self.report_manager.pruebas:
            messagebox.showwarning("Aviso", "No hay pruebas para exportar.")
            return

        self._sync_metadata()
        filename = self._generate_safe_filename()
        
        try:
            self.pdf_service.generate_report(self.report_manager, filename)
            messagebox.showinfo("Éxito", f"Reporte guardado como: {filename}")
        except Exception as e:
            logging.error(f"Fallo en exportación: {e}")
            messagebox.showerror("Error", "No se pudo generar el PDF.")

    # ==========================================
    # MÉTODOS DE APOYO (Helpers)
    # ==========================================

    def _sync_metadata(self):
        """Sincroniza los valores de la UI al modelo de datos."""
        m = self.report_manager.metadata
        m["app"] = self.meta_entries["Aplicación:"].get()
        m["tester"] = self.meta_entries["Tester:"].get()
        m["fecha"] = self.meta_entries["Fecha:"].get()
        m["hu"] = self.meta_entries["Historia de Usuario:"].get()
        m["req"] = self.meta_entries["Requisitos:"].get()
        m["ver"] = self.meta_entries["Versión:"].get()
        m["dep"] = self.ent_dep.get()
        m["resumen"] = self.txt_summary.get("1.0", "end-1c")

    def _generate_safe_filename(self) -> str:
        hu = self.meta_entries["Historia de Usuario:"].get() or "REPORT"
        clean_hu = "".join(c for c in hu if c.isalnum() or c in (' ', '_')).strip()
        return f"Reporte_{clean_hu}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"

    def _clear_step_fields(self):
        self.ent_input.delete(0, "end")
        self.ent_esp.delete(0, "end")
        self.ent_obt.delete(0, "end")
        self.current_img_path = ""
        self.btn_img.configure(text="📸 Evidencia", fg_color="#3b8ed0")

    def _update_ui_log(self):
        self.txt_log.delete("1.0", "end")
        for i, p in enumerate(self.report_manager.pruebas, 1):
            self.txt_log.insert("end", f"{i}. [{p['estado']}] {p['input'][:50]}\n")

    def _save_session_state(self):
        self._sync_metadata()
        try:
            with open(self.archivo_sesion, "w", encoding="utf-8") as f:
                json.dump({
                    "meta": self.report_manager.metadata,
                    "pruebas": self.report_manager.pruebas
                }, f, indent=4)
        except Exception as e:
            logging.error(f"Error guardando sesión: {e}")

    def _load_existing_session(self):
        if not os.path.exists(self.archivo_sesion): return
        try:
            with open(self.archivo_sesion, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.report_manager.pruebas = data.get("pruebas", [])
            m = data.get("meta", {})
            
            # Carga UI
            self.meta_entries["Tester:"].insert(0, m.get("tester", ""))
            self.meta_entries["Historia de Usuario:"].insert(0, m.get("hu", ""))
            self.meta_entries["Requisitos:"].insert(0, m.get("req", ""))
            self.meta_entries["Versión:"].insert(0, m.get("ver", ""))
            self.ent_dep.insert(0, m.get("dep", ""))
            self.txt_summary.insert("1.0", m.get("resumen", ""))
            
            self._update_ui_log()
        except Exception as e:
            logging.error(f"Error cargando sesión: {e}")

if __name__ == "__main__":
    app = TestingApp()
    app.mainloop()