# wafyurl - Premium URL Shortener

> **Shorten links with precision. Fast, secure, and analytics-driven.**

---

## 📌 Features

| Feature | Status | Description |
|---------|--------|-------------|
| ✅ URL Shortening | Complete | Shorten long URLs instantly |
| ✅ Custom Short Codes | Complete | Create branded short links |
| ✅ Password Protection | Complete | Secure links with passwords |
| ✅ Link Expiration | Complete | Set expiry time for links |
| ✅ QR Code Generation | Complete | Generate QR codes for any link |
| ✅ Click Analytics | Complete | Track total clicks and engagement |
| ✅ Bulk Shortening | Complete | Shorten multiple URLs at once |
| ✅ Link Preview | Complete | Preview content before clicking |
| ✅ Referrer Tracking | Complete | See where traffic comes from |
| ✅ Geolocation Tracking | Complete | Track clicks by country/city |
| ✅ Rate Limiting | Complete | Protect against spam |
| ✅ Responsive Design | Complete | Works on all devices |
| ✅ SEO Optimized | Complete | Meta tags, sitemap, robots.txt |
| ✅ Dark Theme | Complete | Modern neon design |

---

## 🚀 Live Demo

🔗 **Visit: https://url.amwafy.xyz/

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask 3.0.0 (Python) |
| **Database** | SQLite / PostgreSQL |
| **ORM** | SQLAlchemy 3.1.1 |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Styling** | CSS Custom Properties, Flexbox, Grid |
| **Charts** | Chart.js |
| **QR Code** | QRCode.js |
| **HTTP Client** | Requests (Python) |
| **HTML Parsing** | BeautifulSoup4 |
| **Deployment** | Render.com |
| **Version Control** | Git & GitHub |

---

## 📁 Project Structure
wafyurl/
├── app.py # Main application
├── requirements.txt # Python dependencies
├── render.yaml # Render deployment config
├── .env.example # Environment variables template
├── static/
│ ├── css/
│ │ └── style.css # Stylesheet
│ └── js/
│ └── script.js # Frontend logic
├── templates/
│ ├── index.html # Home page
│ ├── password.html # Password protected page
│ └── 404.html # Custom 404 page
└── wafyurl.db # SQLite database (auto-created)

text

---

## 🔧 Installation & Setup

### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/wafyurl.git
cd wafyurl
2. Create Virtual Environment
bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install Dependencies
bash
pip install -r requirements.txt
4. Environment Variables
Create a .env file in the root directory:

env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/wafyurl
FLASK_DEBUG=False
5. Run Locally
bash
python app.py
Visit: http://localhost:5000

🚀 Deployment on Render
Step 1: Push to GitHub
bash
git add .
git commit -m "Initial commit"
git push origin main
Step 2: Deploy on Render
Go to render.com

Click "New +" → "Web Service"

Connect your GitHub repository

Configure:

Setting	Value
Build Command	pip install -r requirements.txt
Start Command	gunicorn app:app
Environment	Python 3.11
Step 3: Add Environment Variables
Add these in Render Dashboard → Environment Variables:

Key	Value
SECRET_KEY	your-secret-key (generate new)
PYTHON_VERSION	3.11.0
FLASK_DEBUG	false
Step 4: Deploy
Click "Create Web Service" and wait for deployment.

📊 API Endpoints
Endpoint	Method	Description
/	GET	Home page
/shorten	POST	Create short URL
/<code>	GET	Redirect to original URL
/<code>+	GET	View analytics
/api/stats/<code>	GET	Get click statistics
/api/link/<code>	GET	Get link information
/api/preview	GET	Preview a URL
/sitemap.xml	GET	Sitemap for SEO
/robots.txt	GET	Robots.txt for SEO
📈 Analytics Features
Metric	Description
Total Clicks	Total number of clicks on the link
Click Timeline	Daily click data for last 30 days
Device Breakdown	Mobile/Desktop/Tablet distribution
Top Referrers	Top 10 sources of traffic
Geolocation	Country and city of visitors
Browser & OS	Browser and operating system statistics
🔒 Security Features
✅ Rate Limiting: 50 requests/hour per IP

✅ Password Protection: SHA-256 hashing

✅ URL Validation: Prevents malformed URLs

✅ HTTPS Enforcement: Secure connections only

✅ CSRF Protection: Built-in Flask protection

✅ Input Sanitization: Prevents XSS attacks

🧪 Testing
bash
# Run locally
python app.py

# Test API endpoints
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
🤝 Contributing
Fork the repository

Create your feature branch: git checkout -b feature/amazing-feature

Commit your changes: git commit -m 'Add amazing feature'

Push to the branch: git push origin feature/amazing-feature

Open a Pull Request

📄 License
This project is licensed under the MIT License.

👨‍💻 Author
Afee Muhammod Wafy

🌐 Website: https://www.amwafy.xyz

📧 Email: afeemuhammodwafy@yahoo.com

⭐ Support
If you like this project, give it a ⭐ on GitHub! https://github.com/afeemuhammodwafy1/wafyurl

📝 Changelog
v1.0.0 (2026)
✅ Initial release

✅ URL shortening with custom codes

✅ Password protection

✅ QR code generation

✅ Bulk shortening

✅ Link preview

✅ Analytics dashboard

✅ Referrer tracking

✅ Geolocation tracking

✅ Responsive design

✅ SEO optimized

📞 Contact
For support or inquiries, please open an issue on GitHub or contact the author directly.

Made with ❤️ by Afee Muhammod Wafy