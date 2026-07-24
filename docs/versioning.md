# Версионирование

`@since 0.3`

В addon-системе существуют независимые версии:

| Версия | Что меняется |
|---|---|
| `schemaVersion` | JSON wire-format `stable.json`. |
| `protocolVersion` | Общий Android IPC-протокол OKx/addon. |
| `managementApiVersion` | API статуса, enable/disable и UI entry point. |
| `minimumHostApi` | Минимальный набор host capabilities. |
| `versionCode` | Монотонная Android-версия конкретного APK. |
| `versionName` | Человекочитаемая версия конкретного APK. |

Изменение APK не требует увеличения `schemaVersion`. Изменение JSON-полей не
должно маскироваться повышением `versionCode` аддона.

Для OpenKsenax 0.3 текущие значения:

```text
schemaVersion = 1
protocolVersion = 1
managementApiVersion = 1
minimumHostApi = 1
```

`addonId` и Android `packageName` сохраняются между релизами. Новый package
или addon ID рассматривается OKx как другой продукт, а не обновление.

