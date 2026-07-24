# OpenKsenax Add-on Contract SDK

`@since 0.3`

`openksenax-addon-contract` — единственная compile/runtime-зависимость,
необходимая автономному addon APK для Binder-взаимодействия с OpenKsenax.
Она не содержит Compose, Ktor, LiteRT, UI host-а или логики конкретного аддона.

## Gradle

В `settings.gradle.kts` аддона:

```kotlin
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri(
                "https://raw.githubusercontent.com/" +
                    "CallesnikovProduction/openksenax-addons/main/maven"
            )
        }
    }
}
```

В Android application module:

```kotlin
dependencies {
    implementation("dev.openksenax:openksenax-addon-contract:0.3.0")
}
```

Используется `implementation`, не `compileOnly`: сгенерированные Binder
proxy/stub и Parcelable-типы должны войти в APK аддона. Код аддона импортирует
типы только из:

```text
dev.openksenax.addons.contract
dev.openksenax.addons.contract.management
dev.openksenax.addons.contract.model
```

## Manifest management service

Аддон объявляет ровно один exported service с:

```xml
<service
    android:name=".integration.openksenax.AddonManagementService"
    android:exported="true"
    android:permission="dev.openksenax.permission.BIND_ADDON_MANAGEMENT">

    <intent-filter>
        <action android:name="dev.openksenax.action.ADDON_SERVICE" />
    </intent-filter>

    <meta-data android:name="dev.openksenax.addon.ID"
        android:value="dev.openksenax.addon.example" />
    <meta-data android:name="dev.openksenax.addon.PROTOCOL_VERSION"
        android:value="1" />
    <meta-data android:name="dev.openksenax.addon.MANAGEMENT_API_VERSION"
        android:value="1" />
    <meta-data android:name="dev.openksenax.addon.MINIMUM_HOST_API"
        android:value="1" />
    <meta-data android:name="dev.openksenax.addon.EXECUTION_MODEL"
        android:value="AUTONOMOUS_APPLICATION" />
    <meta-data android:name="dev.openksenax.addon.REQUIRED_CAPABILITIES"
        android:value="model.text-generation" />
</service>
```

Эти значения должны точно совпасть с `registry/stable.json`. OKx до installer
проверяет APK SHA-256, package, versionCode, signing certificate и service
metadata; после установки discovery повторно читает реальный manifest.

## Management API

Service реализует `IOpenKsenaxAddonManagement.Stub` и асинхронно отвечает через
`IAddonManagementCallback`:

- `requestRuntimeStatus`;
- `requestSetEnabled`;
- `requestUiEntryPoint`;
- `cancel`.

Точка входа UI — immutable activity `PendingIntent`, созданный самим аддоном.
OKx не знает имя Activity и не рисует Compose UI аддона.

## Model Provider

Аддон находит service по action `dev.openksenax.action.MODEL_PROVIDER`,
проверяет host package/signing identity и использует
`IOpenKsenaxModelProvider`. Для MVP поддержана capability
`model.text-generation`. `addonId` внутри запроса не является авторизацией:
OKx дополнительно проверяет Binder calling UID, package, signer и registry
verdict.

Полная миграция первого потребителя описана в
[`no-radar-apk-migration.md`](no-radar-apk-migration.md).
