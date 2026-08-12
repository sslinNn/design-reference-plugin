# Scroll/Cursor Motion Triggers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach `design-system` to generate scroll-linked (`parallax`, `scrub`) and cursor-linked (`magnetic`, `spotlight`) motion from tokens, and teach `extract-design` to capture those same four effects from a live reference.

**Architecture:** Two-file instructions change — `skills/extract-design/SKILL.md` step 11 (capture) and `skills/design-system/SKILL.md` step 8's motion bullet (generation) — extending the existing `motion` token group with two new trigger keys (`scroll`, `cursor`), each with a `type` field distinguishing the effect, matching the shape `motion.ambient` already uses. No new code, no new backend, no new dependency. Generation is verified by dry-running the updated skill against a synthetic tokens/skeleton payload (no curated reference has scroll/cursor motion yet, so there's nothing real to fetch via `get_design_system`). Capture cannot be dry-run in this environment (no browser access) — verified by self-review only, consistent with the spec's own accepted limitation.

**Tech Stack:** Markdown skill instructions (`skills/extract-design/SKILL.md`, `skills/design-system/SKILL.md`); generation verification via manual generation from a synthetic payload into a scratch directory.

## Global Constraints

- Two new `motion` trigger keys, `scroll` and `cursor`, each keyed by element type with a `type` field distinguishing the effect within the trigger — same shape as the existing `motion.ambient`. (Spec: "Token schema".)
- `scroll.parallax`: `{ type: "parallax", rate: <number>, axis: "x"|"y" }` — continuous, not tied to entering/exiting the viewport. `scroll.scrub`: `{ type: "scrub", properties: [...], from: {...}, to: {...}, range: <string> }` — property value driven by scroll progress across `range`. A value that changes once near entry and then holds steady is `entrance`, not a new trigger — never reclassify existing `entrance` data as `scroll`. (Spec: "Token schema", "Capture".)
- `cursor.magnetic`: `{ type: "magnetic", strength: <number>, max_distance: <string>, radius: <string>, return_duration: <string>, return_easing: <string> }` — element shifts toward a nearby cursor, springs back on leave. `cursor.spotlight`: `{ type: "spotlight", scope: "element"|"section"|"viewport", radius: <string>, color: <string>, follow_duration: <string> }` — glow/gradient tracks cursor position within `scope`. (Spec: "Token schema".)
- Extraction (`extract-design`): `hover` and `cursor` require a live `<source-url>` and claude-in-chrome — no fallback for `cursor` (no honest way to infer cursor-driven effects from footage with no visible cursor). `ambient` and `scroll` can fall back to frame-sampling a recorded preview when no live URL exists. Never fabricate scroll/cursor parameters from a still screenshot alone. (Spec: "Capture", "Non-goals".)
- Generation (`design-system`): the token specifies the effect, not the mechanism — prefer native CSS (`animation-timeline: view()`/`scroll()` for scroll effects, CSS custom properties + `radial-gradient` for spotlight) and fall back to JS (scroll listener + `requestAnimationFrame`, `pointermove` listeners) only when the target stack needs it. Never invent scroll/cursor motion on an element with no matching `motion` entry. (Spec: "Generation".)
- All four new effect types — and only these four, not the pre-existing `hover`/`entrance`/`ambient` — are wrapped in `@media (prefers-reduced-motion: reduce)` in generated code: `scrub` renders at its `to` state, `parallax`/`magnetic`/`spotlight` render static. (Spec: "Generation" / "Reduced motion".)
- No backend/schema changes, no video-background work, no retrofitting reduced-motion onto `hover`/`entrance`/`ambient` — all explicitly out of scope for this plan. (Spec: "Non-goals".)

---

### Task 1: Add scroll/cursor capture guidance to `extract-design/SKILL.md` step 11

**Files:**
- Modify: `skills/extract-design/SKILL.md` (step 11's intro parenthetical, the `- **Ambient.**` bullet's following sibling, the "Omit the whole `motion` group" bullet, and the low-confidence-flagging bullet)

**Interfaces:**
- Consumes: nothing (pure instructions edit).
- Produces: the `scroll`/`cursor` capture procedure — informs what a future curated reference's `motion.scroll`/`motion.cursor` data should look like, which Task 3's synthetic verification payload is modeled on.

- [ ] **Step 1: Read the current step 11 for exact context**

Run: `grep -n "^11\." skills/extract-design/SKILL.md`

Read the surrounding lines (the whole step 11 block, from its intro line through its last sub-bullet) to confirm the live line numbers before editing — don't hardcode line numbers from this plan, the file may have shifted since this plan was written.

Expected: step 11 currently has this structure (line numbers illustrative only, re-derive them from the grep above):
```
11. **`motion` (hover needs a live `<source-url>`, not the screenshot —
    invoke the claude-in-chrome skill first if it isn't already loaded;
    ambient can work from either a live URL or sampled frames of a
    preview capture, see below):**
    - **Hover.** ...
    - **Entrance.** ...
    - **Ambient.** ...
    - Omit the whole `motion` group if the reference has none of
      hover/entrance/ambient — most references, especially simple
      headers, won't have all three. **If two skeleton elements share a
      `type` but have different `variant`s (e.g. a ghost and a solid
      `cta_button`), key their motion entries `"type:variant"`** instead
      of the bare type — they can genuinely animate differently. See
      `stripe-header.json` for a hover-only worked example and
      `motionsites-portal-hero.json` for an ambient-only one.
    - If an entrance or ambient effect is clearly JS-driven with no
      readable inline `transition`/`animation` (e.g. a class toggled by an
      intersection observer, or no live URL at all — only a preview
      capture), estimate duration/easing from what's visually observed and
      flag it as low-confidence in step 13 rather than inventing exact
      numbers.
```

- [ ] **Step 2: Update the step 11 intro parenthetical**

Using the Edit tool, replace this exact text:

```
11. **`motion` (hover needs a live `<source-url>`, not the screenshot —
    invoke the claude-in-chrome skill first if it isn't already loaded;
    ambient can work from either a live URL or sampled frames of a
    preview capture, see below):**
```

With:

```
11. **`motion` (hover and cursor need a live `<source-url>`, not the
    screenshot — invoke the claude-in-chrome skill first if it isn't
    already loaded; ambient and scroll can work from either a live URL or
    sampled frames of a preview capture, see below):**
```

(Whitespace/line-wrapping in the file may differ slightly from this block — match the file's actual indentation, the content is what matters.)

- [ ] **Step 3: Insert the Scroll and Cursor sub-bullets after Ambient**

Using the Edit tool, insert these two new sub-bullets immediately after the existing `- **Ambient.** ...` sub-bullet (i.e. between the end of the Ambient bullet's text and the start of the `- Omit the whole \`motion\` group...` bullet):

```
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
      `Δelement / Δscroll` between two samples. Without a live URL, the
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
```

- [ ] **Step 4: Update the "Omit the whole motion group" bullet to count five triggers**

Using the Edit tool, replace this exact text:

```
    - Omit the whole `motion` group if the reference has none of
      hover/entrance/ambient — most references, especially simple
      headers, won't have all three. **If two skeleton elements share a
      `type` but have different `variant`s (e.g. a ghost and a solid
      `cta_button`), key their motion entries `"type:variant"`** instead
      of the bare type — they can genuinely animate differently. See
      `stripe-header.json` for a hover-only worked example and
      `motionsites-portal-hero.json` for an ambient-only one.
```

With:

```
    - Omit the whole `motion` group if the reference has none of
      hover/entrance/ambient/scroll/cursor — most references, especially
      simple headers, won't have all five. **If two skeleton elements
      share a `type` but have different `variant`s (e.g. a ghost and a
      solid `cta_button`), key their motion entries `"type:variant"`**
      instead of the bare type — they can genuinely animate differently,
      this applies to `scroll`/`cursor` entries too. See
      `stripe-header.json` for a hover-only worked example and
      `motionsites-portal-hero.json` for an ambient-only one.
```

- [ ] **Step 5: Extend the low-confidence-flagging bullet to cover scroll**

Using the Edit tool, replace this exact text:

```
    - If an entrance or ambient effect is clearly JS-driven with no
      readable inline `transition`/`animation` (e.g. a class toggled by an
      intersection observer, or no live URL at all — only a preview
      capture), estimate duration/easing from what's visually observed and
      flag it as low-confidence in step 13 rather than inventing exact
      numbers.
```

With:

```
    - If an entrance, ambient, or scroll effect is clearly JS-driven with
      no readable inline `transition`/`animation` (e.g. a class toggled by
      an intersection observer, or no live URL at all — only a preview
      capture), estimate duration/easing from what's visually observed and
      flag it as low-confidence in step 13 rather than inventing exact
      numbers.
```

- [ ] **Step 6: Self-review — proofread the whole file**

Read the full `skills/extract-design/SKILL.md` file once. Confirm:
- Step numbering (1–13) is unchanged outside step 11's own content.
- No stray markdown (unmatched `**`, broken list nesting, mismatched backtick counts).
- The new Scroll/Cursor bullets read consistently with the file's existing Hover/Entrance/Ambient bullets (same voice, same level of concreteness).

There is no live-browser environment available to functionally test this capture procedure (it describes an interactive claude-in-chrome session) — this proofread is the full verification for this task. Note this limitation explicitly in your report; it is expected, not a gap you need to solve.

- [ ] **Step 7: Commit**

```bash
git add skills/extract-design/SKILL.md
git commit -m "Add scroll/cursor motion capture guidance to extract-design skill"
```

---

### Task 2: Add scroll/cursor generation guidance to `design-system/SKILL.md` step 8

**Files:**
- Modify: `skills/design-system/SKILL.md` (the "Implementing `motion` tokens" bullet inside step 8)

**Interfaces:**
- Consumes: nothing (pure instructions edit).
- Produces: the generation procedure that Task 3 dry-runs against a synthetic payload.

- [ ] **Step 1: Read the current bullet for exact context**

Run: `grep -n "Implementing \`motion\` tokens" skills/design-system/SKILL.md`

Read the surrounding lines to confirm the live line number before editing — don't hardcode a line number from this plan, the file has been edited several times already.

Expected output includes this exact current bullet text:

```
   - **Implementing `motion` tokens: match the given effect, invent nothing extra.** For each element type listed under `motion.hover`, apply a CSS `transition` using exactly the given `properties`/`duration`/`easing`, targeting the given `to` values on `:hover`/`:focus-visible` (and `:active` if the reference distinguishes it). For each element type under `motion.entrance`, animate it to its resting state on mount or on viewport-entry (plain CSS `@keyframes`+`animation`, an IntersectionObserver-driven class, or the target framework's native transition primitive — pick whatever fits the stack, the token specifies the effect, not the mechanism) using the given `type`/`duration`/`easing`/`delay`/`distance`. For each element type under `motion.ambient`, apply a CSS `animation` that loops forever from mount (`animation-iteration-count: infinite`, no trigger, no `:hover`/viewport condition) implementing the given `type` (e.g. `zoom` → a `@keyframes` alternating `transform: scale(1)`/`scale(var(--ambient-scale, 1.05))`) over `duration` with `easing`. **A motion key can be `"type:variant"` instead of a bare type** (e.g. `cta_button:solid` vs `cta_button:ghost`) when a block has more than one skeleton element of that type — match it against that specific element's own `variant`, not every element of the type. **Don't add hover, entrance, or ambient motion to an element that has no matching entry in `motion`** — same rule as not inventing skeleton elements or borrowing another block's radii: an unlisted element stays static.
```

- [ ] **Step 2: Replace the bullet with the extended version covering scroll/cursor/reduced-motion**

Using the Edit tool, replace the exact bullet text found in Step 1 with:

```
   - **Implementing `motion` tokens: match the given effect, invent nothing extra.** For each element type listed under `motion.hover`, apply a CSS `transition` using exactly the given `properties`/`duration`/`easing`, targeting the given `to` values on `:hover`/`:focus-visible` (and `:active` if the reference distinguishes it). For each element type under `motion.entrance`, animate it to its resting state on mount or on viewport-entry (plain CSS `@keyframes`+`animation`, an IntersectionObserver-driven class, or the target framework's native transition primitive — pick whatever fits the stack, the token specifies the effect, not the mechanism) using the given `type`/`duration`/`easing`/`delay`/`distance`. For each element type under `motion.ambient`, apply a CSS `animation` that loops forever from mount (`animation-iteration-count: infinite`, no trigger, no `:hover`/viewport condition) implementing the given `type` (e.g. `zoom` → a `@keyframes` alternating `transform: scale(1)`/`scale(var(--ambient-scale, 1.05))`) over `duration` with `easing`. For each element type under `motion.scroll`, implement `type: "parallax"` or `type: "scrub"` — prefer native CSS scroll-driven animations where the target supports them (`animation-timeline: view()` with a `@keyframes` for `parallax`; `animation-timeline: scroll()` with a `@keyframes` built from `from`/`to` for `scrub`), falling back to a scroll listener + `requestAnimationFrame` computing the output from `rate * scrollY` (`parallax`) or `clamp((scrollY - start) / (end - start), 0, 1)` interpolated between `from` and `to` (`scrub`, over the span given by `range`) when broader compatibility or a framework's own primitive is needed. For each element type under `motion.cursor`: `type: "magnetic"` is a `pointermove` listener over the element (hit-area sized by `radius`) computing the cursor's offset from the element's center, clamped to `max_distance`, applied via `transform: translate(...)`, returning to rest on `pointerleave`/`mouseleave` via a CSS transition using `return_duration`/`return_easing`; `type: "spotlight"` is a `pointermove` listener at the `scope` level (`"element"`/`"section"`/`"viewport"`) updating CSS custom properties (`--cursor-x`/`--cursor-y`) consumed by a `radial-gradient(circle at var(--cursor-x) var(--cursor-y), ...)` background, with `follow_duration` smoothing the motion via a CSS transition on the custom properties where the stack supports animating them (otherwise the glow tracks the cursor directly, no added lag). Wrap every `scroll`/`cursor` effect (not `hover`/`entrance`/`ambient` — those are unaffected) in `@media (prefers-reduced-motion: reduce)` so it's disabled there: a `scrub` element renders at its `to` (fully revealed) state instead of stuck at `from`; `parallax`/`magnetic`/`spotlight` simply render static, with no scroll- or cursor-driven offset. **A motion key can be `"type:variant"` instead of a bare type** (e.g. `cta_button:solid` vs `cta_button:ghost`) when a block has more than one skeleton element of that type — match it against that specific element's own `variant`, not every element of the type. **Don't add hover, entrance, ambient, scroll, or cursor motion to an element that has no matching entry in `motion`** — same rule as not inventing skeleton elements or borrowing another block's radii: an unlisted element stays static.
```

- [ ] **Step 3: Confirm the file still reads correctly end to end**

Run: `sed -n '1,30p' skills/design-system/SKILL.md`

Expected: step numbering 1–9 (including "1a" and step 7) is untouched — only this one bullet inside step 8 changed. Read the full file once to confirm no stray markdown.

- [ ] **Step 4: Commit**

```bash
git add skills/design-system/SKILL.md
git commit -m "Add scroll/cursor motion generation guidance to design-system skill"
```

---

### Task 3: Verify scroll/cursor generation against a synthetic payload

**Files:**
- Create (scratch, not committed): `/tmp/design-system-verify/motion/index.html`

**Interfaces:**
- Consumes: the updated `skills/design-system/SKILL.md` from Task 2. No MCP tool call — no curated reference has `motion.scroll`/`motion.cursor` data yet, so this task's input is a synthetic payload (below), not a `get_design_system` result.
- Produces: a pass/fail verdict for this task's acceptance check — no other task depends on this output.

- [ ] **Step 1: Use this synthetic tokens/skeleton payload as input**

This is not fetched from any tool — treat it exactly as if it were a `get_design_system` result, and generate from it the same way you would generate from a real one:

```json
{
  "hero": {
    "reference": "synthetic-scroll-cursor-test",
    "tokens": {
      "radii": { "button": "999px" },
      "colors": {
        "accent": "#ffb482",
        "background": "#1a1512",
        "text_primary": "#ffffff",
        "text_secondary": "#8e8a8c"
      },
      "shadows": { "default": "none" },
      "spacing": { "content_padding_x": "32px", "content_bottom_gap": "40px" },
      "typography": {
        "body_size": "15px",
        "font_family": "system-ui, sans-serif",
        "headline_size": "40px",
        "headline_weight": "600"
      },
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
    },
    "skeleton": {
      "layout": "full-bleed-photo-bg, reveal-panel-below, cta-row",
      "elements": [
        { "type": "background_image", "style": "abstract-gradient-mesh", "position": "full-bleed" },
        { "type": "headline", "position": "left" },
        { "type": "reveal_panel", "content": "feature callout card", "position": "center" },
        { "type": "cta_button", "variant": "solid", "position": "left" }
      ]
    }
  },
  "_theme_anchor": "hero"
}
```

- [ ] **Step 2: Generate a standalone hero page from this payload**

Following `skills/design-system/SKILL.md` (as edited in Task 2) with this payload as input, write a single self-contained HTML file to `/tmp/design-system-verify/motion/index.html` implementing the `background_image` (hand-coded per the existing mockup/background rule — an abstract gradient mesh is a CSS gradient, not a sourced file, since `style` says "abstract-gradient-mesh" which is textural/generative, not photographic — use your judgment here and note it in your report), `headline`, `reveal_panel`, and `cta_button` elements, with all four `motion.scroll`/`motion.cursor` entries implemented per the updated SKILL.md.

- [ ] **Step 3: Inspect the generated motion implementation**

Run: `grep -n "animation-timeline\|requestAnimationFrame\|pointermove\|prefers-reduced-motion\|radial-gradient\|--cursor-x\|--cursor-y" /tmp/design-system-verify/motion/index.html`

- [ ] **Step 4: Check against acceptance criteria**

Pass requires all of:
- **`hero_bg` parallax:** either `animation-timeline: view()`-based CSS driving its transform, or a scroll listener + `requestAnimationFrame` computing a transform from `rate * scrollY` (`rate` = 0.4) — a real implementation, not a static element with no scroll response.
- **`reveal_panel` scrub:** either `animation-timeline: scroll()`-based CSS with a `@keyframes` from the given `from`/`to` values, or JS computing `clamp((scrollY - start) / (end - start), 0, 1)` and interpolating `opacity`/`transform` between the given `from`/`to` — driven continuously by scroll progress across the panel's viewport transit, not a one-shot reveal.
- **`cta_button:solid` magnetic:** a `pointermove` (or `mousemove`) listener computing offset from the button's center, clamped to `max_distance` (12px), applied via `transform: translate(...)`, with a `pointerleave`/`mouseleave` handler returning it via a transition using `return_duration`/`return_easing` (400ms/ease-out).
- **`hero_bg` spotlight:** a `pointermove` listener at the section level updating `--cursor-x`/`--cursor-y` custom properties, consumed by a `radial-gradient(circle at var(--cursor-x) var(--cursor-y), ...)` on the hero background, with `follow_duration` (150ms) applied as a transition on those properties (or note if the implementer determined the stack can't animate custom properties and documented tracking the cursor directly instead — that's an acceptable, spec-sanctioned choice, not a fail).
- **Reduced motion:** a `@media (prefers-reduced-motion: reduce)` block (or equivalent per-effect guard) disables all four effects — `reveal_panel` must render at its `to` state (fully opaque, `translateY(0)`) under this media query, not stuck at `from`.
- **No invention:** no hover/entrance/ambient motion was added anywhere (none was specified in the payload), and no fifth skeleton element or extra CTA was invented.

If any criterion fails, the Task 2 bullet text is ambiguous or was not followed — revise the bullet in Task 2 and re-run this task before considering the plan complete.

- [ ] **Step 5: Delete the scratch output**

```bash
rm -rf /tmp/design-system-verify/motion
```
