# DocVault 📁

A simple document sharing website.  
- **Public** users can browse & download files — no login required.  
- **Admin** can upload and delete files via a password-protected panel.  
- Backend: Python (Flask) · Database: MySQL · Frontend: plain HTML/CSS/JS

---

## Project Structure

```
docvault/
├── app.py                  ← Flask backend (all API routes)
├── schema.sql              ← MySQL table definition
├── requirements.txt        ← Python dependencies
├── uploads/                ← Uploaded files stored here (auto-created)
└── templates/
    └── index.html          ← Single-page frontend
```

---

## Setup & Deploy

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up MySQL

Make sure MySQL is running, then:

```bash
mysql -u root -p < schema.sql
```

This creates the `docvault` database and `documents` table.

### 3. Edit config in `app.py`

Open `app.py` and update these lines at the top:

```python
ADMIN_PASSWORD = "admin@123"       # ← your admin password
SECRET_KEY     = "change-me-random" # ← any random string
MYSQL_USER     = "root"            # ← your MySQL user
MYSQL_PASSWORD = "yourpassword"    # ← your MySQL password
```

### 4. Run the server

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Usage

| Who       | What they can do                              |
|-----------|-----------------------------------------------|
| Everyone  | Browse documents, search, download            |
| Admin     | Click "Admin Login" → enter password → upload & delete |

---

## Deploy to a server (optional)

Install gunicorn for production:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use a reverse proxy (nginx/apache) pointing to port 5000.

---

## Notes
- Files are stored in the `uploads/` folder on disk; MySQL only stores metadata.
- Max upload size is 50 MB by default — change `MAX_FILE_MB` in `app.py`.
- Session-based admin login (no tokens needed).
