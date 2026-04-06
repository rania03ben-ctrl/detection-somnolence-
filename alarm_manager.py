import threading
import time

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️  pygame non installé. Lance : pip install pygame")


def generate_beep_sound(frequency=880, duration=0.5, volume=0.8):
    """Génère un son beep synthétique sans fichier audio externe."""
    import numpy as np
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    wave = (np.sin(2 * np.pi * frequency * t) * volume * 32767).astype(np.int16)
    # Fade out pour éviter le clic
    fade = int(sample_rate * 0.05)
    wave[-fade:] = (wave[-fade:] * np.linspace(1, 0, fade)).astype(np.int16)
    return wave


class AlarmManager:
    def __init__(self):
        self.alarm_thread = None
        self.alarm_running = False
        self._sound_cache = {}

        if PYGAME_AVAILABLE:
            self._prepare_sounds()

    def _prepare_sounds(self):
        """Prépare les sons à l'avance pour éviter la latence."""
        import numpy as np

        # Son somnolence : beep grave répété
        wave_drowsy = generate_beep_sound(frequency=660, duration=0.4)
        stereo = np.column_stack([wave_drowsy, wave_drowsy])
        self._sound_cache['drowsy'] = pygame.sndarray.make_sound(stereo)
        self._sound_cache['drowsy'].set_volume(0.8)

        # Son bâillement : bip court aigu
        wave_yawn = generate_beep_sound(frequency=1000, duration=0.2)
        stereo2 = np.column_stack([wave_yawn, wave_yawn])
        self._sound_cache['yawn'] = pygame.sndarray.make_sound(stereo2)
        self._sound_cache['yawn'].set_volume(0.5)

        # Son visage perdu : double bip
        wave_lost = generate_beep_sound(frequency=440, duration=0.15)
        stereo3 = np.column_stack([wave_lost, wave_lost])
        self._sound_cache['lost'] = pygame.sndarray.make_sound(stereo3)
        self._sound_cache['lost'].set_volume(0.6)

    def _alarm_loop(self, alarm_type):
        """Boucle d'alarme qui tourne dans un thread séparé."""
        while self.alarm_running:
            if PYGAME_AVAILABLE and alarm_type in self._sound_cache:
                self._sound_cache[alarm_type].play()
                time.sleep(0.6 if alarm_type == 'drowsy' else 0.4)
            else:
                # Fallback console si pygame absent
                print(f"\a⚠️  ALARME : {alarm_type.upper()}")
                time.sleep(1.0)

    def start_alarm(self, alarm_type='drowsy'):
        """Démarre l'alarme dans un thread (non bloquant)."""
        if self.alarm_running:
            return  # Déjà active
        self.alarm_running = True
        self.alarm_thread = threading.Thread(
            target=self._alarm_loop,
            args=(alarm_type,),
            daemon=True
        )
        self.alarm_thread.start()

    def stop_alarm(self):
        """Arrête l'alarme proprement."""
        self.alarm_running = False
        if PYGAME_AVAILABLE:
            pygame.mixer.stop()

    def beep_once(self, alarm_type='yawn'):
        """Joue un son unique (bâillement, visage perdu...)."""
        if PYGAME_AVAILABLE and alarm_type in self._sound_cache:
            self._sound_cache[alarm_type].play()
        else:
            print(f"\a[{alarm_type}]")

    def cleanup(self):
        """À appeler à la fin du programme."""
        self.stop_alarm()
        if PYGAME_AVAILABLE:
            pygame.mixer.quit()