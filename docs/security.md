# Security policy registry

`@since 0.3`

Registry является trust root для first-party аддонов OpenKsenax.

## Проверяемая цепочка

```text
stable.json
  -> addonId + packageName
  -> expected APK SHA-256
  -> expected signing certificate SHA-256
  -> installed package identity
  -> management/model-provider authorization
```

## Правила

- `official: true` ставится только после ручного review first-party APK.
- Release APK подписывается постоянным release key, не debug key.
- Signing key и пароли не хранятся в этом репозитории или GitHub Release.
- Опубликованный release asset не заменяется другим файлом под тем же tag.
- При компрометации signing key старый catalog entry снимается до выпуска
  отдельной процедуры key rotation.
- SHA-256 считается по финальному байтовому APK после signing/zipalign.
- `packageName` берётся из собранного APK, а не из namespace исходников.
- Capability перечисляются минимально; лишние capability не добавляются
  «на будущее».

Совпадение одного package name не является доверием. OKx дополнительно сверяет
addon ID, manifest contract, compatibility и certificate identity.

