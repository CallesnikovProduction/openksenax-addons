# Публикация addon APK

`@since 0.3`

## Порядок выпуска

1. Соберите release APK аддона с постоянным signing key.
2. Проверьте `applicationId`, `versionCode`, `versionName` и `minSdk`.
3. Запустите `tools/prepare_addon_release.ps1`: он читает package/version/minSdk,
   вычисляет размер и SHA-256 файла, а signer берёт из `apksigner`.
4. Создайте неизменяемый GitHub Release и загрузите APK как asset.
5. Убедитесь, что release URL доступен по HTTPS.
6. Только после этого добавьте или обновите запись в `registry/stable.json`.
7. Обновите `generatedAtEpochMillis`.
8. Запустите локальный validator и отправьте отдельный commit/PR каталога.

APK не коммитится в Git. Рекомендуемое имя:

```text
no-radar-v1.0.0.apk
```

Рекомендуемый release tag:

```text
no-radar-v1.0.0
```

## Получение контрольных значений в PowerShell

```powershell
.\tools\prepare_addon_release.ps1 `
  -ApkPath .\no-radar-v1.0.0.apk `
  -AddonId dev.openksenax.addon.no-radar `
  -DisplayName "NO RADAR" `
  -ShortDescription "Локальный фоновый автоответчик" `
  -ApkUrl "https://github.com/CallesnikovProduction/openksenax-addons/releases/download/no-radar-v1.0.0/no-radar-v1.0.0.apk" `
  -RepositoryUrl "https://github.com/CallesnikovProduction/no-radar-addon-open-source" `
  -OutputPath .\no-radar-entry.json
```

Полученный JSON — одна запись массива `addons`, а не готовый `stable.json`.
Перед публикацией проверьте, что `packageName`, версии и signer действительно
соответствуют ожидаемому release.

## GitHub Release URL

Канонический URL asset выглядит так:

```text
https://github.com/CallesnikovProduction/openksenax-addons/releases/download/<tag>/<file.apk>
```

GitHub может перенаправлять download на CDN. Downloader OKx обязан разрешать
только проверенные HTTPS redirect-hosts; это часть download-фазы host-а, а не
catalog wire-format.

## Проверка

```powershell
python .\tools\validate_catalog.py .\registry\stable.json
```

Публикация каталога до публикации APK запрещена: UI OKx не должен показывать
неустанавливаемый stable release.
