import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM")
FRONTEND_URL = (os.getenv("FRONTEND_URL") or "").rstrip("/")


def safe_send(to_email: str, subject: str, html: str) -> None:
    if not to_email:
        return

    params: resend.Emails.SendParams = {
        "from": MAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    try:
        resend.Emails.send(params)
    except Exception as exc:
        print(f"Email send failed to {to_email}: {exc}")


def send_join_request_confirmation_to_player(player_email: str, player_name: str, club_name: str, club_id: int):
    name = player_name or "there"
    club_url = f"{FRONTEND_URL}/clubs/{club_id}"
    safe_send(
        to_email=player_email,
        subject=f"Join request sent to {club_name}",
        html=(
            f"<p>Hi {name},</p>"
            f"<p>Your request to join <strong>{club_name}</strong> was sent successfully.</p>"
            f'<p>You can view the club here: <a href="{club_url}">{club_name}</a></p>'
        ),
    )


def send_join_request_notification_to_owner(owner_email: str, owner_name: str, player_name: str, club_name: str, club_id: int):
    name = owner_name or "there"
    dashboard_url = f"{FRONTEND_URL}/dashboard"
    safe_send(
        to_email=owner_email,
        subject=f"New join request for {club_name}",
        html=(
            f"<p>Hi {name},</p>"
            f"<p><strong>{player_name}</strong> requested to join <strong>{club_name}</strong>.</p>"
            f'<p>Review it in your dashboard: <a href="{dashboard_url}">Open Dashboard</a></p>'
            f"<p>Club ID: {club_id}</p>"
        ),
    )


def send_join_request_decision_to_player(player_email: str, player_name: str, club_name: str, decision: str, club_id: int) -> None:
    name = player_name or "there"
    normalized_decision = (decision or "").lower()
    decision_label = "approved" if normalized_decision == "approved" else "rejected"
    club_url = f"{FRONTEND_URL}/clubs/{club_id}"
    safe_send(
        to_email=player_email,
        subject=f"Your join request was {decision_label}",
        html=(
            f"<p>Hi {name},</p>"
            f"<p>Your join request for <strong>{club_name}</strong> was <strong>{decision_label}</strong>.</p>"
            f'<p>Club page: <a href="{club_url}">{club_name}</a></p>'
        ),
    )
