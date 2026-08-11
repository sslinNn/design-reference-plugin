# Real Mockup/Background Images Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `design-system`-generated pages render real content for `mockup_image` and `background_image` skeleton elements instead of an empty placeholder or a CSS-gradient standing in for a photo.

**Architecture:** Single-file instructions change to `skills/design-system/SKILL.md` (no new code, no new backend, no new dependency) — extends the existing token/skeleton generation flow with a concrete procedure for two element types. Verified by actually running the (updated) skill against two existing curated references and inspecting the generated output, since the deliverable is a prompt Claude Code follows, not a library with unit tests.

**Tech Stack:** Markdown skill instructions (`skills/design-system/SKILL.md`); verification via the `mcp__design-reference__get_design_system` tool and manual generation into a scratch directory.

## Global Constraints

- `mockup_image` elements (UI panels: chat interface, dashboard, code editor, stacked cards) are always hand-coded as real HTML/CSS/SVG by Claude — never sourced as an image file. (Spec: "Two element types, two different procedures".)
- `background_image` elements (photographic/textural) are sourced as a real file through this exact fallback order, each step tried only if the previous one is unavailable or didn't produce a usable result: (1) an image-generation tool available in the session, (2) search for a stock/CC-licensed photo via `WebSearch`/an available search tool, resolve its direct file URL, and download the bytes via `curl`/`wget` through Bash — `WebFetch` can locate/read the page and check the license but cannot save binary content, so it is not the download step, (3) ask the user for their own file or acceptance of a flat gradient placeholder. Never skip straight to the gradient placeholder without asking. (Spec: "background_image" fallback chain.)
- A file obtained via step (1) or (2) — not one the user hands over directly in step (3) — is resized/compressed before saving: long edge ~1600–2000px, roughly under 300KB; ship as-is with a disclosure to the user if no resize tool is available. (Spec: "Asset storage"; added after the implementing task's own verification run downloaded an unresized 4MB/7600×2426 DSLR original.)
- Every sourced/generated `background_image` file is saved wherever the project already keeps static assets (a framework's `public/`/`static/` directory, or a plain `./assets/` folder for a flat HTML page) and referenced the way the project already references its other images — never hotlinked to an external URL. (Spec: "Asset storage".)
- No backend asset hosting, no changes to `extract-design/SKILL.md`, no scroll/cursor motion, no video backgrounds — all explicitly out of scope for this plan. (Spec: "Non-goals".)
- All pre-existing `design-system/SKILL.md` rules (skeleton is the exact/complete structure, don't invent elements, radii/shadows are per-block, `_theme_anchor` drives shared color/font) continue to apply unchanged — this plan only fills in *how* to render an element the skeleton already specifies.

---

### Task 1: Replace the placeholder-quality bullet in `design-system/SKILL.md` step 8

**Files:**
- Modify: `skills/design-system/SKILL.md` (the bullet inside step 8 that starts `**Don't ship placeholder-quality components.**`)

**Interfaces:**
- Consumes: nothing (pure instructions edit).
- Produces: the two-path procedure text that Tasks 2 and 3 verify by dry-running the skill.

- [ ] **Step 1: Read the current bullet for exact context**

Run: `grep -n "Don't ship placeholder-quality components" skills/design-system/SKILL.md`

Expected output includes this exact current bullet text (inside step 8, currently step numbered per the file's own numbering — read the surrounding lines to confirm the live line number before editing, don't hardcode a line number from this plan):

```
   - **Don't ship placeholder-quality components.** An empty div standing in for an image/mockup, a generic icon-in-a-box feature card, decorative content with no real information in it — these read as bored and unfinished even when the colors are correct. If skeleton.elements includes something like a product mockup or code panel, fill it with content that actually looks like the real thing (realistic example data, not lorem-ipsum-shaped filler) and give it the same attention to detail (spacing, borders, depth) as the block's own tokens imply. One well-executed detail beats several generic ones.
```

- [ ] **Step 2: Replace the bullet with the two-path procedure**

Using the Edit tool, replace the exact bullet text found in Step 1 with:

```
   - **Don't ship placeholder-quality components — and for image-bearing elements, follow the right path for the type.** A `mockup_image` element (a UI panel: chat interface, dashboard, code editor, stacked cards, etc.) is always hand-coded as real HTML/CSS/SVG matching its `style` description — never sourced as an image file. AI image generation reliably produces photography but unreliably produces legible on-screen UI text, so coding the mock yourself is both more reliable and more in your control: realistic example data (not lorem-ipsum-shaped filler), the same attention to spacing/borders/depth as the block's own tokens imply. A `background_image` element (photographic or textural: landscape, texture, abstract) is sourced as a real file through this fallback chain, trying the next step only if the previous one is unavailable or doesn't produce a usable result: (1) if an image-generation tool is available in this session, generate an image matching `style` and save it into the project; (2) otherwise, fetch a suitable stock/CC-licensed photo via `WebFetch` (or another available search tool) matching `style` and save it into the project; (3) if neither worked, ask the user — supply their own file, or accept a flat gradient placeholder as a last resort (same reasoning as the gradient guidance below: a flat background is safer than a botched attempt). Never skip straight to a gradient without trying (1) and (2) first and never skip the ask in (3) — a silent gradient fallback is exactly the "placeholder-quality" outcome this bullet exists to prevent. Whatever file gets sourced or generated for a `background_image`, save it into the user's project (e.g. `./assets/<block>-<element-purpose>.jpg`) and reference it by a relative path — never hotlink to an external URL, since that breaks the moment the source disappears or changes. Any other decorative content (a generic icon-in-a-box feature card, etc.) still just needs real, on-topic detail rather than filler — one well-executed detail beats several generic ones.
```

- [ ] **Step 3: Confirm the file still reads correctly end to end**

Run: `sed -n '1,30p' skills/design-system/SKILL.md`

Expected: step numbering elsewhere in the file (steps 1–9, including the "1a" swap-block step and the "top-nav-overlay" step 7) is untouched — only the one bullet inside step 8 changed. Read the full file once to confirm no stray markdown (unmatched `**`, broken list nesting).

- [ ] **Step 4: Commit**

```bash
git add skills/design-system/SKILL.md
git commit -m "Give design-system a concrete procedure for mockup/background image elements"
```

---

### Task 2: Verify the `mockup_image` path against `figma-hero`

**Files:**
- Create (scratch, not committed): `/tmp/design-system-verify/mockup/index.html`

**Interfaces:**
- Consumes: `mcp__design-reference__get_design_system` tool (`reference_ids: ["figma-hero"]`), and the updated `skills/design-system/SKILL.md` from Task 1.
- Produces: a pass/fail verdict for this task's acceptance check (Step 4) — no other task depends on this output.

- [ ] **Step 1: Fetch the reference data**

Call `mcp__design-reference__get_design_system` with `reference_ids: ["figma-hero"]`.

Expected result includes (this is fixed curated data, already confirmed present):

```json
{
  "hero": {
    "reference": "figma-hero",
    "skeleton": {
      "layout": "two-column, left-aligned-narrow-headline, no-subtext, no-cta-in-hero, colorful-stacked-mockup-right",
      "elements": [
        { "type": "headline", "position": "left", "max_width": "300px" },
        { "type": "mockup_image", "style": "stacked-cards", "position": "right" }
      ]
    }
  },
  "_theme_anchor": null
}
```

- [ ] **Step 2: Generate a standalone hero page from this data**

Following `skills/design-system/SKILL.md` (as edited in Task 1) with this data as input, write a single self-contained HTML file to `/tmp/design-system-verify/mockup/index.html`: a `headline` element (left, max-width 300px) and a `mockup_image` element (right, `style: "stacked-cards"`) using the tokens from Step 1's result.

- [ ] **Step 3: Inspect the generated `mockup_image` markup**

Run: `grep -n "mockup\|<img" /tmp/design-system-verify/mockup/index.html`

- [ ] **Step 4: Check against acceptance criteria**

Pass requires all of:
- No `<img>` tag was used for the mockup (per Task 1's rule, it must be hand-coded HTML/CSS/SVG, not an image file reference).
- The markup visibly represents "stacked cards" (multiple overlapping/offset card-like elements with distinct colors or shadows) — not a single empty `<div>`.
- The element sits on the right per `position: "right"` in the skeleton.

If any criterion fails, the Task 1 bullet text is ambiguous or was not followed — revise the bullet in Task 1 and re-run this task before proceeding to Task 3.

- [ ] **Step 5: Delete the scratch output**

```bash
rm -rf /tmp/design-system-verify/mockup
```

---

### Task 3: Verify the `background_image` path against `motionsites-portal-hero`

**Files:**
- Create (scratch, not committed): `/tmp/design-system-verify/background/index.html`
- Create (scratch, not committed, only if the fallback chain produces one): `/tmp/design-system-verify/background/assets/*`

**Interfaces:**
- Consumes: `mcp__design-reference__get_design_system` tool (`reference_ids: ["motionsites-portal-hero"]`), and the updated `skills/design-system/SKILL.md` from Task 1.
- Produces: a pass/fail verdict for this task's acceptance check (Step 4) — no other task depends on this output.

- [ ] **Step 1: Fetch the reference data**

Call `mcp__design-reference__get_design_system` with `reference_ids: ["motionsites-portal-hero"]`. The result's `hero.skeleton.elements` includes `{ "type": "background_image", "style": "cinematic-sunset-canyon-photo", "position": "full-bleed" }` (already confirmed present in this repo's `.design-system.json` from a prior generation).

- [ ] **Step 2: Generate a standalone hero page from this data**

Following `skills/design-system/SKILL.md` (as edited in Task 1) with this data as input, write a single self-contained HTML file to `/tmp/design-system-verify/background/index.html`, applying the fallback chain from Task 1's Step 2 text for the `background_image` element.

- [ ] **Step 3: Inspect which fallback branch was taken**

Run: `grep -n "background-image\|<img\|assets/" /tmp/design-system-verify/background/index.html`

- [ ] **Step 4: Check against acceptance criteria**

Pass requires exactly one of these three outcomes, matching whatever tools were actually available during Step 2 (this task doesn't mandate which branch — it mandates that the chain was actually followed):

- **If an image-generation tool was available:** a real image file exists under `/tmp/design-system-verify/background/assets/` and the HTML references it by a relative path (not a data URI, not an external URL).
- **If no image-generation tool was available but a stock photo fetch succeeded:** same file-and-relative-path check as above, sourced via `WebFetch`/search instead of generation.
- **If neither worked:** the generation step must have asked the user (visible in this task's own transcript as an `AskUserQuestion` call or equivalent) before falling back to a flat gradient — a gradient present in the HTML with no prior ask is a fail.

If the outcome doesn't match one of these three, the Task 1 bullet text is ambiguous or was not followed — revise the bullet in Task 1 and re-run this task.

- [ ] **Step 5: Delete the scratch output**

```bash
rm -rf /tmp/design-system-verify/background
```
