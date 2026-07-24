# Формат addon-каталога

`@since 0.3`

OpenKsenax загружает `registry/stable.json` как UTF-8 JSON размером не более
1 MiB. URL обязан использовать HTTPS без credentials и fragment.

## Корневой документ

| Поле | Значение |
|---|---|
| `schemaVersion` | Версия wire-format. Для OKx 0.3: `1`. |
| `channel` | Канал каталога. Каноническое значение: `STABLE`. |
| `generatedAtEpochMillis` | Время генерации документа в Unix milliseconds. |
| `addons` | Список опубликованных аддонов. |

`$schema` разрешён для IDE и CI. Runtime OKx его игнорирует.

## Запись аддона

| Поле | Назначение |
|---|---|
| `addonId` | Неизменяемый lowercase ID, не Android package name. |
| `packageName` | Фактический `applicationId` APK. |
| `displayName` | Название для UI. |
| `shortDescription` | Короткое описание карточки. |
| `fullDescription` | Необязательное полное описание. |
| `executionModel` | В API 1 только `AUTONOMOUS_APPLICATION`. |
| `release` | Версия и проверяемый APK artifact. |
| `compatibility` | Требования к host и Android. |
| `requiredHostCapabilities` | Capability, которые аддон реально запрашивает. |
| `presentation` | Необязательные HTTPS icon/repository URL. |
| `security` | Official-флаг и сертификат подписи. |

## Шаблон NO RADAR

Это документационный шаблон, не готовая запись. Значения в угловых скобках
нельзя помещать в production `stable.json`.

```json
{
  "addonId": "dev.openksenax.addon.no-radar",
  "packageName": "com.callesnikovdev.noradar",
  "displayName": "NO RADAR",
  "shortDescription": "Локальный фоновый автоответчик",
  "fullDescription": "Автономный addon APK со своим UI и Android runtime.",
  "executionModel": "AUTONOMOUS_APPLICATION",
  "release": {
    "versionCode": 1,
    "versionName": "1.0",
    "apkUrl": "<HTTPS URL опубликованного release APK>",
    "apkSha256": "<64 hex символа SHA-256 APK>",
    "sizeBytes": 123456
  },
  "compatibility": {
    "protocolVersion": 1,
    "managementApiVersion": 1,
    "minimumHostApi": 1,
    "minimumAndroidSdk": 24
  },
  "requiredHostCapabilities": [
    "model.text-generation"
  ],
  "presentation": {
    "repositoryUrl": "https://github.com/CallesnikovProduction/no-radar-addon-open-source"
  },
  "security": {
    "official": true,
    "signingCertificateSha256": "<64 hex символа сертификата подписи APK>"
  }
}
```

`apkSha256` и `signingCertificateSha256` — разные значения. Первый защищает
конкретный файл релиза, второй связывает все версии аддона с signing identity.

