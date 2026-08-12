# Design: scroll- and cursor-linked motion triggers

## Context

`skills/design-system/SKILL.md`'s motion group currently supports three
triggers, each keyed by element type: `hover` (state change on
`:hover`/`:focus-visible`), `entrance` (one-shot reveal when an element
first scrolls into view), and `ambient` (a continuous loop with no
trigger at all, e.g. a slow Ken Burns zoom). `skills/extract-design/SKILL.md`
step 11 captures all three from a live reference site (via the
claude-in-chrome skill) or, for ambient only, by sampling frames of a
recorded preview when no live URL exists.

This is the second of three planned sub-projects toward richer generated
pages (mockup images → **scroll/cursor motion triggers** → video
backgrounds; see
`docs/superpowers/specs/2026-08-11-mockup-images-design.md`). Mockup
images shipped. Video backgrounds are still out of scope and will get
their own spec/plan cycle, though they will build on the scroll-scrub
mechanics defined here (a video's `currentTime` scrubbed by scroll
position needs the same progress-from-scroll-position math as
`scroll.scrub`).

## Goals

- Add two new motion triggers, `scroll` and `cursor`, each with two
  concrete effect types, so `design-system` can generate:
  - `scroll` → `parallax` (element moves at a rate relative to scroll,
    unbounded/continuous) and `scrub` (a property's value is driven
    directly by scroll progress through a defined range — not a one-shot
    reveal, which `entrance` already covers).
  - `cursor` → `magnetic` (an element shifts toward a nearby cursor, then
    springs back) and `spotlight` (a glow/gradient follows the cursor's
    position within some scope: the element, its containing section, or
    the whole viewport).
- Extend `extract-design` to capture all four from a live reference
  (preferred) or a recorded preview (fallback, scroll-based effects only —
  see Non-goals), matching the tiered fallback story already used for
  hover/ambient.
- Apply `prefers-reduced-motion: reduce` to all four new effect types in
  generated code, since continuous scroll/cursor-linked motion is more
  likely to cause discomfort than a hover transition.

## Non-goals

- Video backgrounds (separate sub-project; will reuse `scroll.scrub`'s
  progress-from-scroll-position math but is not designed here).
- Backend/schema changes — `tokens`/`skeleton` are stored as free-form
  JSON already; no new fields need server-side support.
- Retrofitting `prefers-reduced-motion` onto the existing `hover`,
  `entrance`, or `ambient` triggers — out of scope, not requested.
- A live-interaction fallback for `cursor` capture when no live URL is
  available. Unlike `ambient` (inferable from frames alone) or `scroll`
  (inferable from a scroll-recording GIF/video), cursor-driven effects
  have no honest way to be inferred from passive footage with no visible
  cursor — extraction leaves them unmeasured rather than guessing (see
  Design).

## Design

### Token schema

Two new keys under the existing `motion` group, in the same shape as
`motion.ambient` (keyed by element type; a `type` field distinguishes the
effect within the trigger; `"type:variant"` keys still apply when a block
has more than one element of that type, per the existing rule):

```json
"motion": {
  "scroll": {
    "hero_bg": { "type": "parallax", "rate": 0.4, "axis": "y" },
    "reveal_panel": {
      "type": "scrub",
      "properties": ["opacity", "transform"],
      "from": { "opacity": 0, "transform": "translateY(40px)" },
      "to": { "opacity": 1, "transform": "translateY(0)" },
      "range": "enters-to-exits-viewport"
    }
  },
  "cursor": {
    "cta_button:solid": {
      "type": "magnetic",
      "strength": 0.3,
      "max_distance": "12px",
      "radius": "80px",
      "return_duration": "400ms",
      "return_easing": "ease-out"
    },
    "hero_bg": {
      "type": "spotlight",
      "scope": "section",
      "radius": "300px",
      "color": "rgba(255,255,255,0.08)",
      "follow_duration": "150ms"
    }
  }
}
```

Field notes:
- `scroll.parallax.rate` — element displacement per unit of scroll
  displacement (`Δelement / Δscroll` between two extraction samples); sign
  indicates direction (negative = opposite to scroll direction).
- `scroll.scrub.range` — the scroll span the property interpolates over;
  `"enters-to-exits-viewport"` is the common case (element's own transit
  through the viewport), a explicit distance (e.g. `"0-100vh"`) covers
  page-anchored cases.
- `cursor.magnetic.radius` — activation distance from the element's edge
  at which the pull begins (not the element's own size).
- `cursor.spotlight.scope` — `"element"` | `"section"` | `"viewport"`:
  how large an area the cursor is tracked within to drive the glow's
  position.

The four effects use three different position references (scroll offset;
cursor offset from element center; absolute cursor position within
`scope`), which is why each gets its own field set rather than one shared
template — forcing a common shape here would either under-specify one
effect or carry unused fields on the others.

### Capture: `extract-design/SKILL.md` step 11

Two new sub-bullets, following the same "live first, frame-sampling
fallback, omit rather than invent" structure the existing hover/ambient
bullets use:

**Scroll (`parallax` vs `scrub`).** With a live URL and claude-in-chrome:
scroll the page in increments spanning the target element's transit
through the viewport (e.g. 0/25/50/75/100%), reading the element's
computed `transform` (or the relevant property) at each step. Classify by
the pattern: a value that keeps changing continuously and monotonically
across the whole transit is `scrub`; a constant-rate offset that isn't
tied to entering/exiting the viewport (keeps moving as long as the page
scrolls, at any scroll position) is `parallax`; a value that changes once
near entry and then holds steady is the existing `entrance` trigger, not
a new one — record nothing here in that case. Compute `parallax.rate` as
`Δelement / Δscroll` between two samples. Without a live URL, the same
classification works from frames sampled across a scroll-recording
GIF/video (same fallback `ambient` already uses) — if there's no such
recording, leave `scroll` out for that element rather than guessing a
rate.

**Cursor (`magnetic` vs `spotlight`).** Requires a live URL and
claude-in-chrome — there is no frame-sampling fallback (see Non-goals).
Move the cursor to a few points at increasing distance from the element
(not directly on it, to distinguish from `:hover`) and diff computed
`transform` at each — a shift toward the cursor before real hover is
`magnetic`; record `strength`/`max_distance`/`radius` from the observed
offsets. Move the cursor to a few points within the block/section and
check whether a glow/gradient's position tracks it — that's `spotlight`;
`scope` is however wide the tracking actually extends (test points
outside the element itself, within its section, to tell `"element"` from
`"section"`). No visible response to cursor movement at any tested point
→ leave both out for that element.

### Generation: `design-system/SKILL.md` step 8's motion bullet

Two new paragraphs alongside the existing hover/entrance/ambient
guidance, holding to the same principle: **the token specifies the
effect, not the mechanism** — pick whatever fits the target stack, invent
nothing beyond what the token specifies.

**`scroll.parallax` / `scroll.scrub`.** Prefer native CSS scroll-driven
animations where the target supports them: `animation-timeline: view()`
with a `@keyframes` for `parallax`, `animation-timeline: scroll()` with a
`@keyframes` built from `from`/`to` for `scrub` — no JS, no jank. Where
broader compatibility or a framework's own primitive is needed, fall back
to a scroll listener + `requestAnimationFrame` computing the output from
`rate * scrollY` (`parallax`) or `clamp((scrollY - start) / (end - start),
0, 1)` interpolated between `from` and `to` (`scrub`).

**`cursor.magnetic`.** A `pointermove` listener over the element (with a
hit-area sized by `radius`) computes the cursor's offset from the
element's center, clamps it to `max_distance`, and applies it via
`transform: translate(...)`; on `pointerleave`/`mouseleave`, a CSS
transition using `return_duration`/`return_easing` returns it to rest.

**`cursor.spotlight`.** A `pointermove` listener at the `scope` level
updates CSS custom properties (`--cursor-x`/`--cursor-y`) consumed by a
`radial-gradient(circle at var(--cursor-x) var(--cursor-y), ...)`
background; `follow_duration` smooths the motion via a CSS transition on
the custom properties where the stack supports animating them, otherwise
the glow tracks the cursor directly with no added lag.

**Reduced motion.** All four effects — and only these four, not the
existing `hover`/`entrance`/`ambient` triggers — are wrapped so that under
`@media (prefers-reduced-motion: reduce)` the effect is disabled and the
element renders at its resting state: `scrub` renders at its `to` (fully
revealed) state rather than stuck at `from`; `parallax`/`magnetic`/
`spotlight` simply render static, with no scroll- or cursor-driven
offset.

### Where this lives

- `skills/extract-design/SKILL.md` step 11: two new sub-bullets, same
  structure/tone as the existing hover/entrance/ambient ones.
- `skills/design-system/SKILL.md` step 8's motion-implementation bullet:
  two new paragraphs plus the reduced-motion paragraph, alongside the
  existing hover/entrance/ambient guidance. No other step changes;
  `_theme_anchor`, per-block radii/shadows, and "don't invent elements
  the skeleton doesn't list" all continue to apply unchanged.

## Open questions / risks

- `scroll.scrub`'s `range: "enters-to-exits-viewport"` vs. an explicit
  distance is a judgment call at extraction time with no hard rule for
  which to record when both would visually work — flagged here rather
  than solved; low risk since either renders correctly, it only affects
  how portable the effect is if the element's size changes.
- No fallback exists for capturing `cursor` effects without a live URL
  (see Non-goals). If a curator wants to add a cursor-heavy reference from
  a source with no live page, those effects simply won't be captured —
  that's an accepted limitation, not a gap to silently paper over.
