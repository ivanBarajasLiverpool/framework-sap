"""
Validaciones visuales para SAP GUI (equivalentes a las del framework PAO con Playwright):
  * show_intro()      -> Cortinilla a pantalla completa con nombre del test y resultado esperado
                         (en PAO se hacía con page.goto(data:text/html...); aquí con Tkinter sobre el escritorio).
  * VideoRecorder     -> Grabación del escritorio con ffmpeg (gdigrab), equivalente a record_video_dir de Playwright.
El resaltado de campos (marco rojo) y capturas por paso viven en core/sap_engine.py.
"""
import os
import shutil
import subprocess
import time
from datetime import datetime

from config.settings import Config
from utils.logger import get_logger

logger = get_logger("Visual")

LIVERPOOL_PURPLE = "#78256f"
LIVERPOOL_PINK = "#E10098"


def show_intro(test_name: str, expected_result: str = None, seconds: float = None):
    """Muestra una cortinilla (splash) estilo Liverpool antes de cada test para que quede en el video."""
    if not Config.SHOW_INTRO:
        return
    seconds = seconds if seconds is not None else Config.INTRO_SECONDS
    try:
        import tkinter as tk

        display_name = test_name.replace("test_", "").replace("_", " ").title()
        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(bg=LIVERPOOL_PURPLE)
        root.overrideredirect(True)

        frame = tk.Frame(root, bg=LIVERPOOL_PURPLE)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="EJECUCIÓN DE PRUEBA DE AUTOMATIZACIÓN", fg="white", bg=LIVERPOOL_PINK,
                 font=("Helvetica", 12, "bold"), padx=16, pady=6).pack(pady=(0, 25))
        tk.Label(frame, text=display_name, fg="white", bg=LIVERPOOL_PURPLE,
                 font=("Helvetica", 34, "bold"), wraplength=1100, justify="center").pack()
        tk.Label(frame, text=f"SAP GUI • {Config.PROJECT_NAME}", fg="#d8b4d4", bg=LIVERPOOL_PURPLE,
                 font=("Helvetica", 13)).pack(pady=(10, 30))

        if expected_result:
            box = tk.Frame(frame, bg="#8a3a80", padx=25, pady=18)
            box.pack()
            tk.Label(box, text="📋 RESULTADO ESPERADO", fg="#f0c2ea", bg="#8a3a80",
                     font=("Helvetica", 11, "bold")).pack(anchor="w")
            tk.Label(box, text=expected_result, fg="white", bg="#8a3a80", font=("Helvetica", 15),
                     wraplength=900, justify="left").pack(anchor="w", pady=(6, 0))

        root.after(int(seconds * 1000), root.destroy)
        root.mainloop()
    except Exception as e:
        logger.warning(f"[-] No se pudo mostrar la cortinilla de intro: {e}")


class VideoRecorder:
    """Graba el escritorio completo durante la suite usando ffmpeg (si está instalado)."""

    def __init__(self, videos_dir: str):
        self.videos_dir = videos_dir
        self.process = None
        self.output = None

    def start(self):
        if not Config.RECORD_VIDEO:
            return
        ffmpeg = shutil.which(Config.FFMPEG_PATH) or (Config.FFMPEG_PATH if os.path.exists(Config.FFMPEG_PATH) else None)
        if not ffmpeg:
            logger.warning("[!] RECORD_VIDEO=true pero no se encontró ffmpeg. Se omite la grabación de video.")
            return
        os.makedirs(self.videos_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output = os.path.join(self.videos_dir, f"suite_execution_{timestamp}.mp4")
        cmd = [ffmpeg, "-y", "-f", "gdigrab", "-framerate", "8", "-i", "desktop",
               "-vcodec", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", self.output]
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"[*] Grabación de video iniciada: {self.output}")

    def stop(self):
        if not self.process:
            return None
        try:
            self.process.communicate(input=b"q", timeout=15)
        except Exception:
            self.process.kill()
        time.sleep(0.5)
        logger.info(f"[*] Video de la suite guardado en: {self.output}")
        return self.output
