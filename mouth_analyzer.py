import numpy as np


class MouthAnalyzer:
    def __init__(self):
        self.MOUTH_LEFT   = 61
        self.MOUTH_RIGHT  = 291
        self.MOUTH_TOP    = 13
        self.MOUTH_BOTTOM = 14
        self.MOUTH_TOP2   = 312
        self.MOUTH_BOT2   = 317

        # Seuils
        self.MAR_THRESHOLD         = 0.6   # bouche ouverte
        self.MOE_THRESHOLD         = 2.5   # vrai bâillement (à ajuster)
        self.YAWN_FRAMES_THRESHOLD = 15    # frames consécutives avant alerte

        # Compteurs
        self.yawn_frames = 0
        self.yawn_count  = 0
        self.last_moe    = 0.0

    def calculate_mar(self, landmarks):
        """Calcule le Mouth Aspect Ratio (MAR)."""
        def pt(idx):
            p = landmarks[idx]
            return np.array([p.x, p.y])

        left   = pt(self.MOUTH_LEFT)
        right  = pt(self.MOUTH_RIGHT)
        top    = pt(self.MOUTH_TOP)
        bottom = pt(self.MOUTH_BOTTOM)
        top2   = pt(self.MOUTH_TOP2)
        bot2   = pt(self.MOUTH_BOT2)

        horizontal = np.linalg.norm(right - left)
        if horizontal == 0:
            return 0.0

        vertical1 = np.linalg.norm(bottom - top)
        vertical2 = np.linalg.norm(bot2 - top2)

        return (vertical1 + vertical2) / (2.0 * horizontal)

    def calculate_moe(self, mar, ear):
        """MOE = MAR / EAR — amplifie le signal bâillement."""
        if ear == 0:
            return 0.0
        return mar / ear

    def analyze_mouth(self, landmarks, ear):
        """
        Analyse la bouche en utilisant le MOE pour filtrer les faux positifs.
        Vrai bâillement = MAR élevé ET MOE élevé (yeux qui se ferment un peu).
        """
        mar = self.calculate_mar(landmarks)
        moe = self.calculate_moe(mar, ear)
        self.last_moe = moe

        # Condition double : bouche ouverte ET MOE élevé
        is_yawning = mar > self.MAR_THRESHOLD and moe > self.MOE_THRESHOLD

        if is_yawning:
            self.yawn_frames += 1
        else:
            if self.yawn_frames > self.YAWN_FRAMES_THRESHOLD:
                self.yawn_count += 1
            self.yawn_frames = max(0, self.yawn_frames - 1)

        return mar, moe

    def get_mouth_status(self):
        """Retourne le statut de la bouche."""
        if self.yawn_frames > self.YAWN_FRAMES_THRESHOLD:
            return "Baillement detecte!", True
        elif self.yawn_frames > self.YAWN_FRAMES_THRESHOLD // 2:
            return "Bouche ouverte - Attention", False
        else:
            return "Bouche fermee - Normal", False