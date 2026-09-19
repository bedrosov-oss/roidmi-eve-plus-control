# ROIDMI EVE Plus Control

Windows control application for `roidmi.vacuum.v60`.

## Automatic updates

The application reads `releases/latest.json` and downloads
`dist/ROIDMI_EVE_Plus_Control_Windows_latest.zip`.

Every package is verified by SHA256 before installation.

## Privacy

Never commit user secrets or runtime data:
`AUTO_CONFIG.json`, `CLOUD_SESSION.json`, `PRIVATE_NOTIFY_CONFIG.json`,
robot token, Xiaomi credentials, SMTP App Password, apartment maps,
`history.sqlite3`, personal profiles.

User data stays in `%LOCALAPPDATA%\ROIDMI_EVE_Plus_Control`.
