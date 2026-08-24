# WafyURL 🔗 — Premium Link Management Platform

<div align="center">
  <img src="https://url.amwafy.xyz/og-image.webp" alt="WafyURL Preview" width="100%" />
</div>

<br/>

> A lightning-fast, highly secure, and feature-rich URL shortener with real-time analytics, QR code generation, and password protection, built for the modern web.

[![Live Demo](https://img.shields.io/badge/Live-Demo-00d9ff?style=for-the-badge)](https://url.amwafy.xyz)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge\&logo=github)](https://github.com/afeemuhammodwafy1/wafyurl)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge\&logo=flask)](https://flask.palletsprojects.com/)

---

## 🌐 Live Demo

**Try WafyURL live:**

🔗 **https://url.amwafy.xyz**

---

## 📖 About The Project

**WafyURL** is a modern, full-stack URL shortening and link management platform built to make sharing, securing, and tracking links simple and powerful.

Instead of being just a basic URL shortener, WafyURL combines link management with analytics, security, QR code generation, custom aliases, expiration controls, and bulk URL shortening.

It is designed for developers, marketers, businesses, content creators, and anyone who needs a reliable way to manage shortened URLs.

---

## ✨ Features

### ⚡ Lightning-Fast URL Shortening

Create short, clean, and shareable URLs within seconds.

Example:

```text
https://url.amwafy.xyz/Ab3Xk9
```

---

### 📊 Real-Time Analytics

Track important statistics for every shortened link, including:

* Total clicks
* Geographic information
* Device type
* Browser information
* Link activity

This makes WafyURL useful for campaign tracking and understanding how users interact with shared links.

---

### 🔐 Password Protection

Protect sensitive destinations with password-protected shortened URLs.

Users must enter the correct password before they can access the destination URL.

This is useful for:

* Private resources
* Temporary sharing
* Internal links
* Sensitive content

---

### 📱 QR Code Generation

Every shortened URL can be converted into a QR code.

QR codes can be useful for:

* Posters
* Business cards
* Presentations
* Social media
* Marketing campaigns
* Offline sharing

---

### ⏳ Link Expiration

Create temporary links with automatic expiration.

Supported expiration options include:

* 1 Hour
* 24 Hours
* 7 Days
* 30 Days

Once a link expires, it can no longer be used for redirection.

---

### 🔤 Custom Aliases

Create memorable and branded short links instead of random codes.

Example:

```text
https://url.amwafy.xyz/my-brand
```

Custom aliases make links easier to remember, recognize, and share.

---

### 📦 Bulk URL Shortening

Shorten multiple URLs at once instead of processing them individually.

WafyURL supports up to **50 URLs per batch**, making it useful when managing large numbers of links.

---

### 🔍 Live Link Previews

WafyURL can fetch Open Graph metadata from destination pages to provide useful information about the target URL before visiting it.

This can help users understand where a shortened link leads.

---

### 🛡️ Security & Rate Limiting

WafyURL includes built-in protections designed to reduce abuse and spam.

Security-related features include:

* IP-based rate limiting
* URL validation
* Password-protected links
* Expiring links
* Secure environment variable handling
* Protected database credentials

---

## 🛠️ Tech Stack

| Technology             | Purpose                          |
| ---------------------- | -------------------------------- |
| **Python 3.11**        | Backend programming language     |
| **Flask**              | Web framework                    |
| **Flask-SQLAlchemy**   | Database ORM                     |
| **PostgreSQL**         | Production database              |
| **Neon**               | PostgreSQL hosting               |
| **HTML5**              | Frontend structure               |
| **CSS3**               | Frontend styling                 |
| **Vanilla JavaScript** | Frontend functionality           |
| **Vercel**             | Serverless deployment            |
| **Render**             | Deployment configuration/support |

---

## 🏗️ Architecture

WafyURL follows a lightweight full-stack architecture:

```text
User
 │
 ▼
Frontend
HTML + CSS + JavaScript
 │
 ▼
Flask Application
 │
 ├── URL Shortening
 ├── Redirect Handling
 ├── Analytics
 ├── QR Generation
 ├── Password Protection
 ├── Link Expiration
 ├── Bulk Shortening
 └── Rate Limiting
 │
 ▼
PostgreSQL Database
 │
 ▼
Neon
```

---

## 📁 Project Structure

```text
wafyurl/
├── static/             # CSS, JavaScript, images, and other static assets
├── templates/          # HTML templates
├── Procfile            # Deployment configuration
├── README.md           # Project documentation
├── app.py              # Main Flask application
├── app.py.txt          # Backup/text copy of the application file
├── icon.webp           # Project icon
├── render.yaml         # Render deployment configuration
├── requirements.txt    # Python dependencies
└── vercel.json         # Vercel deployment configuration
```

---

## 🚀 Running Locally

Follow the steps below to run WafyURL on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/afeemuhammodwafy1/wafyurl.git
```

Move into the project directory:

```bash
cd wafyurl
```

---

### 2. Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate it depending on your operating system.

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

---

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=your_postgresql_database_url
SECRET_KEY=your_secret_key
```

Replace the placeholder values with your actual configuration.

> **Important:** Never commit your `.env` file or expose database credentials and secret keys publicly.

---

### 5. Run the Application

Start the Flask application:

```bash
python app.py
```

The application should be available at:

```text
http://localhost:5000
```

---

## 🌍 Deployment

WafyURL is configured for modern cloud deployment.

The repository includes configuration files for deployment platforms:

```text
render.yaml
vercel.json
Procfile
```

The production version is available at:

🔗 **https://url.amwafy.xyz**

---

## 🗄️ Database

WafyURL uses **PostgreSQL** as its production database.

The database is hosted using **Neon** and accessed through **Flask-SQLAlchemy**.

The database stores information required for:

* Shortened URLs
* Custom aliases
* Click statistics
* Link expiration
* Password-protected links
* Analytics data

---

## 📈 Analytics Overview

Analytics help users understand how their shortened URLs are being used.

Depending on the available data, WafyURL can track:

```text
Clicks
 ├── Total clicks
 ├── Device type
 ├── Browser
 └── Geographic information
```

This makes the platform more useful than a traditional URL shortener.

---

## 🔒 Security

Security is an important part of WafyURL.

The application uses multiple mechanisms to improve link and application security:

### Password Protection

Sensitive links can require a password before redirection.

### Rate Limiting

IP-based rate limiting helps reduce spam and automated abuse.

### Environment Variables

Sensitive configuration such as:

* Database credentials
* Secret keys
* API credentials

should be stored in environment variables rather than directly in source code.

### URL Validation

Destination URLs are validated before being processed.

---

## ⏰ Expiring Links

Temporary links are useful when a URL should only remain active for a limited period.

WafyURL supports:

```text
1 Hour
24 Hours
7 Days
30 Days
```

This can be useful for temporary campaigns, events, promotions, and private resources.

---

## 🎨 Custom Short Links

Users can create custom aliases for better branding.

For example:

```text
Long URL:
https://example.com/very/long/path/to/something

WafyURL:
https://url.amwafy.xyz/my-brand
```

This produces a cleaner and more memorable URL.

---

## 📦 Bulk Shortening

Instead of shortening URLs one by one, users can process multiple URLs together.

### Maximum

**50 URLs per batch**

Example workflow:

```text
50 Long URLs
      │
      ▼
 WafyURL Bulk Shortener
      │
      ▼
50 Short URLs
```

---

## 📱 QR Codes

WafyURL makes it easy to turn shortened URLs into QR codes.

A generated QR code can be used anywhere a physical or visual link is needed.

Example use cases:

* Event materials
* Product packaging
* Posters
* Business cards
* Restaurant menus
* Presentations
* Marketing campaigns

---

## 🔎 Link Preview

WafyURL can retrieve Open Graph metadata from destination websites.

This allows the application to provide useful information about a destination before the user follows a shortened URL.

Typical metadata may include:

* Page title
* Description
* Preview image
* Website information

---

## 🤝 Contributing

Contributions and suggestions are welcome.

If you would like to contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Test your changes.
5. Commit your changes.
6. Open a Pull Request.

Example:

```bash
git checkout -b feature/my-feature
```

```bash
git add .
git commit -m "Add new feature"
```

```bash
git push origin feature/my-feature
```

Then open a Pull Request on GitHub.

---

## 🐛 Bug Reports & Suggestions

Found a bug or have an idea for improving WafyURL?

You can open an issue in the GitHub repository.

**GitHub Repository:**

https://github.com/afeemuhammodwafy1/wafyurl

When reporting a bug, try to include:

* What happened
* What you expected
* Steps to reproduce
* Browser/device information
* Relevant error messages

---

## 🔮 Future Improvements

Possible future improvements include:

* Advanced analytics dashboards
* Link management folders
* UTM parameter builder
* API access
* Team collaboration
* More customization options
* Advanced QR code customization
* Exportable analytics
* Improved link monitoring
* Additional security controls

---

## 📜 License

This project is open-source.

Please check the repository for the current licensing information.

---

## 👨‍💻 Author

### Afee Muhammod Wafy

Building projects, experimenting with modern web technologies, and learning software development.

**GitHub:**
https://github.com/afeemuhammodwafy1

**Website:**
https://dev.amwafy.xyz

**WafyURL:**
https://url.amwafy.xyz

---

## ⭐ Support the Project

If you find WafyURL useful, consider giving the repository a ⭐ on GitHub.

Your support helps the project grow and motivates further development.

---

<div align="center">

# 🔗 WafyURL

### Shorten. Secure. Track.

Built with ❤️ by **Afee Muhammod Wafy**

**[Live Demo](https://url.amwafy.xyz) · [GitHub Repository](https://github.com/afeemuhammodwafy1/wafyurl)**

</div>
