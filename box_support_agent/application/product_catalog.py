"""Product catalog for Kalash Packaging based on the brochure"""

class ProductCatalog:
    """Contains all product information from Kalash Packaging"""

    COMPANY_NAME = "Kalash Packaging"
    COMPANY_LOCATION = "Ahmedabad"
    CONTACT_PHONES = ["9106845371", "7600337948"]

    # Window Boxes - Top Window Range
    TOP_WINDOW_BOXES = {
        "8x8x5": {"type": "Top Window", "dimensions": "8x8x5 inch"},
        "10x10x5": {"type": "Top Window", "dimensions": "10x10x5 inch"},
        "12x12x5": {"type": "Top Window", "dimensions": "12x12x5 inch"},
    }

    # L Window Boxes
    L_WINDOW_BOXES = {
        "10x10x5_L": {"type": "L Window", "dimensions": "10x10x5 inch", "suitable_for": "Tall cakes, Gift hampers, Premium bakery products"},
        "8x8x8_L": {"type": "L Window", "dimensions": "8x8x8 inch", "suitable_for": "Tall cakes, Gift hampers, Premium bakery products"},
        "10x10x8_L": {"type": "L Window", "dimensions": "10x10x8 inch", "suitable_for": "Tall cakes, Gift hampers, Premium bakery products"},
        "12x12x8_L": {"type": "L Window", "dimensions": "12x12x8 inch", "suitable_for": "Tall cakes, Gift hampers, Premium bakery products"},
    }

    WINDOW_BOX_COLORS = ["White", "Pastel Pink", "Mint Green", "Sky Blue"]

    WINDOW_BOX_FEATURES = [
        "Strong & durable material",
        "Clean window finish",
        "Premium Pastel colour range",
        "Customisation available"
    ]

    FOIL_STAMPING = {
        "available": True,
        "moq": 1000,
        "features": [
            "Customer name/brand can be stamped",
            "Premium foil finish",
            "Enhances brand visibility"
        ],
        "note": "Design charge extra one time"
    }

    # MDF Boards
    MDF_BOARD_SIZES = ["6 inch", "7 inch", "8 inch", "9 inch", "10 inch", "12 inch",
                       "14 inch", "16 inch", "18 inch", "20 inch", "14x19 inch"]

    MDF_BOARD_COLORS = ["White", "Black", "Golden", "Pastel Colours"]

    MDF_BOARD_SHAPES = ["Square (Round Corners)", "Round", "Round with Handle"]

    MDF_BRANDING = {
        "available": True,
        "options": ["Logo Branding", "Insta Handle", "Phone Number", "Bakery's Name"],
        "note": "MOQ will be there as per size and design charges will be extra one time"
    }

    # Drum Boards
    DRUM_BOARD_SIZES = ["10x10", "12x12", "14x14"]
    DRUM_BOARD_COLORS = ["Black", "White", "Golden"]

    # Cutlery Kits
    CUTLERY_KIT_CONTENTS = {
        "standard": ["1 knife", "4 candles"],
        "suitable_for": ["Cakes", "Parties", "Celebrations & Events"],
        "customization": {
            "available": True,
            "options": ["Kit contents can be customized", "Custom branding & printing available"],
            "moq_for_branding": 10000
        }
    }

    @classmethod
    def get_all_products_summary(cls) -> str:
        """Returns a formatted summary of all products"""
        return f"""**Welcome to {cls.COMPANY_NAME}!**

We are a manufacturer based in {cls.COMPANY_LOCATION}, specializing in:

**1. WINDOW BOXES**
   • Top Window Range: {', '.join([v['dimensions'] for v in cls.TOP_WINDOW_BOXES.values()])}
   • L Window Range: {', '.join([v['dimensions'] for v in cls.L_WINDOW_BOXES.values()])}
   • Colors: {', '.join(cls.WINDOW_BOX_COLORS)}
   • Features: {', '.join(cls.WINDOW_BOX_FEATURES)}
   • Foil Stamping Available (MOQ: {cls.FOIL_STAMPING['moq']} boxes)

**2. MDF BOARDS**
   • Sizes: {', '.join(cls.MDF_BOARD_SIZES)}
   • Colors: {', '.join(cls.MDF_BOARD_COLORS)}
   • Shapes: {', '.join(cls.MDF_BOARD_SHAPES)}
   • Custom Branding Available

**3. DRUM BOARDS**
   • Sizes: {', '.join(cls.DRUM_BOARD_SIZES)}
   • Colors: {', '.join(cls.DRUM_BOARD_COLORS)}

**4. CUTLERY KITS**
   • Standard Kit: {', '.join(cls.CUTLERY_KIT_CONTENTS['standard'])}
   • Ideal for: {', '.join(cls.CUTLERY_KIT_CONTENTS['suitable_for'])}
   • Custom Branding Available (MOQ: {cls.CUTLERY_KIT_CONTENTS['customization']['moq_for_branding']} kits)

We focus on quality, consistency, and timely delivery.
Pricing is dynamic and will be provided based on your requirements."""

    @classmethod
    def get_window_boxes_info(cls) -> str:
        """Returns detailed window box information"""
        top_details = "\n   • ".join([f"{v['dimensions']} - {v['type']}" for v in cls.TOP_WINDOW_BOXES.values()])
        l_details = "\n   • ".join([f"{v['dimensions']} - {v['type']}" for v in cls.L_WINDOW_BOXES.values()])

        return f"""**WINDOW BOXES**

**Top Window Range:**
   • {top_details}

**L Window Range:**
   • {l_details}
   Best suitable for: Tall cakes, Gift hampers, Premium bakery products

**Available Colors (both Top Window & L Window):**
   • {', '.join(cls.WINDOW_BOX_COLORS)}

**Key Features:**
   • {chr(10) + '   • '.join(cls.WINDOW_BOX_FEATURES)}

**Customization (Foil Stamping):**
   • {chr(10) + '   • '.join(cls.FOIL_STAMPING['features'])}
   • Minimum Order: {cls.FOIL_STAMPING['moq']} boxes
   • Note: {cls.FOIL_STAMPING['note']}"""

    @classmethod
    def get_mdf_boards_info(cls) -> str:
        """Returns detailed MDF board information"""
        return f"""**MDF BOARDS**

**Available Sizes:**
   • {', '.join(cls.MDF_BOARD_SIZES)}

**Color Options:**
   • {', '.join(cls.MDF_BOARD_COLORS)}

**Shape Options:**
   • {', '.join(cls.MDF_BOARD_SHAPES)}

**Custom Branding Options:**
   • {', '.join(cls.MDF_BRANDING['options'])}
   • Note: {cls.MDF_BRANDING['note']}"""

    @classmethod
    def get_drum_boards_info(cls) -> str:
        """Returns detailed drum board information"""
        return f"""**DRUM BOARDS**

**Available Sizes:**
   • {', '.join(cls.DRUM_BOARD_SIZES)}

**Color Options:**
   • {', '.join(cls.DRUM_BOARD_COLORS)}

Drum boards are perfect for presenting cakes and other bakery items."""

    @classmethod
    def get_cutlery_kits_info(cls) -> str:
        """Returns detailed cutlery kit information"""
        return f"""**CUTLERY KITS**

**Standard Kit Contains:**
   • {', '.join(cls.CUTLERY_KIT_CONTENTS['standard'])}

**Ideal For:**
   • {', '.join(cls.CUTLERY_KIT_CONTENTS['suitable_for'])}

**Customization Available:**
   • {', '.join(cls.CUTLERY_KIT_CONTENTS['customization']['options'])}
   • Minimum Order for Branding: {cls.CUTLERY_KIT_CONTENTS['customization']['moq_for_branding']} kits

Designed for bakeries, cafes, and bulk requirements, these kits ensure convenience and hygiene."""
