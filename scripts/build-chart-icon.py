#!/usr/bin/env python3
"""Embed the EmberBurn logo into helm/opcua-server/Chart.yaml as a data URI.

Embernet clusters are air-gapped. A Chart.yaml `icon:` pointing at a remote URL
(github avatars, a CDN, anything) renders as a broken image in the Rancher app
catalog because the browser cannot reach it. Embedding the PNG as a data URI
keeps the catalog tile working with no outbound network.

Run this after changing static/images/emberburn-chart-icon.png:

    python scripts/build-chart-icon.py
"""

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_IMAGE = REPO_ROOT / "static" / "images" / "emberburn-chart-icon.png"
CHART_YAML = REPO_ROOT / "helm" / "opcua-server" / "Chart.yaml"
HELPERS_TPL = REPO_ROOT / "helm" / "opcua-server" / "templates" / "_helpers.tpl"

# Rancher renders catalog tiles at roughly 100px; 128px wide gives hi-dpi
# headroom while keeping the encoded icon under ~10KB. That size matters: the
# icon field is copied verbatim into the Helm repo index.yaml for every
# published chart version.
TARGET_WIDTH = 128
MAX_ENCODED_BYTES = 32 * 1024


def build_data_uri(square: bool = False) -> str:
    image = Image.open(SOURCE_IMAGE)

    if square:
        # Dashboard tiles are square. Pad onto a transparent square canvas so the
        # mark keeps its aspect ratio instead of being stretched.
        side = max(image.size)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
        resized = canvas.resize((TARGET_WIDTH, TARGET_WIDTH), Image.LANCZOS)
    else:
        height = round(image.height * TARGET_WIDTH / image.width)
        resized = image.resize((TARGET_WIDTH, height), Image.LANCZOS)

    buffer = io.BytesIO()
    resized.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    if len(encoded) > MAX_ENCODED_BYTES:
        sys.exit(
            f"Encoded icon is {len(encoded)}B, over the {MAX_ENCODED_BYTES}B budget. "
            "Reduce TARGET_WIDTH or simplify the source image."
        )
    return f"data:image/png;base64,{encoded}"


def main() -> None:
    if not SOURCE_IMAGE.exists():
        sys.exit(f"Source image not found: {SOURCE_IMAGE}")

    # Rancher catalog tile — Chart.yaml `icon:`, natural aspect ratio.
    catalog_uri = build_data_uri()
    chart = CHART_YAML.read_text(encoding="utf-8")
    patched, count = re.subn(
        r"^icon:.*$", f"icon: {catalog_uri}", chart, count=1, flags=re.MULTILINE
    )
    if count != 1:
        sys.exit(f"Expected exactly one 'icon:' line in {CHART_YAML}, found {count}")
    CHART_YAML.write_text(patched, encoding="utf-8")
    print(f"Chart.yaml icon:        {len(catalog_uri):>6}B ({TARGET_WIDTH}px wide)")

    # Embernet dashboard app tile — embernet.ai/app-icon annotation, squared.
    tile_uri = build_data_uri(square=True)
    helpers = HELPERS_TPL.read_text(encoding="utf-8")
    patched, count = re.subn(
        r'^\{\{- print "data:image/png;base64,[^"]*" \}\}$',
        f'{{{{- print "{tile_uri}" }}}}',
        helpers,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        sys.exit(
            f"Expected exactly one embedded data URI in {HELPERS_TPL}, found {count}. "
            "Check the emberburn.appIcon helper."
        )
    HELPERS_TPL.write_text(patched, encoding="utf-8")
    print(f"_helpers.tpl app-icon:  {len(tile_uri):>6}B ({TARGET_WIDTH}x{TARGET_WIDTH})")


if __name__ == "__main__":
    main()
