![OpenKsenax add-ons](assets/repo-title.png)

Публичный registry автономных addon APK для OpenKsenax.

OpenKsenax не загружает код аддона в свой process. Каждый аддон является
отдельным Android-приложением со своим UI, разрешениями, сервисами и lifecycle.
Этот репозиторий публикует только доверенные release-метаданные; APK хранятся
в GitHub Releases, а исходники аддонов могут жить в отдельных репозиториях.

`@since 0.3`

## Машинная точка входа

OpenKsenax читает один документ:

```text
https://raw.githubusercontent.com/CallesnikovProduction/openksenax-addons/main/registry/stable.json
```

Остальные файлы нужны людям, CI и процессу выпуска, но не участвуют в runtime
парсинге OKx.

## Структура

```text
registry/stable.json                 # production-каталог OKx
schema/addon-catalog.schema.json     # JSON Schema wire-format v1
addons/no-radar/README.md            # handoff первого реального аддона
tools/validate_catalog.py            # локальная и CI-валидация
tools/prepare_addon_release.ps1      # извлечение integrity/release metadata
maven/dev/openksenax/...             # tokenless Maven-repository contract AAR
docs/catalog-format.md               # описание полей
docs/contract-sdk.md                 # подключение ABI в addon APK
docs/publishing.md                   # выпуск addon APK
docs/security.md                     # trust и signing policy
docs/versioning.md                   # версии schema/protocol/API/APK
.github/workflows/validate-catalog.yml
```

## Два разных артефакта

- `openksenax-addon-contract` — маленькая Android-библиотека, которую разработчик
  аддона подключает через `implementation`;
- addon APK — самостоятельное Android-приложение, публикуемое только как
  GitHub Release asset и описываемое в `registry/stable.json`.

GitHub Packages не нужен: каталог и Maven-репозиторий читаются как обычные
публичные HTTPS-файлы без токена.

## Проверка перед push

```powershell
python .\tools\validate_catalog.py .\registry\stable.json
python -m json.tool .\schema\addon-catalog.schema.json > $null
```

Пока подписанный NO RADAR APK не опубликован, `stable.json` намеренно содержит
пустой `addons`. Заполнять SHA-256, signing certificate или release URL
фиктивными значениями запрещено.
