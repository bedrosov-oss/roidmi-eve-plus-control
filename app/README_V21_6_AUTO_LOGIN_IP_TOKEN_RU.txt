ROIDMI EVE Plus Control v21.6 - AUTO LOGIN IP + TOKEN
=======================================================

IP и token больше не обязаны быть заполнены заранее.

Автовход:
1. Проверяет LocalAppData/AUTO_CONFIG.json.
2. Ищет AUTO_CONFIG.json в старых версиях рядом с программой, на Desktop, Downloads и Documents.
3. Если token не найден, использует действующую Xiaomi Cloud session без повторного ввода пароля.
4. Ищет модель roidmi.vacuum.v60 и восстанавливает token/DID/region/local IP.
5. Если IP изменился по DHCP, выполняет miIO UDP 54321 discovery и проверяет устройство реальным token.
6. Сохраняет актуальные IP/token в LocalAppData.
7. Следующий запуск выполняется автоматически.

Ограничение: token нельзя извлечь из неавторизованного UDP handshake. На полностью новой установке без старой конфигурации и без действующей Xiaomi Cloud session потребуется один успешный вход Xiaomi Cloud.
