import tkinter as tk
from tkinter import ttk
import subprocess
import sys

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚗 Détecteur de Somnolence")
        self.root.geometry("500x400")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)
        
        self._build_ui()
        
    def _build_ui(self):
        # Titre
        tk.Label(
            self.root, 
            text="🚗 DÉTECTEUR DE SOMNOLENCE", 
            bg="#1e1e2e", 
            fg="#cba6f7",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(30, 10))
        
        tk.Label(
            self.root,
            text="Système de surveillance du conducteur",
            bg="#1e1e2e",
            fg="#a6adc8",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 30))
        
        # Cadre pour les boutons
        btn_frame = tk.Frame(self.root, bg="#1e1e2e")
        btn_frame.pack(pady=20)
        
        # Bouton LANCER
        btn_launch = tk.Button(
            btn_frame,
            text="▶  LANCER LA DÉTECTION",
            bg="#a6e3a1",
            fg="#1e1e2e",
            font=("Segoe UI", 14, "bold"),
            padx=30,
            pady=12,
            relief="flat",
            cursor="hand2",
            command=self.launch_detection
        )
        btn_launch.pack(pady=10)
        
        # Bouton CONFIGURATION
        btn_config = tk.Button(
            btn_frame,
            text="⚙  CONFIGURATION AVANCÉE",
            bg="#89b4fa",
            fg="#1e1e2e",
            font=("Segoe UI", 12),
            padx=25,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self.open_config
        )
        btn_config.pack(pady=10)
        
        # Bouton QUITTER
        btn_quit = tk.Button(
            btn_frame,
            text="✖  QUITTER",
            bg="#f38ba8",
            fg="#1e1e2e",
            font=("Segoe UI", 11),
            padx=20,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.root.quit
        )
        btn_quit.pack(pady=10)
        
        # Info
        tk.Label(
            self.root,
            text="Assurez-vous que votre caméra est connectée",
            bg="#1e1e2e",
            fg="#585b70",
            font=("Segoe UI", 8)
        ).pack(side="bottom", pady=20)
    
    def launch_detection(self):
        """Lance directement la détection avec les paramètres par défaut"""
        self.root.destroy()
        # Import et lancement du détecteur
        from main import DrowsinessDetector
        detector = DrowsinessDetector()
        detector.run()
    
    def open_config(self):
        """Ouvre la configuration avant de lancer"""
        self.root.destroy()
        # Lance la configuration puis la détection
        from config_interface import ConfigInterface
        from calibration import Calibrator
        
        # Calibration
        calibrator = Calibrator()
        calibrated = calibrator.run()
        
        # Configuration
        ui = ConfigInterface(calibrated=calibrated)
        config = ui.run()
        
        if config:
            from main import DrowsinessDetector
            detector = DrowsinessDetector(config)
            detector.run()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    launcher = Launcher()
    launcher.run()