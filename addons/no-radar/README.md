# NO RADAR release descriptor

`@since 0.3`

NO RADAR публикуется как автономный Android APK, а не как DEX или embedded UI.
Эта директория содержит только человеческий release-handoff. Runtime
OpenKsenax читает запись аддона исключительно из `registry/stable.json`.

Фиксированная identity:

```text
addonId:       dev.openksenax.addon.no-radar
packageName:   com.callesnikovdev.noradar
capability:    model.text-generation
protocol:      1
managementApi: 1
```

Перед добавлением в stable:

1. подключить `dev.openksenax:openksenax-addon-contract:0.3.0`;
2. реализовать management service и model-provider client;
3. собрать APK с постоянным release key;
4. опубликовать APK в GitHub Releases этого репозитория;
5. запустить `tools/prepare_addon_release.ps1`;
6. перенести полученную запись в `registry/stable.json`;
7. запустить оба validator-а.

Подробная миграция: [`../../docs/no-radar-apk-migration.md`](../../docs/no-radar-apk-migration.md).
