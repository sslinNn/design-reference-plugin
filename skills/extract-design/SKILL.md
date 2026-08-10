---
name: extract-design
description: Read a design reference screenshot and produce tokens/skeleton JSON matching the curated reference schema, for pasting into the design-reference web app's /admin form. Use when the user runs /extract-design, or asks to extract/curate design tokens or a skeleton from a screenshot for the design-reference library.
argument-hint: <screenshot-path> <block-type>
---

## Arguments

Screenshot path and block type (header or hero), space-separated: $ARGUMENTS

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
11. Output only the `tokens` and `skeleton` JSON objects, formatted and
    ready to paste directly into the /admin form's two textareas. Do not
    output the full seed-file shape (no id/name/block_type wrapper) — the
    founder fills those fields separately in the form.
12. Note anything low-confidence (approximated font family, an estimated
    rather than measured size, an ambiguous color) so the founder knows
    what to double-check before saving. Prefer flagging uncertainty over
    silently guessing.
