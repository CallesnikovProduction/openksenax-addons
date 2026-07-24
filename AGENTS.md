# OpenKsenax Add-on Registry

Этот репозиторий хранит публичный каталог автономных addon APK для OpenKsenax.
Он не является монорепозиторием исходников аддонов и не хранит signing keys.

## Инварианты

- OpenKsenax читает только `registry/stable.json`.
- APK публикуются как GitHub Release assets, а не коммитятся в Git.
- Запись добавляется в stable-каталог только после публикации подписанного APK.
- `apkSha256` считается по байтам опубликованного APK.
- `signingCertificateSha256` берётся из сертификата подписи APK.
- Нельзя заменять asset уже опубликованного release-тега: выпускается новая версия.
- Изменения каталога обязаны проходить `tools/validate_catalog.py`.
- Новая документация OpenKsenax 0.3 содержит отметку `@since 0.3`.

