---
description: Load design tokens and structural skeletons for one or more curated design references, grouped by block type (header, hero), and use them to generate on-brand UI code with low drift from the source references.
argument-hint: [reference-id...] | [config-id]
---

## Arguments

Either a saved config id from the web gallery, or reference ids to use directly, space-separated: $ARGUMENTS

## Instructions

1. If $ARGUMENTS is a single argument starting with `cfg_`, call the `resolve_config` tool with that id. Otherwise, call the `get_design_system` tool with the reference ids from $ARGUMENTS as a list.
2. If the tool call fails because a reference id is unknown, call `list_references` to show the user what's available and ask them to pick again. If it fails because the config id is unknown, tell the user the link may have expired and point them back to the gallery.
3. For each block type returned (e.g. `header`, `hero`), use its `skeleton` as the structural scaffold and its `tokens` as the concrete values (colors, typography, spacing, radii, shadows) when generating that block's code. Do not invent structure or values outside what these two fields specify.
4. Persist the resolved design tokens to `.design-system.json` in the project root so follow-up requests in this conversation can reference them without calling the tool again.
