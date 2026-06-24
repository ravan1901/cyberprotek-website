# Cyberprotek — Flask Website

## Run locally
1. Install dependencies:
   pip install -r requirements.txt

2. Start the server:
   python app.py

3. Open http://localhost:5000 in your browser.

## Structure
- app.py            — Flask routes + service data
- templates/         — Jinja2 HTML templates (base.html + page templates)
- static/style.css   — shared stylesheet
- messages.csv        — created automatically when someone submits the contact form

## Pages
- /                       Home
- /services               Services overview
- /services/<slug>        Service detail (vapt, network-security, server-cloud, cctv, it-support, web-development)
- /about                  About
- /contact                Contact (GET shows form, POST saves the message to messages.csv)

## Contact form / email notifications
All inquiries are saved to `messages.csv` automatically — this always works.

To also receive a real email at info@cyberprotek.in when someone submits the form,
set these environment variables before running the app (e.g. in a `.env` file or
your hosting provider's environment settings):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-sending-address@gmail.com
SMTP_PASS=your-app-password
```

Notes:
- If using Gmail as the sender, you need a 16-character "App Password"
  (Google Account → Security → 2-Step Verification → App Passwords),
  not your normal Gmail password.
- The notification email is hardcoded to go to info@cyberprotek.in in app.py
  (see NOTIFY_EMAIL) — change it there if needed.
- If SMTP variables aren't set, the form still works and still saves to
  messages.csv — it just won't send the email.

## Notes
- Update placeholder phone numbers directly in templates/base.html and templates/contact.html.
- Update service descriptions/pricing-free copy in the SERVICES list inside app.py.
- For production, run behind gunicorn/waitress instead of the Flask dev server, and set debug=False.
