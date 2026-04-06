import numpy as np


class EyeAnalyzer:
    def __init__(self):
        # Points spécifiques pour le calcul EAR
        # Indices des points MediaPipe nécessaires au calcul
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]

        # Compteur de frames consécutives où les yeux sont fermés
        self.eye_closed_frames = 0

        # Seuils de base (mode normal, sans lunettes)
        self.EAR_THRESHOLD = 0.25          # en-dessous de ce seuil → œil considéré fermé
        self.CLOSED_FRAMES_THRESHOLD = 20  # nombre de frames avant alarme

        # Compter combien de frames où l'EAR est très bas (pour détecter les lunettes)
        self.low_ear_frames = 0

    def calculate_ear(self, landmarks, eye_points):
        """Calcule le Eye Aspect Ratio (EAR) pour un œil."""
        points = []
        for point_idx in eye_points:
            point = landmarks[point_idx]  # récupération du point MediaPipe
            points.append((point.x, point.y))

        # Calcul des distances verticales
        vertical1 = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
        vertical2 = np.linalg.norm(np.array(points[2]) - np.array(points[4]))

        # Calcul de la distance horizontale
        horizontal = np.linalg.norm(np.array(points[0]) - np.array(points[3]))

        if horizontal == 0:
            return 0.0  # évite une division par zéro

        # EAR = (somme des distances verticales) / (2 * distance horizontale)
        ear = (vertical1 + vertical2) / (2.0 * horizontal)
        return ear

    def analyze_eyes(self, landmarks):
        """Analyse l'état des yeux et détecte la fermeture."""
        left_ear = self.calculate_ear(landmarks, self.LEFT_EYE_POINTS)
        right_ear = self.calculate_ear(landmarks, self.RIGHT_EYE_POINTS)

        avg_ear = (left_ear + right_ear) / 2.0

        # Détection de "lunettes probables" : EAR souvent très bas même yeux ouverts
        if avg_ear < 0.22:  # valeur à ajuster après tests
            self.low_ear_frames += 1
        else:
            self.low_ear_frames = max(0, self.low_ear_frames - 1)

        # Détection de fermeture des yeux (somnolence)
        if avg_ear < self.EAR_THRESHOLD:
            self.eye_closed_frames += 1
        else:
            # On décrémente sans descendre en dessous de 0
            self.eye_closed_frames = max(0, self.eye_closed_frames - 1)

        return avg_ear, left_ear, right_ear

    def wearing_glasses(self):
        """Retourne True si la personne porte probablement des lunettes."""
        # Si plus de 40 frames avec un EAR très bas → lunettes probables
        return self.low_ear_frames > 40

    def get_eye_status(self):
        """Retourne le statut des yeux basé sur les frames accumulés."""
        if self.eye_closed_frames > self.CLOSED_FRAMES_THRESHOLD:
            return "SOMNOLENCE DETECTEE!", True
        elif self.eye_closed_frames > self.CLOSED_FRAMES_THRESHOLD // 2:
            return "Attention! Fatigue detectee", False
        else:
            return "Yeux ouverts - Normal", False
