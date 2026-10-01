#!/usr/bin/env python3
# Empaqueta la extension py2spark en un .vsix SIN depender de vsce/npm.
#
# Un .vsix es un ZIP OPC con:
#   extension.vsixmanifest      (manifiesto XML de la extension)
#   [Content_Types].xml         (tipos MIME del paquete OPC)
#   extension/<archivos>        (package.json, extension.js, README, ...)
#
# Este script lee package.json para el manifiesto y comprime todo. Se usa desde
# la CLI (python build_vsix.py) y desde el endpoint /download/vsix del portal.

import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Archivos de la extension que van dentro de extension/ (excluye artefactos).
_INCLUDE = ["package.json", "extension.js", "README.md", "CHANGELOG.md", "LICENSE.txt"]


def _manifest(pkg):
    name = pkg["name"]
    publisher = pkg.get("publisher", "bnx")
    version = pkg["version"]
    display = pkg.get("displayName", name)
    desc = pkg.get("description", "")
    engine = pkg.get("engines", {}).get("vscode", "^1.75.0").lstrip("^>=")
    return f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}" />
    <DisplayName>{display}</DisplayName>
    <Description xml:space="preserve">{desc}</Description>
    <Tags>pyspark,pandas,spark,python,etl</Tags>
    <Categories>Other,Programming Languages</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{engine}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value="" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
  </Assets>
</PackageManifest>
'''


_CONTENT_TYPES = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="js" ContentType="application/javascript" />
  <Default Extension="md" ContentType="text/markdown" />
  <Default Extension="txt" ContentType="text/plain" />
  <Default Extension="vsixmanifest" ContentType="text/xml" />
  <Default Extension="png" ContentType="image/png" />
</Types>
'''


def build(out_path=None):
    """Construye el .vsix y devuelve la ruta del archivo generado."""
    with open(os.path.join(HERE, "package.json"), "r", encoding="utf-8") as f:
        pkg = json.load(f)
    out_path = out_path or os.path.join(HERE, f"{pkg['name']}-{pkg['version']}.vsix")

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("extension.vsixmanifest", _manifest(pkg))
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        for fname in _INCLUDE:
            fpath = os.path.join(HERE, fname)
            if os.path.isfile(fpath):
                z.write(fpath, arcname=f"extension/{fname}")
    return out_path


if __name__ == "__main__":
    out = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"[vsix] generado: {out} ({os.path.getsize(out)} bytes)")
