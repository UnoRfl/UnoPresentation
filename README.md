# UnoPresentation

A presentation that the whole room can follow on their own phones.

It is an ordinary HTML deck on a projector. Press **L** and two QR codes appear: one for the
audience, one private. Everyone who scans the first one gets the deck on their phone, on the
slide you are on right now — when you advance, their screens advance. Scan the second one
yourself and your phone becomes the remote: next and back, your speaker notes at full size, a
running timer, and a pointer you drag with your thumb.

**Live:** https://unorfl.github.io/UnoPresentation/

Built for my own talks, not as a product. The whole thing is one self-contained `index.html` —
no build server, no app to install, nothing to sign in to.

---

## The three roles

Every role is the same page, opened at a different fragment.

| Fragment | Role | What it is |
| --- | --- | --- |
| `#live` | **Stage** | The laptop on the projector. Owns the current slide, shows the codes. |
| `#ctl=CODE.TOKEN` | **Remote** | Your phone. Drives the deck. |
| `#join=CODE` | **Audience** | Everyone else. Follows along. |

Pressing **L** on any deck turns that tab into the stage. The `/N` appended to a fragment is
the slide number, so a link stays shareable and survives a reload.

## Audience modes

Switch these live from the stage panel; every phone updates at once.

- **Locked** — they follow exactly, navigation disabled.
- **Follow** (default) — they follow, but can stray back to re-read, then tap **Back to live**.
- **Open** — the whole deck is theirs, no sync.

There is also a quiet **I'm lost** tap on the audience view. It shows as a decaying count on
the stage panel and nowhere else.

## Only your phone can drive it

The stage mints a random 16-character token that rides only in the private QR, and ignores any
command that does not carry it. A room code on its own lets you watch, not steer.

The honest limit: anyone who photographs your phone screen can take over. That is fine for a
classroom and it is not trying to be more than that.

## It is loaded before it says LIVE

Nothing should be discovered for the first time in front of an audience. Behind an opaque
cover, the deck resolves fonts, decodes every image, walks each slide through the real render
path, takes a Screen Wake Lock so the laptop never blanks, and joins the room — and only then
does it call itself live. Each phone does the same when it joins.

If the connection drops, sync stops and the deck keeps working like any other deck. It can
never take the presentation down with it.

## Authoring a new talk

```
build/
  build.py          assembles ../index.html from the parts
  make-cover.py     renders og-cover.jpg, the link preview
  parts/
    loader.html     <head> + the runtime unpacker
    assets.html     the gzipped runtime -- reuse verbatim, never regenerate
    helmet.html     palette, type scale, reading view styles
    slides.html     the 1920x1080 artboards        <- edit this
    mv.html         the phone reading view         <- and this, in step
    tail.html       entrance replay, responsive shell
    live.html       QR rooms, remote, audience sync
```

### A deck that predates the pipeline

Older decks are a finished `index.html` with no `build/` to rebuild from. For those, splice the
live layer into the bundle instead:

```bash
python build/inject_live.py ../old-deck/index.html build/parts/live.html -o out.html
```

It patches the fragment handling, adds the `__amEntry` capture the live layer needs, stamps a
build id, and leaves the slides alone.

### Authoring

Edit `parts/slides.html` and `parts/mv.html`, then:

```bash
python build/build.py
```

Keep the two files in step: each `article` in `mv.html` carries `data-slide="N"` pointing at
its artboard, which is what a following phone uses to show the right card. Speaker notes come
from `data-speaker-notes` on each `<section>` — write them once and the remote picks them up.

Artboards are a fixed 1080px tall and content overflows the grid track silently, so check
`scrollHeight - clientHeight` on the inner containers rather than trusting the look of it.

## Transport

One Supabase Realtime broadcast channel, spoken directly over a WebSocket — no client library,
which is what keeps the deck a single file. No database tables and no rows are written; the
channel is a relay and nothing else. Measured about 80ms from stage to phone.

The QR encoder is hand-written (byte mode, ECC level M, versions 1–10) for the same reason.
It is checked byte-for-byte against a reference encoder on all eight mask patterns.
