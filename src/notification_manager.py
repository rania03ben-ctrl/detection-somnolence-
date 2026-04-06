import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============================================================
#  CONFIGURATION — à remplir avec tes infos
# ============================================================
EMAIL_CONFIG = {
    "sender":   "rania03ben@gmail.com",
    "password": "tkqt nkzd dtns axia",
    "receiver": "benslimarania@gmail.com",
}

SMS_CONFIG = {
    "account_sid": "AC585f55799e869303538a74b1c0aeb635",
    "auth_token":  "8f92111091edf4c67bae06d5ca5601c2",
    "from_number": "+14155238886",   # numéro sandbox WhatsApp Twilio
    "to_number":   "+33745307327",  # numéro du contact d'urgence
}

ALERT_INTERVAL    = 120  # secondes entre deux alertes
FIRST_ALERT_DELAY = 180  # secondes avant la PREMIÈRE alerte (3 min)
# ============================================================
 
 
class NotificationManager:
    def __init__(self, alert_interval=ALERT_INTERVAL, first_alert_delay=FIRST_ALERT_DELAY):
        self.alert_interval    = alert_interval
        self.first_alert_delay = first_alert_delay
        self.last_alert_time   = 0
        self.drowsy_since      = None   # timestamp début de somnolence
        self.first_sent        = False  # première alerte déjà envoyée ?
        self._lock             = threading.Lock()
 
        try:
            from twilio.rest import Client
            self._twilio_client = Client(
                SMS_CONFIG["account_sid"],
                SMS_CONFIG["auth_token"]
            )
            self.twilio_available = True
            print("✅ Twilio initialisé")
        except ImportError:
            self.twilio_available = False
            print("⚠️  Twilio non installé. Lance : pip install twilio")
        except Exception as e:
            self.twilio_available = False
            print(f"⚠️  Twilio erreur : {e}")
 
    def notify_drowsy_start(self):
        """À appeler dès que la somnolence commence."""
        with self._lock:
            if self.drowsy_since is None:
                self.drowsy_since = time.time()
                print("⏳ Somnolence détectée — alerte dans 3 min si ça persiste")
 
    def notify_drowsy_stop(self):
        """À appeler quand la somnolence s'arrête — remet le compteur à zéro."""
        with self._lock:
            self.drowsy_since = None
            self.first_sent   = False
 
    def _can_send(self):
        """Vérifie le délai avant première alerte + intervalle entre alertes."""
        with self._lock:
            now = time.time()
 
            # Pas encore de somnolence enregistrée
            if self.drowsy_since is None:
                return False
 
            # Première alerte : attendre FIRST_ALERT_DELAY secondes
            if not self.first_sent:
                elapsed = now - self.drowsy_since
                if elapsed < self.first_alert_delay:
                    remaining = int(self.first_alert_delay - elapsed)
                    print(f"⏳ Première alerte dans {remaining}s")
                    return False
                self.first_sent      = True
                self.last_alert_time = now
                return True
 
            # Alertes suivantes : respecter ALERT_INTERVAL
            if now - self.last_alert_time >= self.alert_interval:
                self.last_alert_time = now
                return True
 
            remaining = int(self.alert_interval - (now - self.last_alert_time))
            print(f"⏳ Prochaine alerte dans {remaining}s")
            return False
 
    def _send_email(self, subject, body):
        """Envoie un email via Gmail SMTP."""
        try:
            msg = MIMEMultipart()
            msg["From"]    = EMAIL_CONFIG["sender"]
            msg["To"]      = EMAIL_CONFIG["receiver"]
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
 
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
                server.sendmail(
                    EMAIL_CONFIG["sender"],
                    EMAIL_CONFIG["receiver"],
                    msg.as_string()
                )
            print("✅ Email envoyé")
 
        except smtplib.SMTPAuthenticationError:
            print("❌ Email : erreur d'authentification Gmail.")
        except Exception as e:
            print(f"❌ Email erreur : {e}")
 
    def _send_sms(self, body):
        """Envoie un message WhatsApp via Twilio Sandbox."""
        if not self.twilio_available:
            print("❌ WhatsApp non disponible")
            return
        try:
            from twilio.rest import Client
            client = Client(SMS_CONFIG["account_sid"], SMS_CONFIG["auth_token"])
            client.messages.create(
                body=body,
                from_="whatsapp:+14155238886",
                to=f"whatsapp:{SMS_CONFIG['to_number']}"
            )
            print("✅ WhatsApp envoyé")
        except Exception as e:
            print(f"❌ WhatsApp erreur : {e}")
 
    def send_alert(self, alert_type="drowsy", ear=None, tilt=None):
        """Envoie email + WhatsApp si l'intervalle est respecté."""
        if not self._can_send():
            return
 
        timestamp = datetime.now().strftime("%H:%M:%S")
 
        if alert_type == "drowsy":
            subject = "⚠️ ALERTE SOMNOLENCE CONDUCTEUR"
            body = (
                f"🚨 Alerte somnolence détectée à {timestamp}\n\n"
                f"Le conducteur montre des signes de fatigue.\n"
                f"Veuillez vérifier son état immédiatement."
            )
        elif alert_type == "yawn":
            subject = "😴 Bâillement détecté - Conducteur fatigué"
            body = (
                f"Bâillement détecté à {timestamp}.\n"
                f"Le conducteur montre des signes de fatigue légère."
            )
        else:
            subject = "⚠️ Alerte système détection somnolence"
            body    = f"Alerte de type '{alert_type}' détectée à {timestamp}."
 
        threading.Thread(
            target=self._send_both,
            args=(subject, body),
            daemon=True
        ).start()
 
    def _send_both(self, subject, body):
        """Envoie email et WhatsApp en parallèle."""
        t_email = threading.Thread(target=self._send_email, args=(subject, body))
        t_sms   = threading.Thread(target=self._send_sms,   args=(body,))
        t_email.start()
        t_sms.start()
        t_email.join()
        t_sms.join()
 
