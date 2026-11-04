---
name: static-pwa-edge-skill
description: Стандарт швидкої розробки та розгортання автономних вебзастосунків (PWA), Web Push сповіщень на Cloudflare D1/WebCrypto, бекенду на Cloudflare (Pages + Functions/Workers + D1/KV), локалізації (i18n), обходу CORS, інтерактивних таймлайнів блекаутів, покрокового гіда встановлення PWA, Chart.js дашбордів, SEO (robots/sitemap) та Observability (Edge Cache HIT/MISS, RUM Web Analytics).
---

# 🚀 Стандарт розробки автономних веб-додатків на Cloudflare (Static PWA & Edge Skill)

Цей скіл закріплює перевірені архітектурні практики, застосовані під час створення енергетичного порталу **Fayna SES** (Vue 3, TypeScript, PWA, Cloudflare Pages, Functions & KV, SEO, Observability).

---

## 1. 🏗️ Архітектура: JAMstack + Edge Proxy + PWA

### А. Стек технологій
* **Фронтенд**: Vue 3 (Composition API, `<script setup lang="ts">`), TailwindCSS (Pure Light Theme), Lucide Icons.
* **Графіки**: `Chart.js` + `vue-chartjs` з вибірковим Tree-shaking (Line, Bar).
* **Мобільність & PWA**: `vite-plugin-pwa` (автономна робота, Service Worker, встановлення на Desktop/iOS/Android).
* **Мови (i18n)**: `vue-i18n` з автодетектом (`navigator.language.startsWith('uk') ? 'uk' : 'en'`) та збереженням у `localStorage`.
* **SEO**: `robots.txt`, `sitemap.xml`, OpenGraph SVG банер, canonical та alternate hreflang.
* **Observability (o11y)**: Cloudflare Web Analytics бікон, діагностичний роут `/api/health`, Edge Cache HIT/MISS телеметрія, W3C Server-Timing.

### Б. Вирішення проблеми CORS та High-Load через Cloudflare Pages Functions
Якщо стороннє джерело (upstream API) блокує CORS або має ліміти запитів:
1. Створюється файл `functions/api/[[path]].ts`.
2. Функція проксує запити до джерела на edge-рівні Cloudflare, підставляючи браузерний `User-Agent`.
3. Виставляються заголовки для кешування та CORS:
   ```typescript
   'Access-Control-Allow-Origin': '*',
   'Cache-Control': 'public, max-age=30, s-maxage=60, stale-while-revalidate=300'
   ```
4. У клієнтському коді використовується патерн **Smart Fetch**: спершу запит на власне проксі `/api/...`, у разі збою — прямий fallback до джерела.

---

## 2. 📲 PWA Інсталяція та покроковий гід для всіх платформ (iOS / Android / Desktop)

Оскільки на iOS Safari подія `beforeinstallprompt` не підтримується Apple з міркувань політики системи, обов'язково реалізується комбінований підхід:

### А. Обробка `beforeinstallprompt`:
```typescript
const deferredPrompt = ref<any>(null);
const canDirectInstall = ref(false);

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt.value = e;
  canDirectInstall.value = true;
});
```

### Б. Універсальна поведінка кнопки «Встановити» (`handleInstallClick`):
1. **Якщо браузер підтримує прямий промпт (Chrome, Edge, Android)**: викликається `deferredPrompt.value.prompt()`.
2. **Якщо прямий промпт недоступний або користувач на iOS Safari**: відкривається локалізована модалка (`PwaInstallModal.vue`) з вкладками:
   * **iOS / Safari**: «Поділитися» $\to$ «На початковий екран» (Add to Home Screen).
   * **Android**: Меню Chrome (три крапки) $\to$ «Встановити додаток».
   * **Desktop (Windows/Mac)**: Іконка в адресному рядку браузера $\to$ «Встановити додаток».
3. **Приховування кнопки встановлення у Standalone-режимі**:
   Якщо застосунок вже запущено як PWA (з іконки робочого столу), кнопку інсталяції слід автоматично приховувати, щоб не захаращувати панель:
   ```typescript
   const isStandalone = ref(false);
   onMounted(() => {
     if (typeof window !== 'undefined') {
       isStandalone.value = window.matchMedia('(display-mode: standalone)').matches || (window.navigator as any).standalone === true;
     }
   });
   ```

---

## 3. 🔔 Нуль-витратна Web Push інфраструктура на Cloudflare D1 та WebCrypto (Zero-Cost Web Push)

Для реалізації нативних пуш-сповіщень про вимкнення та повернення світла **без сторонніх платних сервісів (OneSignal/Firebase)**:

### А. Політика Apple iOS Safari (iOS 16.4+)
На iPhone/iPad `window.PushManager` та `Notification` **заблоковані у звичайних вкладках Safari**.
Пуш-повідомлення стають доступними **тільки після додавання сайту на домашній екран** (PWA Standalone).
Якщо користувач відкриває налаштування пушів у звичайному браузері на iOS, модальне вікно показує чітку покрокову інструкцію:
1. Натиснути кнопку «Поділитися» (квадрат зі стрілкою ⎋).
2. Обрати «На початковий екран» (Add to Home Screen).
3. Відкрити додаток з домашнього екрана та активувати дзвіночок 🔔.

### Б. VAPID & Native WebCrypto (Edge-сумісність без Node.js залежностей)
Cloudflare Workers / Pages Functions не підтримують старі бібліотеки, що використовують `crypto.createSign` з Node.js.
Генерація та підпис VAPID токенів виконуються через стандартизований **W3C WebCrypto API**:
- Еліптична крива: `ECDSA P-256` (`ES256`).
- **JWK імпорт приватного ключа**: Ніколи не збирати сирі PKCS#8 DER-заголовки вручну через буфери (Cloudflare WebCrypto кине `Invalid PKCS8 input`). Завжди конвертувати base64url приватний ключ у чистий JSON Web Key (`crypto.subtle.importKey('jwk', { kty: 'EC', crv: 'P-256', x, y, d }, ...)`).
- **Специфіка Apple APNs (Web Push iOS Safari)**:
  - Apple APNs (`*.apple.com`) строго відхиляє заголовок `Topic` з дефісами (`BadWebPushTopic`) і вимагає строго base64url або повну відсутність цього заголовка. Опускайте заголовок `Topic` для `apple.com`.
  - Apple APNs **вимагає суворого шифрування RFC 8291 (`aes128gcm`)**. Використання порожніх пінгів (`Content-Length: 0`) без навантаження на iOS Safari призводить до блокування сповіщень або анулювання підписки WebKit. Обов'язково шифрувати payload за допомогою стандартизованих WebCrypto бібліотек (наприклад, `@block65/webcrypto-web-push`).
  - **Заборона SVG у сповіщеннях WebKit**: На iOS Safari виклик `self.registration.showNotification(title, { badge: '/favicon.svg' })` кидає внутрішній `TypeError` у WebKit (Apple підтримує виключно растрові PNG/JPEG і не підтримує параметр `badge` у `showNotification`). Опускайте `badge` для Apple-клієнтів та використовуйте виключно PNG-іконки.
- **Ротація секретів та Zero-Fallback Standard**: Ніколи не залишати у коді дефолтні запасні ключі (`DEFAULT_VAPID_*`). Якщо ключ відсутній у хмарному середовищі Cloudflare Secrets, бекенд повинен повертати чітку помилку конфігурації замість роботи на тестових ключах з коду.
- Заголовок `Urgency: high` або `Urgency: normal`.

### В. Захист від вичерпання квот Cloudflare D1 (5M row reads/day limit)
У безкоштовному тарифі D1 повне сканування таблиці підписників (Full Table Scan) під час частих перевірок швидко спалює безкоштовний ліміт читань.
Обов'язково створюються покриваючі композитні індекси:
```sql
CREATE INDEX IF NOT EXISTS idx_subs_active_scope ON push_subscriptions(is_active, scope);
CREATE INDEX IF NOT EXISTS idx_subs_stats ON push_subscriptions(is_active, failed_attempts);
```
Це гарантує вибірку лише активних підписників для конкретного будинку або всього комплексу за $O(\log N)$ замість $O(N)$.

### Г. Анти-спам схлопування (Debounce & Collapse Tag)
Навіть якщо будинки вимикаються каскадом або електромережа блимає кілька разів за хвилину:
- У пуш-повідомленні обов'язково передається єдиний `tag: 'fayna-grid-status'`.
- Мобільна ОС автоматично схлопує сповіщення у шторці: користувач бачить рівно 1 актуальний зведений пуш замість спам-черги з десятків звукових сигналів.

---

## 4. ⚡ Алгоритм детекції блекаутів (Blackout Engine) та таймлайн

Для телеметрії з полями `grid` (мережа, Вт), `load` (споживання, Вт), `batt` (акумулятор, Вт):
```typescript
const isBlackout = (gridPower <= 20) && (buildingLoad > 20);
```

### А. 24-годинна шкала з точним відсотком заповнення
Замість грубого поділу на півгодини, розраховується точна кількість хвилин відключення $M \in [0, 60]$ у кожній годині:
$$\text{Percent} = \text{round}\left(\frac{M}{60} \times 100\%\right)$$
Клітинка забарвлюється знизу вгору динамічним градієнтом:
```typescript
:style="stat.level === 'partial' ? {
  background: `linear-gradient(to top, #f43f5e 0%, #f43f5e ${stat.percent}%, #d1fae5 ${stat.percent}%, #d1fae5 100%)`
} : stat.level === 'full' ? { background: '#f43f5e' } : {}"
```
* **Рівні**:
  - `none` (< 15 хв): 100% зелена (`220V`).
  - `partial` (15-89%): динамічний рівень червоного з відображенням відсотка (`35%`, `70%`).
  - `full` ($\ge 90\%$): повне червоне заповнення (`АКБ` / `BATT`).
  - `future`: години, що ще не настали (`border-dashed`, дефіс `—`).

### Б. Місячний зріз відключень (Monthly Backup Energy):
$$E_{\text{Backup}} = \max(0, \text{Load} - \text{Grid}) \quad \text{[кВт·г]}$$
Якщо на початку місяця архів за поточний місяць повертає 404/порожнечу, клієнт автоматично робить запит за минулий місяць `YYYY-(MM-1)`.

---

## 5. 🌍 Двомовна локалізація (i18n) та реверсний перемикач мови

1. **Реверсний перемикач (Action-Oriented)**:
   Кнопка показує мову, на яку користувач перейде при кліку:
   - Якщо активна `uk` $\to$ на кнопці **`EN`** (*Switch to English*).
   - Якщо активна `en` $\to$ на кнопці **`UA`** (*Перемкнути на українську*).
2. **Локалізація одиниць вимірювання та бейджів**:
   Одиниці вимірювання та бейджі клітинок мають виводитись через `t()`:
   - `t('kwhUnit')` $\to$ `кВт·г` / `kWh`
   - `t('kwUnit')` $\to$ `кВт` / `kW`
   - `t('wUnit')` $\to$ `Вт` / `W`
   - `t('history.badgeBatt')` $\to$ `АКБ` / `BATT`
3. **Захист від витоку системних ключів (Missing Keys Guard)**:
   Усі стандартні кнопки модальних вікон (`close`, `cancel`, `save`, `gotIt`) повинні мати синхронні записи в обох словниках (`uk.json` та `en.json`). Якщо ключ відсутній, Vue i18n відображає голий ідентифікатор ключа маленькими літерами (наприклад, `close`), що руйнує типографіку.
4. **Чистота кодової бази**:
   Усі коментарі в коді, моделях та конфігах ведуться **англійською мовою**, а вся українізація ізолюється виключно в `src/locales/uk.json`.

---

## 6. 🔍 SEO, Краулери соцмереж (Telegram / FB / X) та Google Індексування

Для повноцінної індексації SPA у пошуковиках та **миттєвої генерації rich-cards прев'ю в месенджерах** (Telegram, WhatsApp, Viber, Facebook, Twitter/X):

### А. Базові файли та мета-теги:
1. `robots.txt` у `public/`:
   ```text
   User-agent: *
   Allow: /
   Sitemap: https://<domain>/sitemap.xml
   ```
2. `sitemap.xml` з підтримкою мовних альтернатив (`xhtml:link rel="alternate" hreflang="uk"` та `hreflang="en"`).
3. У `index.html`:
   - `<link rel="canonical" href="https://<domain>/" />`
   - `<meta name="robots" content="index, follow" />`
   - `<link rel="alternate" hreflang="uk" ... />` та `hreflang="en"`.
   - **Schema.org Structured Data**: розмітка `<script type="application/ld+json">` для типу `WebApplication`, яка вказує ім'я застосунку, URL, опис, автора (`Person` з беклінком на портфоліо) та масив підтримуваних мов (`["en", "uk"]`).
   - **`<noscript>` Fallback**: легка інформаційна картка в чистій світлій темі для веб-краулерів та користувачів із вимкненим JS, що містить текстовий опис суті сервісу та інструкцію увімкнути JavaScript для інтерактивних метрик.

### Б. 🛡️ Суворі стандарти OpenGraph для краулера Telegram (`TelegramBot`):
Telegram використовує власний асинхронний кешуючий бот-парсер, який **ігнорує або відкладає скачування зображення у фонову чергу**, якщо мета-теги не містять точних геометричних параметрів. Щоб прев'ю картки з великим банером (`summary_large_image`) відображалось **миттєво** при першому ж надсиланні лінка в чат:
1. **Обов'язковий `og:site_name`**: назва платформи/додатку повинна бути явно задана (виводиться над заголовком у картці Telegram).
2. **Явні розміри та MIME-тип зображення**:
   - `og:image:width` $\to$ `1200`
   - `og:image:height` $\to$ `630` (співвідношення 1.91:1)
   - `og:image:type` $\to$ `image/png` (або `image/jpeg`)
   - `og:image:secure_url` $\to$ прямий захищений HTTPS лінк (для iOS/macOS Telegram-клієнтів).
3. **Twitter/X специфікація**:
   - `<meta name="twitter:card" content="summary_large_image">` (завжди використовувати атрибут `name=""`, а не `property=""`).
   - `<meta name="twitter:image" content="https://<domain>/og-image.png">`
4. **Мовна локалізація краулера**:
   - `<meta property="og:locale" content="uk_UA">`
   - `<meta property="og:locale:alternate" content="en_US">`
5. **Поведінка кнопки «Update with content» у Telegram**:
   - Якщо натиснути кнопку «Update with content» у діалозі з ботом, Telegram примусово перепаршує розмітку та перші видимі семантичні заголовки (`<h1>`, `<p>`). Вони мають бути інформативними і синхронізованими з текстом `og:description`.

### В. Шаблон перевіреного блоку мета-тегів:
```html
<!-- Open Graph / Telegram / Facebook / WhatsApp -->
<meta property="og:site_name" content="App Title">
<meta property="og:type" content="website">
<meta property="og:url" content="https://<domain>/">
<meta property="og:title" content="App Title — Короткий влучний заголовок">
<meta property="og:description" content="Опис суті сервісу, ключові функції та користь для користувача.">
<meta property="og:image" content="https://<domain>/og-image.png">
<meta property="og:image:secure_url" content="https://<domain>/og-image.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Опис банера">
<meta property="og:locale" content="uk_UA">
<meta property="og:locale:alternate" content="en_US">

<!-- Twitter / X Cards -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="App Title — Короткий влучний заголовок">
<meta name="twitter:description" content="Опис суті сервісу.">
<meta name="twitter:image" content="https://<domain>/og-image.png">
<meta name="twitter:image:alt" content="Опис банера">
```

---

## 7. 📊 Observability (o11y) на Cloudflare

1. **Edge Cache Telemetry (`functions/api/[[path]].ts`)**:
   - Перевірка `caches.default.match(cacheKey)`.
   - Повернення заголовків `X-Edge-Cache: HIT | MISS`, `X-Proxy-Latency`, та W3C `Server-Timing`.
   - Фонове оновлення кешу через `context.waitUntil(cache.put(...))`.
2. **Health Check роут**:
   `GET /api/health` повертає JSON зі станом Edge-вузла (Colo, Country, City), доступністю Upstream сервера та latency в мілісекундах.
3. **RUM Web Analytics**:
   Вставка легкого скрипта Cloudflare Insights у підвал `index.html` з атрибутом `defer` (запобігає блокуванню FCP/LCP).

---

## 8. 🛠️ Часті підводні камені та виправлення (Troubleshooting & Fixes)

1. **PWA Manifest Валідація та помилки встановлення (Chrome & Lighthouse Audits)**:
   * *Проблема*: Chrome DevTools або Lighthouse кидає помилки маніфесту:
     - `Manifest: property 'id' should be specified`
     - `Manifest: does not contain a suitable icon (maskable / any)`
     - `Page does not provide a valid apple-touch-icon`
     - `Manifest: screenshots missing or invalid aspect ratio for richer install UI`
   * *Еталонне рішення у `vite.config.ts`*:
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
   * *Обов'язкові метатеги в `<head>` (`index.html`)*:
     - `<link rel="manifest" href="/manifest.webmanifest?v=4" />`
     - `<meta name="mobile-web-app-capable" content="yes" />`
     - `<meta name="apple-mobile-web-app-capable" content="yes" />`
     - `<meta name="apple-mobile-web-app-status-bar-style" content="default" />`
     - `<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=4" />`

2. **Захист від кешування старих файлів (Cache Busting & PWA Updates)**:
   * *Проблема*: Мешканці / користувачі бачать старі версії коду, іконки чи дані навіть після нового деплою.
   * *Трирівневе вирішення*:
     1. **Vite Content Hashing**: Зібрані JS/CSS отримують унікальний хеш у назві (`index-[hash].js`), тому CDN ніколи не повертає старий файл за тим самим ім'ям.
     2. **Workbox Skip Waiting**: У `vite.config.ts` обов'язково активувати `skipWaiting: true`, `clientsClaim: true`, `cleanupOutdatedCaches: true`. Новий Service Worker миттєво активується без очікування закриття всіх вкладок.
     3. **Query Parameter Versioning (`?v=N`)**: Для статичних ресурсів у папці `public/` (favicon, маніфест, банери) явно додавати версію: `/favicon.svg?v=4`, `/manifest.webmanifest?v=4`.

3. **Оптимізація Core Web Vitals (LCP, CLS, INP) та ліквідація стрибків верстки**:
   * *Проблема*: 
     - Великі графічні бібліотеки (`Chart.js`, модальні вікна) роздувають початковий JS бандл (>400 kB), погіршуючи LCP (Largest Contentful Paint) на смартфонах під час блекаутів.
     - Числові показники, статус мережі («0 з 0 станцій» $\to$ «5 з 5», «АКБ» $\to$ «Мережа») та висота банерів змінюються після завантаження телеметрії, викликаючи високий CLS (Cumulative Layout Shift) у 15–20% користувачів.
     - Графіки на мобільних пристроях «залипають» із чорними тултипами при тапі пальцем.
   * *Архітектурні рішення*:
     1. **Lazy-Loading важких модулів (LCP Boost)**:
        Замість статичного імпорту використовувати `defineAsyncComponent` для всіх модалок (`StationHistoryModal`, `AddStationModal`, `PwaInstallModal`):
        ```typescript
        const StationHistoryModal = defineAsyncComponent(() => import('@/components/StationHistoryModal.vue'));
        ```
        Зменшує стартовий бандл на 55–65% (з 410 kB до ~195 kB / 67 kB gzip), забезпечуючи LCP <650ms.
     2. **Невидима фіксація простору кольором фону (Zero CLS Pattern)**:
        Замість миготливих сірих смуг-скелетонів (`animate-pulse`), які створюють візуальний шум, фіксувати точну геометрію контейнерів:
        - Задавати фіксовану висоту чи мінімальні розміри (`min-h-[36px]`, `min-h-[58px]`, `min-w-[140px]`, `whitespace-nowrap`).
        - Застосовувати `opacity-0` під час завантаження та м'який `transition-opacity duration-300` при надходженні даних.
        - Ініціалізувати конфігуровані константи (наприклад, `totalStations: 5`), щоб уникнути стрибка цифр «0 $\to$ 5».
     3. **Повний цикл сенсорних подій для Chart.js (Mobile Tooltip Dismissal)**:
        Явно конфігурувати масив подій графіка:
        ```typescript
        events: ['mousemove', 'mouseout', 'click', 'touchstart', 'touchmove', 'touchend']
        ```
        Це гарантує зникнення хінтів/тултипів при відриві пальця або тапі поза графіком.
     4. **Шрифти**: Уникати грубого `font-display: swap` без узгоджених метрик шрифту, щоб не викликати FOUT (Flash of Unstyled Text) чи стрибки верстки. Використовувати `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`.
     5. **Атомарний батч-коміт при оновленні (Atomic Batch Commit & Anti-Jitter)**:
        При паралельному підтягуванні даних (`Promise.allSettled`) **ніколи не оновлювати спільний реактивний масив покартково**. Це викликає $N$ проміжних перемалювань (reflow) та смикання карток.
        - Спочатку зібрати всі результати в тимчасовий буфер.
        - Записати оновлений масив у стан в один кадр (`telemetries.value = nextList`).
        - Зарезервувати мінімальну висоту під динамічні показники (наприклад, прогноз автономності `min-h-[18px]` + `tabular-nums`), щоб висота карток була монолітною.
     6. **Тактильна анімація рефрешу та захист від стрибка фокусу (iOS Focus Jump & Refresh Wiggle)**:
        - **Ніколи не вішати HTML-атрибут `:disabled` на кнопку в шапці**: у WebKit (iOS Safari) деактивація кнопки, на яку щойно натиснули пальцем, скидає фокус на `document.body`, викликаючи миттєвий підкид екрана до вершини сторінки (`top: 0`) і повернення назад (ілюзія, ніби шапка чи фон промайнули перед очима).
        - Блокувати повторні кліки слід виключно через CSS-клас `pointer-events-none opacity-60` та програмний `if (isRefreshing) return`.
        - На контейнерах карток використовувати строгий `transition-[box-shadow,border-color]` замість `transition-all`, щоб Safari не анімував власні координати при перерахунку лейауту.
        ```css
        @keyframes refresh-wiggle {
          0% { transform: rotate(0deg); }
          50% { transform: rotate(90deg); }
          100% { transform: rotate(0deg); }
        }
        .animate-refresh-wiggle {
          animation: refresh-wiggle 500ms cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        ```

4. **Wrangler Deploy у безперервному середовищі (Non-interactive)**:
   * *Проблема*: Wrangler у headless консолях вимагає входу або кидає помилку відсутності токена.
   * *Рішення*: Завжди передавати змінні середовища перед викликом wrangler:
     `$env:CLOUDFLARE_API_TOKEN="<token>"; $env:CLOUDFLARE_ACCOUNT_ID="<account_id>"; npx wrangler pages deploy dist --project-name=<name>`

5. **PowerShell робоча директорія у мультипроєктних середовищах**:
   * *Проблема*: Команди `npm run build` виконуються у поточному `PWD`, який може відрізнятися від папки репозиторію застосунку.
   * *Рішення*: Завжди явно задавати `Set-Location "<project-root>"` або запускати з перевіркою існування `package.json`.

6. **SVG OpenGraph візуальні накладання**:
   * *Проблема*: Емодзі всередині SVG рендеряться з різною шириною шрифту залежно від OS (Linux vs Windows vs Mac), спричиняючи зміщення бейджів.
   * *Рішення*: Використовувати чисту векторну графіку (`<polygon>`, `<rect>`, `<path>`) замість текстових смайлів та задавати фіксовані безпечні ширини контейнерів (215–235px).

7. **Захист від витоку секретів (Zero-Leak Secret Safety)**:
   * *Проблема*: Додавання тимчасових VAPID ключів чи API токенів у код для швидких тестів призводить до миттєвого потрапляння у публічні бази сканерів (GitGuardian, Trufflehog) відразу після `git push`.
   * *Рішення*: 
     - Жодних рядкових констант на кшталт `DEFAULT_VAPID_PRIVATE_KEY` чи `ADMIN_API_KEY` у вихідному коді (`.ts`, `.vue`, `.js`).
     - Секрети зберігаються **виключно** у Cloudflare Secrets (`npx wrangler pages secret put <KEY>`) та GitHub Secrets.
     - За відсутності змінної в `env` функція повинна повертати явну помилку `500 Server Configuration Error`, а не підставляти захардкоджений фолбек.
     - Перед будь-яким коммітом виконувати ретельний аудит змінених файлів (`git diff --staged`).

---

## 9. 🚀 Пайплайн розгортання в один клік

```bash
# 1. Збірка з перевіркою типів
npm run build

# 2. Деплой на Cloudflare Pages через Wrangler CLI з передачею API токенів
$env:CLOUDFLARE_API_TOKEN="<token>"
$env:CLOUDFLARE_ACCOUNT_ID="<account_id>"
npx wrangler pages deploy dist --project-name=<project-name> --commit-dirty=true
```
