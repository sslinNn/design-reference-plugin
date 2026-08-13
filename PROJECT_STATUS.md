# design-reference — project status

_Last updated: 2026-08-13_

## TL;DR (the pitch)

**design-reference turns "make it look modern" into "make it look exactly
like Stripe's header and Linear's hero."** It's a Claude Code plugin,
backed by an MCP server and a curated reference library, that hands your
coding agent the *exact* tokens (color, type, radii, shadows, motion) and
*structure* (skeleton) for one real product's header and another's hero —
composed into one coherent page with a shared color/type anchor, not a
blended "kind of Stripe-ish" guess. Pick a reference per block instead of
one aesthetic direction for the whole page.

**What's new this week:** the generation side stopped being CSS-only.
Three shipped sub-projects took it from "static tokens → static markup"
to "static tokens *and* real sourced assets *and* scroll/cursor-reactive
motion *and* video backgrounds" — while keeping the same zero-config
promise: run `/design-system <references>`, get back a real, on-brand,
low-drift page.

**Where it stands:** v0.2.0, 12 curated references (7 headers, 5 heroes),
a working web app (gallery, admin curation form, API-key dashboard, auth),
a FastAPI backend with Postgres + MinIO for screenshots, and an MCP server
exposing `list_references`/`get_design_system`/`resolve_config` to any
Claude Code session with the plugin installed. The three newest
capabilities (real image/video sourcing, scroll/cursor motion) are
implemented and dry-run-verified, but **not yet exercised against a real
curated reference** — no reference in the library has scroll, cursor, or
video motion data yet, and the live-capture side of that pipeline has
never run against an actual browser. That's the honest next milestone,
not a shipped-and-proven one.

---

## Architecture

Three repos, one product:

| Repo | Role |
|---|---|
| `design-reference-plugin` (this repo) | The Claude Code plugin: two skills (`extract-design`, `design-system`) as Markdown instructions, plugin manifest, `.mcp.json` pointing at the backend's MCP endpoint. |
| `design-reference-backend` | FastAPI app: Postgres-backed reference storage, MinIO for screenshot uploads, auth (login/signup/API keys), the MCP server itself (`/mcp`), `seed_data/*.json` for the 12 curated references, `docs/reference-format.md` as the schema doc. |
| `design-reference-web` | Next.js app: public gallery (browse/pick per block type, generate a config), `/admin` curation form (paste tokens/skeleton JSON, upload a screenshot), dashboard (API keys), login/signup. |

**The loop:** a founder curates a reference (`/extract-design` on a
screenshot + live URL → paste into `/admin`) → it's stored in Postgres,
screenshot in MinIO → a Claude Code user runs `/design-system
stripe-header linear-hero` (or a saved `cfg_...` id from the gallery) →
the skill calls `get_design_system`/`resolve_config` over MCP → gets back
normalized tokens + skeleton per block → generates real code from it,
following the skill's rules (don't invent structure, don't blend colors
across blocks except through the anchor, etc).

## What's shipped, in order

### Baseline (pre-existing before this session)
Header/hero composition with a shared `_theme_anchor` (one block donates
color/font, every block keeps its own radii/shadows), `hover`/`entrance`/
`ambient` motion triggers, the block-swap workflow ("change the header,
keep the hero" reuses the persisted config instead of re-specifying
everything), and a fix for a structural conflict where a hero with its own
`top-nav-overlay` skeleton would double up with a separate header block.

### Sub-project 1 — real mockup/background images
`mockup_image` elements (chat UI, dashboards, code panels) are hand-coded
HTML/CSS/SVG by Claude — AI image generation is unreliable at legible UI
text, so this is more reliable than sourcing a file. `background_image`
elements (photos/textures) are sourced through a fallback chain:
image-gen tool → stock/CC photo via `WebSearch`+`curl` → ask the user →
gradient as an explicit last resort, never silently. Sourced files are
resized (~1600–2000px / ~300KB), saved into the project's own static-asset
convention (not hardcoded to a flat-HTML `./assets/` path — that was a
bug the final review caught), never hotlinked.

*Caught in review, now fixed: `WebFetch` can't download binary content
(only `curl`/`wget` via Bash can); the asset path must match the target
project's actual convention (`public/` for Next/Vite, not always
`./assets/`).*

### Sub-project 2 — scroll- and cursor-linked motion
Two new `motion` triggers alongside the existing three: `scroll`
(`parallax` — continuous, rate-based; `scrub` — property value driven by
scroll progress across a range) and `cursor` (`magnetic` — element pulled
toward a nearby cursor; `spotlight` — glow/gradient tracking cursor
position within a scope). Generation prefers native CSS
(`animation-timeline`, `@property`-registered custom properties) with a
JS fallback; all four new effects respect `prefers-reduced-motion`
(the pre-existing three don't, by design — untouched).

*Caught in review, now fixed: the two CSS scroll-driven-animation
timelines (`scroll()` vs `view()`) were originally paired backwards with
`parallax`/`scrub` — a real bug the dry run's JS-fallback path never
exercised, only caught by the final whole-plan review reasoning through
the actual CSS semantics.*

### Sub-project 3 — video backgrounds
`background_video`: an autoplaying, muted, looping `<video>` with a poster
frame, full-bleed. Sourcing mirrors the image chain (video-gen tool →
stock/CC video → ask user) with a video-specific last resort: downgrade to
`background_image` rather than inventing a placeholder video. File prep
(strip audio, cap ~1080p, trim to a short loop, extract poster) runs
through `ffmpeg` *if genuinely already present* — never installed for the
occasion. `scroll.scrub` targeting a video element drives `video.
currentTime` directly instead of interpolating CSS properties, with
native playback paused so autoplay and the scroll-driven position don't
fight each other.

*Caught in review, now fixed: a dry run initially `pip install`-ed a
missing `ffmpeg` to complete file-prep — ruled out of bounds and the rule
now says explicitly that "available" means already-present, never
install-to-acquire (this reasoning was then hoisted to govern *every*
tool-availability check in the sourcing bullet, not just the one that
tripped it). A second dry run then shipped an unprocessed 7.4MB/20s video
as "fine" under the old wording — closed with an explicit size ceiling.
The final review also caught that `extract-design`'s capture side had
never been taught to recognize `video.currentTime`-driven scroll as
`scroll.scrub` at all — the flagship feature of this sub-project could
never have been fed by a real curated reference until that was fixed.*

## Current data state

12 curated references (`seed_data/*.json` in the backend repo):

- **Headers (7):** airbnb, figma, mailchimp, notion, stripe, vercel, +1
- **Heroes (5):** figma, framer, linear, mailchimp, notion, motionsites-portal

**Motion coverage:** 6 references have `hover`, 1 has `entrance`, 1
(`motionsites-portal-hero`) has `ambient`. **Zero references have
`scroll`, `cursor`, or `background_video` data.** Every check performed on
these three new capabilities in this session used either a synthetic
hand-written payload or a live dry-run against a throwaway `/tmp` scratch
file — never the real `get_design_system`/`resolve_config` path against
real stored data.

## What's genuinely untested

This is the honest gap, not a footnote:

1. **Live capture for scroll/cursor/video has never run.** `extract-design`'s
   new Scroll/Cursor bullets describe an interactive claude-in-chrome
   procedure (increment-scroll and sample computed style; move the cursor
   and diff). No browser was available in the session that wrote and
   verified those instructions — they're internally reviewed for
   consistency, not battle-tested against a real page.
2. **No curated reference exercises the new schema.** Generation was
   verified with synthetic payloads matching the intended shape, not with
   data that actually came out of the capture pipeline above. If capture
   produces something subtly different from what the synthetic payloads
   assumed, generation's real-world behavior is unverified.
3. **`design-reference-web` has uncommitted in-progress changes**
   (`admin`, `dashboard`, `gallery`, nav — modified and new files, not
   part of this session's work) — a separate, currently-open thread.

## How to test it right now

Services observed running during this session (confirm before relying on
them, they may have been restarted since):

| Service | Where | Port |
|---|---|---|
| Backend API + MCP | `design-reference-backend`, `uvicorn app.main:app --reload` | `:8000` (`/mcp` for the plugin) |
| Web app | `design-reference-web`, `next dev` | `:3000` |
| MinIO | `design-reference-backend/.bin/minio`, `make minio` | `:9010` (API), `:9011` (console) |

`.mcp.json` in this repo points the plugin at `http://localhost:8000/mcp`.

**Three test layers, cheapest first:**

1. **Regression check on existing data** — run `/design-system figma-hero`
   (tests hand-coded `mockup_image`) and `/design-system <a header>
   motionsites-portal-hero` (tests sourced `background_image` + `ambient`)
   against the real MCP tool, not a synthetic payload.
2. **New-schema generation, still without a browser** — hand-write a
   config with `motion.scroll`/`motion.cursor`/`background_video` (the
   plans in `docs/superpowers/plans/2026-08-1{1,2}-*.md` have ready-made
   example payloads), save it via `/admin` as a `cfg_...`, run
   `/design-system cfg_...`. First time the new schema goes through the
   *real* `resolve_config` path.
3. **Live capture, the real gap** — connect claude-in-chrome, pick a real
   site with parallax/magnetic/spotlight/scroll-video (Awwwards-style
   sites are a good hunting ground), run `/extract-design` against it,
   check whether the new Scroll/Cursor bullets produce sane tokens, save
   it, then generate from that reference. This closes the loop on real
   data for the first time.

## Suggested next steps

- Run test layer 3 above — it's the only way to know if the capture-side
  instructions actually work, and it's currently pure judgment-call text
  that's never seen a live page.
- Curate at least one reference each for `scroll`, `cursor`, and
  `background_video` once capture is validated, so the gallery has real
  examples and future generation runs exercise real data by default.
- `design-reference-web`'s uncommitted changes are a separate open thread
  — worth finding out what state that work is in before it's lost or
  conflicts with anything else.
