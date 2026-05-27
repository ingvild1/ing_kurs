# Frontend

Static assets served by the FastAPI backend from the repository root path `/`.

## No build step

This frontend ships zero build tooling — no bundler, no transpiler, no Node, no `package.json`. All client-side JavaScript is either written directly in `app.js` (vanilla JS, served as-is) or vendored as a single static file under `vendor/`. The FastAPI app mounts this directory at `/` with `index.html` as the default document, so opening <http://localhost:8000/> in a browser loads the page and the browser fetches `app.js` and `vendor/tailwind.js` via relative URLs.

## Vendored Tailwind

We vendor a pinned copy of `@tailwindcss/browser` v4.3.0 at `vendor/tailwind.js`. Tailwind classes in `index.html` work because this runtime compiles them in the browser at page load. For production you would swap this in-browser runtime for a build-time Tailwind CLI pipeline — see <https://tailwindcss.com/docs/installation>.

Two SHA-256 values are tracked to keep audits unambiguous:

- **Upstream (jsDelivr body, pre-header):** `b91f8cd2dbae57f19d35a51934e6e4af24865d9725d4acf737a2993794270a1e` — matches the jsDelivr per-file SRI hash and the value recorded in the header comment at the top of `vendor/tailwind.js`. Use this to verify the upstream payload during a re-vendor.
- **Committed file (with header prepended):** `f29049665db504abd160f514c09c26dd995c0c1cbdbe5cd4fcbf47697cbcd504` — matches `shasum -a 256 vendor/tailwind.js` against the file as checked into the repo. Use this to verify the working-tree copy hasn't drifted.

## Re-vendoring procedure (with SHA-256 verification)

When updating Tailwind:

1. Pick a new pinned version V (e.g. `4.4.0`).
2. Verify the dist path against the package manifest:
   ```
   curl -fsSL https://data.jsdelivr.com/v1/package/npm/@tailwindcss/browser@V
   ```
   The browser runtime entry point is typically `dist/index.global.js`.
3. Download:
   ```
   curl -fsSLo frontend/vendor/tailwind.js \
     https://cdn.jsdelivr.net/npm/@tailwindcss/browser@V/dist/index.global.js
   ```
4. Record the SHA-256 of the freshly downloaded file (**before** prepending any header):
   ```
   shasum -a 256 frontend/vendor/tailwind.js
   ```
   Cross-check this value against the per-file SRI hash jsDelivr publishes for the package (visible in the same manifest URL from step 2).
5. Prepend the standard header comment to the file with the new version, SHA-256, and today's date. Keep the existing file body intact.
6. Recompute the committed-file SHA-256 (`shasum -a 256 frontend/vendor/tailwind.js`) and update both SHA-256 values in this README to match.
7. Reload <http://localhost:8000/> and confirm Tailwind classes still render correctly.
