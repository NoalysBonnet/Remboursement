import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)


def envoyer_email_reinitialisation(smtp_config: dict, destinataire_email: str, sujet: str, corps_message: str) -> tuple[
    bool, str]:
    """
    Envoie un email de réinitialisation de mot de passe.
    Retourne (True, "Succès") ou (False, "Message d'erreur").
    """
    if not smtp_config or not all(
            k in smtp_config for k in ['serveur', 'port', 'email_expediteur', 'mot_de_passe_application']):
        logger.error("Configuration SMTP incomplète ou manquante.")
        return False, "Configuration SMTP incomplète ou manquante."

    serveur_smtp = smtp_config['serveur']
    port_smtp = smtp_config.get('port', 587)  # Default au port 587 si non spécifié
    email_expediteur = smtp_config['email_expediteur']
    mot_de_passe_application = smtp_config['mot_de_passe_application']
    use_tls = smtp_config.get('use_tls', True)  # TLS par défaut
    use_ssl = smtp_config.get('use_ssl', False)

    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = destinataire_email
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps_message, 'plain'))

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(serveur_smtp, port_smtp) as server:
                server.ehlo()  # Optionnel, mais peut aider pour certains serveurs
                # server.starttls() # Ne pas utiliser starttls avec SMTP_SSL
                server.login(email_expediteur, mot_de_passe_application)
                server.send_message(msg)
                logger.info(f"Email de réinitialisation (via SSL) envoyé avec succès à {destinataire_email}.")
        elif use_tls:
            with smtplib.SMTP(serveur_smtp, port_smtp) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()  # Re-ehlo après starttls
                server.login(email_expediteur, mot_de_passe_application)
                server.send_message(msg)
                logger.info(f"Email de réinitialisation (via TLS) envoyé avec succès à {destinataire_email}.")
        else:  # Connexion non sécurisée (non recommandé)
            with smtplib.SMTP(serveur_smtp, port_smtp) as server:
                server.login(email_expediteur, mot_de_passe_application)
                server.send_message(msg)
                logger.info(f"Email de réinitialisation (non sécurisé) envoyé avec succès à {destinataire_email}.")

        return True, "Email de réinitialisation envoyé avec succès."

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erreur d'authentification SMTP: {e}")
        return False, "Erreur d'authentification SMTP. Vérifiez l'email et le mot de passe d'application."
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"Déconnexion du serveur SMTP: {e}")
        return False, "Le serveur SMTP s'est déconnecté de manière inattendue."
    except smtplib.SMTPConnectError as e:
        logger.error(f"Erreur de connexion SMTP au serveur {serveur_smtp}:{port_smtp} : {e}")
        return False, f"Impossible de se connecter au serveur SMTP ({serveur_smtp}:{port_smtp}). Vérifiez l'adresse et le port."
    except smtplib.SMTPException as e:
        logger.error(f"Erreur SMTP générale: {e}", exc_info=True)
        return False, f"Une erreur SMTP générale est survenue: {e}"
    except ConnectionRefusedError as e:  # Souvent lié au serveur/port incorrect ou pare-feu
        logger.error(f"Connexion refusée par le serveur SMTP {serveur_smtp}:{port_smtp} : {e}")
        return False, f"Connexion refusée par le serveur SMTP ({serveur_smtp}:{port_smtp}). Vérifiez l'adresse, le port et le pare-feu."
    except TimeoutError as e:
        logger.error(f"Timeout lors de la connexion au serveur SMTP {serveur_smtp}:{port_smtp} : {e}")
        return False, f"Timeout lors de la connexion au serveur SMTP ({serveur_smtp}:{port_smtp})."
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'envoi de l'email: {e}", exc_info=True)
        return False, f"Une erreur inattendue est survenue: {e}"