from flask import Flask, render_template, request, redirect, url_for
import csv
import os
import smtplib
import re
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)

MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "messages.csv")
NOTIFY_EMAIL = "info@cyberprotek.in"
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587")) if os.environ.get("SMTP_PORT") else 587
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_REGEX = r'^(\+91[\-\s]?)?[0-9]{10}$'


def send_inquiry_email(name, email, phone, service, message):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        return False
    body = (
        f"New inquiry from the Cyberprotek website:\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
        f"Service of interest: {service or 'General inquiry'}\n\n"
        f"Message:\n{message}\n"
    )
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = f"New website inquiry from {name}"
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL
    msg["Reply-To"] = email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [NOTIFY_EMAIL], msg.as_string())
        return True
    except Exception as e:
        print(f"[email] Failed to send: {e}")
        return False


SERVICES = [
    {"slug": "vapt", "name": "VAPT — Vulnerability Assessment & Penetration Testing", "short": "VAPT",
     "tag": "Specialty", "desc": "Web, API, mobile, and network penetration testing that finds real exploitable flaws, not just scanner output.",
     "icon": '<path d="M12 2l8 4v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4z"/>',
     "overview": "Our VAPT engagements combine automated scanning with manual exploitation by certified testers — covering web applications, REST/GraphQL APIs, mobile apps (Android/iOS), and internal or external network infrastructure. We don't stop at a vulnerability scan report; every finding is manually verified to confirm it's actually exploitable before it makes it into your report.",
     "whatweTest": ["Authentication & session management", "Injection flaws (SQL, NoSQL, command)",
                    "Business logic & access control bypass", "API endpoint abuse & rate limiting",
                    "Mobile app local storage & API security", "Network segmentation & exposed services"],
     "approach": "We follow a structured four-phase methodology: reconnaissance to map your real attack surface, controlled exploitation attempts against anything we find, a severity-ranked written report, and finally a guided remediation and re-test cycle so fixes are verified, not assumed. Testing windows are agreed with you in advance to avoid any disruption to live systems.",
     "idealFor": "Any business handling customer data, processing payments, or required to demonstrate due diligence to clients, auditors, or regulators — including SaaS startups before a funding round, fintechs ahead of compliance audits, and e-commerce platforms before a major sale season.",
     "deliverable": "A severity-ranked report (Critical/High/Medium/Low) mapped to CVSS scores, with reproduction steps and remediation guidance your dev team can act on — plus one round of re-testing once fixes are deployed."},
    {"slug": "network-security", "name": "Network Infrastructure & Security", "short": "Network Security", "tag": "Infrastructure",
     "desc": "Firewall setup, segmentation, VPN, and ongoing network security management built for SMB budgets.",
     "icon": '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>',
     "overview": "We design and harden the network layer that everything else depends on — firewalls, VPNs, segmentation, and monitoring — sized for offices that don't have a dedicated network engineer on staff.",
     "whatweTest": ["Firewall rule configuration & hardening", "Site-to-site and remote-access VPN setup",
                    "Network segmentation (VLANs, zones)", "Wireless network security audit",
                    "Intrusion detection/prevention setup", "Ongoing monitoring & alerting"],
     "approach": "We start with a full audit of your existing network topology, identify exposed or misconfigured points, then implement firewall rules, VPN access, and segmentation in a planned maintenance window to avoid downtime. Documentation is handed over so you're never dependent on us to make a basic change.",
     "idealFor": "Growing offices adding remote staff, businesses that have never had a formal network security review, or any company that's had an informal 'flat' network where every device can see every other device.",
     "deliverable": "A hardened, documented network with firewall rules, VPN access, and segmentation in place — plus a configuration handover doc so you're never locked out of your own network."},
    {"slug": "server-cloud", "name": "Server & Cloud Management", "short": "Server & Cloud", "tag": "Infrastructure",
     "desc": "Setup, migration, backup, and monitoring for on-prem servers and cloud infrastructure (AWS, Azure, GCP).",
     "icon": '<rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><circle cx="7" cy="7" r="0.8" fill="#F7F8F6"/><circle cx="7" cy="17" r="0.8" fill="#F7F8F6"/>',
     "overview": "Whether you run on-prem servers, the cloud, or both, we set up, migrate, and manage the infrastructure so uptime and backups aren't left to chance. This includes everything from a single file server to a multi-region cloud deployment.",
     "whatweTest": ["Server provisioning & OS hardening", "Cloud migration (AWS, Azure, GCP)",
                    "Automated backup & disaster recovery", "Performance monitoring & alerting",
                    "Cost optimization review", "Patch management"],
     "approach": "We assess your current setup, design a migration or management plan around your actual usage patterns (not a generic template), and implement backups that we test by actually restoring from them — not just assuming the backup job ran. Ongoing monitoring catches issues before they become outages.",
     "idealFor": "Businesses outgrowing a single physical server, companies migrating to the cloud for the first time, or anyone who has never actually tested whether their backups can be restored.",
     "deliverable": "A documented, monitored server/cloud environment with backups verified to actually restore — plus a regular health report so you always know the state of your infrastructure."},
    {"slug": "cctv", "name": "CCTV & Surveillance", "short": "CCTV & Surveillance", "tag": "Physical Security",
     "desc": "IP camera installation, NVR setup, and remote monitoring for offices, warehouses, and retail sites.",
     "icon": '<path d="M3 9l9-6 9 6v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><circle cx="12" cy="13" r="2.4"/>',
     "overview": "Full-site CCTV design and installation — IP cameras, NVR/DVR setup, and remote viewing on your phone — sized for single offices up to multi-site retail chains. We plan camera placement around actual blind spots and high-risk areas, not just an even spread.",
     "whatweTest": ["Site survey & camera placement plan", "IP camera & NVR installation",
                    "Remote/mobile monitoring setup", "Storage sizing for retention needs",
                    "Low-light & night vision coverage", "Annual maintenance contracts available"],
     "approach": "We start with a physical site survey to map entry points, blind spots, and high-value areas, then design a camera layout before any installation begins. Once installed, we configure remote access on your devices and size storage to match your required retention period.",
     "idealFor": "Retail stores, warehouses, offices, and multi-location businesses that need reliable footage for security incidents, staff accountability, or insurance requirements.",
     "deliverable": "A fully installed, tested surveillance system with remote access configured on your devices, and an optional maintenance plan to keep footage retention reliable long-term."},
    {"slug": "it-support", "name": "IT Support & AMC", "short": "IT Support & AMC", "tag": "Ongoing Support",
     "desc": "Helpdesk, on-site support, and annual maintenance contracts that keep day-to-day IT actually running.",
     "icon": '<path d="M14.7 6.3a1 1 0 010 1.4l-7 7a1 1 0 01-1.4 0l-2-2a1 1 0 010-1.4l7-7a1 1 0 011.4 0l2 2z"/><path d="M9 17H3v-6"/>',
     "overview": "An annual maintenance contract that gives you a real IT department on call — remote helpdesk, scheduled on-site visits, and priority response when something breaks. Instead of calling a different freelancer every time something goes wrong, you get one accountable team that already knows your setup.",
     "whatweTest": ["Remote helpdesk (email, chat, phone)", "Scheduled on-site visits",
                    "Device & software troubleshooting", "Server & network monitoring",
                    "Priority SLA for critical issues", "Asset & license tracking"],
     "approach": "We begin every AMC with an IT asset audit so we know exactly what we're supporting from day one, then set defined response-time SLAs based on issue severity. Recurring issues get root-caused rather than just patched repeatedly.",
     "idealFor": "Any business without in-house IT staff, or with a small IT team that needs backup for overflow and after-hours issues.",
     "deliverable": "A signed AMC with defined response-time SLAs, a regular support summary, and a single point of contact instead of a rotating cast of freelancers."},
    {"slug": "web-development", "name": "Website & Digital", "short": "Website & Digital", "tag": "Development",
     "desc": "Business websites and web apps built with security baked in from day one — not bolted on after launch.",
     "icon": '<rect x="3" y="4" width="18" height="14" rx="1"/><path d="M3 9h18"/>',
     "overview": "We build and secure business websites and web applications — from a marketing site to a customer portal — with the same security discipline we apply in VAPT engagements, so the site you launch with isn't the one a basic scan flags on day two.",
     "whatweTest": ["Business websites & landing pages", "Custom web applications", "E-commerce setup",
                    "Security hardening at launch", "Hosting & domain setup", "Ongoing maintenance plans"],
     "approach": "We design and build with secure defaults from the first commit — HTTPS, secure headers, input validation, and access control reviewed before launch rather than patched afterward. Hosting and domain setup is handled so you launch with one less thing to coordinate yourself.",
     "idealFor": "New businesses needing an online presence, companies replacing an outdated or insecure site, or anyone launching a customer portal or e-commerce store who wants security considered from the start.",
     "deliverable": "A live, hardened website or web app with HTTPS, secure headers, and basic hardening applied by default — plus hosting setup and an optional ongoing maintenance plan."},
]

SERVICES_BY_SLUG = {s["slug"]: s for s in SERVICES}


@app.context_processor
def inject_globals():
    return {"all_services": SERVICES}


@app.route("/")
def home():
    return render_template("home.html", title="Cyberprotek — Secure IT Infrastructure & VAPT Services",
                            description="Full-stack IT services and security testing for SMBs and startups.",
                            active="home")


@app.route("/services")
def services():
    return render_template("services.html", title="Our Services — Cyberprotek",
                            description="All 7 IT and security services offered by Cyberprotek.",
                            active="services")


@app.route("/services/<slug>")
def service_detail(slug):
    s = SERVICES_BY_SLUG.get(slug)
    if not s:
        return redirect(url_for("services"))
    related = [o for o in SERVICES if o["slug"] != slug][:4]
    return render_template("service_detail.html", title=f"{s['short']} — Cyberprotek",
                            description=s["desc"], active="services", s=s, related=related)


@app.route("/about")
def about():
    return render_template("about.html", title="About — Cyberprotek",
                            description="Why Cyberprotek exists and how we work with SMBs and startups.",
                            active="about")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    submitted = None
    error_msg = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service = request.form.get("service", "")
        message = request.form.get("message", "").strip()

        if not name or not email or not phone or not message:
            error_msg = "All fields are required."
        elif not re.match(EMAIL_REGEX, email):
            error_msg = "Please enter a valid email address."
        elif not re.match(PHONE_REGEX, phone):
            error_msg = "Please enter a valid 10-digit phone number."
        else:
            file_exists = os.path.isfile(MESSAGES_FILE)
            with open(MESSAGES_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "name", "email", "phone", "service", "message"])
                writer.writerow([datetime.now().isoformat(timespec="seconds"), name, email, phone, service, message])
            send_inquiry_email(name, email, phone, service, message)
            submitted = {"name": name, "email": email}

    return render_template("contact.html", title="Contact — Cyberprotek",
                            description="Get in touch with Cyberprotek for a free consult.",
                            active="contact", submitted=submitted, error_msg=error_msg)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)