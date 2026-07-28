"""
Approved database views that the chatbot is allowed to read.

Security Boundary
-----------------
The chatbot NEVER queries application tables directly.

Instead it only reads from curated SQL views.

Each view:

• Contains only chatbot-safe information.
• Already joins related tables.
• Hides internal columns.
• Removes sensitive information.
• Has one handwritten row_to_text() template.

One row in one view
        ↓
One chunk
        ↓
Vector Database
"""

APPROVED_VIEWS = [

    # ---------------------------------------------------------
    # Bonus & Promotions
    # ---------------------------------------------------------

    "v_bonus_rules",

    "v_promotions",

    # ---------------------------------------------------------
    # Casino
    # ---------------------------------------------------------

    "v_games",

    "v_game_category",

    "v_casino_categories",

    # ---------------------------------------------------------
    # Sportsbook
    # ---------------------------------------------------------

    "v_sportsbook_providers",

    # ---------------------------------------------------------
    # Payment
    # ---------------------------------------------------------

    "v_payment_gateway_settings",

    "v_withdrawal_rules",

    # ---------------------------------------------------------
    # Website Content
    # ---------------------------------------------------------

    "v_faq_content",

    "v_cms_pages",

    "v_announcements",

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    "v_site_settings",

    "v_supported_currencies",

    "v_supported_countries",

]