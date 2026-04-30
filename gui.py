import customtkinter as ctk
from tkinter import messagebox, filedialog
import datetime, json, os, re
from models import ReportData
from services import PDFService, CSVService

class TestingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.report_data = ReportData()
        self.pdf_service = PDFService()
        self.csv_service = CSVService()
        
        self.session_file = "sesion_testing.json"
        self.current_img = ""
        
        self.title("QA Tool v1.0.0 Secure")
        self.geometry("1200x900")
        self.after(0, lambda: self.state('zoomed'))
        
        self.vcmd = (self.register(self._validate_date_input), '%P')
        
        self._setup_top_bar()
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Panel de Control QA")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._setup_metadata_grid()
        self._setup_execution_form()
        self._load_session()

    def _validate_date_input(self, P):
        if len(P) > 10: return False
        return all(c in "0123456789/" for c in P)

    def _setup_top_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(bar, text="RESET TOTAL", fg_color="#c0392b", command=self._on_reset).pack(side="right", padx=5)
        ctk.CTkButton(bar, text="EXPORTAR PDF", fg_color="#27ae60", command=self._on_export).pack(side="right", padx=5)

    def _on_export(self):
        """Gestiona la exportación manual del PDF y el backup automático en Drive."""
        self._sync()
        
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", self.entries["Fecha:"].get()):
            messagebox.showwarning("Formato", "Usa el formato DD/MM/AAAA en la fecha.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if path:
            try:
                self.pdf_service.generate_report(self.report_data, path)
                
                success, msg = self.csv_service.export(self.report_data)
                if success:
                    print(f"Sincronizado en Drive: {msg}")
                else:
                    print(f"Backup de Drive omitido: {msg}")
                
                messagebox.showinfo("Éxito", f"Informe generado.\nBackup en Drive: {'Ok' if success else 'No disponible'}")
                
            except Exception as e:
                messagebox.showerror("Error Crítico", f"No se pudo crear el PDF: {e}")

    def _sync(self):
        """Sincroniza los widgets de la UI con el objeto report_data."""
        m = self.report_data.metadata
        for k, v in self.entries.items(): 
            m[k] = v.get()
        m["dep"] = self.ent_dep.get()
        m["resumen"] = self.txt_resumen.get("1.0", "end-1c")

    
    def _setup_metadata_grid(self):
        self.meta_frame = ctk.CTkFrame(self.scroll)
        self.meta_frame.pack(fill="x", padx=10, pady=10)
        for i in [1, 3, 5]: self.meta_frame.grid_columnconfigure(i, weight=1)

        self.entries = {}
        fields = [
            ("Aplicación:", 0, 0, ""), 
            ("Tester:", 0, 2, ""), 
            ("Fecha:", 0, 4, datetime.datetime.now().strftime('%d/%m/%Y')),
            ("Historia de Usuario:", 1, 0, ""), 
            ("Requisitos:", 1, 2, ""), 
            ("Versión:", 1, 4, "")
        ]
        
        for text, r, c, d in fields:
            ctk.CTkLabel(self.meta_frame, text=text).grid(row=r, column=c, padx=5, pady=5, sticky="e")
            if text == "Fecha:":
                ent = ctk.CTkEntry(self.meta_frame, validate="key", validatecommand=self.vcmd)
            else:
                ent = ctk.CTkEntry(self.meta_frame)
            ent.grid(row=r, column=c+1, padx=5, pady=5, sticky="ew")
            ent.insert(0, d)
            ent.bind("<KeyRelease>", lambda e: self._update_log())
            self.entries[text] = ent
        
        ctk.CTkLabel(self.meta_frame, text="Dependencias:").grid(row=2, column=0, padx=5, pady=10, sticky="e")
        self.ent_dep = ctk.CTkEntry(self.meta_frame)
        self.ent_dep.grid(row=2, column=1, columnspan=5, sticky="ew", padx=(5, 10), pady=10)
        self.ent_dep.bind("<KeyRelease>", lambda e: self._update_log())

    def _setup_execution_form(self):
        ctk.CTkLabel(self.scroll, text="Resumen Ejecutivo:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)
        self.txt_resumen = ctk.CTkTextbox(self.scroll, height=80)
        self.txt_resumen.pack(fill="x", padx=15, pady=5)
        self.txt_resumen.bind("<KeyRelease>", lambda e: self._update_log())

        f = ctk.CTkFrame(self.scroll)
        f.pack(fill="x", padx=10, pady=10)
        f.grid_columnconfigure((0, 1), weight=1)

        self.ent_in = ctk.CTkEntry(f, placeholder_text="Acción...", height=35)
        self.ent_in.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.ent_es = ctk.CTkEntry(f, placeholder_text="Esperado...")
        self.ent_es.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.ent_ob = ctk.CTkEntry(f, placeholder_text="Obtenido...")
        self.ent_ob.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        btn_f = ctk.CTkFrame(f, fg_color="transparent")
        btn_f.grid(row=2, column=0, columnspan=2, pady=10)
        self.btn_img = ctk.CTkButton(btn_f, text="📸 Imagen", command=self._on_img)
        self.btn_img.pack(side="left", padx=10)
        self.cmb_st = ctk.CTkComboBox(btn_f, values=["Pass", "Fail"], state="readonly", width=100)
        self.cmb_st.set("Pass")
        self.cmb_st.pack(side="left", padx=10)
        
        ctk.CTkButton(f, text="AÑADIR PASO", command=self._on_add, height=40, fg_color="#2c3e50").grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.log = ctk.CTkTextbox(self.scroll, height=300, font=("Consolas", 12))
        self.log.pack(fill="x", padx=10, pady=10)

    def _update_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        t = self.log._textbox
        t.tag_config("title", foreground="#3498db", font=("Consolas", 12, "bold"))
        t.tag_config("pass", foreground="#2ecc71")
        t.tag_config("fail", foreground="#e74c3c")

        t.insert("end", "--- VISTA PREVIA DEL INFORME ---\n", "title")
        for k, v in self.entries.items():
            t.insert("end", f"{k} {v.get()}\n")
        
        if self.report_data.pruebas:
            t.insert("end", f"\n--- PASOS ({len(self.report_data.pruebas)}) ---\n", "title")
            for i, p in enumerate(self.report_data.pruebas, 1):
                tag = "pass" if p['estado'] == "Pass" else "fail"
                t.insert("end", f"Paso {i}: {p['input'][:40]}...\n", tag)
        self.log.configure(state="disabled")
        self.log.see("end")

    def _on_add(self):
        action = self.ent_in.get().strip()
        if not action: return
        step = {
            "input": action, "esp": self.ent_es.get(), 
            "obt": self.ent_ob.get(), "estado": self.cmb_st.get(), 
            "img": self.current_img
        }
        self.report_data.pruebas.append(step)
        self._update_log()
        self._save_session()
        self._clear_step()

    def _on_reset(self):
        if messagebox.askyesno("Borrar", "¿Deseas limpiar todo el informe?"):
            self.report_data.reset_data()
            if os.path.exists(self.session_file):
                try: os.remove(self.session_file)
                except: pass
            for e in self.entries.values(): e.delete(0, "end")
            self.entries["Aplicación:"].insert(0, "")
            self.entries["Fecha:"].insert(0, datetime.datetime.now().strftime('%d/%m/%Y'))
            self.ent_dep.delete(0, "end")
            self.txt_resumen.delete("1.0", "end")
            self._update_log()

    def _save_session(self):
        try:
            self._sync()
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump({"meta": self.report_data.metadata, "pruebas": self.report_data.pruebas}, f, indent=4)
        except Exception: pass

    def _load_session(self):
        if not os.path.exists(self.session_file): return
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.report_data.pruebas = d.get("pruebas", [])
            m = d.get("meta", {})
            for k, v in self.entries.items():
                if k in m:
                    v.delete(0, "end")
                    v.insert(0, m[k])
            self.ent_dep.insert(0, m.get("dep", ""))
            self.txt_resumen.insert("1.0", m.get("resumen", ""))
            self._update_log()
        except Exception: pass

    def _on_img(self):
        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if path:
            self.current_img = path
            self.btn_img.configure(text="✅ Imagen Ok", fg_color="#2c3e50")

    def _clear_step(self):
        self.ent_in.delete(0, "end"); self.ent_es.delete(0, "end"); self.ent_ob.delete(0, "end")
        self.current_img = ""; self.btn_img.configure(text="📸 Imagen", fg_color="#3b8ed0")