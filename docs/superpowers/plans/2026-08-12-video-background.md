# Video Background Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach `design-system` to generate a `background_video` skeleton element (autoplaying muted loop, optionally scroll/cursor-linked) and teach `extract-design` to tell it apart from `background_image` on a live reference.

**Architecture:** Two-file instructions change — `skills/design-system/SKILL.md` step 8 (the background-sourcing bullet gets a `background_video` clause with its own fallback chain and file-prep rules; the motion-implementation bullet gets one special case for `scroll.scrub` targeting a video) and `skills/extract-design/SKILL.md` step 4 (one sentence on classifying a full-bleed background as video vs image from the live page). No new `motion` token fields, no backend/schema changes — confirmed against `design-reference-backend/docs/reference-format.md`, which does not enumerate skeleton element types (unlike `motion`'s sub-groups, which do have a documented field schema and required the companion commits in the prior sub-project); `background_video` is just another free-form `type` string, same as `background_image`/`mockup_image` already are, so no backend doc change is needed this time. Generation is verified by dry-running the updated skill against a synthetic tokens/skeleton payload, same approach as both prior sub-projects.

**Tech Stack:** Markdown skill instructions (`skills/design-system/SKILL.md`, `skills/extract-design/SKILL.md`); verification via manual generation from a synthetic payload into a scratch directory.

## Global Constraints

- `background_video` is a new skeleton element type, generated as `<video autoplay muted loop playsinline poster="...">` (or the target framework's equivalent), `object-fit: cover`, full-bleed — same positioning as `background_image`. No `motion` entry is required for it to render; scroll/cursor entries are additive. (Spec: "Element type and baseline generation".)
- Sourcing fallback chain, in order, each step tried only if the previous didn't produce a usable result: (1) a video-generation tool if available in the session, (2) a stock/CC-licensed video found via `WebSearch`/an available search tool, direct URL resolved, downloaded via `curl`/`wget` through Bash (`WebFetch` cannot download binary content, only locate/read the page and check the license — same caveat as the image rule), (3) ask the user for their own file. If none of the three produce a usable video, do not invent a placeholder video — downgrade the element to `background_image` instead, tell the user why, and run *that* type's own existing fallback chain from the top (gradient last resort included). (Spec: "Sourcing fallback chain".)
- Any sourced/generated video: audio track stripped unconditionally (element is always muted), resolution capped (~1080p, lower if still large), trimmed to a short loop (seconds, not minutes), via `ffmpeg` (the only realistic video-transcoding tool, unlike images which had 3 options). A poster frame is extracted (`ffmpeg -vframes 1` or equivalent) and run through the *existing* image size/compression rule — no new rule for the poster frame itself. If no transcode tool is available, ship what was obtained but tell the user it's unoptimized — same posture as the image rule, never silently degrade further without saying so. (Spec: "File preparation".)
- `motion.scroll` with `type: "scrub"` on a `background_video` element drives `video.currentTime` directly from scroll progress (`progress * video.duration`) across `range`, instead of interpolating CSS properties — `properties`/`from`/`to` don't apply to this case. `motion.scroll` with `type: "parallax"` and every `motion.cursor` entry need no special case for `background_video` — already type-agnostic from the prior sub-project. No new token fields. (Spec: "`scroll.scrub` on `background_video`".)
- `extract-design`: a full-bleed hero background rendered as a `<video>` tag on the *live* page (not just the screenshot — a still image can't distinguish photo from video) is typed `background_video`, not `background_image`; its content is described via `style` the same way `background_image`'s already is. A `background_video` element whose `video.currentTime` moves in sync with scroll (rather than a CSS property) is still `scroll.scrub` — record it the same way, noting there's no `properties`/`from`/`to` for this case (the video's own duration is the implicit range). (Spec: "Capture: `extract-design`".)
- No new `motion` trigger types/fields, no backend/schema changes, no placeholder-video fallback, no audio support — all explicitly out of scope. (Spec: "Non-goals".)

---

### Task 1: Add `background_video` sourcing and the video-scrub special case to `design-system/SKILL.md`

**Files:**
- Modify: `skills/design-system/SKILL.md` (the background-sourcing bullet inside step 8, and the "Implementing `motion` tokens" bullet inside step 8)

**Interfaces:**
- Consumes: nothing (pure instructions edit).
- Produces: the `background_video` sourcing/generation procedure and the `scroll.scrub`-on-video behavior that Task 3 dry-runs.

- [ ] **Step 1: Read the current background-sourcing bullet for exact context**

Run: `grep -n "Don't ship placeholder-quality components" skills/design-system/SKILL.md`

Read the surrounding lines to confirm the live line number before editing — don't hardcode a line number from this plan, the file has been edited many times already. Confirm the bullet currently ends with (verify this exact fragment is present, re-derive its surrounding line from the grep above rather than trusting a line number here):

```
...Any other decorative content (a generic icon-in-a-box feature card, etc.) still just needs real, on-topic detail rather than filler — one well-executed detail beats several generic ones.
```

- [ ] **Step 2: Insert the `background_video` clause into the background-sourcing bullet**

Using the Edit tool, find this exact fragment within the bullet (the boundary between the `background_image` file-prep sentence and the bullet's closing sentence):

```
However the file was obtained, save it wherever the project already keeps static assets (a framework's `public/`/`static/` directory, or a plain `./assets/` folder for a flat HTML page) and reference it the way the project already references its other images — never hotlink to an external URL, since that breaks the moment the source disappears or changes. Any other decorative content (a generic icon-in-a-box feature card, etc.) still just needs real, on-topic detail rather than filler — one well-executed detail beats several generic ones.
```

Replace it with:

```
However the file was obtained, save it wherever the project already keeps static assets (a framework's `public/`/`static/` directory, or a plain `./assets/` folder for a flat HTML page) and reference it the way the project already references its other images — never hotlink to an external URL, since that breaks the moment the source disappears or changes. A `background_video` element (a full-bleed autoplaying loop) is sourced through the same three-step chain as `background_image` — (1) a video-generation tool if available, (2) a stock/CC-licensed video found via `WebSearch`/an available search tool and downloaded via `curl`/`wget` (same `WebFetch`-can't-download-binaries caveat as images), (3) ask the user for their own file — except its last resort: if none of the three work, don't invent a placeholder video, downgrade the element to `background_image` instead (tell the user why) and run *that* type's own fallback chain from the top, gradient included if it comes to that. A sourced/generated video always ships `muted`, `loop`, `playsinline`, and `autoplay` (autoplay silently fails without `muted`), with its audio track stripped unconditionally (it's muted regardless, so audio is pure dead weight), resolution capped (around 1080p, lower if still large) and trimmed to a short loop (seconds, not minutes) — `ffmpeg` is the realistic tool for all of this, unlike the image tools above. Extract a poster frame (`ffmpeg -vframes 1` or equivalent) and run it through the same image size/compression rule just described for `background_image` — a poster frame is an image once extracted, no separate rule needed. Same posture as images if no transcode tool is available: ship what you got, tell the user it's unoptimized, don't silently degrade further. Any other decorative content (a generic icon-in-a-box feature card, etc.) still just needs real, on-topic detail rather than filler — one well-executed detail beats several generic ones.
```

- [ ] **Step 3: Read the current motion bullet for exact context**

Run: `grep -n "Implementing \`motion\` tokens" skills/design-system/SKILL.md`

Confirm the live line, don't hardcode from this plan.

- [ ] **Step 4: Insert the video-scrub special case into the motion bullet**

Using the Edit tool, find this exact fragment (the boundary between the `motion.cursor` clause and the reduced-motion sentence):

```
`type: "spotlight"` is a `pointermove` listener at the `scope` level (`"element"`/`"section"`/`"viewport"`) updating CSS custom properties (`--cursor-x`/`--cursor-y`) consumed by a `radial-gradient(circle <radius> at var(--cursor-x) var(--cursor-y), <color>, transparent)` background sized by `radius` and tinted by `color`, with `follow_duration` smoothing the motion via a CSS transition on the custom properties — register them with `@property` (e.g. `syntax: '<length-percentage>'`) to make them transitionable — where the stack supports it (otherwise the glow tracks the cursor directly, no added lag). Wrap every `scroll`/`cursor` effect
```

Replace it with:

```
`type: "spotlight"` is a `pointermove` listener at the `scope` level (`"element"`/`"section"`/`"viewport"`) updating CSS custom properties (`--cursor-x`/`--cursor-y`) consumed by a `radial-gradient(circle <radius> at var(--cursor-x) var(--cursor-y), <color>, transparent)` background sized by `radius` and tinted by `color`, with `follow_duration` smoothing the motion via a CSS transition on the custom properties — register them with `@property` (e.g. `syntax: '<length-percentage>'`) to make them transitionable — where the stack supports it (otherwise the glow tracks the cursor directly, no added lag). When the element carrying a `motion.scroll` entry with `type: "scrub"` is a `background_video`, drive `video.currentTime` directly from scroll progress (`progress * video.duration`) across `range` instead of interpolating CSS properties — `properties`/`from`/`to` don't apply to this case and won't be present on the token. `scroll.parallax` and every `motion.cursor` entry need no special case for `background_video` — they move or tint the element as a whole exactly as already described, regardless of what's inside it. Wrap every `scroll`/`cursor` effect
```

- [ ] **Step 5: Confirm the file still reads correctly end to end**

Run: `sed -n '1,30p' skills/design-system/SKILL.md`

Expected: step numbering 1–9 (including "1a" and step 7) is untouched — only the two targeted bullets inside step 8 changed. Read the full file once to confirm no stray markdown (unmatched `**`, broken list nesting).

- [ ] **Step 6: Commit**

```bash
git add skills/design-system/SKILL.md
git commit -m "Add background_video sourcing and scroll-scrub-on-video generation guidance"
```

---

### Task 2: Add `background_video` vs `background_image` classification to `extract-design/SKILL.md`

**Files:**
- Modify: `skills/extract-design/SKILL.md` (step 4)

**Interfaces:**
- Consumes: nothing (pure instructions edit).
- Produces: the classification rule Task 3 doesn't directly exercise (Task 3 dry-runs generation, not capture — capture has no live-browser test available, same limitation as the prior sub-project) but which keeps this plan's two files consistent with each other.

- [ ] **Step 1: Read step 4 for exact context**

Run: `grep -n "^4\." skills/extract-design/SKILL.md`

Confirm the live line, don't hardcode from this plan. Expected current step 4 ends with:

```
   isn't clearly visible in the screenshot, leave it out — do not add it
   because "hero sections usually have one."
```

- [ ] **Step 2: Append the classification sentence to step 4**

Using the Edit tool, find this exact fragment:

```
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
```

Replace it with:

```
4. **Count every visually distinct element before writing the skeleton.**
   This is the single most common source of drift: don't assume a header
   has one button on the right or a hero has a centered CTA — actually
   look and count. Real examples that were wrong before this rule
   existed: a header with three right-side items (an outline button,
   plain text, a solid button) modeled as one `cta_button`; a hero
   modeled with a `subtext` and a centered `cta_button` that don't exist
   on the real page at all. If an element type (subtext, CTA, badge...)
   isn't clearly visible in the screenshot, leave it out — do not add it
   because "hero sections usually have one." A full-bleed hero background
   is `background_video`, not `background_image`, if it's actually a
   `<video>` tag on the live page — a still screenshot can't tell photo
   from video, so check the live page, not just the screenshot, before
   typing this element.
```

- [ ] **Step 3: Self-review — proofread the whole file**

Read the full `skills/extract-design/SKILL.md` file once. Confirm:
- Step numbering (1–13) is unchanged outside step 4's own added sentence.
- No stray markdown.
- The new sentence reads consistently with the rest of step 4's voice.

There is no live-browser environment available to functionally test this classification rule (same limitation noted in the scroll/cursor sub-project) — this proofread is the full verification for this task, not a gap to solve.

- [ ] **Step 4: Commit**

```bash
git add skills/extract-design/SKILL.md
git commit -m "Add background_video vs background_image classification to extract-design skill"
```

---

### Task 3: Verify `background_video` generation against a synthetic payload

**Files:**
- Create (scratch, not committed): `/tmp/design-system-verify/video/index.html`

**Interfaces:**
- Consumes: the updated `skills/design-system/SKILL.md` from Task 1. No MCP tool call — no curated reference has a `background_video` element yet, so this task's input is a synthetic payload (below), not a `get_design_system` result.
- Produces: a pass/fail verdict for this task's acceptance check — no other task depends on this output.

- [ ] **Step 1: Use this synthetic tokens/skeleton payload as input**

Treat this exactly as if it were a `get_design_system` result:

```json
{
  "hero": {
    "reference": "synthetic-video-bg-test",
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
          "hero_bg": {
            "type": "scrub",
            "range": "enters-to-exits-viewport"
          }
        }
      }
    },
    "skeleton": {
      "layout": "full-bleed-video-bg, headline-left, cta-row",
      "elements": [
        { "type": "background_video", "style": "slow-drone-footage-over-mountains", "position": "full-bleed" },
        { "type": "headline", "position": "left" },
        { "type": "cta_button", "variant": "solid", "position": "left" }
      ]
    }
  },
  "_theme_anchor": "hero"
}
```

Note this payload's `hero_bg` scroll entry has no `properties`/`from`/`to` — that's intentional, per this plan's Global Constraints, since it targets a `background_video` element.

- [ ] **Step 2: Generate a standalone hero page from this payload**

Following `skills/design-system/SKILL.md` (as edited in Task 1) with this payload as input, write a single self-contained HTML file to `/tmp/design-system-verify/video/index.html` implementing the `background_video`, `headline`, and `cta_button` elements. For sourcing the actual video file, follow the fallback chain for real: check honestly whether a video-generation tool is available in this session, then whether a stock video search + download is achievable, then whether asking the user is the right next step — whichever branch is actually reachable, follow it genuinely (this mirrors how the prior sub-project's background_image dry run worked; it's fine and expected if this bottoms out at asking the user, or even downgrading to `background_image` if that's what's honestly available — record whichever outcome actually happens).

- [ ] **Step 3: Inspect the generated markup**

Run: `grep -n "<video\|autoplay\|muted\|loop\|playsinline\|poster\|currentTime\|<img" /tmp/design-system-verify/video/index.html`

- [ ] **Step 4: Check against acceptance criteria**

Pass requires all of:
- **Fallback chain genuinely followed:** the report names which branch was reached and why (tool search results, or an actual `AskUserQuestion` call, etc.) — not asserted without evidence. If it bottoms out in a downgrade to `background_image`, that's an acceptable, spec-sanctioned outcome — check that the downgrade was actually communicated to the user, not silent.
- **If a `<video>` element was produced:** it has `autoplay`, `muted`, `loop`, `playsinline`, and a `poster` attribute pointing at a real extracted/sourced image file (not the video file itself, not a missing/broken reference).
- **`hero_bg` scroll-scrub targets `video.currentTime`, not a CSS property:** real JS computing scroll progress across the element's viewport transit and setting `video.currentTime` proportionally — not a `from`/`to` CSS interpolation (the payload deliberately has no `from`/`to`/`properties` for this entry, so a correct implementation can't have interpolated them from nothing).
- **No invention:** no `motion.cursor`, `motion.ambient`, or `motion.hover` entries were added anywhere (none were specified in the payload), and no fourth skeleton element was invented.
- **If the element was downgraded to `background_image` instead:** the same acceptance bar from the prior sub-project's Task 3 applies to it (real sourced/generated file or an honest ask, local relative path, no hotlink) — and the scroll-scrub entry should then interpolate CSS properties/opacity the normal (non-video) way, since `video.currentTime` no longer applies to an `<img>`. Note in the report which of the two element types actually got generated and judge against the matching criteria.

If any criterion fails, the Task 1 bullet text is ambiguous or was not followed — revise the bullet in Task 1 and re-run this task before considering the plan complete.

- [ ] **Step 5: Delete the scratch output**

```bash
rm -rf /tmp/design-system-verify/video
```
