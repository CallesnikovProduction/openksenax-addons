# NO RADAR: migration from DEX to autonomous APK

`@since 0.3`

Этот документ является handoff для отдельной Codex-сессии в репозитории
`no-radar-addon-open-source`. Он заменяет устаревшее предположение, что NO RADAR
поставляется как DEX и получает Android-компоненты от host-процесса.

## Целевое состояние

NO RADAR остаётся самостоятельным Android APK:

- package name: `com.callesnikovdev.noradar`;
- владеет Compose UI и resource table;
- владеет NotificationListenerService, foreground service, alarms и permissions;
- владеет Monitor, Gate, Timer, Rule Engine, очередью и sending-контуром;
- не загружает Gemma/LiteRT-модель;
- вызывает `model.text-generation` через Binder Model Provider OpenKsenax;
- предоставляет OpenKsenax маленький management service: status, enable/disable,
  UI PendingIntent и cancellation.

## Что оставить без архитектурного переписывания

- `app/src/main/java/.../background`;
- `core/notification`;
- `core/decision`, кроме inference adapter;
- `core/deferred`;
- `core/rules`;
- `core/sending`;
- `core/log`;
- весь Compose UI и ресурсы, кроме model-picker UX;
- `MainActivity` как настоящий экран APK;
- `NRReplyGenerator` как внутренний порт бизнес-логики.

Не переносить эти контуры в OpenKsenax. Host не рисует UI NO RADAR и не
исполняет его notification/auto-reply pipeline.

## Что удалить или вывести из production graph

1. Gradle-модуль `:addon`, который выпускает DEX и asset ZIP.
2. `libs/openksenax-addon-api.jar` и `openksenax-addon-compose-api.jar`.
3. DEX factory/lifecycle/command bridge и задачи `prepareNoRadarDexRelease`.
4. `NRLiteRtModelRuntime` как владелец локального Engine.
5. `NRModelSelectionRepository`, SAF model picker и импорт `.litertlm`.
6. Зависимость `google.ai.edge.litertlm.android` из APK NO RADAR.
7. Документацию и AGENTS-инструкции, утверждающие, что актуальный артефакт — DEX.

Историю можно сохранить в `legacy/`, но она не должна управлять новой сборкой.

## Contract dependency

OpenKsenax публикует один Android Library artifact:

```text
openksenax-addon-contract-0.3.0.aar
```

Он содержит только стабильный IPC ABI:

- `AddonId`, `HostCapabilityId`, protocol/manifest constants;
- management AIDL и Parcelable types;
- model-provider AIDL и Parcelable types.

Он не содержит Compose, Ktor, registry, downloader, model runtime или UI.

Основной способ подключения — tokenless Maven tree этого репозитория:

```kotlin
repositories {
    maven {
        url = uri(
            "https://raw.githubusercontent.com/" +
                "CallesnikovProduction/openksenax-addons/main/maven"
        )
    }
}

dependencies {
    implementation("dev.openksenax:openksenax-addon-contract:0.3.0")
}
```

Именно `implementation`, не `compileOnly`: Binder proxy/stub и Parcelable
классы должны находиться внутри APK аддона во время выполнения.

GitHub Packages не использовать. Если ноутбук временно работает без сети,
`openksenax-addon-contract-0.3.0.aar` можно скопировать из Maven tree в
`app/libs/` и оставить тот же `implementation(files(...))`.

## Android Manifest

Добавить ровно один exported management service:

```xml
<queries>
    <intent>
        <action android:name="dev.openksenax.action.MODEL_PROVIDER" />
    </intent>
</queries>

<service
    android:name=".integration.openksenax.NRAddonManagementService"
    android:exported="true"
    android:permission="dev.openksenax.permission.BIND_ADDON_MANAGEMENT">

    <intent-filter>
        <action android:name="dev.openksenax.action.ADDON_SERVICE" />
    </intent-filter>

    <meta-data
        android:name="dev.openksenax.addon.ID"
        android:value="dev.openksenax.addon.no-radar" />
    <meta-data
        android:name="dev.openksenax.addon.PROTOCOL_VERSION"
        android:value="1" />
    <meta-data
        android:name="dev.openksenax.addon.MANAGEMENT_API_VERSION"
        android:value="1" />
    <meta-data
        android:name="dev.openksenax.addon.MINIMUM_HOST_API"
        android:value="1" />
    <meta-data
        android:name="dev.openksenax.addon.EXECUTION_MODEL"
        android:value="AUTONOMOUS_APPLICATION" />
    <meta-data
        android:name="dev.openksenax.addon.REQUIRED_CAPABILITIES"
        android:value="model.text-generation" />
</service>
```

В package должен быть ровно один service с action `ADDON_SERVICE`.

Production APK открывается через PendingIntent, возвращённый management service.
Launcher icon можно оставить в debug manifest overlay, а из release manifest
убрать `MAIN/LAUNCHER`, если NO RADAR должен открываться только через OKx.

## Management adapter

Создать package:

```text
app/src/main/java/com/callesnikovdev/noradar/integration/openksenax/
```

Минимальные типы:

```text
NRAddonManagementService.kt
NRAddonManagementBinder.kt
NROpenKsenaxCallerVerifier.kt
NROpenKsenaxModelProviderClient.kt
NROpenKsenaxModelProviderConnection.kt
```

`NRAddonManagementService` возвращает
`IOpenKsenaxAddonManagement.Stub` и реализует:

- `requestRuntimeStatus(requestId, callback)`;
- `requestSetEnabled(requestId, enabled, callback)`;
- `requestUiEntryPoint(requestId, callback)`;
- `cancel(requestId)`.

Правила response:

- callback вызывается не более одного раза на requestId;
- ответ сохраняет исходные `requestId` и operation;
- `RUNTIME_STATUS` содержит только `runtimeStatus`;
- успешный `SET_ENABLED` содержит `commandResult` и финальный `runtimeStatus`;
- `UI_ENTRY_POINT` содержит только immutable Activity PendingIntent;
- failure содержит `failureCode/failureMessage` и не содержит success payload;
- Binder thread не блокируется: работа запускается в service-owned coroutine scope;
- `cancel` отменяет job этого requestId;
- `CancellationException` не преобразуется в обычный success/failure.

PendingIntent должен быть создан самим NO RADAR, указывать на `MainActivity`,
быть activity PendingIntent и иметь `FLAG_IMMUTABLE` на Android 12+.

### Caller authentication

Одного `android:permission` недостаточно. Перед каждой Binder-командой:

1. прочитать `Binder.getCallingUid()` до перехода в coroutine;
2. проверить, что UID разрешается в package `com.kolesnikovprod.ksetaorch`;
3. проверить SHA-256 signing certificate host package по allow-list;
4. отклонить package-name-only совпадение.

Debug и release сертификаты задаются разными BuildConfig/manifest resource
allow-list. Signing fingerprint не хардкодится случайным значением.

## Mapping management to existing NO RADAR runtime

- runtime status строится из `NRBackgroundModeController.enabled` и состояния
  foreground/runtime pipeline;
- enable вызывает `NRAppGraph.setMasterEnabled(context, true)`;
- disable вызывает `NRAppGraph.setMasterEnabled(context, false)`;
- `NotificationAccessRequired` и `ExactAlarmAccessRequired` возвращаются как
  `REJECTED`/`UNAVAILABLE`; Binder service не открывает permission UI;
- пользователь исправляет permissions внутри собственного UI NO RADAR;
- `requestUiEntryPoint` всегда возвращает PendingIntent, даже если runtime stopped.

## Model Provider adapter

Сохранить `NRReplyGenerator` и заменить только реализацию:

```text
NRLiteRtModelRuntime : NRReplyGenerator
            ->
NROpenKsenaxModelProviderClient : NRReplyGenerator
```

Клиент:

1. bind-ится к action `dev.openksenax.action.MODEL_PROVIDER` в package
   `com.kolesnikovprod.ksetaorch`;
2. проверяет `getProviderApiVersion() == 1`;
3. проверяет наличие `model.text-generation`;
4. создаёт уникальный `requestId`;
5. отправляет `ModelGenerationRequest`:
   - `addonId = dev.openksenax.addon.no-radar`;
   - `capabilityId = model.text-generation`;
   - messages содержат USER prompt;
   - sampling остаётся `HOST_DEFAULT`;
   - priority остаётся `FOREGROUND_AUTOMATION`;
   - timeout находится в диапазоне 1-120 секунд;
6. преобразует callback в существующий `NRReplyGenerationResult`;
7. вызывает remote `cancel(requestId)` при coroutine cancellation;
8. корректно обрабатывает Binder death, timeout, `PROVIDER_NOT_READY`, trust и
   capability failures.

NO RADAR не передаёт host-у notification object, RemoteInput, rules или Android
permissions. Model Provider получает только текстовый stateless generation request.

## Изменения существующих файлов

### `settings.gradle.kts`

- удалить `include(":addon")`;
- оставить `:app`;
- не добавлять отдельный module на каждый integration package.

### `app/build.gradle.kts`

- добавить contract AAR через `implementation`;
- удалить LiteRT-LM dependency;
- сохранить Compose/Android dependencies;
- настроить настоящий release signing вне Git history.

### `NRAppGraph.kt`

- удалить `NRModelSelectionRepository` и `NRLiteRtModelRuntime`;
- создать один process-owned `NROpenKsenaxModelProviderClient`;
- зарегистрировать его в `NRModelReplyBridge` или, предпочтительно, передать
  `NRReplyGenerator` явно в decision contour;
- `setMasterEnabled` проверяет provider availability вместо SAF model selection;
- process-death recovery повторно связывается с provider, а не прогревает LiteRT;
- при disable закрывается Binder connection, а не model engine.

### UI

- удалить SAF model picker и кнопку выбора `.litertlm`;
- заменить model verification overlay на состояние OKx provider:
  disconnected / connecting / ready / unavailable / failed;
- сообщение пользователю должно вести к запуску/настройке OpenKsenax, а не к
  выбору локального файла модели;
- остальной визуальный UI не переписывать.

### `AGENTS.md`, README и SPECIFICATION

- заменить DEX/Compose-host API на autonomous APK + Binder contracts;
- явно зафиксировать ownership Android-компонентов за NO RADAR;
- удалить утверждения о `DexClassLoader`, asset ZIP и compileOnly Compose API.

## Registry и release gate

Не добавлять NO RADAR в `registry/stable.json`, пока одновременно не выполнены:

- release APK собирается;
- manifest discovery видит ровно один management service;
- management status/enable/open проходят на устройстве;
- model generation проходит через OKx;
- APK подписан постоянным release key;
- получены APK SHA-256, signing certificate SHA-256 и sizeBytes;
- GitHub Release asset опубликован и доступен по HTTPS.

После этого добавить registry entry по шаблону из `docs/catalog-format.md`.

## Definition of done

1. NO RADAR отсутствует как DEX и устанавливается как отдельный APK.
2. В release APK нет LiteRT-LM и собственной модели.
3. OKx обнаруживает APK через PackageManager.
4. OKx получает runtime status.
5. OKx включает/выключает Master через management AIDL.
6. OKx открывает `MainActivity` через immutable PendingIntent.
7. NO RADAR получает генерацию через OKx Model Provider.
8. Notification listener, queue, rules и sending работают внутри NO RADAR.
9. Отсутствующий/не готовый OKx приводит к явному recoverable состоянию.
10. Все старые DEX-инструкции удалены или помечены legacy.
