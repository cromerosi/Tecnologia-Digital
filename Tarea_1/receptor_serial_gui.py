"""
Receptor Serial ESP32 - Interfaz Gráfica
Requiere: pip install pyserial
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, time, serial, serial.tools.list_ports
from datetime import datetime


class App:
    def __init__(self, root):
        root.title("Receptor Serial ESP32")
        root.geometry("650x450")
        root.configure(bg="#1e1e2e")

        self.ser = None
        self.running = False

        # ── Fila de controles ──
        ctrl = tk.Frame(root, bg="#1e1e2e")
        ctrl.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(ctrl, text="Puerto:", bg="#1e1e2e", fg="white").pack(side=tk.LEFT)
        self.puertos = ttk.Combobox(ctrl, width=20, state="readonly")
        self.puertos.pack(side=tk.LEFT, padx=4)

        ttk.Button(ctrl, text="🔄", width=3, command=self._cargar_puertos).pack(side=tk.LEFT, padx=2)

        tk.Label(ctrl, text="Baud:", bg="#1e1e2e", fg="white").pack(side=tk.LEFT, padx=(10, 0))
        self.baud = ttk.Combobox(ctrl, width=8, values=["9600", "115200", "230400", "921600"], state="readonly")
        self.baud.set("115200")
        self.baud.pack(side=tk.LEFT, padx=4)

        self.btn = ttk.Button(ctrl, text="Conectar", command=self._toggle)
        self.btn.pack(side=tk.LEFT, padx=8)

        ttk.Button(ctrl, text="Limpiar", command=self._limpiar).pack(side=tk.LEFT, padx=2)

        # ── Log ──
        self.log = scrolledtext.ScrolledText(root, font=("Consolas", 10),
                                             bg="#181825", fg="#cdd6f4",
                                             state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.log.tag_configure("hora", foreground="#6c7086")
        self.log.tag_configure("dato", foreground="#a6e3a1")
        self.log.tag_configure("info", foreground="#89b4fa")
        self.log.tag_configure("err", foreground="#f38ba8")

        self._cargar_puertos()
        root.protocol("WM_DELETE_WINDOW", self._salir)

    # ── Puertos ──
    def _cargar_puertos(self):
        ports = [f"{p.device} - {p.description}" for p in serial.tools.list_ports.comports()]
        self.puertos["values"] = ports
        if ports:
            self.puertos.current(0)

    # ── Conectar / Desconectar ──
    def _toggle(self):
        if self.running:
            self._desconectar()
        else:
            self._conectar()

    def _conectar(self):
        sel = self.puertos.get()
        if not sel:
            return
        puerto = sel.split(" - ")[0]
        try:
            self.ser = serial.Serial(puerto, int(self.baud.get()), timeout=1)
            time.sleep(1.5)
        except serial.SerialException as e:
            self._log(f"[ERROR] {e}", "err")
            return
        self.running = True
        self.btn.configure(text="Desconectar")
        self._log(f"[INFO] Conectado a {puerto}", "info")
        threading.Thread(target=self._leer, daemon=True).start()

    def _desconectar(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.btn.configure(text="Conectar")
        self._log("[INFO] Desconectado", "info")

    # ── Lectura serial (hilo) ──
    def _leer(self):
        while self.running:
            try:
                if self.ser and self.ser.in_waiting:
                    linea = self.ser.readline().decode("utf-8", errors="replace").strip()
                    if linea:
                        ts = datetime.now().strftime("%H:%M:%S")
                        self._log(f"[{ts}] {linea}", "dato")
                else:
                    time.sleep(0.005)
            except serial.SerialException:
                self._log("[ERROR] Conexión perdida", "err")
                self._desconectar()
                break

    # ── Utilidades ──
    def _log(self, msg, tag=""):
        def _w():
            self.log.configure(state=tk.NORMAL)
            self.log.insert(tk.END, msg + "\n", tag)
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)
        self.log.after(0, _w)

    def _limpiar(self):
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def _salir(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root = self.log.winfo_toplevel()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
