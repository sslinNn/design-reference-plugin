---
name: extract-design
description: Read a design reference screenshot and produce tokens/skeleton JSON matching the curated reference schema, for pasting into the design-reference web app's /admin form. Use when the user runs /extract-design, or asks to extract/curate design tokens or a skeleton from a screenshot for the design-reference library.
argument-hint: <screenshot-path> <block-type> [source-url]
---

## Arguments

Screenshot path, block type (header or hero), and the reference's live
source URL, space-separated: $ARGUMENTS

The screenshot is the basis for colors/typography/skeleton (it's the
agreed-upon, already-captured state). The source URL is used for the live
hover- and cursor-inspection steps below (step 11) — neither can be read
from a still image. It's optional: when curating from a source with no
interactive live page at all (e.g. a marketplace's preview GIF/video for a
template with no public URL), skip hover and cursor entirely and rely on
frame-sampling for ambient/scroll motion instead (see step 11's ambient
and scroll bullets) — don't invent a source URL or fake a hover/cursor
reading to fill the gap.

## Instructions

1. Read the image at the given path using the Read tool. If the screenshot
   shows more than the requested block type (e.g. a full page with both
   header and hero visible), extract only the region matching the
   `<block-type>` argument — don't let the other region's colors/type
   bleed into what you record.
2. Read `docs/reference-format.md` in design-reference-backend for the
   exact tokens/skeleton schema, including the `gradient` group. Tokens
   must include a `colors` group at minimum (background, text_primary,
   text_secondary, accent); skeleton must include a `layout` string and
   may include an `elements` array.
3. **If the requested block type doesn't actually exist as a recognizable
   pattern on this screenshot, say so instead of forcing an extraction.**
   Not every site has a classic marketing hero (headline + subtext + CTA)
   — some homepages are the product itself (a search tool, a dashboard).
   Forcing that pattern onto a page that doesn't have it produces a
   skeleton for something that isn't there. Tell the founder the page
   doesn't fit and suggest either a different URL/route for this brand,
   or curating this brand as header-only (or hero-only).
4. **Count every visually distinct element before writing the skeleton.**
   This is the single most common source of drift: don't assume a header
   has one button on the right or a hero has a centered CTA — actually
   look and count. Real examples that were wrong before this rule
   existed: a header with three right-side items (an outline button,
   plain text, a solid button) modeled as one `cta_button`; a hero
   modeled with a `subtext` and a centered `cta_button` that don't exist
   on the real page at all. If an element type (subtext, CTA, badge...)
   isn't clearly visible in the screenshot, leave it out — do not add it
   because "hero sections usually have one."
5. **Check alignment per element, don't default to centered.** Look at
   the actual x-position of the headline/subtext/buttons relative to the
   viewport width. Left-aligned marketing heroes are at least as common
   as centered ones. Record `position` as `"left"`, `"center"`, or
   `"right"` based on what you actually see, never as a default.
6. **Colors, and give `accent` extra scrutiny.** Sample the dominant
   background, primary text, and secondary/muted text as hex values. For
   `accent` (the color on the primary CTA/branded element): sample it
   carefully and pick one clear, confident hex — this token ends up doing
   more work than the others. When this reference gets combined with
   others, `accent` is one of the colors shared across the whole
   composed page (see `design-system.md`'s `theme_anchor`), not confined
   to this block alone. A muddy or wrong accent sample propagates further
   than a slightly-off secondary text color would. If unsure between two
   close shades, prefer the value that would render correctly against the
   sampled background (contrast should look right at a glance).
7. Typography: font family if identifiable (note low confidence if
   guessing a fallback stack like `system-ui, sans-serif`), and estimate
   pixel sizes by comparison to known landmarks rather than guessing a
   round "88px"-style number — e.g. a header nav bar is typically
   60–72px tall, so a headline that's roughly 3-4x the nav-bar text
   height is a much better estimate than an arbitrary large number.
   Capture both the headline size/weight and the body/nav size/weight —
   the contrast between them is what the generator uses to build a real
   type scale later, not just the headline number alone.
8. Spacing (padding, heights), border radii (look closely: fully round
   pill buttons vs. moderately rounded vs. sharp corners are easy to
   mix up), and `shadows` (box-shadow on individual elements like cards
   or buttons — omit or set `"default": "none"` if you don't see one,
   don't invent one).
9. **`gradient` (separate group from `shadows`):** only add this if the
    screenshot shows a background glow, radial/linear gradient, or
    similar ambient lighting effect (e.g. a colored glow behind a hero
    panel, a diagonal multi-color band). Most references — especially
    headers — won't have this group at all; don't add it speculatively.
    Record which element it's associated with in the `layout` string
    (e.g. `"glow-panel-below"`) so the generator knows what to center it
    behind later — a glow with no anchor point tends to end up mis-sized
    or clipped.
10. **If a skeleton element is a mockup/panel (product screenshot, code
    editor, chat UI...), describe what kind of content it shows**, not
    just that it exists — e.g. `"style": "chat-interface-with-prompt-
    input"` or `"style": "stacked-photo-cards"` (see figma-hero's
    `mockup_image` for a worked example). An element type with no content
    hint tends to get generated as an empty placeholder box later.
11. **`motion` (hover and cursor need a live `<source-url>`, not the
    screenshot — invoke the claude-in-chrome skill first if it isn't
    already loaded; ambient and scroll can work from either a live URL or
    sampled frames of a preview capture, see below):**
    - **Hover.** For each interactive skeleton element (`cta_button`,
      `nav`, and similar) navigate to the element, read its baseline
      computed style, trigger hover, read computed style again, and diff
      `transform`/`background-color`/`color`/`box-shadow`. Read
      `transition-duration`/`transition-timing-function` directly from
      computed style rather than guessing. No visible diff on an element →
      leave that element type out of `motion.hover` entirely, same as any
      other token — don't add a default transition because "buttons
      usually have one."
    - **Entrance.** Scroll so the target block sits below the fold,
      snapshot the element's `opacity`/`transform`, scroll it into view,
      wait roughly half a second to a second, snapshot again, and diff. No
      change → leave that element type out of `motion.entrance`.
    - **Ambient.** A continuous loop with no trigger at all (a slow
      Ken Burns zoom/pan on a hero photo, a shimmering gradient) — check
      for it even when there's no `<source-url>` to interact with (e.g.
      when working from a marketplace preview GIF/video instead of a live
      site): sample a few frames spread across the loop and compare. If
      the visual content is identical frame to frame, there's no ambient
      motion — leave it out. If it visibly shifts, record `type`
      (`zoom`/`pan`/`shimmer`/...), `duration` for one full cycle (real
      timing from the frames/GIF metadata if available), and `easing` if
      inferrable — flag `scale`/`direction` as estimated, not measured,
      since a still-frame comparison can't give exact numbers the way a
      live computed-style read can.
    - **Scroll (`parallax` vs `scrub`).** With a live URL and
      claude-in-chrome: scroll the page in increments spanning the target
      element's transit through the viewport (e.g. 0/25/50/75/100%),
      reading the element's computed `transform` (or the relevant
      property) at each step. A value that keeps changing continuously
      and monotonically across the whole transit is `scrub`; a
      constant-rate offset that isn't tied to entering/exiting the
      viewport (keeps moving as long as the page scrolls, at any scroll
      position) is `parallax`; a value that changes once near entry and
      then holds steady is the existing `entrance` trigger, not a new
      one — record nothing here in that case. Compute `parallax.rate` as
      `Δelement / Δscroll` between two samples, and record `axis` as
      whichever direction (`"x"`/`"y"`) the offset actually moves along.
      Without a live URL, the
      same classification works from frames sampled across a
      scroll-recording GIF/video (the same fallback `ambient` already
      uses) — with no such recording, leave `scroll` out for that element
      rather than guessing a rate.
    - **Cursor (`magnetic` vs `spotlight`).** Requires a live URL and
      claude-in-chrome — there's no frame-sampling fallback for this one,
      unlike ambient/scroll: cursor-driven effects have no honest way to
      be inferred from footage with no visible cursor. Move the cursor to
      a few points at increasing distance from the element (not directly
      on it, to distinguish from `:hover`) and diff computed `transform`
      at each — a shift toward the cursor before real hover is
      `magnetic`; record `strength`/`max_distance`/`radius` from the
      observed offsets. Move the cursor to a few points within the
      block/section and check whether a glow/gradient's position tracks
      it — that's `spotlight`; `scope` is however wide the tracking
      actually extends (test points outside the element itself, within
      its section, to tell `"element"` from `"section"`). No visible
      response to cursor movement at any tested point → leave both out
      for that element.
    - Omit the whole `motion` group if the reference has none of
      hover/entrance/ambient/scroll/cursor — most references, especially
      simple headers, won't have all five. **If two skeleton elements
      share a `type` but have different `variant`s (e.g. a ghost and a
      solid `cta_button`), key their motion entries `"type:variant"`**
      instead of the bare type — they can genuinely animate differently;
      this applies to `scroll`/`cursor` entries too. See
      `stripe-header.json` for a hover-only worked example and
      `motionsites-portal-hero.json` for an ambient-only one.
    - If an entrance, ambient, or scroll effect is clearly JS-driven with
      no readable inline `transition`/`animation` (e.g. a class toggled by
      an intersection observer, or no live URL at all — only a preview
      capture), estimate duration/easing from what's visually observed and
      flag it as low-confidence in step 13 rather than inventing exact
      numbers.
12. Output only the `tokens` and `skeleton` JSON objects, formatted and
    ready to paste directly into the /admin form's two textareas. Do not
    output the full seed-file shape (no id/name/block_type wrapper) — the
    founder fills those fields separately in the form.
13. Note anything low-confidence (approximated font family, an estimated
    rather than measured size, an ambiguous color, an estimated motion
    duration/easing) so the founder knows what to double-check before
    saving. Prefer flagging uncertainty over silently guessing.
