ROIDMI EVE Plus Control v21.5 - GITHUB AUTO UPDATE
===================================================

Целевой канал:
https://github.com/bedrosov-oss/roidmi-eve-plus-control

Manifest:
https://raw.githubusercontent.com/bedrosov-oss/roidmi-eve-plus-control/main/releases/latest.json

Программа:
- проверяет GitHub через 8 секунд после запуска;
- затем каждые 12 часов;
- сравнивает версии;
- скачивает ZIP потоково;
- обязательно проверяет SHA256;
- устанавливает обновление внешним PowerShell updater;
- новую версию распаковывает в соседнюю папку;
- запускает START_ONE_CLICK.cmd;
- старую версию автоматически не удаляет.

Все пользовательские данные остаются в:
%LOCALAPPDATA%\ROIDMI_EVE_Plus_Control
