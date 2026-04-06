import tkinter as tk
from tkinter import ttk


class ConfigInterface:
    def __init__(self, calibrated=None):
        """
        calibrated : dict avec les seuils calculés par la calibration
        """
        self.config = None
        self.root = tk.Tk()
        self.root.title("⚙️ Configuration - Détection Somnolence")
        self.root.geometry("580x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        # Valeurs par défaut
        defaults = {
            "ear_threshold": calibrated["ear_threshold"] if calibrated else 0.25,
            "ear_frames":    calibrated["ear_frames"]    if calibrated else 20,
            "mar_threshold": calibrated["mar_threshold"] if calibrated else 0.60,
            "moe_threshold": calibrated["moe_threshold"] if calibrated else 2.5,
            "first_delay":   3,
            "first_delay_unit": "sec",  # "sec" ou "min"
            "alert_interval": 2,
            "alert_interval_unit": "min",
        }
        
        self.defaults = defaults
        self._build_ui(defaults)

    def _build_ui(self, defaults):
        # ========== TITRE ==========
        tk.Label(
            self.root, text="🚗  Détection de Somnolence",
            bg="#1e1e2e", fg="#cba6f7",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 5))
        
        tk.Label(
            self.root, text="Ajustez les paramètres puis lancez la détection",
            bg="#1e1e2e", fg="#a6adc8",
            font=("Segoe UI", 9)
        ).pack(pady=(0, 15))

        # ========== CADRE SCROLLABLE ==========
        canvas = tk.Canvas(self.root, bg="#1e1e2e", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e1e2e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y")

        # ========== SECTION YEUX ==========
        self._section_title(scrollable_frame, "👁  Détection des yeux")
        
        self.ear_threshold = self._slider_row(
            scrollable_frame, "Seuil EAR (fermeture yeux)",
            0.15, 0.35, defaults["ear_threshold"], 0.01, ""
        )
        
        self.ear_frames = self._slider_row(
            scrollable_frame, "Frames avant alerte yeux",
            10, 40, defaults["ear_frames"], 1, "frames"
        )

        # ========== SECTION BOUCHE ==========
        self._section_title(scrollable_frame, "👄  Détection du bâillement")
        
        self.mar_threshold = self._slider_row(
            scrollable_frame, "Seuil MAR (ouverture bouche)",
            0.40, 0.90, defaults["mar_threshold"], 0.01, ""
        )
        
        self.moe_threshold = self._slider_row(
            scrollable_frame, "Seuil MOE (filtre faux positifs)",
            1.5, 5.0, defaults["moe_threshold"], 0.1, ""
        )

        # ========== SECTION NOTIFICATIONS ==========
        self._section_title(scrollable_frame, "🔔  Notifications")
        
        # ----- Délai avant première notification (AVEC CHOIX secondes/minutes) -----
        delay_frame = tk.Frame(scrollable_frame, bg="#1e1e2e")
        delay_frame.pack(fill="x", padx=16, pady=6)
        
        tk.Label(
            delay_frame, text="Délai avant 1ère notification",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 11)
        ).pack(anchor="w")
        
        # Slider pour la valeur
        row1 = tk.Frame(delay_frame, bg="#1e1e2e")
        row1.pack(fill="x", pady=(5, 0))
        
        self.first_delay_var = tk.DoubleVar(value=defaults["first_delay"])
        self.first_delay_str = tk.StringVar()
        
        val_label = tk.Label(
            row1, textvariable=self.first_delay_str,
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 10, "bold"), width=10, anchor="w"
        )
        
        def update_delay(*_):
            v = self.first_delay_var.get()
            unit = "sec" if self.delay_unit_var.get() == "sec" else "min"
            self.first_delay_str.set(f"{int(v)} {unit}")
        
        self.delay_slider = tk.Scale(
            row1,
            from_=1, to=60,
            orient="horizontal",
            variable=self.first_delay_var,
            resolution=1,
            command=update_delay,
            length=350,
            bg="#1e1e2e", fg="#cdd6f4",
            troughcolor="#313244",
            highlightthickness=0,
            showvalue=0,
            bd=0
        )
        self.delay_slider.pack(side="left", padx=(0, 6))
        val_label.pack(side="left")
        
        # Boutons radio pour choisir l'unité
        row2 = tk.Frame(delay_frame, bg="#1e1e2e")
        row2.pack(fill="x", pady=(5, 0))
        
        self.delay_unit_var = tk.StringVar(value=defaults["first_delay_unit"])
        
        tk.Radiobutton(
            row2, text="Secondes", variable=self.delay_unit_var, value="sec",
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#1e1e2e",
            activebackground="#1e1e2e", command=update_delay
        ).pack(side="left", padx=(0, 15))
        
        tk.Radiobutton(
            row2, text="Minutes", variable=self.delay_unit_var, value="min",
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#1e1e2e",
            activebackground="#1e1e2e", command=update_delay
        ).pack(side="left")
        
        update_delay()
        
        # ----- Intervalle entre alertes -----
        self.alert_interval = self._slider_row(
            scrollable_frame, "Intervalle entre alertes",
            1, 10, defaults["alert_interval"], 1, "min"
        )

        # ========== BOUTONS ==========
        button_frame = tk.Frame(scrollable_frame, bg="#1e1e2e")
        button_frame.pack(pady=25)

        # Bouton LANCER (VERT)
        btn_launch = tk.Button(
            button_frame,
            text="▶  LANCER LA DÉTECTION",
            bg="#a6e3a1", fg="#1e1e2e",
            font=("Segoe UI", 12, "bold"),
            relief="flat", padx=25, pady=12,
            cursor="hand2",
            command=self._on_launch
        )
        btn_launch.pack(side="left", padx=8)

        # Bouton RÉINITIALISER
        btn_reset = tk.Button(
            button_frame,
            text="⟳  RÉINITIALISER",
            bg="#585b70", fg="#cdd6f4",
            font=("Segoe UI", 10),
            relief="flat", padx=15, pady=8,
            cursor="hand2",
            command=self._reset_defaults
        )
        btn_reset.pack(side="left", padx=8)

        # Bouton QUITTER (ROUGE)
        btn_quit = tk.Button(
            scrollable_frame,
            text="✖  QUITTER",
            bg="#f38ba8", fg="#1e1e2e",
            font=("Segoe UI", 10),
            relief="flat", padx=20, pady=8,
            cursor="hand2",
            command=self._on_quit
        )
        btn_quit.pack(pady=(0, 20))

    def _label(self, parent, text, small=False):
        return tk.Label(
            parent, text=text,
            bg="#1e1e2e",
            fg="#cdd6f4" if not small else "#a6adc8",
            font=("Segoe UI", 9 if small else 11)
        )

    def _section_title(self, parent, text):
        tk.Label(
            parent, text=text,
            bg="#313244", fg="#cba6f7",
            font=("Segoe UI", 10, "bold"),
            padx=8, pady=4, anchor="w"
        ).pack(fill="x", pady=(12, 4))

    def _slider_row(self, parent, label, from_, to, default, resolution, unit):
        """Ligne : label + slider + valeur numérique."""
        frame = tk.Frame(parent, bg="#1e1e2e")
        frame.pack(fill="x", padx=16, pady=6)

        self._label(frame, label).pack(anchor="w")

        row = tk.Frame(frame, bg="#1e1e2e")
        row.pack(fill="x")

        var = tk.DoubleVar(value=default)
        str_var = tk.StringVar()
        
        val_label = tk.Label(
            row, textvariable=str_var,
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 10, "bold"), width=10, anchor="w"
        )

        def update(*_):
            v = var.get()
            if resolution >= 1:
                str_var.set(f"{int(round(v))} {unit}")
            else:
                str_var.set(f"{v:.2f} {unit}")

        slider = tk.Scale(
            row,
            from_=from_, to=to,
            orient="horizontal",
            variable=var,
            resolution=resolution,
            command=update,
            length=350,
            bg="#1e1e2e", fg="#cdd6f4",
            troughcolor="#313244",
            highlightthickness=0,
            showvalue=0,
            bd=0
        )
        slider.pack(side="left", padx=(0, 6))
        val_label.pack(side="left")

        update()
        return var

    def _reset_defaults(self):
        """Réinitialise tous les curseurs aux valeurs par défaut."""
        self.ear_threshold.set(self.defaults["ear_threshold"])
        self.ear_frames.set(self.defaults["ear_frames"])
        self.mar_threshold.set(self.defaults["mar_threshold"])
        self.moe_threshold.set(self.defaults["moe_threshold"])
        self.first_delay_var.set(self.defaults["first_delay"])
        self.delay_unit_var.set(self.defaults["first_delay_unit"])
        self.alert_interval.set(self.defaults["alert_interval"])
        print("✅ Paramètres réinitialisés")

    def _on_quit(self):
        """Quitte sans lancer."""
        self.config = None
        self.root.destroy()

    def _on_launch(self):
        """Lance la détection avec les paramètres actuels."""
        # Convertir le délai en secondes
        delay_value = int(self.first_delay_var.get())
        delay_unit = self.delay_unit_var.get()
        
        if delay_unit == "sec":
            first_delay_sec = delay_value
        else:
            first_delay_sec = delay_value * 60
        
        self.config = {
            "ear_threshold":      round(self.ear_threshold.get(), 2),
            "ear_frames":         int(self.ear_frames.get()),
            "mar_threshold":      round(self.mar_threshold.get(), 2),
            "moe_threshold":      round(self.moe_threshold.get(), 1),
            "first_delay_sec":    first_delay_sec,
            "alert_interval_sec": int(self.alert_interval.get() * 60),
        }
        
        print("\n" + "="*50)
        print("✅ CONFIGURATION ENREGISTRÉE")
        print("="*50)
        for k, v in self.config.items():
            print(f"   {k} = {v}")
        print("="*50 + "\n")
        print("🎯 Lancement de la détection...\n")
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.config