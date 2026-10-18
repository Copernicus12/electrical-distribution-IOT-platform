# Electrical Distribution IoT — interfața web

Aplicație separată în `web/`, bazată pe Laravel 13 și Starter Kit-ul oficial Vue: Vue 3, Inertia 3, TypeScript, Tailwind CSS și autentificare Laravel Fortify. Directorul face parte din repository-ul proiectului; nu are un repository Git separat.

În această etapă avem structura inițială, autentificare și paginile standard. Dashboard-ul nu afișează încă telemetria gateway-ului.

## Instalare după clonare

Mediul local verificat: PHP 8.5.2, Composer 2.9.5, Node.js 25.5.0 și npm 11.8.0. Cerințele exacte ale dependențelor sunt în fișierele lock; pentru PHP se pot verifica prin `composer check-platform-reqs --lock`. Din rădăcina repository-ului:

```bash
cd web
composer install
npm ci
cp .env.example .env
php artisan key:generate
php -r "file_exists('database/database.sqlite') || touch('database/database.sqlite');"
php artisan migrate
npm run build
```

Copiați `.env.example` doar la prima instalare, dacă `.env` nu există deja. Configurația implicită folosește SQLite local; PostgreSQL va fi configurat când integrăm persistența platformei. Fișierele `.env`, `database/database.sqlite`, `vendor/`, `node_modules/` și `public/build/` nu se comit. Păstrați `composer.lock` și `package-lock.json` în Git.

## Pornire manuală

Într-un terminal, din `web/`:

```bash
php artisan serve --host=127.0.0.1 --port=8000
```

În al doilea terminal, tot din `web/`:

```bash
npm run dev
```

Accesați http://127.0.0.1:8000. Înregistrarea creează contul local; nu există utilizator sau parolă implicită. Dacă vi se solicită verificarea emailului, mesajele trimise local sunt în `storage/logs/laravel.log`, deoarece `MAIL_MAILER=log`. Opriți fiecare terminal cu Ctrl+C.

Gateway-ul și tablourile Python se pornesc independent. Interfața nu comunică încă cu ele.

## Verificare

```bash
php artisan test
composer run lint:check
composer run types:check
npm run check
npm run types:check
npm run build
```

Testele Laravel utilizează SQLite în memorie, conform `phpunit.xml`, separat de baza locală. Testele Python rămân la rădăcina repository-ului, în `unit_testing/` și `integration_testing/`.

## Organizare

- `resources/js/pages/`: paginile Vue, inclusiv `Dashboard.vue` și paginile de autentificare.
- `resources/js/components/` și `resources/js/layouts/`: componentele reutilizabile și structura vizuală.
- `routes/web.php`: rutele web; dashboard-ul necesită autentificare și verificare conform configurației Starter Kit-ului.
- `app/`: controllere, modele, middleware și logica Laravel.
- `database/migrations/`: schema bazei de date.
- `tests/Unit/` și `tests/Feature/`: testele aplicației web, organizate conform convențiilor Laravel.

Sursă: [Laravel Vue Starter Kit](https://github.com/laravel/vue-starter-kit), revizia `d282e817c6c2fa1bd475f7c42ea785ccfc67d0ab`. Versiunile instalate sunt fixate în fișierele lock.

## Administrare

Utilizatorii au marcajul `is_admin`, implicit `false`. Administratorii au acces complet la acțiunile autorizate prin gates și policies Laravel; permisiunea `access-admin` identifică accesul administrativ. Marcajul nu este acceptat prin înregistrarea publică sau prin mass assignment. Contul administrativ creat în mediul local este păstrat numai în baza de date locală, cu parola hash-uită; datele sale de autentificare nu sunt incluse în seedere. Nu există încă o pagină separată pentru administrarea utilizatorilor.
