# Design: real image content for mockup/background skeleton elements

## Context

`design-system` (and the `extract-design` capture step behind it) currently
represents image-bearing skeleton elements — `mockup_image` (a UI panel:
chat interface, dashboard, code editor) and `background_image` (a
photographic backdrop: landscape, texture, abstract) — as plain text
(`"style": "cinematic-sunset-canyon-photo"`). At generation time this text
is either ignored (empty placeholder box) or approximated with a CSS
gradient standing in for a photo. Step 8 of `design-system/SKILL.md`
already tells Claude not to ship placeholder-quality components, but gives
no concrete procedure for turning the `style` description into real
content.

This is the first of three planned sub-projects toward richer generated
pages (mockup images → scroll/cursor motion triggers → video backgrounds).
Scroll/cursor motion and video backgrounds are explicitly out of scope
here and will get their own spec/plan cycles once this one ships.

## Goals

- When `design-system` generates a block whose skeleton includes a
  `mockup_image` or `background_image` element, the result should contain
  real, on-topic visual content — not an empty box or an approximated
  gradient standing in for a photo — using only tools that may or may not
  be present in a given Claude Code session (no new backend, no bundled
  dependency).
- Keep the existing token/skeleton architecture as the only extension
  point: this is an instructions change to `design-system/SKILL.md`, not a
  new subsystem.

## Non-goals

- Backend asset hosting/storage in `design-reference-web` (rejected —
  would need moderation, an upload flow, and rights-to-use handling for
  scraped screenshots; generation-time sourcing avoids all of that).
- Scroll-linked or cursor-linked animation (separate sub-project).
- Video backgrounds (separate sub-project; depends on this one).
- Changes to `extract-design`'s capture step — it already requires a
  content-descriptive `style` string (e.g.
  `"chat-interface-with-prompt-input"`), which is a sufficient input for
  the generation-time procedure below.

## Design

### Two element types, two different procedures

AI image generation reliably produces photography and textures but
unreliably produces legible on-screen UI text, so the two element types
diverge:

**`mockup_image`** (chat UI, dashboard, code panel, stacked cards, etc.) —
Claude hand-codes it as real HTML/CSS/SVG matching the `style`
description, at the same level of craft as any other skeleton element
(spacing, borders, depth called out in existing step 8 guidance). This is
not a new capability so much as making the existing "don't ship
placeholder-quality components" instruction concrete and mandatory for
this element type specifically.

(This section originally called for "worked guidance on what 'real' means
per common `style` values" — a lookup table from `style` strings to what a
good mock of that kind contains. The implementing plan dropped this in
favor of the general craft bar above, deliberately: a verification dry run
against `figma-hero`'s `stacked-cards` style produced a genuinely
well-executed mock — three distinct overlapping cards with real content —
from the general guidance alone, with no per-style table. Recorded here so
the drop reads as a decision, not a gap.)

**`background_image`** (photographic/textural) — a real image file,
obtained through a fallback chain evaluated once per element, each step
tried only if the previous one wasn't available or didn't produce a
usable result:

1. **Image-generation tool available in the session** → generate an image
   whose subject/composition matches `style`.
2. **No image-gen tool** → search for a suitable stock/CC-licensed photo
   (`WebSearch` or an available search tool), resolve its direct file URL,
   and download the bytes via `curl`/`wget` through Bash. `WebFetch` can
   locate and read the page and check the license, but it returns a
   text/markdown rendering — it cannot save binary content, so it is not
   the download step itself (confirmed during implementation: an earlier
   draft of this rule named `WebFetch` as the downloader, which doesn't
   work).
3. **Neither produced a usable image** → ask the user: supply their own
   file (path), or accept a flat gradient placeholder as a last resort —
   same tone as the existing gradient guidance in step 7 ("a flat
   background is safer than a botched glow"). Don't silently fall back
   without asking first.

### Asset storage

A file obtained via step 1 or 2 above (not one the user hands over
directly in step 3) is resized/compressed before saving: long edge around
1600–2000px, roughly under 300KB (an available tool like ImageMagick,
`sips`, or `ffmpeg` can do this; an image-generation tool's own output is
often already close to this size). If no resize tool is available, ship
the file as-is but tell the user it's unoptimized — added after
implementation surfaced that an unresized fetch can be a multi-MB DSLR
original, a real page-weight problem for a hero background.

However the file was obtained, it's saved wherever the project already
keeps static assets — a framework's `public/`/`static/` directory, or a
plain `./assets/` folder for a flat HTML page — and referenced the way the
project already references its other images, never hotlinked to an
external URL. Rationale: offline/build-safe, doesn't silently break if the
source disappears or changes, reads as a normal project asset rather than
a dependency on a third party. (A literal `./assets/...` path only works
for a flat HTML project; a framework project needs its own static-asset
convention, e.g. Next.js/Vite's `public/`.)

### Where this lives in `design-system/SKILL.md`

Replace step 8's existing "don't ship placeholder-quality components"
bullet with the concrete two-path procedure above. No other step changes;
`_theme_anchor`, radii/shadows-per-block, and "don't invent elements the
skeleton doesn't list" rules all continue to apply unchanged — this only
fills in *how* to render an element the skeleton already specified.

## Open questions / risks

- Fetched stock photos carry their own licensing terms; this design
  doesn't add a license-tracking mechanism. Acceptable for now since the
  user is generating a page for their own project and can swap the asset
  later — flagged here rather than solved, in case it needs revisiting.
- Session tool availability varies (some sessions may have no image-gen
  tool and no working `WebFetch`), in which case step 3's "ask the user"
  path is the guaranteed-to-terminate fallback.
