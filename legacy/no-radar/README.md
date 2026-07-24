# Устаревший DEX bundle NO RADAR

`@since 0.3`

Этот каталог оставлен только как историческая пометка. Формат
`*.dex + assets.zip + *.sha256` больше не является addon API OpenKsenax 0.3.

Актуальная модель поставки — отдельный подписанный Android APK, который владеет
своим UI, разрешениями, сервисами и lifecycle. APK публикуется через GitHub
Releases, а его metadata добавляется в `registry/stable.json`.

Старые DEX-артефакты нельзя возвращать в production registry.

