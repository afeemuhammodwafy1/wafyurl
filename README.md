<p align="center">
  <img src="docs/images/wafyurl-banner.webp" alt="WafyURL — Shorten Smarter. Share Faster. Track Everything." width="100%">
</p>

# WafyURL

**Shorten smarter. Share faster. Track everything.**

WafyURL is a Flask-based URL shortener with custom aliases, optional password protection, expiring links, click analytics, QR-code support, bulk shortening, and destination-page previews.

**Live website:** https://url.amwafy.xyz  
**Source code:** https://github.com/afeemuhammodwafy1/wafyurl

## Features

- **Short links:** Create short URLs from publicly accessible HTTP or HTTPS destinations.
- **Custom aliases:** Choose a custom short code when it is available.
- **Password-protected links:** Require a password before redirecting to a destination.
- **Link expiration:** Set links to expire after 1 hour, 24 hours, 7 days, 30 days, or at a custom date and time.
- **Click analytics:** Record click totals and selected device/browser/referrer metadata. Visitor geolocation is currently disabled by default to avoid sharing visitor IP addresses with a third party.
- **QR codes:** Generate QR codes for shortened links.
- **Bulk shortening:** Submit multiple URLs in one batch (the interface supports up to 50 URLs per batch).
- **Link preview:** Retrieve page title, description, and Open Graph image metadata.
- **Rate limiting:** Apply in-process limits to link creation, bulk batches and password attempts. For multi-instance production deployments, configure a shared rate-limit store before relying on these limits as a security boundary.
- **SEO pages:** Include distinct feature and guide pages, page-specific metadata, canonical URLs, `robots.txt`, and a sitemap that lists public content rather than generated short links.

## Technology

- Python and Flask
- Flask-SQLAlchemy
- PostgreSQL in production; SQLite is the local default
- HTML, CSS, and vanilla JavaScript
- Gunicorn
- Render/Vercel deployment configuration

## Run locally

### Requirements

- Python 3.10 or newer (the Render configuration specifies Python 3.11)
- pip
- A PostgreSQL database for production; local development can use SQLite by default

### 1. Clone the repository

```bash
git clone https://github.com/afeemuhammodwafy1/wafyurl.git
cd wafyurl
```

### 2. Create and activate a virtual environment

**Windows (Command Prompt):**

```bat
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Set a strong, unique `SECRET_KEY` before deploying. To use PostgreSQL, set `DATABASE_URL` to your database connection URL. If `DATABASE_URL` is omitted, the app uses a local SQLite database.

Copy `.env.example` to `.env` and set values for your environment. Example:

```env
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
PUBLIC_BASE_URL=https://url.amwafy.xyz
```

Never commit real secrets, passwords, or production database credentials. The `.env` file should remain private.

### 5. Start the app

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Deployment

The repository includes `Procfile`, `render.yaml`, and `vercel.json` deployment configuration. Set `SECRET_KEY`, `DATABASE_URL`, and `PUBLIC_BASE_URL` in the host environment. Use a persistent PostgreSQL database such as Neon in production; local SQLite storage is not suitable for ephemeral serverless filesystems. The live deployment URL configured by default is:

**https://url.amwafy.xyz**

For Vercel, connect the GitHub repository, add the environment variables in Project Settings, and add `url.amwafy.xyz` under Domains. Configure the DNS record exactly as Vercel instructs for the project; verify the domain before switching production traffic. In Neon, create a database and use its pooled connection string where appropriate. Configure `PUBLIC_BASE_URL=https://url.amwafy.xyz` so generated links use the intended hostname.

The app currently creates missing tables at startup; `db.create_all()` does not migrate existing schemas. Use a versioned migration workflow before making future database-model changes. Confirm the selected host supports the app's database and filesystem/runtime requirements before deploying.

## Data and privacy notes

- Link creation records the originating IP for abuse prevention. New click logs retain user-agent and normalized referrer-domain data; click IP retention and third-party geolocation are disabled in the current implementation. Existing historical records created by older versions may still contain IP values.
- Scan history and account behavior should be reviewed against the current implementation before making privacy claims; this project does not document a user account system.
- The in-process rate limiter is not shared across multiple worker processes and may reset when the process restarts.
- The link-preview endpoint validates public HTTP(S) destinations and revalidates redirects to reduce SSRF risk. Server-side URL fetching remains a sensitive feature and should be tested further before a high-risk production launch.
- Keep `SECRET_KEY` private and use a strong production value.
- Password-protected links should not be treated as a substitute for sharing sensitive information through a dedicated secure channel.

## Project structure

```text
wafyurl/
├── docs/
│   └── images/
│       └── wafyurl-banner.webp
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── script.js
│       └── analytics.js
├── templates/
│   ├── index.html
│   ├── seo_page.html
│   ├── password.html
│   └── 404.html
├── app.py
├── icon.webp
├── og-image.webp
├── .env.example
├── .gitignore
├── CHANGELOG_REDESIGN.md
├── Procfile
├── render.yaml
├── requirements.txt
└── vercel.json
```

## Contributing

Bug reports and improvements are welcome. Open an issue with steps to reproduce the problem, or submit a pull request with a clear description of the change.

## License

This project is licensed under the [MIT License](LICENSE).

## About

**WafyURL** is a product of **Wafyro Software**.

**Founder and Software Developer:** Afee Muhammod Wafy  


## Application structure

The Flask application now uses an application factory (`app.create_app`) and separates database models, configuration, reusable services, rate limiting, and route blueprints. The root `app.py` remains the WSGI entrypoint for Vercel and Gunicorn.

```text
app/
├── __init__.py          # application factory and shared handlers
├── config.py             # environment-based configuration
├── extensions.py         # SQLAlchemy extension
├── models/               # SQLAlchemy models
├── routes/               # page, link, and API blueprints
├── services/             # reusable URL and analytics helpers
├── security/             # request rate limiting
└── utils/                # shared utility package
migrations/               # database migration workspace
tests/                    # automated test workspace
```
