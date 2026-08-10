---
name: extract-design
description: Read a design reference screenshot and produce tokens/skeleton JSON matching the curated reference schema, for pasting into the design-reference web app's /admin form. Use when the user runs /extract-design, or asks to extract/curate design tokens or a skeleton from a screenshot for the design-reference library.
argument-hint: <screenshot-path> <block-type>
---

## Arguments

Screenshot path and block type (header or hero), space-separated: $ARGUMENTS

## Instructions

1. Read the image at the given path using the Read tool.
2. Read `docs/reference-format.md` in design-reference-backend for the
   exact tokens/skeleton schema, including the `gradient` group. Tokens
   must include a `colors` group at minimum (background, text_primary,
   text_secondary, accent); skeleton must include a `layout` string and
   may include an `elements` array.
3. **Count every visually distinct element before writing the skeleton.**
   This is the single most common source of drift: don't assume a header
   has one button on the right or a hero has a centered CTA — actually
   look and count. Real examples that were wrong before this rule
   existed: a header with three right-side items (an outline button,
   plain text, a solid button) modeled as one `cta_button`; a hero
   modeled with a `subtext` and a centered `cta_button` that don't exist
   on the real page at all. If an element type (subtext, CTA, badge...)
   isn't clearly visible in the screenshot, leave it out — do not add it
   because "hero sections usually have one."
4. **Check alignment per element, don't default to centered.** Look at
   the actual x-position of the headline/subtext/buttons relative to the
   viewport width. Left-aligned marketing heroes are at least as common
   as centered ones. Record `position` as `"left"`, `"center"`, or
   `"right"` based on what you actually see, never as a default.
5. Colors: sample the dominant background, primary text, secondary/muted
   text, and accent (the color used on the primary CTA button or another
   clearly "branded" element) as hex values. If unsure between two close
   shades, prefer the value that would render correctly against the
   sampled background (contrast should look right at a glance).
6. Typography: font family if identifiable (note low confidence if
   guessing a fallback stack like `system-ui, sans-serif`), and estimate
   pixel sizes by comparison to known landmarks rather than guessing a
   round "88px"-style number — e.g. a header nav bar is typically
   60–72px tall, so a headline that's roughly 3-4x the nav-bar text
   height is a much better estimate than an arbitrary large number.
7. Spacing (padding, heights), border radii (look closely: fully round
   pill buttons vs. moderately rounded vs. sharp corners are easy to
   mix up), and `shadows` (box-shadow on individual elements like cards
   or buttons — omit or set `"default": "none"` if you don't see one,
   don't invent one).
8. **`gradient` (separate group from `shadows`):** only add this if the
   screenshot shows a background glow, radial/linear gradient, or similar
   ambient lighting effect (e.g. a colored glow behind a hero panel, a
   diagonal multi-color band). Most references — especially headers —
   won't have this group at all; don't add it speculatively.
9. Output only the `tokens` and `skeleton` JSON objects, formatted and
   ready to paste directly into the /admin form's two textareas. Do not
   output the full seed-file shape (no id/name/block_type wrapper) — the
   founder fills those fields separately in the form.
10. Note anything low-confidence (approximated font family, an estimated
    rather than measured size, an ambiguous color) so the founder knows
    what to double-check before saving. Prefer flagging uncertainty over
    silently guessing.
