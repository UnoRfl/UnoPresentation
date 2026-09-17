"""Assemble ../demo/index.html from the parts in this folder.

    python build.py

The deck runs on the Claude Design canvas runtime: a React UMD pair, the x-dc
runtime and the deck-stage component, gzipped into the manifest at the bottom
of index.html and unpacked into blob URLs by the loader at the top. Nothing is
fetched at run time -- the published page is one self-contained file.

  parts/loader.html   <head> + the unpacker script that mints the blob URLs
  parts/assets.html   the gzipped runtime: manifest, ext_resources, page_order
  parts/helmet.html   the design system -- palette, type scale, reading view
  parts/slides.html   the twelve 1920x1080 artboards          <- edit for content
  parts/mv.html       the portrait reading view               <- edit for content
  parts/tail.html     entrance replay, pointer glow, responsive shell
  parts/live.html     QR room, phone remote, audience sync   <- transport only

Edit a part, run this, and index.html is rebuilt. og-cover.jpg is separate:
python make-cover.py.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "demo" / "index.html"

TITLE = "UnoPresentation — The Deck That Follows You"
DESC = ("A live-sync HTML presentation: put it on a projector, let the room scan a QR code, and every phone follows the slide you are on. Your own phone becomes the remote, with speaker notes, a timer and a pointer.")

XIMPORT = ('<x-import component-from-global-scope="deck-stage" '
           'from="1fd805ec-3320-4cee-aa8d-147c6eb868ea#/deck-stage.js" '
           'width="1920" height="1080" hint-size="100%,100%">')


def read(name):
    return (HERE / "parts" / name).read_text(encoding="utf-8")


def main():
    template = "\n".join([
        "<!DOCTYPE html>",
        "<html><head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        "<title>%s</title>" % TITLE,
        '<meta name="description" content="%s">' % DESC,
        '<meta name="theme-color" content="#101013">',
        '<meta name="color-scheme" content="dark">',
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
        # Resolved to a blob: URL by the loader before this document is parsed.
        '<script src="51be032f-cae7-4457-9543-d064ef34b61f"></script>',
        "</head>",
        "<body>",
        "<x-dc>",
        read("helmet.html"),
        "",
        XIMPORT,
        "",
        read("slides.html"),
        "",
        "</x-import>",
        "",
        read("mv.html"),
        "",
        "</x-dc>",
        read("tail.html"),
        read("live.html"),
        "</body></html>",
        "",
    ])

    # A short digest of the assembled template. It changes whenever any part
    # changes, and rides in every QR so a phone always fetches this build
    # rather than whatever its browser cached from the last one.
    build_id = hashlib.sha1(template.encode("utf-8")).hexdigest()[:8]
    template = template.replace("__BUILD__", build_id)

    index = "".join([
        read("loader.html"),
        read("assets.html"),
        "\n\n  ",
        '<script type="__bundler/template">\n',
        # The template rides as a JSON string; </ would close this script tag.
        json.dumps(template, ensure_ascii=False).replace("</", "<\\/"),
        "\n  </script>\n</body>\n",
    ])
    OUT.write_text(index, encoding="utf-8")
    print("demo/index.html  %d bytes  build %s" % (len(index.encode("utf-8")), build_id))


if __name__ == "__main__":
    main()
