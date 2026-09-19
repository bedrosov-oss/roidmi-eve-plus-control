# ROIDMI EVE Plus Control

Windows control application for `roidmi.vacuum.v60` / ROIDMI EVE Plus.

## v21.6 - automatic login, IP and token recovery

The application now automatically tries to restore the vacuum connection at startup:

- shared `%LOCALAPPDATA%\\ROIDMI_EVE_Plus_Control\\AUTO_CONFIG.json`;
- older unpacked versions on Desktop, Downloads, Documents, or a sibling folder;
- an already-authorized Xiaomi Cloud session;
- Xiaomi Cloud device lookup by model `roidmi.vacuum.v60` to recover the token;
- Xiaomi Cloud local IP when available;
- miIO UDP 54321 discovery when DHCP changed the robot IP.

After a successful connection, current IP/token/DID/region are persisted in LocalAppData.

A completely new installation with neither an old config nor a valid Xiaomi Cloud session still requires one successful Xiaomi Cloud login. An unauthenticated LAN handshake cannot reveal the miIO token.

## Automatic updates

The application reads `releases/latest.json`, downloads
`dist/ROIDMI_EVE_Plus_Control_Windows_latest.zip`, verifies SHA256, and then offers installation.

## Privacy

This repository must not contain Xiaomi passwords, service tokens, robot tokens,
cloud sessions, SMTP App Passwords, apartment maps, personal profiles, or history databases.
