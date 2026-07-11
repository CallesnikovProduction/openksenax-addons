# NO RADAR 0.3

First-party OpenKsenax add-on release bundle.

- `no-radar-0.3.dex` — standalone DEX with factory, lifecycle, command bridge
  and `OpenKsenaxComposeAddon` UI.
- `no-radar-0.3.assets.zip` — images, fonts and default configuration extracted
  by OpenKsenax into the private add-on asset directory.
- Each artifact has a matching GNU `sha256sum` sidecar.

Build and verify all four files from the NO RADAR project root:

```powershell
.\gradlew.bat --no-configuration-cache :addon:prepareNoRadarDexRelease
```

The add-on API JARs and Compose runtime are host-owned and must not be bundled
into the DEX.
