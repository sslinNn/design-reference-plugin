# Design: video backgrounds with scroll/cursor interaction

## Context

The plugin already supports two prior sub-projects toward richer generated
pages: real images for `mockup_image`/`background_image` skeleton elements
(sourcing fallback chain, local asset storage, size/compression bar — see
`docs/superpowers/specs/2026-08-11-mockup-images-design.md`), and
scroll-/cursor-linked motion triggers (`motion.scroll` with `parallax`/
`scrub`, `motion.cursor` with `magnetic`/`spotlight` — see
`docs/superpowers/specs/2026-08-12-scroll-cursor-motion-design.md`, whose
Non-goals explicitly deferred video to "will reuse `scroll.scrub`'s
progress-from-scroll-position math but is not designed here"). This is
that third and final planned sub-project.

## Goals

- Add a `background_video` skeleton element type (distinct from
  `background_image` — different technical requirements: autoplay policy,
  `muted`/`loop`/`playsinline`, a poster frame, and an order-of-magnitude
  larger file) that `design-system` can generate as a simple autoplaying,
  looping background video — the baseline case, with no scroll/cursor tie
  required.
- Let a `background_video` element additionally carry `motion.scroll`/
  `motion.cursor` entries when the source reference actually has them:
  `parallax` and `cursor.spotlight`/`magnetic` already work on any element
  type with zero schema changes (confirmed against the existing
  sub-project 2 design — they're type-agnostic). `scroll.scrub` needs one
  special case: on a `background_video` element, scroll progress drives
  `video.currentTime` directly instead of interpolating CSS properties.
- Source and prepare the actual video file: a fallback chain mirroring
  `background_image`'s (video-gen tool → stock/CC search+download → ask
  user), with video-appropriate size/format handling, and a final fallback
  down to `background_image` (not a placeholder video) if nothing else
  works.
- Teach `extract-design` to tell a `<video>` background apart from an
  `<img>`/CSS one, and to recognize when an existing `scroll.scrub`
  observation is driving `video.currentTime` rather than a CSS property.

## Non-goals

- Any new `motion` trigger types or fields — `scroll.parallax`,
  `cursor.magnetic`, `cursor.spotlight` apply to `background_video`
  unchanged. Only `scroll.scrub`'s *generation-side* behavior gets a
  video-specific branch; its token shape doesn't change.
- Backend/schema changes beyond documenting the new element type in
  `reference-format.md` (companion-commit pattern, same as the prior two
  sub-projects).
- A synthetic "placeholder video" fallback — unlike a flat gradient
  standing in for a photo, there's no honest static substitute for "video
  content." The fallback is to downgrade the element to
  `background_image` and go through *that* element type's own fallback
  chain (which does end in a gradient, if truly nothing else works).
- Audio. Background videos are always `muted`; there is no case in scope
  where a background video plays sound.

## Design

### Element type and baseline generation

`background_video` is generated as a `<video autoplay muted loop
playsinline poster="...">` (or the target framework's equivalent) sized
`object-fit: cover` full-bleed, matching how `background_image` is
positioned today. `poster` is required whenever a poster frame is
available (see Sourcing) — it covers the load-before-play gap and any
context where the video doesn't render (a crawler, a browser that blocks
autoplay outright). No `motion` entry is required for a `background_video`
to render correctly; scroll/cursor entries are additive.

### Sourcing fallback chain

Same shape as `background_image`'s chain, with a video-specific step 4:

1. **Video-generation tool available in the session** → generate a video
   matching `style`.
2. **No video-gen tool** → search for a suitable stock/CC-licensed video
   (`WebSearch` or another available search tool), resolve its direct file
   URL, and download the bytes via `curl`/`wget` through Bash — same
   `WebFetch`-can't-download-binaries caveat as images.
3. **Neither worked** → ask the user for their own file.
4. **Still nothing** → don't invent a placeholder video. Downgrade the
   element to `background_image` instead, tell the user why, and run
   *that* element type's own existing fallback chain from the top
   (image-gen → stock photo → ask → gradient last resort). This is a
   legitimate, spec-sanctioned degrade path, not a failure state to hide.
   A `scroll.scrub` entry on the downgraded element has nothing left to
   interpolate (`properties`/`from`/`to` never applied to the video case)
   — drop it and tell the user, don't invent values for it. This same
   downgrade-or-ask choice also applies if a video *was* sourced but
   couldn't be prepared down to a reasonable size (see File preparation's
   ceiling) — shipping an unprocessed multi-MB loop isn't a real option.

"Available," throughout this whole area of the rule (image-gen, video-gen,
resize, and transcode tool checks alike), means a tool already present in
the session/environment — never install one to satisfy a check. An
earlier draft of this rule stated that only for the image-resize case and
a session read the video/transcode case as licensing an install; the
generation-side text now states the rule once, up front, governing every
tool check in the bullet.

### File preparation

Video is heavier than images by an order of magnitude, so the bar is
different in kind, not just degree:

- **Strip audio unconditionally** — the element is always `muted`, so an
  audio track is pure dead weight.
- **Cap resolution** (around 1080p, lower if the source is still large
  after that) and **trim to a short loop** (seconds, not minutes) — a
  background loop doesn't need feature-length footage.
- **`ffmpeg` is the tool** for all of the above (extract-design's image
  guidance could offer ImageMagick/`sips`/`ffmpeg` as alternatives;
  `ffmpeg` is the only realistic option for video transcoding).
- **Extract a poster frame** (`ffmpeg -vframes 1` or equivalent) and run
  it through the existing image size/compression rule from the
  `mockup-images` sub-project — a poster frame is just an image once
  extracted, no new rule needed for it.
- If no resize/transcode tool is genuinely available (not one to install
  for the occasion — see the availability note above), same posture as the
  image rule: ship what was obtained but tell the user, don't silently
  degrade further without saying so. That posture has a ceiling, though:
  video is heavy enough that "unoptimized" and "a real page-weight
  problem" are different outcomes, not the same one at a different scale.
  If the untranscoded file is more than a few MB, ask the user for a
  smaller/shorter clip (or a poster image to pair with it) instead of
  shipping it as obtained, or downgrade to `background_image` — a
  multi-MB autoplay loop is worse for a real visitor than a static photo.

### `scroll.scrub` on `background_video`

No token shape change. When the element carrying a `scroll.scrub` entry is
`background_video`, generation drives `video.currentTime` directly from
scroll progress (`progress * video.duration`) across `range`, instead of
interpolating the `properties`/`from`/`to` CSS-property machinery the
non-video case uses — `properties`/`from`/`to` simply don't apply to a
video-scrub entry and are omitted from it. `scroll.parallax` and
`cursor.magnetic`/`cursor.spotlight` need no special case at all; they
already move/tint the element as a whole regardless of what's inside it.

Autoplay and scroll-scrub fight each other if both drive `currentTime` at
once — the video's own `loop`/`autoplay` playback keeps advancing while
the scroll handler is also setting it. Generation pauses native playback
for the duration a `scroll.scrub` entry is driving the element, and under
`prefers-reduced-motion: reduce` (which disables the scrub, same as any
other `scroll`/`cursor` effect) a video-scrub element has no `to` value to
rest at the way a CSS-property scrub does — it holds its last frame
(`currentTime` at the video's full `duration`) instead.

### Capture: `extract-design`

Two small additions, not a new procedure:

- When cataloguing skeleton elements (step 4), a full-bleed hero
  background rendered as a `<video>` tag (check the live page, not just
  the screenshot — a still image can't tell photo from video) is
  `background_video`, not `background_image`; describe its content in
  `style` the same way `background_image` already is. That turned out to
  require widening step 10 itself, not just step 4 — step 10 only covered
  mockup/panel `style` descriptions before this plan, and never actually
  said `background_image` (already a real element type) needed one
  either. Both background element types get folded into step 10 together,
  since `design-system`'s whole sourcing chain for both searches/generates
  against `style`.
- In the existing Scroll capture bullet (from the scroll/cursor
  sub-project): if the element under test is a `background_video` and
  scrolling drives its `video.currentTime` in sync with scroll position
  (rather than a CSS property), that's still `scroll.scrub` — record it
  the same way, just note there's no `properties`/`from`/`to` to capture
  for this case (the video's own duration is the implicit range).

### Where this lives

- `skills/design-system/SKILL.md`: extend the existing background-sourcing
  bullet (step 8) with the `background_video` element type, its fallback
  chain (including the downgrade-to-`background_image` step), and file
  preparation; extend the motion-implementation bullet (also step 8) with
  the `scroll.scrub`-on-video special case.
- `skills/extract-design/SKILL.md`: the two small additions above (element
  cataloguing, Scroll bullet note).
- `design-reference-backend/docs/reference-format.md`: turned out to need
  one companion-commit sentence after all — not because skeleton element
  types are enumerated there (they aren't; `background_video` is just
  another free-form `type` string, same as `background_image`, and
  needed no doc change on that count), but because the doc's `motion`
  section *does* document `scrub`'s exact field list (`properties`,
  `from`, `to`, `range`), and that list needed the same
  `background_video` exception (`properties`/`from`/`to` omitted, only
  `range` applies) that the skill files got. The distinction that
  mattered was "is this schema documented with a fixed field list,"
  not "is this a motion field vs. an element type."

## Open questions / risks

- Stock video licensing carries the same unresolved risk as stock photos
  (spec'd and accepted in the `mockup-images` sub-project) — not
  re-litigated here.
- "Around 1080p, trim to a short loop" is a judgment call with no hard
  numeric floor, same posture as the image sub-project's "roughly under
  300KB" — flagged as a deliberate range, not a precise spec, since the
  right size depends on the specific footage.
