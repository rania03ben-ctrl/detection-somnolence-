import cv2
import mediapipe as mp
import numpy as np
from utils import initialize_face_mesh, draw_landmarks
from eye_analyzer import EyeAnalyzer
from head_analyzer import HeadAnalyzer
from mouth_analyzer import MouthAnalyzer             # NOUVEAU
from alarm_manager import AlarmManager               # NOUVEAU
from notification_manager import NotificationManager # NOUVEAU
from config_interface import ConfigInterface         # NOUVEAU
from calibration import Calibrator                   # NOUVEAU


class DrowsinessDetector:
    def __init__(self, config=None):
        self.face_mesh      = initialize_face_mesh()
        self.eye_analyzer   = EyeAnalyzer()
        self.head_analyzer  = HeadAnalyzer()
        self.mouth_analyzer = MouthAnalyzer()
        self.alarm          = AlarmManager()
        self.alarm_active   = False

        # Applique la config si fournie
        if config:
            self.eye_analyzer.EAR_THRESHOLD             = config["ear_threshold"]
            self.eye_analyzer.CLOSED_FRAMES_THRESHOLD   = config["ear_frames"]
            self.mouth_analyzer.MAR_THRESHOLD           = config["mar_threshold"]
            self.mouth_analyzer.MOE_THRESHOLD           = config["moe_threshold"]
            self.notifier = NotificationManager(
                alert_interval=config["alert_interval_sec"],
                first_alert_delay=config["first_delay_sec"]
            )
        else:
            self.notifier = NotificationManager()

    def display_info(self, image, eye_status, head_status, mouth_status,
                     avg_ear, tilt_angle, mar, moe):
        """Affiche les informations sur l'image."""

        # --- Yeux ---
        color_eyes = (
            (0, 0, 255) if "SOMNOLENCE" in eye_status
            else (0, 255, 255) if "Attention" in eye_status
            else (255, 255, 255)
        )
        cv2.putText(image, f"Yeux: {eye_status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_eyes, 2)

        # --- Tête ---
        color_head = (
            (0, 0, 255) if "DANGER" in head_status
            else (0, 255, 255) if "Attention" in head_status
            else (255, 255, 255)
        )
        cv2.putText(image, f"Tete: {head_status}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_head, 2)

        # --- Bouche / Bâillement ---           NOUVEAU
        color_mouth = (
            (0, 165, 255) if "Baillement" in mouth_status
            else (0, 255, 255) if "Attention" in mouth_status
            else (255, 255, 255)
        )
        cv2.putText(image, f"Bouche: {mouth_status}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_mouth, 2)

        # --- Métriques ---
        cv2.putText(image, f"EAR: {avg_ear:.3f}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(image, f"MAR: {mar:.3f}  MOE: {moe:.2f}", (10, 140),  # NOUVEAU
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(image, f"Inclinaison: {tilt_angle:.1f}deg", (10, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(image,
                    f"Frames yeux fermes: {self.eye_analyzer.eye_closed_frames}",
                    (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(image,                                                    # NOUVEAU
                    f"Baillement(s): {self.mouth_analyzer.yawn_count}",
                    (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)

    def trigger_visual_alarm(self, image):
        """Déclenche une alarme visuelle (rectangle rouge clignotant)."""
        if cv2.getTickCount() % 20 > 10:
            cv2.rectangle(image, (0, 0),
                          (image.shape[1], image.shape[0]), (0, 0, 255), 10)
        cv2.putText(image, "ALARME! SOMNOLENCE DETECTEE!",
                    (50, image.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    def trigger_yawn_visual(self, image):
        """Affichage discret pour le bâillement (pas d'alarme rouge)."""       # NOUVEAU
        cv2.putText(image, "BAILLEMENT DETECTE",
                    (50, image.shape[0] // 2 + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)

    def run(self):
        """Lance la détection en temps réel."""
        cap = cv2.VideoCapture(0)

        print("Démarrage de la détection de somnolence...")
        print("Appuyez sur 'ESC' pour quitter")
        print("Appuyez sur 'r' pour réinitialiser les compteurs")

        try:
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    print("Erreur de lecture caméra")
                    continue

                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
                results   = self.face_mesh.detect(mp_image)

                if results.face_landmarks:
                    landmarks = results.face_landmarks[0]

                    # -------- Yeux --------
                    avg_ear, left_ear, right_ear = self.eye_analyzer.analyze_eyes(landmarks)
                    eye_status, eye_drowsy = self.eye_analyzer.get_eye_status()

                    # Adaptation lunettes
                    detected_glasses = self.eye_analyzer.wearing_glasses()
                    if detected_glasses:
                        self.eye_analyzer.EAR_THRESHOLD        = 0.20
                        self.eye_analyzer.CLOSED_FRAMES_THRESHOLD = 25
                        cv2.putText(image, "LUNETTES DETECTEES", (10, 230),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    else:
                        self.eye_analyzer.EAR_THRESHOLD        = 0.25
                        self.eye_analyzer.CLOSED_FRAMES_THRESHOLD = 20

                    # -------- Tête --------
                    tilt_angle = self.head_analyzer.analyze_head_pose(landmarks)
                    head_status, head_drowsy = self.head_analyzer.get_head_status()

                    # -------- Bouche / Bâillement --------   NOUVEAU
                    mar, moe = self.mouth_analyzer.analyze_mouth(landmarks, avg_ear)
                    mouth_status, yawn_detected = self.mouth_analyzer.get_mouth_status()

                    # -------- Affichage --------
                    self.display_info(image, eye_status, head_status, mouth_status,
                                      avg_ear, tilt_angle, mar, moe)

                    # -------- Alarmes --------
                    if eye_drowsy or head_drowsy:
                        self.trigger_visual_alarm(image)
                        if not self.alarm_active:
                            self.alarm.start_alarm('drowsy')
                        self.notifier.notify_drowsy_start()          # début somnolence
                        self.notifier.send_alert('drowsy', ear=avg_ear, tilt=tilt_angle)
                        self.alarm_active = True

                    elif yawn_detected:
                        self.trigger_yawn_visual(image)
                        self.alarm.beep_once('yawn')
                        self.notifier.send_alert('yawn')
                        if self.alarm_active:
                            self.alarm.stop_alarm()
                            self.notifier.notify_drowsy_stop()        # fin somnolence
                            self.alarm_active = False

                    else:
                        if self.alarm_active:
                            self.alarm.stop_alarm()
                            self.notifier.notify_drowsy_stop()        # fin somnolence
                        self.alarm_active = False

                else:
                    cv2.putText(image, "Aucun visage detecte", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if self.alarm_active:                  # NOUVEAU
                        self.alarm.stop_alarm()
                        self.alarm_active = False

                # Affichage des touches disponibles
                h = image.shape[0]
                cv2.putText(image, "ESC: quitter | R: reset | C: config",
                            (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.45, (150, 150, 150), 1)

                cv2.imshow('Detection de Somnolence', image)

                key = cv2.waitKey(5) & 0xFF
                if key == 27:   # ESC
                    break
                elif key == ord('c') or key == ord('C'):  # Reconfigurer
                    cv2.destroyAllWindows()
                    self.alarm.stop_alarm()
                    ui = ConfigInterface()
                    new_config = ui.run()
                    if new_config:
                        self.eye_analyzer.EAR_THRESHOLD           = new_config["ear_threshold"]
                        self.eye_analyzer.CLOSED_FRAMES_THRESHOLD = new_config["ear_frames"]
                        self.mouth_analyzer.MAR_THRESHOLD         = new_config["mar_threshold"]
                        self.mouth_analyzer.MOE_THRESHOLD         = new_config["moe_threshold"]
                        self.notifier = NotificationManager(
                            alert_interval=new_config["alert_interval_sec"],
                            first_alert_delay=new_config["first_delay_sec"]
                        )
                        print("✅ Configuration mise à jour")
                elif key == ord('r'):
                    self.eye_analyzer.eye_closed_frames  = 0
                    self.head_analyzer.head_tilt_frames  = 0
                    self.mouth_analyzer.yawn_frames      = 0
                    self.mouth_analyzer.yawn_count       = 0
                    print("Compteurs réinitialisés")

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.alarm.cleanup()   # NOUVEAU : nettoyage propre
            print("Détection terminée")


if __name__ == "__main__":
    # 1. Calibration automatique
    print("🎯 Lancement de la calibration...")
    calibrator = Calibrator()
    calibrated = calibrator.run()   # None si pas assez de données

    # 2. Interface de configuration (pré-remplie avec les seuils calibrés)
    ui = ConfigInterface(calibrated=calibrated)
    config = ui.run()

    if config is None:
        print("Configuration annulée.")
    else:
        # 3. Lancement de la détection
        detector = DrowsinessDetector(config)
        detector.run()