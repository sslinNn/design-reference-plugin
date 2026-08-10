---
description: Load design tokens and structural skeletons for one or more curated design references, grouped by block type (header, hero), and use them to generate on-brand UI code with low drift from the source references.
argument-hint: [reference-id...] | [config-id]
---

## Arguments

A saved config id from the web gallery, or reference ids to use directly, space-separated, plus whatever else the user said in plain language: $ARGUMENTS

## Instructions

1. Take the reference ids (or the single `cfg_...` config id) out of $ARGUMENTS. Ignore this step's output for step 2 below — it's just the ids.
2. If the remaining text says which block should set the color theme (e.g. "let the header set the colors", "keep it stripe's white", "match the hero"), resolve that to one of the requested block types and pass it as `theme_anchor`. Otherwise pass no `theme_anchor` — the default (the hero, if one was requested) already makes every block compose into one theme with zero input from the user, which is the common case.
3. If $ARGUMENTS resolved to a single `cfg_` id, call the `resolve_config` tool with that id (and `theme_anchor` if set in step 2). Otherwise call `get_design_system` with the reference ids as a list (and `theme_anchor` if set).
4. `get_design_system`/`resolve_config` normalize every block's visual language (colors incl. accent, radii, shadows, and typography's font_family) to match the anchor block so blocks always compose into one design — only structure (skeleton) and component-specific sizes/spacing stay per block's own reference. Don't ask the user to pick an anchor up front; only act on it if they mention one, and only re-run with a different `theme_anchor` if they ask to change it after seeing the result.
5. If the tool call fails because a reference id is unknown, call `list_references` to show the user what's available and ask them to pick again. If it fails because the config id is unknown, tell the user the link may have expired and point them back to the gallery. If it fails because of an unknown `theme_anchor`, tell the user which block types were actually requested and ask in plain language which one should set the theme.
5. For each block type returned (e.g. `header`, `hero`), use its `skeleton` as the structural scaffold and its `tokens` as the concrete values (colors, typography, spacing, radii, shadows) when generating that block's code. Do not invent structure or values outside what these two fields specify.
6. Persist the resolved design tokens to `.design-system.json` in the project root so follow-up requests in this conversation can reference them without calling the tool again.
