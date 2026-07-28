"""
allowed_tables.py

Defines which PostgreSQL tables are allowed to be exported
for chatbot knowledge ingestion.

Security Notes
--------------
• Only tables listed here can be read.
• Any table not listed here is ignored.
• This prevents accidental exposure of sensitive tables
  such as users, wallets, bets, transactions, OTPs, etc.
"""


ALLOWED_TABLES = [

    # ---------------------------------------------------------
    # Bonus & Promotions
    # ---------------------------------------------------------
    "bonus",

    # ---------------------------------------------------------
    # Casino
    # ---------------------------------------------------------
    "casino_categories",

    "casino_providers",

    # ---------------------------------------------------------
    # Website CMS
    # ---------------------------------------------------------
    "cms",

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------
    "countries",

]