---
name: static-pwa-edge-skill
description: Rapid development and deployment standards for standalone Progressive Web Apps (PWA), Web Push notifications on Cloudflare D1/WebCrypto, Cloudflare backend (Pages + Functions/Workers + D1/KV), localization (i18n), CORS bypass, interactive blackout timelines, step-by-step PWA install guides, Chart.js dashboards, SEO (robots/sitemap), and Observability (Edge Cache HIT/MISS, RUM Web Analytics).
---

# 🚀 Cloudflare Autonomous Web Application Standard (Static PWA & Edge Skill)

This skill codifies battle-tested architectural practices developed and proven during the creation of high-load, resilient edge web applications (such as the **Fayna SES** energy portal: Vue 3, TypeScript, PWA, Cloudflare Pages, Functions & KV, SEO, Observability).

---

## 1. 🏗️ Architecture: JAMstack + Edge Proxy + PWA

### A. Technology Stack
* **Frontend**: Vue 3 (Composition API, `<script setup lang="ts">`), TailwindCSS (Pure Light Theme), Lucide Icons.
* **Charts**: `Chart.js` + `vue-chartjs` with selective tree-shaking (Line, Bar).
* **Portability & PWA**: `vite-plugin-pwa` (offline capability, Service Worker, installable on Desktop/iOS/Android).
* **Internationalization (i18n)**: `vue-i18n` with auto-detection (`navigator.language.startsWith('uk') ? 'uk' : 'en'`) and persistent preference in `localStorage`.
* **SEO**: `robots.txt`, `sitemap.xml`, OpenGraph SVG banners, canonical and alternate hreflang links.
* **Observability (o11y)**: Cloudflare Web Analytics beacon, `/api/health` diagnostic route, Edge Cache HIT/MISS telemetry, W3C Server-Timing.

### B. Resolving CORS and Rate Limits via Cloudflare Pages Functions
When an upstream API blocks CORS or enforces strict request quotas:
1. Create `functions/api/[[path]].ts`.
2. The edge function proxies requests to upstream at the Cloudflare Edge layer, spoofing a valid browser `User-Agent`.
3. Set aggressive edge caching and permissive CORS headers:
   ```typescript
   'Access-Control-Allow-Origin': '*',
   'Cache-Control': 'public, max-age=30, s-maxage=60, stale-while-revalidate=300'
   ```
4. Client code follows the **Smart Fetch** pattern: query the local edge proxy `/api/...` first; on failure, fall back directly to upstream.

---

## 2. 📲 PWA Installation & Multi-Platform Guide (iOS / Android / Desktop)

Because Apple iOS Safari does not support the `beforeinstallprompt` event due to system policy, implement a hybrid approach:

### A. Handling `beforeinstallprompt`:
```typescript
const deferredPrompt = ref<any>(null);
const canDirectInstall = ref(false);

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt.value = e;
  canDirectInstall.value = true;
});
```

### B. Universal Install Button Handler (`handleInstallClick`):
1. **If the browser supports direct prompt (Chrome, Edge, Android)**: invoke `deferredPrompt.value.prompt()`.
2. **If direct prompt is unavailable or user is on iOS Safari**: open a localized modal (`PwaInstallModal.vue`) with tabbed instructions:
   * **iOS / Safari**: "Share" $\to$ "Add to Home Screen".
   * **Android**: Chrome Menu (three dots) $\to$ "Install app".
   * **Desktop (Windows/Mac)**: Address bar icon $\to$ "Install app".
3. **Hide Install Trigger in Standalone Mode**:
   When the app is already launched as a PWA (from home screen/desktop icon), hide the install button to avoid clutter:
   ```typescript
   const isStandalone = ref(false);
   onMounted(() => {
     if (typeof window !== 'undefined') {
       isStandalone.value = window.matchMedia('(display-mode: standalone)').matches || (window.navigator as any).standalone === true;
     }
   });
   ```

---

## 3. 🔔 Zero-Cost Web Push Infrastructure on Cloudflare D1 & WebCrypto

Native blackout/alert notifications without third-party paid services (OneSignal, Firebase):

### A. Apple iOS Safari Policy (iOS 16.4+)
On iPhone/iPad, `window.PushManager` and `Notification` are **blocked in standard Safari tabs**.
Push notifications are only available **after the site is added to the Home Screen** (PWA Standalone).
If a user accesses push settings in a regular browser on iOS, display a clear walkthrough modal:
1. Tap "Share" (box with upward arrow ⎋).
2. Choose "Add to Home Screen".
3. Open the app from the Home Screen and tap the bell icon 🔔.

### B. VAPID & Native WebCrypto (Edge-Compatible without Node.js Runtimes)
Cloudflare Workers / Pages Functions do not support legacy Node.js crypto (`crypto.createSign`).
Generate and sign VAPID tokens using the standard **W3C WebCrypto API**:
- Elliptic Curve: `ECDSA P-256` (`ES256`).
- **JWK Private Key Import**: Never construct raw PKCS#8 DER headers manually in buffers (`Invalid PKCS8 input`). Always import base64url private keys as clean JSON Web Keys (`crypto.subtle.importKey('jwk', { kty: 'EC', crv: 'P-256', x, y, d }, ...)`).
- **Apple APNs Web Push Requirements (iOS Safari)**:
  - Apple APNs (`*.apple.com`) strictly rejects hyphenated `Topic` headers (`BadWebPushTopic`). Omit the `Topic` header for `apple.com` endpoints.
  - Apple APNs **requires strict RFC 8291 (`aes128gcm`) encryption**. Empty ping payloads (`Content-Length: 0`) cause delivery drops or WebKit subscription invalidation. Always encrypt payloads using a WebCrypto-compliant library (e.g., `@block65/webcrypto-web-push`).
  - **No SVG in WebKit Notifications**: On iOS Safari, `self.registration.showNotification(title, { badge: '/favicon.svg' })` throws an internal WebKit `TypeError`. Omit `badge` on Apple clients and use raster PNG icons exclusively.
- **Secret Rotation & Zero-Fallback Standard**: Never leave default fallback keys in code (`DEFAULT_VAPID_*`). If secrets are missing in Cloudflare Secrets, throw a clear configuration error instead of failing silently with insecure keys.
- Set `Urgency: high` or `Urgency: normal`.

### C. Preventing Cloudflare D1 Quota Exhaustion (5M row reads/day limit)
On the free D1 tier, full-table scans during high-frequency status checks quickly exhaust read limits.
Always create covering composite indices:
```sql
CREATE INDEX IF NOT EXISTS idx_subs_active_scope ON push_subscriptions(is_active, scope);
CREATE INDEX IF NOT EXISTS idx_subs_stats ON push_subscriptions(is_active, failed_attempts);
```
This guarantees $O(\log N)$ subscriber lookups instead of $O(N)$ full scans.

### D. Anti-Spam Debounce & Collapse Tag
When multiple sensors trip or grid power fluctuates repeatedly within minutes:
- Always send notifications with a static collapse tag: `tag: 'fayna-grid-status'`.
- The mobile OS collapses notifications into a single active status card instead of spamming consecutive alerts.

---

## 4. ⚡ Blackout Detection Algorithm & Visual Timeline

Telemetry with fields `grid` (grid power, W), `load` (consumption, W), `batt` (battery, W):
```typescript
const isBlackout = (gridPower <= 20) && (buildingLoad > 20);
```

### A. 24-Hour Timeline with Exact Fill Percentage
Calculate the exact outage duration $M \in [0, 60]$ minutes per hour:
$$\text{Percent} = \text{round}\left(\frac{M}{60} \times 100\%\right)$$
Fill each hour slot dynamically using CSS gradients:
```typescript
:style="stat.level === 'partial' ? {
  background: `linear-gradient(to top, #f43f5e 0%, #f43f5e ${stat.percent}%, #d1fae5 ${stat.percent}%, #d1fae5 100%)`
} : stat.level === 'full' ? { background: '#f43f5e' } : {}"
```
* **Status Levels**:
  - `none` (< 15 min): 100% green (`220V`).
  - `partial` (15-89%): dynamic rose fill showing percentage (`35%`, `70%`).
  - `full` ($\ge 90\%$): full rose fill (`АКБ` / `BATT`).
  - `future`: upcoming hours (`border-dashed`, dash `—`).

### B. Monthly Backup Energy Calculation:
$$E_{\text{Backup}} = \max(0, \text{Load} - \text{Grid}) \quad \text{[kWh]}$$
If the current month archive returns 404/empty at the start of a month, automatically query the previous month (`YYYY-(MM-1)`).

---

## 5. 🌍 Dual-Language Localization (i18n) & Action-Oriented Switcher

1. **Action-Oriented Switcher**:
   The switcher displays the target language the user will switch to:
   - When active language is `uk` $\to$ button shows **`EN`** (*Switch to English*).
   - When active language is `en` $\to$ button shows **`UA`** (*Switch to Ukrainian*).
2. **Localizing Units & Badges**:
   Units and badge text must pass through `t()`:
   - `t('kwhUnit')` $\to$ `kWh` / `кВт·г`
   - `t('kwUnit')` $\to$ `kW` / `кВт`
   - `t('history.badgeBatt')` $\to$ `BATT` / `АКБ`
3. **Missing Keys Guard**:
   All modal action buttons (`close`, `cancel`, `save`, `gotIt`) must exist in both dictionaries (`uk.json` and `en.json`). Missing keys render as unstyled lowercase strings (e.g. `close`), breaking typography.
4. **Codebase Cleanliness**:
   All code comments, models, and config files must be written in **English**, isolating language strings strictly inside locale files (`src/locales/uk.json`, `src/locales/en.json`).

---

## 6. 🔍 SEO, Social Media Crawlers (Telegram / FB / X) & Indexing

Ensure full SPA indexability by search engines and rich preview cards in messaging platforms (Telegram, WhatsApp, Viber, Facebook, Twitter/X):

### A. Base Files & Meta Tags:
1. `robots.txt` in `public/`:
   ```text
   User-agent: *
   Allow: /
   Sitemap: https://<domain>/sitemap.xml
   ```
2. `sitemap.xml` with alternate language links (`xhtml:link rel="alternate" hreflang="uk"` and `hreflang="en"`).
3. In `index.html`:
   - `<link rel="canonical" href="https://<domain>/" />`
   - `<meta name="robots" content="index, follow" />`
   - `<link rel="alternate" hreflang="uk" ... />` and `hreflang="en"`.
   - **Schema.org Structured Data**: `<script type="application/ld+json">` for `WebApplication` specifying name, URL, description, author (`Person` with backlink), and supported languages (`["en", "uk"]`).
   - **`<noscript>` Fallback**: Clean light-theme card for web crawlers and JS-disabled users explaining service purpose and prompting JavaScript activation.

### B. 🛡️ Strict OpenGraph Standards for Telegram (`TelegramBot`):
Telegram uses an asynchronous crawler that **ignores or delays image downloads** if geometric metadata is missing. For immediate large card preview generation (`summary_large_image`):
1. **Mandatory `og:site_name`**: Must be explicitly set (appears above title in Telegram).
2. **Explicit Dimensions and MIME Type**:
   - `og:image:width` $\to$ `1200`
   - `og:image:height` $\to$ `630` (1.91:1 aspect ratio)
   - `og:image:type` $\to$ `image/png` (or `image/jpeg`)
   - `og:image:secure_url` $\to$ direct HTTPS URL (required for iOS/macOS Telegram clients).
3. **Twitter/X Specification**:
   - `<meta name="twitter:card" content="summary_large_image">` (use `name=""`, never `property=""`).
   - `<meta name="twitter:image" content="https://<domain>/og-image.png">`
4. **Crawler Locales**:
   - `<meta property="og:locale" content="en_US">`
   - `<meta property="og:locale:alternate" content="uk_UA">`
5. **Telegram "Update with content" Handling**:
   When re-parsed via Telegram, ensure semantic headings (`<h1>`, `<p>`) align with `og:description`.

### C. Standard Meta Tag Block:
```html
<!-- Open Graph / Telegram / Facebook / WhatsApp -->
<meta property="og:site_name" content="App Title">
<meta property="og:type" content="website">
<meta property="og:url" content="https://<domain>/">
<meta property="og:title" content="App Title — Concise Feature Headline">
<meta property="og:description" content="Core service purpose, key features, and user benefit.">
<meta property="og:image" content="https://<domain>/og-image.png">
<meta property="og:image:secure_url" content="https://<domain>/og-image.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Preview Banner">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="uk_UA">

<!-- Twitter / X Cards -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="App Title — Concise Feature Headline">
<meta name="twitter:description" content="Core service purpose.">
<meta name="twitter:image" content="https://<domain>/og-image.png">
<meta name="twitter:image:alt" content="Preview Banner">
```

---

## 7. 📊 Observability (o11y) on Cloudflare

1. **Edge Cache Telemetry (`functions/api/[[path]].ts`)**:
   - Check `caches.default.match(cacheKey)`.
   - Return headers `X-Edge-Cache: HIT | MISS`, `X-Proxy-Latency`, and W3C `Server-Timing`.
   - Background cache refresh via `context.waitUntil(cache.put(...))`.
2. **Health Check Route**:
   `GET /api/health` returns JSON with edge node state (Colo, Country, City), Upstream connectivity, and latency in milliseconds.
3. **RUM Web Analytics**:
   Insert lightweight Cloudflare Insights script before `</body>` with `defer` attribute to avoid blocking FCP/LCP.

---

## 8. 🛠️ Common Pitfalls & Solutions (Troubleshooting)

1. **PWA Manifest Validation & Install Errors (Chrome & Lighthouse Audits)**:
   * *Problem*: Chrome DevTools / Lighthouse flags manifest errors (`property 'id' should be specified`, missing maskable icons, screenshots missing).
   * *Solution in `vite.config.ts`*:
     ```typescript
     manifest: {
       id: '/',
       start_url: '/',
       scope: '/',
       name: 'App Name — Descriptive Title',
       short_name: 'AppShort',
       display: 'standalone',
       orientation: 'any',
       icons: [
         { src: '/icon-192.png?v=4', sizes: '192x192', type: 'image/png', purpose: 'any' },
         { src: '/icon-512.png?v=4', sizes: '512x512', type: 'image/png', purpose: 'any' },
         { src: '/icon-512.png?v=4', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
       ],
       screenshots: [
         { src: '/screenshot-desktop.png', sizes: '1280x720', type: 'image/png', form_factor: 'wide', label: 'Desktop View' },
         { src: '/screenshot-mobile.png', sizes: '750x1334', type: 'image/png', form_factor: 'narrow', label: 'Mobile View' }
       ]
     }
     ```
   * *Required `<head>` tags in `index.html`*:
     - `<link rel="manifest" href="/manifest.webmanifest?v=4" />`
     - `<meta name="mobile-web-app-capable" content="yes" />`
     - `<meta name="apple-mobile-web-app-capable" content="yes" />`
     - `<meta name="apple-mobile-web-app-status-bar-style" content="default" />`
     - `<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=4" />`

2. **Stale Assets & PWA Cache Busting**:
   * *Problem*: Users receive stale code, icons, or data after deployment.
   * *Three-Tier Fix*:
     1. **Vite Content Hashing**: Output JS/CSS filenames include unique hashes (`index-[hash].js`).
     2. **Workbox Skip Waiting**: Set `skipWaiting: true`, `clientsClaim: true`, `cleanupOutdatedCaches: true`. The new Service Worker activates immediately without waiting for open tabs to close.
     3. **Query Parameter Versioning (`?v=N`)**: For public root assets (favicon, manifest), append query versions: `/favicon.svg?v=4`, `/manifest.webmanifest?v=4`.

3. **Core Web Vitals (LCP, CLS, INP) Optimization**:
   * *Problem*: Large libraries inflate initial bundles (>400 kB); dynamic card heights cause high CLS (Cumulative Layout Shift).
   * *Solutions*:
     1. **Lazy Loading**: Dynamic imports for heavy dialogs (`defineAsyncComponent`) and Chart.js.
     2. **Skeleton & Placeholders**: Fixed card dimensions before telemetry resolves.
     3. **Atomic Batch Commit**: When aggregating parallel queries (`Promise.allSettled`), never update shared reactive state per-item. Aggregate into a local buffer and assign in one tick (`telemetries.value = nextList`).
     4. **Prevent iOS Safari Focus Jump**: Never set `:disabled` on header buttons. In WebKit, disabling an active button blurs focus to `document.body`, snapping viewport to top (`top: 0`). Use `pointer-events-none opacity-60` and programmatic guards (`if (isRefreshing) return`).

4. **Non-Interactive Wrangler Deploy**:
   * *Solution*: Export Cloudflare credentials directly before invoking Wrangler:
     ```powershell
     $env:CLOUDFLARE_API_TOKEN="<token>"
     $env:CLOUDFLARE_ACCOUNT_ID="<account_id>"
     npx wrangler pages deploy dist --project-name=<name> --commit-dirty=true
     ```

5. **SVG OpenGraph Visual Consistency**:
   * Use pure SVG vector elements (`<polygon>`, `<rect>`, `<path>`) instead of system emojis to prevent font-width discrepancies across Linux/Windows/macOS.

---

## 9. 🚀 One-Click Deployment Pipeline

```bash
# 1. Type-check and build
npm run build

# 2. Deploy to Cloudflare Pages via Wrangler CLI with credentials
$env:CLOUDFLARE_API_TOKEN="<token>"
$env:CLOUDFLARE_ACCOUNT_ID="<account_id>"
npx wrangler pages deploy dist --project-name=<project-name> --commit-dirty=true
```
