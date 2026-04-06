import numpy as np
import math

class HeadAnalyzer:
    def __init__(self):
        # compteur de frames avec tête inclinée
        self.head_tilt_frames = 0

        # seuils
        self.TILT_THRESHOLD = 15          # degré d'inclinaison autorisé
        self.TILT_FRAMES_THRESHOLD = 25   # nb de frames avant alerte

    def calculate_head_pose(self, landmarks):
        """Calcule l'inclinaison (roll) de la tête à partir des yeux."""

        left_eye = landmarks[33]    # coin externe œil gauche
        right_eye = landmarks[263]  # coin externe œil droit

        dx = right_eye.x - left_eye.x
        dy = right_eye.y - left_eye.y

        angle = math.degrees(math.atan2(dy, dx))
        return angle

    def analyze_head_pose(self, landmarks):
        """Analyse la position de la tête"""
        tilt_angle = self.calculate_head_pose(landmarks)

        if abs(tilt_angle) > self.TILT_THRESHOLD:
            self.head_tilt_frames += 1
        else:
            self.head_tilt_frames = max(0, self.head_tilt_frames - 1)

        return tilt_angle

    def get_head_status(self):
        """Retourne le statut de la tête"""

        if self.head_tilt_frames > self.TILT_FRAMES_THRESHOLD:
            return "Tete inclinee - DANGER!", True
        elif self.head_tilt_frames > self.TILT_FRAMES_THRESHOLD // 2:
            return "Tete penchee - Attention", False
        else:
            return "Tete droite - Normal", False
