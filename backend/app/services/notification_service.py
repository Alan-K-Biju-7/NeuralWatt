import aiohttp
import aiosmtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from app.core.config import settings
from app.models.alert_config import AlertConfigDocument
from app.models.anomaly import AnomalyDocument

logger = logging.getLogger(__name__)


def _build_email_html(anomaly: AnomalyDocument) -> str:
    severity_colors = {
        "low":    "#d19900",
        "medium": "#da7101",
        "high":   "#a12c7b",
    }
    color = severity_colors.get(anomaly.severity.value, "#a12c7b")
    detected_at = anomaly.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""
    <html>
    <body style="font-family:sans-serif;background:#f7f6f2;padding:32px;">
      <div style="max-width:560px;margin:auto;background:#fff;border-radius:12px;
                  padding:32px;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
        <h2 style="margin:0 0 8px;color:#28251d;">⚡ NeuralWatt Alert</h2>
        <span style="display:inline-block;padding:4px 12px;border-radius:999px;
                     background:{color};color:#fff;font-size:13px;font-weight:600;
                     text-transform:uppercase;letter-spacing:0.05em;">
          {anomaly.severity.value} anomaly
        </span>

        <hr style="margin:24px 0;border:none;border-top:1px solid #dcd9d5;" />

        <table style="width:100%;border-collapse:collapse;font-size:15px;">
          <tr>
            <td style="padding:8px 0;color:#7a7974;width:160px;">Device ID</td>
            <td style="padding:8px 0;color:#28251d;font-family:monospace;">
              {anomaly.device_id}
            </td>
          </tr>
          <tr style="background:#f7f6f2;">
            <td style="padding:8px 6px;color:#7a7974;">Actual watts</td>
            <td style="padding:8px 6px;color:#28251d;font-weight:600;">
              {anomaly.watts:.1f} W
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#7a7974;">Expected watts</td>
            <td style="padding:8px 0;color:#28251d;">{anomaly.expected_watts:.1f} W</td>
          </tr>
          <tr style="background:#f7f6f2;">
            <td style="padding:8px 6px;color:#7a7974;">Deviation</td>
            <td style="padding:8px 6px;color:{color};font-weight:600;">
              {anomaly.deviation_pct:+.1f}%
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#7a7974;">Detected at</td>
            <td style="padding:8px 0;color:#28251d;">{detected_at}</td>
          </tr>
        </table>

        <hr style="margin:24px 0;border:none;border-top:1px solid #dcd9d5;" />
        <p style="margin:0;font-size:13px;color:#bab9b4;">
          NeuralWatt · Automated energy anomaly alert
        </p>
      </div>
    </body>
    </html>
    """


async def send_email_alert(
    to_address: str,
    anomaly: AnomalyDocument,
) -> None:
    subject = (
        f"[NeuralWatt] {anomaly.severity.value.upper()} Anomaly — "
        f"{anomaly.watts:.0f}W detected on device {anomaly.device_id[:8]}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.smtp_from
    msg["To"]      = to_address

    plain = (
        f"NeuralWatt Anomaly Alert\n\n"
        f"Severity : {anomaly.severity.value.upper()}\n"
        f"Device   : {anomaly.device_id}\n"
        f"Watts    : {anomaly.watts:.1f}W  (expected {anomaly.expected_watts:.1f}W)\n"
        f"Deviation: {anomaly.deviation_pct:+.1f}%\n"
        f"Detected : {anomaly.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_email_html(anomaly), "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info(f"Email alert sent to {to_address} for anomaly {anomaly._id}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")


async def send_webhook_alert(
    webhook_url: str,
    anomaly: AnomalyDocument,
    config: AlertConfigDocument,
) -> None:
    payload = {
        "event":          "anomaly.detected",
        "severity":       anomaly.severity.value,
        "device_id":      anomaly.device_id,
        "household_id":   anomaly.household_id,
        "reading_id":     anomaly.reading_id,
        "watts":          anomaly.watts,
        "expected_watts": anomaly.expected_watts,
        "deviation_pct":  anomaly.deviation_pct,
        "message":        anomaly.message,
        "detected_at":    anomaly.detected_at.isoformat(),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Content-Type": "application/json", "User-Agent": "NeuralWatt/1.0"},
            ) as resp:
                if resp.status >= 400:
                    logger.warning(
                        f"Webhook {webhook_url} returned HTTP {resp.status}"
                    )
                else:
                    logger.info(
                        f"Webhook alert sent to {webhook_url} "
                        f"(status {resp.status}) for anomaly {anomaly._id}"
                    )
    except Exception as e:
        logger.error(f"Failed to send webhook alert to {webhook_url}: {e}")


async def dispatch_alerts(
    anomaly: AnomalyDocument,
    configs: list[AlertConfigDocument],
) -> None:
    """Fire all enabled channels for every matching alert config."""
    severity_rank = {"low": 1, "medium": 2, "high": 3}
    anomaly_rank  = severity_rank.get(anomaly.severity.value, 0)

    for cfg in configs:
        threshold_rank = severity_rank.get(cfg.severity_threshold.value, 3)
        if anomaly_rank < threshold_rank:
            logger.info(
                "Alert skipped by threshold | device=%s | anomaly=%s | threshold=%s",
                anomaly.device_id,
                anomaly.severity.value,
                cfg.severity_threshold.value,
            )
            continue  # anomaly below this config's threshold — skip

        if cfg.email_enabled and cfg.email_address:
            await send_email_alert(cfg.email_address, anomaly)

        if cfg.webhook_enabled and cfg.webhook_url:
            await send_webhook_alert(str(cfg.webhook_url), anomaly, cfg)
