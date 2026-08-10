---
name: extract-design
description: Read a design reference screenshot and produce tokens/skeleton JSON matching the curated reference schema, for pasting into the design-reference web app's /admin form. Use when the user runs /extract-design, or asks to extract/curate design tokens or a skeleton from a screenshot for the design-reference library.
argument-hint: <screenshot-path> <block-type>
---

## Arguments

Screenshot path and block type (header or hero), space-separated: $ARGUMENTS

## Instructions

1. Read the image at the given path using the Read tool.
2. Read `docs/reference-format.md` in design-reference-backend (or infer
   from `seed_data/stripe-header.json` as a worked example) for the exact
   tokens/skeleton schema: tokens must include a `colors` group at minimum
   (background, text_primary, text_secondary, accent); skeleton must
   include a `layout` string and may include an `elements` array.
3. Analyze the screenshot: dominant colors (background, text, accent),
   typography (font family if identifiable, relative sizes/weights),
   spacing (padding, heights), border radii, shadows, and structural
   layout (element positions, e.g. "logo-left, nav-center, cta-right").
4. Output only the `tokens` and `skeleton` JSON objects, formatted and
   ready to paste directly into the /admin form's two textareas. Do not
   output the full seed-file shape (no id/name/block_type wrapper) — the
   founder fills those fields separately in the form.
5. Note anything low-confidence (e.g. an approximated font family) so the
   founder knows what to double-check before saving.
