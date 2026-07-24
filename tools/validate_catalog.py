#!/usr/bin/env python3
"""Validate the OpenKsenax catalog without third-party dependencies.

@since 0.3
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


IDENTIFIER = re.compile(r"^[a-z0-9]+([._-][a-z0-9]+)*$")
PACKAGE_NAME = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
SHA256 = re.compile(r"^[A-Fa-f0-9]{64}$")

ROOT_REQUIRED = {
    "schemaVersion",
    "channel",
    "generatedAtEpochMillis",
    "addons",
}
ROOT_ALLOWED = ROOT_REQUIRED | {"$schema"}
ADDON_REQUIRED = {
    "addonId",
    "packageName",
    "displayName",
    "shortDescription",
    "executionModel",
    "release",
    "compatibility",
    "requiredHostCapabilities",
    "presentation",
    "security",
}
ADDON_ALLOWED = ADDON_REQUIRED | {"fullDescription"}
RELEASE_REQUIRED = {"versionCode", "versionName", "apkUrl", "apkSha256"}
RELEASE_ALLOWED = RELEASE_REQUIRED | {"sizeBytes"}
COMPATIBILITY_REQUIRED = {
    "protocolVersion",
    "managementApiVersion",
    "minimumHostApi",
    "minimumAndroidSdk",
}
PRESENTATION_ALLOWED = {"iconUrl", "repositoryUrl"}
SECURITY_REQUIRED = {"official", "signingCertificateSha256"}


class CatalogErrors:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, path: str, message: str) -> None:
        self.items.append(f"{path}: {message}")

    def require_object(self, value: object, path: str) -> dict | None:
        if not isinstance(value, dict):
            self.add(path, "must be an object")
            return None
        return value

    def check_keys(
        self,
        value: dict,
        path: str,
        required: set[str],
        allowed: set[str],
    ) -> None:
        for key in sorted(required - value.keys()):
            self.add(path, f"missing required property {key!r}")
        for key in sorted(value.keys() - allowed):
            self.add(path, f"unknown property {key!r}")


def is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def is_non_blank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme.lower() == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and not parsed.fragment
    )


def validate_release(value: object, path: str, errors: CatalogErrors) -> None:
    release = errors.require_object(value, path)
    if release is None:
        return
    errors.check_keys(release, path, RELEASE_REQUIRED, RELEASE_ALLOWED)
    if not is_positive_int(release.get("versionCode")):
        errors.add(f"{path}.versionCode", "must be a positive integer")
    if not is_non_blank_string(release.get("versionName")):
        errors.add(f"{path}.versionName", "must be non-blank")
    if not is_https_url(release.get("apkUrl")):
        errors.add(f"{path}.apkUrl", "must be an absolute HTTPS URL without credentials or fragment")
    if not isinstance(release.get("apkSha256"), str) or not SHA256.fullmatch(release["apkSha256"]):
        errors.add(f"{path}.apkSha256", "must contain 64 hexadecimal characters")
    if "sizeBytes" in release and not is_positive_int(release["sizeBytes"]):
        errors.add(f"{path}.sizeBytes", "must be a positive integer")


def validate_compatibility(value: object, path: str, errors: CatalogErrors) -> None:
    compatibility = errors.require_object(value, path)
    if compatibility is None:
        return
    errors.check_keys(
        compatibility,
        path,
        COMPATIBILITY_REQUIRED,
        COMPATIBILITY_REQUIRED,
    )
    for key in sorted(COMPATIBILITY_REQUIRED):
        if not is_positive_int(compatibility.get(key)):
            errors.add(f"{path}.{key}", "must be a positive integer")


def validate_presentation(value: object, path: str, errors: CatalogErrors) -> None:
    presentation = errors.require_object(value, path)
    if presentation is None:
        return
    errors.check_keys(presentation, path, set(), PRESENTATION_ALLOWED)
    for key in sorted(PRESENTATION_ALLOWED & presentation.keys()):
        if not is_https_url(presentation[key]):
            errors.add(f"{path}.{key}", "must be an absolute HTTPS URL without credentials or fragment")


def validate_security(value: object, path: str, errors: CatalogErrors) -> None:
    security = errors.require_object(value, path)
    if security is None:
        return
    errors.check_keys(security, path, SECURITY_REQUIRED, SECURITY_REQUIRED)
    if not isinstance(security.get("official"), bool):
        errors.add(f"{path}.official", "must be a boolean")
    certificate = security.get("signingCertificateSha256")
    if not isinstance(certificate, str) or not SHA256.fullmatch(certificate):
        errors.add(
            f"{path}.signingCertificateSha256",
            "must contain 64 hexadecimal characters",
        )


def validate_addon(value: object, index: int, errors: CatalogErrors) -> tuple[str | None, str | None]:
    path = f"addons[{index}]"
    addon = errors.require_object(value, path)
    if addon is None:
        return None, None
    errors.check_keys(addon, path, ADDON_REQUIRED, ADDON_ALLOWED)

    addon_id = addon.get("addonId")
    if not isinstance(addon_id, str) or not IDENTIFIER.fullmatch(addon_id):
        errors.add(f"{path}.addonId", "must be a lowercase stable identifier")
        addon_id = None

    package_name = addon.get("packageName")
    if not isinstance(package_name, str) or not PACKAGE_NAME.fullmatch(package_name):
        errors.add(f"{path}.packageName", "must be a valid lowercase Android package name")
        package_name = None

    for key in ("displayName", "shortDescription"):
        if not is_non_blank_string(addon.get(key)):
            errors.add(f"{path}.{key}", "must be non-blank")
    if "fullDescription" in addon and not isinstance(addon["fullDescription"], str):
        errors.add(f"{path}.fullDescription", "must be a string")
    if addon.get("executionModel") != "AUTONOMOUS_APPLICATION":
        errors.add(f"{path}.executionModel", "must be AUTONOMOUS_APPLICATION")

    capabilities = addon.get("requiredHostCapabilities")
    if not isinstance(capabilities, list):
        errors.add(f"{path}.requiredHostCapabilities", "must be an array")
    else:
        seen_capabilities: set[str] = set()
        for capability_index, capability in enumerate(capabilities):
            capability_path = f"{path}.requiredHostCapabilities[{capability_index}]"
            if not isinstance(capability, str) or not IDENTIFIER.fullmatch(capability):
                errors.add(capability_path, "must be a lowercase stable identifier")
            elif capability in seen_capabilities:
                errors.add(capability_path, "must not be duplicated")
            else:
                seen_capabilities.add(capability)

    validate_release(addon.get("release"), f"{path}.release", errors)
    validate_compatibility(addon.get("compatibility"), f"{path}.compatibility", errors)
    validate_presentation(addon.get("presentation"), f"{path}.presentation", errors)
    validate_security(addon.get("security"), f"{path}.security", errors)
    return addon_id, package_name


def validate_document(document: object) -> list[str]:
    errors = CatalogErrors()
    root = errors.require_object(document, "$")
    if root is None:
        return errors.items
    errors.check_keys(root, "$", ROOT_REQUIRED, ROOT_ALLOWED)

    if root.get("schemaVersion") != 1:
        errors.add("schemaVersion", "must be 1")
    if root.get("channel") != "STABLE":
        errors.add("channel", "must be STABLE")
    if not is_positive_int(root.get("generatedAtEpochMillis")):
        errors.add("generatedAtEpochMillis", "must be a positive integer")

    addons = root.get("addons")
    if not isinstance(addons, list):
        errors.add("addons", "must be an array")
        return errors.items

    seen_ids: set[str] = set()
    seen_packages: set[str] = set()
    for index, addon in enumerate(addons):
        addon_id, package_name = validate_addon(addon, index, errors)
        if addon_id is not None:
            if addon_id in seen_ids:
                errors.add("addons", f"duplicate addonId {addon_id!r}")
            seen_ids.add(addon_id)
        if package_name is not None:
            if package_name in seen_packages:
                errors.add("addons", f"duplicate packageName {package_name!r}")
            seen_packages.add(package_name)
    return errors.items


def main() -> int:
    catalog_path = Path(sys.argv[1] if len(sys.argv) > 1 else "registry/stable.json")
    try:
        raw_document = catalog_path.read_text(encoding="utf-8")
        document = json.loads(raw_document)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Catalog cannot be read: {error}", file=sys.stderr)
        return 2

    errors = validate_document(document)
    if errors:
        print(f"Catalog is invalid ({len(errors)} violation(s)):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Catalog is valid: {catalog_path} ({len(document['addons'])} add-on(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

