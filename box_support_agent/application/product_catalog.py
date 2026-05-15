"""
Product catalog for Kavacch — Enriched Edition
Combines the original catalog structure with full visual data from the
Festival Edition Gift Boxes Brochure (PDF).

Added for every product:
  - size / dimensions
  - color variants
  - color_pattern  (visual/design description of the print)
  - design         (shape / structural design)
  - description    (full enriched description)
  - product_name   (human-readable display name)
"""


class ProductCatalog:
    """Contains all product information for Kavacch — Ahmedabad."""

    COMPANY_NAME = "Kavacch"
    COMPANY_LOCATION = "Ahmedabad"
    CONTACT_PHONES = ["9106845371", "7600337948"]

    # ──────────────────────────────────────────────────────────────────────────
    # WINDOW BOXES
    # ──────────────────────────────────────────────────────────────────────────
    TOP_WINDOW_BOXES = {
        "8x8x5": {
            "product_name": "Top Window Box — 8×8×5",
            "type": "Top Window",
            "dimensions": "8×8×5 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": "Square box with top-facing transparent window panel.",
            "description": (
                "A compact square gift/bakery box with a top-facing PVC window. "
                "Available in four soft pastel shades. Strong, durable material "
                "with clean window finish. Foil stamping (MOQ 1000) available."
            ),
        },
        "10x10x5": {
            "product_name": "Top Window Box — 10×10×5",
            "type": "Top Window",
            "dimensions": "10×10×5 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": "Square box with top-facing transparent window panel.",
            "description": (
                "Medium square gift/bakery box with a top-facing PVC window. "
                "Same pastel color range as the 8×8×5. Foil stamping available."
            ),
        },
        "12x12x5": {
            "product_name": "Top Window Box — 12×12×5",
            "type": "Top Window",
            "dimensions": "12×12×5 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": "Square box with top-facing transparent window panel.",
            "description": (
                "Large square gift/bakery box with a top-facing PVC window. "
                "Same pastel color range. Foil stamping available."
            ),
        },
    }

    L_WINDOW_BOXES = {
        "10x10x5_L": {
            "product_name": "L Window Box — 10×10×5",
            "type": "L Window",
            "dimensions": "10×10×5 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": (
                "Square box with an L-shaped front+side transparent window, "
                "giving a wider view of contents."
            ),
            "suitable_for": "Tall cakes, Gift hampers, Premium bakery products",
            "description": (
                "Premium square box with an L-shaped PVC window for maximum "
                "product visibility. Ideal for tall cakes and gift hampers."
            ),
        },
        "8x8x8_L": {
            "product_name": "L Window Box — 8×8×8",
            "type": "L Window",
            "dimensions": "8×8×8 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": "Tall square box with L-shaped transparent window panel.",
            "suitable_for": "Tall cakes, Gift hampers, Premium bakery products",
            "description": (
                "Tall square box (cube proportion) with L-window for full-height "
                "display of contents. Strong and durable."
            ),
        },
        "10x10x8_L": {
            "product_name": "L Window Box — 10×10×8",
            "type": "L Window",
            "dimensions": "10×10×8 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": "Large tall square box with L-shaped transparent window panel.",
            "suitable_for": "Tall cakes, Gift hampers, Premium bakery products",
            "description": (
                "Large tall square box with L-window. Designed for premium "
                "presentation of tall cakes or stacked gift hampers."
            ),
        },
        "12x12x8_L": {
            "product_name": "L Window Box — 12×12×8",
            "type": "L Window",
            "dimensions": "12×12×8 inch",
            "colors": ["White", "Pastel Pink", "Mint Green", "Sky Blue"],
            "color_pattern": "Solid pastel finish — clean, flat color with no print.",
            "design": "Extra-large tall square box with L-shaped transparent window panel.",
            "suitable_for": "Tall cakes, Gift hampers, Premium bakery products",
            "description": (
                "Largest L-window box variant. Ideal for big celebration cakes "
                "and luxury gift hampers."
            ),
        },
    }

    WINDOW_BOX_FEATURES = [
        "Strong & durable material",
        "Clean window finish",
        "Premium Pastel colour range",
        "Customisation available",
    ]

    FOIL_STAMPING = {
        "available": True,
        "moq": 1000,
        "features": [
            "Customer name/brand can be stamped",
            "Premium foil finish",
            "Enhances brand visibility",
        ],
        "note": "Design charge extra one time",
    }

    # ──────────────────────────────────────────────────────────────────────────
    # MDF BOARDS  (Cake Bases / Cake Boards)
    # ──────────────────────────────────────────────────────────────────────────
    MDF_BOARD_ALIASES = ["cake base", "cake board", "base board", "cake base board", "mdf board"]

    MDF_BOARDS = {
        "MDF_SQUARE": {
            "product_name": "MDF Board — Square (Round Corners)",
            "shape": "Square (Round Corners)",
            "sizes": [
                "6 inch", "7 inch", "8 inch", "9 inch", "10 inch",
                "12 inch", "14 inch", "16 inch", "18 inch", "20 inch", "14×19 inch",
            ],
            "colors": ["White", "Black", "Golden", "Pastel Colours"],
            "color_pattern": (
                "Solid flat finish in the chosen color. "
                "Pastel variants are soft matte tones. "
                "Golden variant has a metallic sheen."
            ),
            "design": "Flat rigid board, square shape with rounded corners.",
            "description": (
                "Sturdy MDF cake base in square shape with safe rounded corners. "
                "Available across a wide size range from 6″ to 20″ plus a "
                "rectangular 14×19″ option. Custom branding (logo, insta handle, "
                "phone number, bakery name) available — MOQ and one-time design "
                "charge apply."
            ),
        },
        "MDF_ROUND": {
            "product_name": "MDF Board — Round",
            "shape": "Round",
            "sizes": [
                "6 inch", "7 inch", "8 inch", "9 inch", "10 inch",
                "12 inch", "14 inch", "16 inch", "18 inch", "20 inch",
            ],
            "colors": ["White", "Black", "Golden", "Pastel Colours"],
            "color_pattern": (
                "Solid flat finish. Golden has metallic sheen. "
                "Pastel variants are soft matte tones."
            ),
            "design": "Flat rigid circular board.",
            "description": (
                "Sturdy MDF cake base in round shape. Same broad size range as "
                "square variant. Branding options available."
            ),
        },
        "MDF_ROUND_HANDLE": {
            "product_name": "MDF Board — Round with Handle",
            "shape": "Round with Handle",
            "sizes": [
                "6 inch", "7 inch", "8 inch", "9 inch", "10 inch",
                "12 inch", "14 inch", "16 inch", "18 inch", "20 inch",
            ],
            "colors": ["White", "Black", "Golden", "Pastel Colours"],
            "color_pattern": (
                "Solid flat finish. Golden has metallic sheen."
            ),
            "design": "Flat rigid circular board with an attached carry handle.",
            "description": (
                "Round MDF cake base with a built-in carry handle for easy "
                "transport. Ideal for delivery-ready cake presentation."
            ),
        },
    }

    MDF_BRANDING = {
        "available": True,
        "options": ["Logo Branding", "Insta Handle", "Phone Number", "Bakery's Name"],
        "note": "MOQ will be there as per size and design charges will be extra one time",
    }

    # ──────────────────────────────────────────────────────────────────────────
    # DRUM BOARDS
    # ──────────────────────────────────────────────────────────────────────────
    DRUM_BOARDS = {
        "DRUM_10x10": {
            "product_name": "Drum Board — 10×10",
            "dimensions": "10×10 inch",
            "colors": ["Black", "White", "Golden"],
            "color_pattern": "Solid flat or metallic finish.",
            "design": "Thick double-layered board (drum style) for sturdy cake base.",
            "description": "10×10 inch drum board — extra thick and sturdy cake base.",
        },
        "DRUM_12x12": {
            "product_name": "Drum Board — 12×12",
            "dimensions": "12×12 inch",
            "colors": ["Black", "White", "Golden"],
            "color_pattern": "Solid flat or metallic finish.",
            "design": "Thick double-layered drum board.",
            "description": "12×12 inch drum board for medium and large cakes.",
        },
        "DRUM_14x14": {
            "product_name": "Drum Board — 14×14",
            "dimensions": "14×14 inch",
            "colors": ["Black", "White", "Golden"],
            "color_pattern": "Solid flat or metallic finish.",
            "design": "Thick double-layered drum board.",
            "description": "14×14 inch drum board for large cakes and tiered displays.",
        },
    }

    # ──────────────────────────────────────────────────────────────────────────
    # CUTLERY KITS
    # ──────────────────────────────────────────────────────────────────────────
    CUTLERY_KITS = {
        "STANDARD_KIT": {
            "product_name": "Cutlery Kit — Standard",
            "contents": ["1 knife", "4 candles"],
            "suitable_for": ["Cakes", "Parties", "Celebrations & Events"],
            "color_pattern": "N/A — utility product.",
            "design": "Compact kit packaging holding knife and candles.",
            "description": (
                "Standard celebration cutlery kit with 1 knife and 4 candles. "
                "Contents and branding fully customisable. "
                "MOQ for branding: 10,000 kits."
            ),
            "customization": {
                "available": True,
                "options": ["Kit contents can be customized", "Custom branding & printing available"],
                "moq_for_branding": 10000,
            },
        },
    }

    # ──────────────────────────────────────────────────────────────────────────
    # GIFT BOXES  (Decorative / Fancy Gift Packaging — Festival Edition)
    # ──────────────────────────────────────────────────────────────────────────
    # All sizes and visual details sourced from the Festival Edition PDF brochure.
    # "Regular shape" = upright vertical box with arch/dome/peaked flap + window.
    # "Hut shape"    = 3-D house/hut form with pitched roof.
    # "Landscape"    = wide horizontal bag-style box.
    # "Tray"         = flat tray base with full clear-PVC lid.
    GIFT_BOX_ALIASES = ["gift box", "gift boxes", "fancy box", "decorative box", "sa box"]

    GIFT_BOXES = {

        # ── GROUP 1 : Mughal arch-top  (Catalogue page 1) ─────────────────────
        "SA_001_BLUE": {
            "product_name": "Mughal Arch-Top Gift Box — Blue",
            "code": "SA 001",
            "color": "Blue",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — arch-top vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Deep indigo/purple-blue base with intricate Mughal motifs: "
                "gold lotus blooms, ornate lanterns, royal horse carriage, "
                "peacock-feather border, and arch-shaped window frame in navy."
            ),
            "design": (
                "Tall upright box with a pointed arch-top flap. Front face has "
                "an arched die-cut PVC window. Fitted with a gold metal "
                "carry handle and a purple silk ribbon bow."
            ),
            "description": (
                "Classic Mughal-themed arch-top gift box in deep blue. "
                "The pointed flap and arched window give it an elegant haveli "
                "silhouette. Gold handle, purple bow. Ideal for Diwali, weddings, "
                "and premium sweet gifting."
            ),
            "group": "Mughal Arch-Top",
        },
        "SA_002_GREEN": {
            "product_name": "Mughal Arch-Top Gift Box — Green",
            "code": "SA 002",
            "color": "Green",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — arch-top vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Soft sage/pastel green base with the same Mughal motif set "
                "as SA 001 — lotus, lanterns, royal carriage, arch border — "
                "rendered in gold and deeper green tones."
            ),
            "design": (
                "Identical structural design to SA 001: pointed arch-top flap, "
                "arched window, gold metal handle, coordinating ribbon bow."
            ),
            "description": (
                "Mughal arch-top gift box in soft pastel green. "
                "Same premium motifs and structure as SA 001."
            ),
            "group": "Mughal Arch-Top",
        },
        "SA_003_ORANGE": {
            "product_name": "Mughal Arch-Top Gift Box — Orange",
            "code": "SA 003",
            "color": "Orange / Peach",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — arch-top vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Warm peach-orange base with Mughal motifs (lotus, lanterns, "
                "carriage, arch border) in complementary amber and gold tones."
            ),
            "design": (
                "Same structure as SA 001: pointed arch-top flap, "
                "arched window, gold handle, ribbon bow."
            ),
            "description": (
                "Mughal arch-top gift box in warm peach-orange. "
                "Festive tone — great for Diwali gifting."
            ),
            "group": "Mughal Arch-Top",
        },

        # ── GROUP 2 : Floral dome-top  (Catalogue page 2) ─────────────────────
        "SA_004_PINK": {
            "product_name": "Floral Dome-Top Gift Box — Pink",
            "code": "SA 004",
            "color": "Pink",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — dome/arch-top vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Soft pink base with abstract floral damask medallion print "
                "in watercolor style — delicate flowers, vines, and fine gold "
                "line accents on the body; dome top in solid pink."
            ),
            "design": (
                "Upright box with a rounded dome-top arch flap. "
                "Arched die-cut PVC window on front. Gold metal carry handle "
                "with matching pink ribbon bow."
            ),
            "description": (
                "Feminine floral dome-top gift box in pastel pink watercolor. "
                "Suited for Eid, birthdays, and sweet hampers."
            ),
            "group": "Floral Dome-Top",
        },
        "SA_005_BLUE": {
            "product_name": "Floral Dome-Top Gift Box — Blue",
            "code": "SA 005",
            "color": "Blue",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — dome/arch-top vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Soft sky-blue base with abstract floral damask medallion print "
                "in watercolor style. Blue ribbon bow and matching dome top."
            ),
            "design": "Same dome-top structure as SA 004.",
            "description": (
                "Floral dome-top gift box in sky blue. Watercolor damask motif "
                "with gold line accents. Matching blue ribbon bow."
            ),
            "group": "Floral Dome-Top",
        },

        # ── GROUP 3 : House window box with shutters  (Catalogue page 3) ──────
        "SA_006_PURPLE": {
            "product_name": "House Window Gift Box — Purple",
            "code": "SA 006",
            "color": "Purple / Magenta",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — house/peaked-roof vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Vibrant magenta-purple body covered in a tonal damask scroll "
                "pattern. Peaked triangular flap has white botanical branches. "
                "Base border features vivid multicolor garden flowers "
                "(sunflowers, lilies, daisies) in orange, green, and blue."
            ),
            "design": (
                "Upright box with a peaked triangular house-roof flap. "
                "Front face has an arched PVC window styled like a villa window "
                "with yellow louvred wooden shutters. Gold handle, cream ribbon bow."
            ),
            "description": (
                "Eye-catching magenta house-window gift box with a botanical "
                "garden border. The louvred shutter detail makes it stand out. "
                "Ideal for festive gift hampers."
            ),
            "group": "House Window Box with Shutters",
        },
        "SA_007_BROWN": {
            "product_name": "House Window Gift Box — Brown",
            "code": "SA 007",
            "color": "Brown / Earthy",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — house/peaked-roof vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Warm earthy brown body with tonal scroll pattern. "
                "Same colorful garden flower border at base. "
                "Arched window with yellow louvred shutters."
            ),
            "design": "Same peaked house-roof structure as SA 006.",
            "description": (
                "Earthy-toned house window gift box with garden flower border "
                "and louvred shutter window."
            ),
            "group": "House Window Box with Shutters",
        },
        "SA_008_CREAM": {
            "product_name": "House Window Gift Box — Cream",
            "code": "SA 008",
            "color": "Cream / Beige",
            "size": "7.25 × 8.25 inch (W × H)",
            "shape": "Regular — house/peaked-roof vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Light cream-beige body with subtle tonal pattern. "
                "Bright garden flower border at base. "
                "Arched louvred shutter window as on other group variants."
            ),
            "design": "Same peaked house-roof structure as SA 006.",
            "description": (
                "Soft cream house window gift box — understated elegance with "
                "the signature garden border and shutter window."
            ),
            "group": "House Window Box with Shutters",
        },

        # ── GROUP 4 : Wide landscape bag — gold handle  (Catalogue page 4) ────
        "SA_009_PINK": {
            "product_name": "Wide Landscape Gift Bag — Pink (Gold Handle)",
            "code": "SA 009",
            "color": "Pink",
            "size": "17.5 × 10.25 × 3.5 inch (W × H × D)",
            "shape": "Landscape bag — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Pink base with a diamond/lattice quilted pattern on side panels. "
                "Top border features a dense hanging floral-and-vine print "
                "(wisteria/bellflower style) in deeper pinks and greens."
            ),
            "design": (
                "Wide horizontal gift bag with flat gold metallic carry handle. "
                "Large transparent PVC window across the front face. "
                "Fits multiple sweet trays or jar assortments side by side."
            ),
            "description": (
                "Large wide-format pink gift bag with gold handle. Diamond "
                "lattice sides, floral vine top border, big display window. "
                "Great for Diwali, wedding, and corporate gifting."
            ),
            "group": "Wide Landscape Bag — Gold Handle",
        },
        "SA_010_GREEN": {
            "product_name": "Wide Landscape Gift Bag — Green (Gold Handle)",
            "code": "SA 010",
            "color": "Green / Mint",
            "size": "17.5 × 10.25 × 3.5 inch (W × H × D)",
            "shape": "Landscape bag — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Mint-green base with teal diamond/lattice quilted pattern on "
                "sides. Floral vine top border in deeper green and gold tones."
            ),
            "design": "Same wide landscape structure as SA 009. Gold flat handle.",
            "description": "Wide mint-green landscape gift bag with gold handle and display window.",
            "group": "Wide Landscape Bag — Gold Handle",
        },
        "SA_011_PURPLE": {
            "product_name": "Wide Landscape Gift Bag — Purple (Gold Handle)",
            "code": "SA 011",
            "color": "Purple",
            "size": "17.5 × 10.25 × 3.5 inch (W × H × D)",
            "shape": "Landscape bag — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Purple base with diamond/lattice quilted pattern. "
                "Floral vine top border in purple and gold."
            ),
            "design": "Same wide landscape structure as SA 009. Gold flat handle.",
            "description": "Wide purple landscape gift bag with gold handle and display window.",
            "group": "Wide Landscape Bag — Gold Handle",
        },

        # ── GROUP 5 : Wide landscape bag — rope handle  (Catalogue page 5) ────
        "SA_011_TREE": {
            "product_name": "Wide Landscape Gift Bag — Tree Design (Rope Handle)",
            "code": "SA 011",
            "color": "Blush Pink / Multicolor",
            "size": "14 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape bag — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Soft blush-pink sky background with a scenic Indian art-style "
                "landscape: two golden deer mid-stride, teal stylised trees, "
                "rolling hills in red, teal and amber. Scalloped cartouche window cutout."
            ),
            "design": (
                "Wide horizontal box with twisted rope carry handle. "
                "Scalloped decorative window cutout on the front. "
                "Slightly smaller format than the gold-handle landscape range."
            ),
            "description": (
                "Artistic landscape gift bag with a deer-and-tree scenic print. "
                "Rope handle, scalloped window. Elegant and nature-inspired."
            ),
            "group": "Wide Landscape Bag — Rope Handle / Nature Scenes",
        },
        "SA_012_LEAF": {
            "product_name": "Wide Landscape Gift Bag — Leaf Design (Rope Handle)",
            "code": "SA 012",
            "color": "Teal / Amber Multicolor",
            "size": "14 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape bag — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Watercolor-style autumn leaf print across the full box surface: "
                "teal, amber, rust, and gold leaves on a soft neutral background. "
                "Scalloped cartouche window cutout."
            ),
            "design": "Same rope-handle wide landscape structure as SA 011 Tree.",
            "description": "Wide landscape gift bag with watercolor autumn leaf print. Rope handle, scalloped window.",
            "group": "Wide Landscape Bag — Rope Handle / Nature Scenes",
        },
        "SA_013_FLOWER": {
            "product_name": "Wide Landscape Gift Bag — Flower Design (Rope Handle)",
            "code": "SA 013",
            "color": "Mint Green / Multicolor",
            "size": "14 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape bag — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Mint-green base with a botanical flower print — tropical blossoms "
                "in peach, coral, and white with teal-green leaves. "
                "Scalloped cartouche window cutout."
            ),
            "design": "Same rope-handle wide landscape structure as SA 011 Tree.",
            "description": "Wide landscape gift bag with tropical floral print on mint green. Rope handle, scalloped window.",
            "group": "Wide Landscape Bag — Rope Handle / Nature Scenes",
        },

        # ── GROUP 6 : 3-D Realistic Hut Box  (Catalogue page 6) ──────────────
        "SA_014_HUT": {
            "product_name": "3-D Realistic Hut Gift Box",
            "code": "SA 014",
            "color": "Multicolor — teal roof, stone-brick walls",
            "size": "10 × 10 × 8.5 inch (W × D × H, excluding roof apex)",
            "shape": "Hut — full 3-D house form",
            "finish": "Plain",
            "color_pattern": (
                "Photo-realistic illustration: teal/aqua tiled roof, "
                "warm stone-brick walls, brown/teal front door, "
                "white-frame windowpane, ornate wrought-iron lamppost, "
                "garden flowers (red poppies, butterflies), and a bicycle detail. "
                "Transparent PVC window panel on one side face."
            ),
            "design": (
                "True 3-D house-shaped box — peaked roof forms the top lid, "
                "sides form the house walls. Rope carry handle over the roof ridge. "
                "One side has a large rectangular PVC display window."
            ),
            "description": (
                "A charming cottage-style 3-D gift box that looks like a real "
                "stone house. One of the most distinctive designs in the range. "
                "Suitable for Diwali hampers, housewarming gifts, and premium gifting."
            ),
            "group": "3-D Realistic Hut Box",
        },

        # ── GROUP 7 : Wide gable box — candy/sweet print  (Catalogue page 7) ─
        "SA_015_PINK_G": {
            "product_name": "Wide Gable Gift Box — Pink (Candy Print, Rope Handle)",
            "code": "SA 015",
            "color": "Pink G",
            "size": "12 × 8.0 × 5.0 inch (W × H × D)",
            "shape": "Landscape gable box — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Soft pink background covered in a dense all-over illustrated "
                "candy-shop print: cupcakes, ice creams, doughnuts, macarons, "
                "lollipops, candies — in a playful cartoon style. "
                "'Paris / France' stamp motif with Eiffel Tower on one face."
            ),
            "design": (
                "Wide horizontal box with a gable-style arched top flap. "
                "Two twisted rope handles at the top. "
                "Large rectangular PVC window on the front."
            ),
            "description": (
                "Fun Paris-themed candy-print wide gift box in pink. "
                "Great for bakery gifting, kids' parties, and sweet hampers."
            ),
            "group": "Wide Gable Box — Candy/Sweet Print",
        },
        "SA_016_FLOWER_CANDY": {
            "product_name": "Wide Gable Gift Box — Blue (Candy Print, Rope Handle)",
            "code": "SA 016",
            "color": "Blue / Grey",
            "size": "12 × 8.0 × 5.0 inch (W × H × D)",
            "shape": "Landscape gable box — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Soft blue-grey background with the same all-over candy/cupcake "
                "illustrated print as SA 015. 'Paris / France' stamp motif. "
                "Navy blue twisted rope handles."
            ),
            "design": "Same gable structure as SA 015. Navy rope handles.",
            "description": (
                "Blue-grey candy-print wide gable gift box with navy rope handles. "
                "Companion to the pink SA 015."
            ),
            "group": "Wide Gable Box — Candy/Sweet Print",
        },

        # ── GROUP 8 : Four-jar landscape box — bougainvillea  (Catalogue page 8)
        "SA_017_FOUR_JAR": {
            "product_name": "Four-Jar Landscape Box — Cream (Bougainvillea, Golden Leaf)",
            "code": "SA 017",
            "color": "Cream / Beige",
            "size": "14 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape — 4-jar wide box",
            "finish": "Golden Leaf",
            "capacity": "4 jars",
            "color_pattern": (
                "Cream/beige body with a geometric diamond lattice pattern. "
                "Top edge has a lush bougainvillea cascade print (hot pink flowers, "
                "deep green leaves). Four arched PVC window cutouts on front face, "
                "each framing one jar. Eiffel Tower motif on the side panel. "
                "Golden Leaf accent print on the lattice."
            ),
            "design": (
                "Wide horizontal landscape box designed to hold 4 upright jars. "
                "Four individual arched windows allow the contents to be seen. "
                "Twisted rope carry handle."
            ),
            "description": (
                "Premium 4-jar landscape gift box in cream with golden leaf "
                "finish. Bougainvillea cascade across the top, four arched windows. "
                "Ideal for dry fruit, cookies, or jar-gift sets."
            ),
            "group": "Four-Jar Landscape Box — Bougainvillea",
        },
        "SA_018_FOUR_JAR": {
            "product_name": "Four-Jar Landscape Box — Teal (Bougainvillea, Golden Leaf)",
            "code": "SA 018",
            "color": "Teal / Mint",
            "size": "14 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape — 4-jar wide box",
            "finish": "Golden Leaf",
            "capacity": "4 jars",
            "color_pattern": (
                "Teal/mint-green body with the same bougainvillea cascade top, "
                "four arched windows, and Eiffel Tower side motif as SA 017. "
                "Golden Leaf accent print."
            ),
            "design": "Same 4-jar rope-handle landscape structure as SA 017.",
            "description": (
                "Premium 4-jar landscape gift box in teal with golden leaf finish. "
                "Bougainvillea top, four arched windows."
            ),
            "group": "Four-Jar Landscape Box — Bougainvillea",
        },

        # ── GROUP 9 : Baby/kids gable box  (Catalogue page 9) ─────────────────
        "SA_019_BLUE": {
            "product_name": "Baby Gift Box — Blue (It's a Boy, Rope Handle)",
            "code": "SA 019",
            "color": "Blue",
            "size": "12.5 × 10.25 × 5 inch (W × H × D)",
            "shape": "Landscape gable box",
            "finish": "Plain",
            "color_pattern": (
                "Sky-blue base with a baby/toy illustrated print: teddy bears, "
                "colorful balloons, spinning tops, toy train, alphabets, and "
                "'it's a boy' script. A white lace-trim band separates the gable "
                "top from the body."
            ),
            "design": (
                "Wide horizontal gable-top box with twisted rope carry handles. "
                "No front window — full illustrated surface."
            ),
            "description": (
                "Fun 'It's a Boy' baby-themed wide gift box in sky blue. "
                "Suitable for baby shower gifts and gender-reveal hampers."
            ),
            "group": "Baby / Kids Gift Box",
        },
        "SA_020_PINK": {
            "product_name": "Baby Gift Box — Pink (It's a Girl, Rope Handle)",
            "code": "SA 020",
            "color": "Pink",
            "size": "12.5 × 10.25 × 5 inch (W × H × D)",
            "shape": "Landscape gable box",
            "finish": "Plain",
            "color_pattern": (
                "Hot pink base with baby girl illustrated print: pram/pushchair, "
                "star confetti, 'it's a girl' script, hearts, and toy motifs. "
                "White lace-trim band on gable top."
            ),
            "design": "Same gable structure as SA 019.",
            "description": (
                "'It's a Girl' baby-themed wide gift box in hot pink. "
                "Baby shower, gender reveal, and newborn gifting."
            ),
            "group": "Baby / Kids Gift Box",
        },

        # ── GROUP 10 : Hut box — gold tiled roof, carousel  (Catalogue page 10)
        "SA_001_HUT_GOLDEN": {
            "product_name": "Hut Gift Box — Carousel (Gold Tiled Roof, Golden Leaf)",
            "code": "SA 001",
            "color": "Peach / Rose-Gold",
            "size": "5.7 × 8.5 × 10.5 inch (W × D × H)",
            "shape": "Hut — house-shaped vertical box",
            "finish": "Golden Leaf",
            "color_pattern": (
                "Peach/rose-gold body with a carousel horse print on the lower "
                "section. Upper section has a star and string-light motif. "
                "The pitched roof is printed with interlocking gold tile rows "
                "in a warm red-peach tone with gold metallic highlights (Golden Leaf). "
                "Large arched front window is dressed with printed draped curtains "
                "in orange-red with a decorative gold crown motif above."
            ),
            "design": (
                "Hut/house-shaped upright box with a pitched roof lid. "
                "Gold flat metallic carry handle arches over the roof. "
                "Large arched PVC window on the front face, framed with "
                "printed drape/curtain artwork."
            ),
            "description": (
                "Premium carousel-themed hut gift box with Golden Leaf finish. "
                "The metallic tiled roof and curtained window give it a "
                "stage/carousel aesthetic. Great for luxury sweet and dry-fruit gifting."
            ),
            "group": "Hut Box — Gold Tiled Roof / Carousel",
        },

        # ── GROUP 11 : Garden house hut box  (Catalogue page 11) ──────────────
        "SA_001_GARDEN_GREEN": {
            "product_name": "Garden House Hut Box — Green",
            "code": "SA 001",
            "color": "Green / Sage",
            "size": "5.7 × 8.5 × 10.5 inch (W × D × H)",
            "shape": "Hut — house-shaped vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Soft sage-green pitched roof. Body has a front-door scene: "
                "a weathered arched door covered in climbing vines and flower pots. "
                "Side and back panels covered in large pink peony blooms and "
                "soft green leaves on a natural-toned background."
            ),
            "design": (
                "House-shaped hut box with peaked roof, rope carry handle. "
                "Front face features a garden-door illustration. "
                "Side panel has a rectangular PVC window."
            ),
            "description": (
                "Garden cottage hut gift box in sage green. "
                "The painted front door with climbing vines makes it instantly "
                "charming. Suitable for floral gifts, festive hampers."
            ),
            "group": "Garden House Hut Box",
        },
        "SA_003_GARDEN_PINK": {
            "product_name": "Garden House Hut Box — Pink",
            "code": "SA 003",
            "color": "Pink / Rose",
            "size": "5.7 × 8.5 × 10.5 inch (W × D × H)",
            "shape": "Hut — house-shaped vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Pink/rose pitched roof. Same garden-door scene on front, "
                "pink bloom panels on sides, rope handle."
            ),
            "design": "Same garden-house structure as SA 001 Garden Green.",
            "description": "Garden cottage hut gift box in pink. Same charming garden-door design.",
            "group": "Garden House Hut Box",
        },
        "SA_001_GARDEN_BLUE": {
            "product_name": "Garden House Hut Box — Blue",
            "code": "SA 001",
            "color": "Blue / Powder Blue",
            "size": "5.7 × 8.5 × 10.5 inch (W × D × H)",
            "shape": "Hut — house-shaped vertical box",
            "finish": "Plain",
            "color_pattern": (
                "Powder-blue peaked roof. Garden-door illustration on front, "
                "floral panels on sides."
            ),
            "design": "Same garden-house structure.",
            "description": "Garden cottage hut gift box in powder blue.",
            "group": "Garden House Hut Box",
        },

        # ── GROUP 12 : Small 2-jar bag — marble ink, MGI  (Catalogue page 12) ─
        "SA_0020_2JAR_MGI": {
            "product_name": "2-Jar Upright Bag — Marble Ink (MGI Golden Work)",
            "code": "SA 0020",
            "color": "Blue-Pink Marble / Available in 2 colors",
            "size": "7 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Regular — small upright bag-style box",
            "finish": "MGI Golden Work",
            "capacity": "2 jars",
            "color_pattern": (
                "Abstract alcohol-ink marble art: swirling teal-blue, blush-pink, "
                "white, and gold veins across the full surface. "
                "MGI metallic gold foil printing adds shimmer to the gold veins. "
                "A decorative scalloped-edge label panel on the front (for logo/name). "
                "Available in 2 color variants."
            ),
            "design": (
                "Small upright square bag-style box holding 2 jars side by side. "
                "Gold metal carry handle with a circular ball clasp. "
                "Scalloped label panel on front instead of a window."
            ),
            "description": (
                "Elegant 2-jar marble-ink gift bag with premium MGI gold foil work. "
                "The swirling abstract print is sophisticated and contemporary. "
                "Ideal for premium mithai, chocolate, or dry-fruit pairs."
            ),
            "group": "Small 2-Jar Upright Bag — Marble Ink (MGI)",
        },

        # ── GROUP 13 : Wide 3-jar bag — blue peony, MGI  (Catalogue page 13) ──
        "SA_00022_3JAR_MGI": {
            "product_name": "3-Jar Landscape Bag — Blue Peony (MGI Golden Work)",
            "code": "SA 00022",
            "color": "Mint / Blue Peony — Available in 2 colors",
            "size": "10.5 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape — wide bag-style box",
            "finish": "MGI Golden Work",
            "capacity": "3 jars",
            "color_pattern": (
                "Mint-green/white base covered with large indigo-blue peony "
                "blooms and copper-brown/gold leaves. MGI gold foil accents on "
                "the leaf veins and petal edges. "
                "Large scalloped-edge label panel on front."
            ),
            "design": (
                "Wide landscape bag-style box for 3 jars. "
                "Gold flat metallic carry handles. "
                "Scalloped label panel on front face."
            ),
            "description": (
                "Premium 3-jar landscape gift bag with blue peony floral print "
                "and MGI gold foil work. Rich and contemporary floral design. "
                "Available in 2 color variants."
            ),
            "group": "Wide 3-Jar Landscape Bag — Peony (MGI)",
        },

        # ── GROUP 14 : Hut box — MGI Golden Work, crane  (Catalogue page 14) ──
        "HUT_MGI_GOLDEN": {
            "product_name": "Hut Gift Box — Crane (MGI Golden Work)",
            "code": "Hut Shaped",
            "color": "Brown / Maroon & Pink",
            "size": "8.5 × 7.5 × 10.5 inch (W × D × H)",
            "shape": "Hut — house-shaped vertical box",
            "finish": "MGI Golden Work",
            "color_pattern": (
                "Dark brown/maroon pitched roof with fine gold art-deco line "
                "grid — MGI gold foil printing gives a metallic sheen. "
                "Pink body with watercolor floral sprigs (small pink cherry-blossom "
                "style flowers and green leaves). "
                "White cranes (saras/egrets) illustrated on lower body. "
                "Large square PVC window on front, framed with a gold-printed border."
            ),
            "design": (
                "Hut/house-shaped upright box with dark-toned pitched roof lid. "
                "Gold flat metallic carry handle. "
                "Large square PVC display window on front face."
            ),
            "description": (
                "Sophisticated hut gift box with MGI gold work. The crane motif "
                "and watercolor florals give it an Indo-Japanese aesthetic. "
                "Perfect for premium Diwali and wedding gifting."
            ),
            "group": "Hut Box — Crane (MGI Golden Work)",
        },

        # ── GROUP 15 : Small 2-jar bag — floral  (Catalogue page 15) ──────────
        "SA_0021_FLOWER_GREEN": {
            "product_name": "2-Jar Upright Bag — Flower Green Theme",
            "code": "SA 0021",
            "color": "Green / Mint",
            "size": "7.0 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Regular — small upright bag-style box",
            "finish": "Plain",
            "capacity": "2 jars",
            "color_pattern": (
                "Mint/sage-green base with bold blue peony blooms and "
                "copper-brown/gold leaves. Gold metal handles. "
                "Large scalloped-edge label panel on front."
            ),
            "design": (
                "Small upright square bag-style 2-jar box. "
                "Gold flat metallic carry handles with ball clasp. "
                "Large scalloped label panel on front."
            ),
            "description": "2-jar upright gift bag in flower green theme. Bold blue peony print on mint base.",
            "group": "Small 2-Jar Upright Bag — Flower Themes",
        },
        "SA_0026_FLOWER_PINK": {
            "product_name": "2-Jar Upright Bag — Flower Pink Theme",
            "code": "SA 0026",
            "color": "Pink",
            "size": "7.0 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Regular — small upright bag-style box",
            "finish": "Plain",
            "capacity": "2 jars",
            "color_pattern": (
                "Pink base with crimson/magenta peony blooms and gold leaves. "
                "Gold handles, scalloped label panel."
            ),
            "design": "Same structure as SA 0021 Flower Green.",
            "description": "2-jar upright gift bag in flower pink theme. Rich crimson peonies on pink base.",
            "group": "Small 2-Jar Upright Bag — Flower Themes",
        },
        "SA_0027_FLOWER_BLUE": {
            "product_name": "2-Jar Upright Bag — Flower Blue Theme",
            "code": "SA 0027",
            "color": "Blue / Cream",
            "size": "7.0 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Regular — small upright bag-style box",
            "finish": "Plain",
            "capacity": "2 jars",
            "color_pattern": (
                "Off-white/cream base with deep royal-blue peony blooms and "
                "gold leaves. Gold handles, scalloped label panel."
            ),
            "design": "Same structure as SA 0021 Flower Green.",
            "description": "2-jar upright gift bag in flower blue theme. Royal blue peonies on cream base.",
            "group": "Small 2-Jar Upright Bag — Flower Themes",
        },

        # ── GROUP 16 : Wide 3-jar bag — marble running theme  (Catalogue page 16)
        "SA_0022_3JAR_RUNNING": {
            "product_name": "3-Jar Landscape Bag — Marble Running Theme (MGI Golden Work)",
            "code": "SA 0022",
            "color": "Blue-Pink-Gold Marble",
            "size": "10.5 × 8.5 × 3.5 inch (W × H × D)",
            "shape": "Landscape — wide bag-style box",
            "finish": "MGI Golden Work",
            "capacity": "3 jars",
            "color_pattern": (
                "Abstract flowing alcohol-ink marble art in blue, blush-pink, "
                "white and gold — a dynamic 'running/flowing' composition rather "
                "than a static repeat. MGI gold foil highlights on the golden veins. "
                "Wide horizontal scalloped-edge label panel on front."
            ),
            "design": (
                "Wide landscape bag-style box for 3 jars. "
                "Gold flat metallic carry handles."
            ),
            "description": (
                "3-jar landscape gift bag in flowing marble-ink running theme "
                "with MGI gold foil. Luxurious contemporary aesthetic."
            ),
            "group": "Wide 3-Jar Landscape Bag — Marble Running (MGI)",
        },

        # ── GROUP 17 : Wide gable box — daisy/flower  (Catalogue page 17) ─────
        "SA_0014_FLOWER": {
            "product_name": "Wide Gable Gift Box — Daisy Flower Print (Rope Handle)",
            "code": "SA 0014",
            "color": "Pink / Purple accent",
            "size": "12 × 8 × 5 inch (W × H × D)",
            "shape": "Landscape gable box — wide horizontal",
            "finish": "Plain",
            "color_pattern": (
                "Soft pink base covered in a repeating white daisy / marguerite "
                "flower print with orange-centered blooms, pink leaves, and "
                "small blue butterfly accents. "
                "Gable top panel is a contrasting deep purple with a "
                "golden plant motif. Scalloped-edge window cutout on front."
            ),
            "design": (
                "Wide horizontal gable-top box with a single twisted rope handle. "
                "Scalloped-edge die-cut window on the front face."
            ),
            "description": (
                "Cheerful pink daisy-print wide gable gift box. "
                "Purple gable top with gold plant motif adds a contrast pop. "
                "Rope handle, scalloped window. Feminine and festive."
            ),
            "group": "Wide Gable Box — Daisy/Flower Print",
        },
    }

    # ──────────────────────────────────────────────────────────────────────────
    # TRAY BOXES  (Catalogue page 18)
    # ──────────────────────────────────────────────────────────────────────────
    TRAY_BOX_ALIASES = ["tray box", "tray boxes", "tray packaging"]

    TRAY_BOXES = {
        "TRAY_WITH_HANDLE_PEACH": {
            "product_name": "Tray Box with Handle — Peach/Orange",
            "type": "Tray Box with Handle",
            "size": "9 inch",
            "color": "Peach / Orange",
            "color_pattern": "Solid pastel peach-orange flat finish on the tray base. Full clear PVC lid.",
            "design": (
                "Flat cardboard tray base with a full-height clear PVC/acetate lid "
                "that slots over it. Twisted rope handle attached to the base sides."
            ),
            "handle": True,
            "description": "9-inch tray box with rope handle in peach/orange. Clear lid for full content visibility.",
            "suitable_for": "Sweets, Mithai, Dry fruits, Bakery items, Gifts",
        },
        "TRAY_WITH_HANDLE_GREEN": {
            "product_name": "Tray Box with Handle — Light Green",
            "type": "Tray Box with Handle",
            "size": "9 inch",
            "color": "Light Green / Mint",
            "color_pattern": "Solid pastel mint-green flat finish. Full clear PVC lid.",
            "design": "Same tray-with-handle structure. Rope handle.",
            "handle": True,
            "description": "9-inch tray box with rope handle in mint green.",
            "suitable_for": "Sweets, Mithai, Dry fruits, Bakery items, Gifts",
        },
        "TRAY_WITH_HANDLE_BLUE": {
            "product_name": "Tray Box with Handle — Light Blue",
            "type": "Tray Box with Handle",
            "size": "9 inch",
            "color": "Light Blue / Sky Blue",
            "color_pattern": "Solid pastel sky-blue flat finish. Full clear PVC lid.",
            "design": "Same tray-with-handle structure. Rope handle.",
            "handle": True,
            "description": "9-inch tray box with rope handle in sky blue.",
            "suitable_for": "Sweets, Mithai, Dry fruits, Bakery items, Gifts",
        },
        "TRAY_WITHOUT_HANDLE_PINK": {
            "product_name": "Tray Box without Handle — Pink",
            "type": "Tray Box without Handle",
            "size": "11 inch",
            "color": "Pink",
            "color_pattern": "Solid pastel pink/lavender-pink flat finish. Full clear PVC lid.",
            "design": (
                "Larger flat cardboard tray base with full-height clear PVC lid. "
                "No handle — open tray style for display."
            ),
            "handle": False,
            "description": "11-inch tray box without handle in pink. Larger display-style tray.",
            "suitable_for": "Sweets, Mithai, Dry fruits, Bakery items, Gifts",
        },
        "TRAY_WITHOUT_HANDLE_PURPLE": {
            "product_name": "Tray Box without Handle — Purple",
            "type": "Tray Box without Handle",
            "size": "11 inch",
            "color": "Purple / Lavender",
            "color_pattern": "Solid pastel lavender-purple flat finish. Full clear PVC lid.",
            "design": "Same no-handle tray structure as pink variant.",
            "handle": False,
            "description": "11-inch tray box without handle in purple/lavender.",
            "suitable_for": "Sweets, Mithai, Dry fruits, Bakery items, Gifts",
        },
    }

    TRAY_BOX_FEATURES = [
        "Strong & durable material",
        "Neat tray-style presentation",
        "Full clear PVC lid for product visibility",
        "Available with (9 inch, 3 colors) or without handle (11 inch, 2 colors)",
        "Ideal for sweets, dry fruits, mithai, bakery items",
        "Customisation available",
    ]

    GIFT_BOX_FEATURES = [
        "Premium decorative finish",
        "Unique shapes — Regular (vertical), Hut/House, Landscape (wide horizontal)",
        "Jar box variants: 2-jar, 3-jar, 4-jar",
        "MGI Golden Work finish — metallic gold foil print on select models",
        "Golden Leaf finish — embossed gold on select models",
        "Rope or flat gold metallic carry handle depending on model",
        "PVC window or scalloped label panel for product display",
        "Ideal for gifting dry fruits, sweets, chocolates, mithai",
        "Customisation available",
    ]

    # ──────────────────────────────────────────────────────────────────────────
    # QUICK-REFERENCE LOOKUPS
    # ──────────────────────────────────────────────────────────────────────────
    GIFT_BOX_FINISHES = ["Plain", "Golden Leaf", "MGI Golden Work"]
    GIFT_BOX_SHAPES = ["Regular (Vertical)", "Hut / House", "Landscape (Wide Horizontal)", "Landscape Gable"]
    GIFT_BOX_COLORS = [
        "Blue", "Green", "Orange", "Pink", "Purple", "Brown", "Cream",
        "Teal", "Multicolor / Golden", "Marble (Blue-Pink-Gold)",
    ]
    WINDOW_BOX_COLORS = ["White", "Pastel Pink", "Mint Green", "Sky Blue"]
    MDF_BOARD_SIZES = [
        "6 inch", "7 inch", "8 inch", "9 inch", "10 inch", "12 inch",
        "14 inch", "16 inch", "18 inch", "20 inch", "14×19 inch",
    ]
    MDF_BOARD_COLORS = ["White", "Black", "Golden", "Pastel Colours"]
    MDF_BOARD_SHAPES = ["Square (Round Corners)", "Round", "Round with Handle"]
    DRUM_BOARD_COLORS = ["Black", "White", "Golden"]

    @classmethod
    def get_window_boxes_info(cls) -> str:
        top = "\n   • ".join(
            f"{v['product_name']} ({v['dimensions']}) — {v['description']}"
            for v in cls.TOP_WINDOW_BOXES.values()
        )
        l = "\n   • ".join(
            f"{v['product_name']} ({v['dimensions']}) — {v['description']}"
            for v in cls.L_WINDOW_BOXES.values()
        )
        return f"""**WINDOW BOXES**

**Top Window Range:**
   • {top}

**L Window Range:**
   • {l}

**Available Colors:** {', '.join(cls.WINDOW_BOX_COLORS)}
**Key Features:** {' | '.join(cls.WINDOW_BOX_FEATURES)}
**Foil Stamping:** MOQ {cls.FOIL_STAMPING['moq']} boxes — {cls.FOIL_STAMPING['note']}"""

    @classmethod
    def get_mdf_boards_info(cls) -> str:
        board_lines = "\n   • ".join(
            f"{v['product_name']} — Sizes: {', '.join(v['sizes'])} — Colors: {', '.join(v['colors'])}"
            for v in cls.MDF_BOARDS.values()
        )
        return f"""**MDF BOARDS (Cake Bases / Cake Boards)**
Also known as: {', '.join(cls.MDF_BOARD_ALIASES)}

**Available Boards:**
   • {board_lines}

**Custom Branding Options:** {', '.join(cls.MDF_BRANDING['options'])}
**Note:** {cls.MDF_BRANDING['note']}"""

    @classmethod
    def get_drum_boards_info(cls) -> str:
        board_lines = "\n   • ".join(
            f"{v['product_name']} — Colors: {', '.join(v['colors'])}"
            for v in cls.DRUM_BOARDS.values()
        )
        return f"""**DRUM BOARDS**

**Available Sizes & Colors:**
   • {board_lines}

Drum boards are extra-thick, double-layered cake bases for premium presentation."""

    @classmethod
    def get_cutlery_kits_info(cls) -> str:
        kit = cls.CUTLERY_KITS['STANDARD_KIT']
        return f"""**CUTLERY KITS**

**Standard Kit Contains:** {', '.join(kit['contents'])}
**Ideal For:** {', '.join(kit['suitable_for'])}
**Customization:** {' | '.join(kit['customization']['options'])}
**MOQ for Branding:** {kit['customization']['moq_for_branding']} kits

{kit['description']}"""

    @classmethod
    def get_gift_boxes_info(cls) -> str:
        groups: dict = {}
        for v in cls.GIFT_BOXES.values():
            g = v.get("group", "Other")
            groups.setdefault(g, [])
            finish_tag = f" [{v['finish']}]" if v.get("finish") and v["finish"] != "Plain" else ""
            capacity_tag = f" — {v['capacity']}" if v.get("capacity") else ""
            groups[g].append(
                f"{v['code']} — {v['color']} | Size: {v.get('size', 'N/A')}{finish_tag}{capacity_tag}"
            )
        group_text = ""
        for g, lines in groups.items():
            group_text += f"\n  [{g}]\n    " + "\n    ".join(lines) + "\n"

        return f"""**GIFT BOXES — Festival Edition ({len(cls.GIFT_BOXES)} variants)**

**Design Groups & Variants:**
{group_text}
**Shapes:** {', '.join(cls.GIFT_BOX_SHAPES)}
**Colors:** {', '.join(cls.GIFT_BOX_COLORS)}
**Finishes:** {', '.join(cls.GIFT_BOX_FINISHES)}
  • MGI Golden Work — metallic gold foil print on select models
  • Golden Leaf — embossed gold leaf finish on select models

**Key Features:**
  • {chr(10) + '  • '.join(cls.GIFT_BOX_FEATURES)}

*Pricing is dynamic — share your requirements for a quote.*"""

    @classmethod
    def get_tray_boxes_info(cls) -> str:
        with_handle = [(k, v) for k, v in cls.TRAY_BOXES.items() if v.get("handle")]
        without_handle = [(k, v) for k, v in cls.TRAY_BOXES.items() if not v.get("handle")]
        wh_lines = "\n    ".join(
            f"{v['product_name']} — {v['size']} — {v['color']}" for _, v in with_handle
        )
        woh_lines = "\n    ".join(
            f"{v['product_name']} — {v['size']} — {v['color']}" for _, v in without_handle
        )
        return f"""**TRAY BOXES**

**Tray Box WITH Handle (9 inch, 3 color options):**
    {wh_lines}

**Tray Box WITHOUT Handle (11 inch, 2 color options):**
    {woh_lines}

**Design:** Flat cardboard tray base with full-height clear PVC/acetate lid. Rope handle on the with-handle variant.
**Suitable For:** Sweets, Mithai, Dry fruits, Bakery items, Gifts

**Key Features:**
  • {chr(10) + '  • '.join(cls.TRAY_BOX_FEATURES)}

*Pricing is dynamic — share your requirements for a quote.*"""

    @classmethod
    def get_gift_box_by_group(cls, group_name: str) -> list:
        """Return all gift box variants belonging to a given group."""
        return [
            (key, val) for key, val in cls.GIFT_BOXES.items()
            if val.get("group", "").lower() == group_name.lower()
        ]

    @classmethod
    def get_all_products_summary(cls) -> str:
        groups = {}
        for v in cls.GIFT_BOXES.values():
            g = v.get("group", "Other")
            groups.setdefault(g, []).append(f"{v['code']} — {v['color']}")
        gift_lines = "\n".join(
            f"   [{g}]\n     " + "\n     ".join(codes)
            for g, codes in groups.items()
        )
        return f"""Welcome to {cls.COMPANY_NAME} — {cls.COMPANY_LOCATION}

WINDOW BOXES
  Top Window: {' | '.join(v['dimensions'] for v in cls.TOP_WINDOW_BOXES.values())}
  L Window  : {' | '.join(v['dimensions'] for v in cls.L_WINDOW_BOXES.values())}
  Colors    : {', '.join(cls.WINDOW_BOX_COLORS)}

MDF BOARDS (Cake Bases / Cake Boards)
  Sizes     : {', '.join(cls.MDF_BOARD_SIZES)}
  Colors    : {', '.join(cls.MDF_BOARD_COLORS)}
  Shapes    : {', '.join(cls.MDF_BOARD_SHAPES)}

DRUM BOARDS
  Sizes     : {' | '.join(v['dimensions'] for v in cls.DRUM_BOARDS.values())}
  Colors    : {', '.join(cls.DRUM_BOARD_COLORS)}

CUTLERY KITS
  Standard Kit: {', '.join(cls.CUTLERY_KITS['STANDARD_KIT']['contents'])}
  MOQ for branding: {cls.CUTLERY_KITS['STANDARD_KIT']['customization']['moq_for_branding']} kits

GIFT BOXES — FESTIVAL EDITION  ({len(cls.GIFT_BOXES)} variants across 17 design groups)
{gift_lines}

TRAY BOXES
  With Handle    (9 inch): Peach, Light Green, Light Blue
  Without Handle (11 inch): Pink, Purple

Pricing is dynamic — share requirements for a quote.
"""