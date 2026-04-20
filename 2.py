# # .env file for LOCAL development with Docker Compose
# # DO NOT use this file directly for PRODUCTION deployment on GCP.

# # .env

SECRET_KEY=django-insecure-jx8+f(ufuh1511f^6r54*p=^q&_k8(ea0xuaq#d3gnf79skjkp
DEBUG=true
ALLOWED_HOSTS=127.0.0.1,localhost,75.119.151.28,.ngrok-free.app
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres-user-password
DB_HOST=75.119.151.28
DB_PORT=5432

EMAIL_HOST_USER=ayodelefestusng@gmail.com
EMAIL_HOST_PASSWORD=nbcttuaiguzszciv
# DEFAULT_FROM_EMAIL=ayodelefestusng@gmail.com
DEFAULT_FROM_EMAIL=ayula

STRIPE_PUBLISHABLE_KEY =pk_test_51S65lID1wcj2Cw7OMRd2s5q325Wz7k7Zmuj0Ue4fs1883CqzSTT327jT90pLKpyDAIB22qw2hTqUafDOl4lHYofk00O9HIFUcw  
STRIPE_SECRET_KEY =sk_test_51S65lID1wcj2Cw7OcBU2855rqjNap3MR4qLdMfyxcOapxc9KMwofJ83YPpjnEdywcexl4Kzm7kSHLJXJezOtgcza00PN5hRluR


PAYPAL_CLIENT_ID =AYo71w6UpSabbybMX8L92gpj3fzgWwupxfivtIGwYED5YvzFJwTjBd7j6_DVoR8jsM8ozQeHJJumrJ5m
PAYPAL_CLIENT_SECRET =EM2aPb5Og5zrpOyZXD5ihF9qaDWEx5AARImKbeU1JkXi7xbWlA_NFinSeGkoJXZt3BINo7V6g4S5qBIL



GOOGLE_API_KEY=AIzaSyBszV0VjdcGFrHlkgfIw6Z0q8zTzIVlUXU
# GOOGLE_MAPS_API_KEY=AIzaSyBszV0VjdcGFrHlkgfIw6Z0q8zTzIVlUXU   # antigravity placehodlder 
GOOGLE_MAPS_API_KEY=AIzaSyDuPZzHxMY3HYN-3tnFGrMN6M_wae-XaSU
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=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
LANGSMITH_PROJECT=Agent_Creation
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
TAVILY_API_KEY=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


GROQ_API_KEY=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
DEEPSEEK_API_KEY=sk-ed1202ed2d634e83bea1ea6c72e076e9
OPENAI_API_KEY=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






DATABASE_URI = postgresql://postgres:postgres-user-password@75.119.151.28:5432/postgres

DB_URI= postgresql://postgres:postgres-user-password@75.119.151.28:5432/postgres?connect_timeout=10



# myproject/settings.py

# ... other settings ...

# WhatsApp API Configuration
WHATSAPP_ACCESS_TOKEN = EAAOmGyek9hYBO2evDltQreNVxp7HhdezY8nXjI9KxYYsVmsECAoifNh1OzvsbRR6PNR7a70E3PZAjZCpbSPvuGqtTEcFriUxMc8tpmFhZAH1vE6sANSk5Ybl4shNIZCb0WWZCCAOm8nCdRsZCgaGnMcp6tl4LDKzZA9koFhhY05mekr3x0FRj7mZCMOZBcF8Du9Rw5VZAU1lc0hCiepPKRgLcZBMENgMJv9K6PpidoRM0YZD # Replace with your actual token
WHATSAPP_PHONE_NUMBER_ID = 722142394308907# Replace with your Phone Number ID
WHATSAPP_VERIFY_TOKEN = HAPPY # The token you set when configuring the webhook
WHATSAPP_API_VERSION = v22.0 # Or the latest version you are using, e.g., 'v20.0'





# WHATSAPP_ACCESS_TOKEN = EAAOmGyek9hYBPPcVZCx5HnVouVK6K221MD30qjgVoyiMZBy1N6uVWPKZBf67hQ7WkaqfkevyStV2GeqDwsmsAWij6mK2WrkEbhCsv3CIXtaZAspOjUMYX6Ie8h1Nh4JzfKpsl1pl1CTlXW83ZBd9eD0FKN3ggiQwXwq80JUoVDUtC8muK6iehotimhRAv41ZBRXMT6DZB1CSHDwK4ORlUMoQhhoo1jkF0mLZAMCdwtGZB # Replace with your actual token
# WHATSAPP_PHONE_NUMBER_ID = 722142394308907# Replace with your Phone Number ID
# WHATSAPP_VERIFY_TOKEN = HAPPY # The token you set when configuring the webhook
# WHATSAPP_API_VERSION = v22.0 # Or the latest version you are using, e.g., 'v20.0'