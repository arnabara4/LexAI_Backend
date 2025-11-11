# in backend/test_tls.py
import smtplib
import ssl
import certifi  # <-- 1. Import certifi

# --- Configuration ---
SMTP_SERVER = "smtp.googlemail.com"
SMTP_PORT = 465  # We'll stick with SSL
SENDER_EMAIL = "lexai222005@gmail.com"
SENDER_PASSWORD = "wwwe lfkm hiuu ejxb"

print(f"--- Python SSL Test (Port 465) with certifi ---")

# --- 2. THE FIX ---
# Create an SSL context that points *directly*
# to certifi's bundle of trusted certificates.
context = ssl.create_default_context(cafile=certifi.where())
# --- END FIX ---

try:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        
        print("[Step 1] Secure SSL connection established.")
        
        print(f"[Step 2] Logging in as {SENDER_EMAIL}...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("         >>> Login successful!")
        
        print("[Step 3] Sending a test email to yourself...")
        server.sendmail(
            SENDER_EMAIL, 
            SENDER_EMAIL,
            "Subject: Python SSL Test (Port 465) with certifi\n\nThis is a successful test."
        )
        print("         >>> Test email sent!")
        print("\n--- TEST SUCCEEDED! ---")

except smtplib.SMTPException as e:
    print(f"\n--- SMTP ERROR (e.g., Bad Password) ---")
    print(f"An SMTP error occurred: {e}")
except Exception as e:
    print(f"\n--- GENERIC ERROR ---")
    print(f"A different error occurred: {e}")

print("\nTest complete.")