import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
import threading
import time
from utils import initialize_face_mesh
from eye_analyzer import EyeAnalyzer
from mouth_analyzer import MouthAnalyzer


CALIBRATION_DURATION = 10  # secondes


class CalibrationScreen:
    """Fenêtre de compte à rebours pendant la calibration."""

    def __init__(self, duration=CALIBRATION_DURATION):
        self.duration = duration
        self.root = tk.Tk()
        self.root.title("Calibration")
        self.root.geometry("400x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")
        self.root.attributes("-topmost", True)

        tk.Label(
            self.root, text="🎯 Calibration en cours...",
            bg="#1e1e2e", fg="#cba6f7",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(24, 4))

        tk.Label(
            self.root,
            text="Regardez la caméra, yeux ouverts,\nvisage droit et expression neutre.",
            bg="#1e1e2e", fg="#a6adc8",
            font=("Segoe UI", 10), justify="center"
        ).pack(pady=(0, 12))

        self.countdown_var = tk.StringVar(value=f"{duration}s")
        tk.Label(
            self.root, textvariable=self.countdown_var,
            bg="#1e1e2e", fg="#a6e3a1",
            font=("Segoe UI", 32, "bold")
        ).pack()

        self.status_var = tk.StringVar(value="Démarrage...")
        tk.Label(
            self.root, textvariable=self.status_var,
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 9)
        ).pack(pady=8)

    def update(self, remaining, faces_detected):
        """Met à jour le compte à rebours."""
        self.countdown_var.set(f"{remaining}s")
        if faces_detected:
            self.status_var.set("✅ Visage détecté — collecte en cours")
        else:
            self.status_var.set("⚠️  Aucun visage détecté — repositionnez-vous")
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass


class Calibrator:
    """Lance la calibration et retourne les seuils adaptés."""

    def __init__(self):
        self.face_mesh    = initialize_face_mesh()
        self.eye_analyzer = EyeAnalyzer()
        self.mouth_analyzer = MouthAnalyzer()

    def run(self):
        """
        Ouvre la caméra + fenêtre de calibration pendant CALIBRATION_DURATION s.
        Retourne un dict de seuils calculés, ou None si annulé.
        """
        screen = CalibrationScreen(CALIBRATION_DURATION)
        cap    = cv2.VideoCapture(0)

        ear_values = []
        mar_values = []
        start_time = time.time()

        print("🎯 Calibration démarrée — restez neutre devant la caméra")

        while True:
            elapsed   = time.time() - start_time
            remaining = max(0, int(CALIBRATION_DURATION - elapsed))

            if elapsed >= CALIBRATION_DURATION:
                break

            success, frame = cap.read()
            if not success:
                continue

            frame     = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            results   = self.face_mesh.detect(mp_image)

            face_found = bool(results.face_landmarks)

            if face_found:
                landmarks = results.face_landmarks[0]
                avg_ear, _, _ = self.eye_analyzer.analyze_eyes(landmarks)
                mar           = self.mouth_analyzer.calculate_mar(landmarks)
                if avg_ear > 0.1:   # ignore les frames aberrantes
                    ear_values.append(avg_ear)
                if mar > 0:
                    mar_values.append(mar)

            # Affichage caméra avec overlay
            cv2.putText(frame, f"Calibration : {remaining}s", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2)
            cv2.putText(frame, "Yeux ouverts - Expression neutre", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
            if ear_values:
                cv2.putText(frame, f"EAR actuel : {ear_values[-1]:.3f}", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 220, 255), 1)
            cv2.imshow("Calibration", frame)

            screen.update(remaining, face_found)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC annule
                break

        cap.release()
        cv2.destroyWindow("Calibration")
        screen.close()

        if len(ear_values) < 10:
            print("⚠️  Pas assez de données — utilisation des seuils par défaut")
            return None

        return self._compute_thresholds(ear_values, mar_values)

    def _compute_thresholds(self, ear_values, mar_values):
        """Calcule les seuils à partir des valeurs collectées."""
        ear_mean = np.mean(ear_values)
        ear_std  = np.std(ear_values)
        mar_mean = np.mean(mar_values) if mar_values else 0.3

        # Seuil EAR = moyenne - 2 écarts-types (yeux à moitié fermés)
        ear_threshold = round(max(0.15, ear_mean - 2 * ear_std), 2)

        # Seuil MAR = moyenne * 2 (bouche bien ouverte = bâillement)
        mar_threshold = round(min(0.85, mar_mean * 2.0), 2)

        result = {
            "ear_threshold": ear_threshold,
            "ear_frames":    20,
            "mar_threshold": mar_threshold,
            "moe_threshold": 2.5,
        }

        print(f"✅ Calibration terminée :")
        print(f"   EAR moyen        = {ear_mean:.3f}")
        print(f"   EAR seuil calculé = {ear_threshold:.3f}")
        print(f"   MAR moyen        = {mar_mean:.3f}")
        print(f"   MAR seuil calculé = {mar_threshold:.3f}")

        return result