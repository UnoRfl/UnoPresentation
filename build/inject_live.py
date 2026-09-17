"""Inject the live layer into an already-built deck bundle.

`contemporary-group-1` predates the build/ pipeline: there are no parts to
rebuild from, only the finished index.html with the whole page carried as a
JSON string inside <script type="__bundler/template">. So the live layer is
spliced into that string, and the loader is given the __amEntry capture that
live.html depends on -- deck-stage rewrites location.hash during its own init,
before anything in the template runs.

    python inject_live.py <deck index.html> <live.html part> [-o out.html]
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TEMPLATE_RE = re.compile(r'(<script type="__bundler/template">\s*)(.*?)(\s*</script>)', re.S)

AM_ENTRY = (
    '<script>\n'
    '    /* deck-stage replaces location.hash with its own #<slide> during init,\n'
    '       before the template below is swapped in, so any other fragment scheme\n'
    '       has to be captured here. window survives documentElement.replaceWith. */\n'
    '    try { window.__amEntry = (location.hash || "").slice(1); } catch (e) {}\n'
    '  </script>\n  '
)

# The stock per-slide hash writer, and the version that defers to live.html.
OLD_HASH = """    let internal = false;
    on(document, 'slidechange', (e) => {
      const n = (e.detail && e.detail.index || 0) + 1;
      const h = '#' + n;
      if (location.hash !== h) { internal = true; history.replaceState(null, '', h); }
    });
    on(window, 'hashchange', () => {
      if (internal) { internal = false; return; }
      const n = parseInt(location.hash.slice(1), 10);
      if (n > 0) deck.goTo(n - 1);
    });"""

NEW_HASH = """    // When the deck is live the fragment also carries the room role, so
    // live.html owns the format and this defers to it. Off-air it is #N as
    // before. Without this a phone that reloads loses its room.
    const LH = () => window.__liveHash;
    let internal = false;
    on(document, 'slidechange', (e) => {
      const n = (e.detail && e.detail.index || 0) + 1;
      const h = LH() ? LH().fmt(n) : '#' + n;
      if (location.hash !== h) { internal = true; history.replaceState(null, '', h); }
    });
    on(window, 'hashchange', () => {
      if (internal) { internal = false; return; }
      const n = LH() ? LH().parse() : parseInt(location.hash.slice(1), 10);
      if (n > 0) deck.goTo(n - 1);
    });"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("live")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    deck_path = Path(args.deck)
    html = deck_path.read_text(encoding="utf-8")
    live = Path(args.live).read_text(encoding="utf-8")

    report = []

    if "__liveHash" in html:
        print("already carries the live layer -- nothing to do", file=sys.stderr)
        return 1

    m = TEMPLATE_RE.search(html)
    if not m:
        print("no bundler template found; is this a canvas deck?", file=sys.stderr)
        return 1

    tpl = json.loads(m.group(2).replace("<\\/", "</"))

    # 1. Hash delegation, so #join=/#ctl= survive the deck's own rewriting.
    if OLD_HASH in tpl:
        tpl = tpl.replace(OLD_HASH, NEW_HASH, 1)
        report.append("hash writer now defers to live.html")
    elif "__liveHash" not in tpl:
        report.append("WARNING: hash writer not found -- links will fall back to #N")

    # 2. The live layer itself, immediately before the document closes.
    close = "</body></html>"
    idx = tpl.rfind(close)
    if idx == -1:
        print("template has no closing body", file=sys.stderr)
        return 1
    tpl = tpl[:idx] + "\n" + live + "\n" + tpl[idx:]
    report.append("live layer spliced in before </body>")

    # 3. Stamp this build so a scanned QR can never load a cached older copy.
    build_id = hashlib.sha1(tpl.encode("utf-8")).hexdigest()[:8]
    tpl = tpl.replace("__BUILD__", build_id)
    report.append("build %s" % build_id)

    out_html = html[:m.start(2)] + json.dumps(tpl, ensure_ascii=False).replace("</", "<\\/") + html[m.end(2):]

    # 4. The entry capture, in the head, ahead of everything. Test for the
    #    assignment, not the identifier: live.html *reads* window.__amEntry, so
    #    a bare substring check is satisfied by the layer we just injected and
    #    the capture silently never gets added -- which breaks every join link.
    if "window.__amEntry =" not in out_html and "window.__amEntry=" not in out_html:
        head = out_html.find("<head>") + len("<head>")
        out_html = out_html[:head] + "\n  " + AM_ENTRY + out_html[head:]
        report.append("__amEntry capture added to <head>")

    out = Path(args.out or args.deck)
    out.write_text(out_html, encoding="utf-8")
    for line in report:
        print(" -", line)
    print("%s  %d bytes" % (out.name, len(out_html.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
