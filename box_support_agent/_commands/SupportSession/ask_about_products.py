"""Ask about products in the catalog"""

import os
from typing import Optional
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ...application.support_session import SupportSession
from ...application.product_catalog import ProductCatalog


class Signature:
    """Ask about specific product categories or get detailed information"""

    class Input(BaseModel):
        product_category: Optional[str] = Field(
            description=(
                "The product category to learn about. "
                "Set to null/empty when this is a follow-up message and the user has NOT explicitly "
                "named a product — the system will resolve the category from conversation context."
            ),
            examples=['window boxes', 'MDF boards', 'drum boards', 'cutlery kits', 'all products', 'foil stamping', 'gift boxes', 'tray boxes'],
            default=None,
        )
        detail_aspect: Optional[str] = Field(
            description=(
                "The specific aspect the customer wants to explore. "
                "Use 'design_features' when they ask about design, style, shape, finish, or features. "
                "Use 'color_only' when they ask ONLY about colours or color options (e.g. 'what colors does it come in'). "
                "Use 'size_only' when they ask ONLY about sizes or dimensions (e.g. 'what sizes are available'). "
                "Use 'size_color' when they ask about both sizes AND colours together. "
                "Use 'pricing_moq' when they ask about pricing, cost, or minimum order quantity. "
                "Leave as None when the customer is asking about a product for the first time "
                "and has not specified any particular aspect."
            ),
            examples=['design_features', 'color_only', 'size_only', 'size_color', 'pricing_moq'],
            default=None,
        )

    plain_utterances = [
        "tell me about window boxes",
        "what are your MDF board options",
        "tell me about cake bases",
        "what cake boards do you have",
        "show me your base boards",
        "what cake base options are available",
        "I want to know about drum boards",
        "do you have cutlery kits",
        "what products do you offer",
        "show me all products",
        "what sizes of window boxes do you have",
        "what colors are available for MDF boards",
        "can you do custom branding",
        "tell me about foil stamping",
        "tell me about gift boxes",
        "what gift boxes do you have",
        "show me SA 001",
        "do you have hut shaped boxes",
        "what are your fancy decorative boxes",
        "tell me about tray boxes",
        "do you have tray boxes with handle",
        "what tray packaging is available",
        "show me jar boxes",
        "do you have 2 jar box or 3 jar box",
        "what MGI golden work boxes do you have",
        # aspect follow-up utterances
        "design and features",
        "show me the design",
        "what does it look like",
        "sizes and colors",
        "what sizes do they come in",
        "what colors are available",
        "pick a size and color",
        "what is the minimum order",
        # color-only
        "what color does it come in",
        "only show me the colors",
        "which colors are available",
        "what colour options do you have",
        # size-only
        "what sizes are available",
        "just tell me the sizes",
        "which sizes do you have",
        "show me only the sizes",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:

    # ── shared helper ─────────────────────────────────────────────────────────

    @staticmethod
    def _overview_menu(product_name: str, brief: str) -> str:
        return (
            f"**{product_name}**\n\n"
            f"{brief}\n\n"
            "**What do you want to do next?**\n"
            "- Know about design and features\n"
            "- Just show me the colours\n"
            "- Just show me the sizes\n"
            "- Sizes and colours together\n"
            "- Pricing and MOQ"
        )

    # ── gift boxes ────────────────────────────────────────────────────────────

    @staticmethod
    def _gift_boxes_response(aspect: str) -> str:
        if aspect == "design_features":
            features = ("\n  • ").join(ProductCatalog.GIFT_BOX_FEATURES)
            finishes = "\n  • ".join(ProductCatalog.GIFT_BOX_FINISHES)
            return (
                "**Gift Boxes — Design & Features**\n\n"
                f"**Structural Shapes:** {', '.join(ProductCatalog.GIFT_BOX_SHAPES)}\n\n"
                f"**Available Finishes:**\n  • {finishes}\n"
                "  • MGI Golden Work — metallic gold foil print on select models\n"
                "  • Golden Leaf — embossed gold leaf finish on select models\n\n"
                f"**Key Features:**\n  • {features}"
            )
        elif aspect == "color_only":
            return (
                "**Gift Boxes — Available Colours**\n\n"
                f"{', '.join(ProductCatalog.GIFT_BOX_COLORS)}"
            )
        elif aspect == "size_only":
            groups: dict = {}
            for v in ProductCatalog.GIFT_BOXES.values():
                g = v.get("group", "Other")
                groups.setdefault(g, [])
                groups[g].append(f"{v['code']} | Size: {v.get('size', 'N/A')}")
            group_text = ""
            for g, lines in groups.items():
                group_text += f"\n  [{g}]\n    " + "\n    ".join(lines) + "\n"
            return f"**Gift Boxes — Sizes by Variant**\n{group_text}"
        elif aspect == "size_color":
            groups: dict = {}
            for v in ProductCatalog.GIFT_BOXES.values():
                g = v.get("group", "Other")
                groups.setdefault(g, [])
                size = v.get("size", "N/A")
                groups[g].append(f"{v['code']} — {v['color']} | Size: {size}")
            group_text = ""
            for g, lines in groups.items():
                group_text += f"\n  [{g}]\n    " + "\n    ".join(lines) + "\n"
            return (
                "**Gift Boxes — Sizes & Colours**\n\n"
                f"**Available Colours:** {', '.join(ProductCatalog.GIFT_BOX_COLORS)}\n\n"
                f"**Variants by Design Group:**\n{group_text}"
            )
        elif aspect == "pricing_moq":
            return (
                "**Gift Boxes — Pricing & MOQ**\n\n"
                "Pricing is dynamic and depends on the variant, quantity, and finish selected.\n\n"
                "Please share your requirements (variant code, quantity, finish) and the "
                "Kavacch team will provide a custom quote."
            )
        else:
            return ResponseGenerator._overview_menu(
                "Gift Boxes — Festival Edition",
                f"33 decorative variants across 17 design groups — Mughal Arch-Top, "
                f"Floral Dome-Top, Hut/3-D shapes, Jar Boxes with MGI Golden Work, and more. "
                f"Available in {len(ProductCatalog.GIFT_BOX_COLORS)} colour options with "
                f"{len(ProductCatalog.GIFT_BOX_FINISHES)} finish types."
            )

    # ── window boxes ──────────────────────────────────────────────────────────

    @staticmethod
    def _window_boxes_response(aspect: str) -> str:
        if aspect == "design_features":
            return (
                "**Window Boxes — Design & Features**\n\n"
                "**Box Types:**\n"
                "  • **Top Window** — Square box with a top-facing transparent PVC window. "
                "Clean pastel finish, ideal for bakery items and gifts.\n"
                "  • **L Window** — Square box with an L-shaped front+side window for maximum "
                "product visibility. Ideal for tall cakes and premium hampers.\n\n"
                f"**Key Features:** {' | '.join(ProductCatalog.WINDOW_BOX_FEATURES)}\n\n"
                f"**Customisation:** Foil stamping available — {ProductCatalog.FOIL_STAMPING['note']}"
            )
        elif aspect == "color_only":
            return (
                "**Window Boxes — Available Colours**\n\n"
                f"{', '.join(ProductCatalog.WINDOW_BOX_COLORS)}"
            )
        elif aspect == "size_only":
            top_sizes = ", ".join(v["dimensions"] for v in ProductCatalog.TOP_WINDOW_BOXES.values())
            l_sizes = ", ".join(v["dimensions"] for v in ProductCatalog.L_WINDOW_BOXES.values())
            return (
                "**Window Boxes — Available Sizes**\n\n"
                f"**Top Window:** {top_sizes}\n"
                f"**L Window:** {l_sizes}"
            )
        elif aspect == "size_color":
            top_sizes = ", ".join(v["dimensions"] for v in ProductCatalog.TOP_WINDOW_BOXES.values())
            l_sizes = ", ".join(v["dimensions"] for v in ProductCatalog.L_WINDOW_BOXES.values())
            return (
                "**Window Boxes — Sizes & Colours**\n\n"
                f"**Top Window sizes:** {top_sizes}\n"
                f"**L Window sizes:** {l_sizes}\n\n"
                f"**Available Colours:** {', '.join(ProductCatalog.WINDOW_BOX_COLORS)}"
            )
        elif aspect == "pricing_moq":
            return (
                "**Window Boxes — Pricing & MOQ**\n\n"
                "Pricing is dynamic based on quantity and customisation.\n\n"
                f"**Foil Stamping MOQ:** {ProductCatalog.FOIL_STAMPING['moq']} boxes\n"
                f"Note: {ProductCatalog.FOIL_STAMPING['note']}\n\n"
                "Share your size, colour, and quantity for a quote."
            )
        else:
            sizes = ", ".join(v["dimensions"] for v in ProductCatalog.TOP_WINDOW_BOXES.values())
            return ResponseGenerator._overview_menu(
                "Window Boxes",
                f"Square gift/bakery boxes with a transparent PVC window. "
                f"Available in Top Window and L Window styles across 3 sizes ({sizes}). "
                f"Colours: {', '.join(ProductCatalog.WINDOW_BOX_COLORS)}."
            )

    # ── mdf boards ────────────────────────────────────────────────────────────

    @staticmethod
    def _mdf_boards_response(aspect: str) -> str:
        if aspect == "design_features":
            board_lines = "\n  • ".join(
                f"**{v['product_name']}** — {v['description']}"
                for v in ProductCatalog.MDF_BOARDS.values()
            )
            return (
                "**MDF Boards — Design & Features**\n\n"
                f"Also known as: {', '.join(ProductCatalog.MDF_BOARD_ALIASES)}\n\n"
                f"**Board Types:**\n  • {board_lines}\n\n"
                f"**Custom Branding:** {', '.join(ProductCatalog.MDF_BRANDING['options'])}\n"
                f"Note: {ProductCatalog.MDF_BRANDING['note']}"
            )
        elif aspect == "color_only":
            lines = "\n  • ".join(
                f"**{v['product_name']}:** {', '.join(v['colors'])}"
                for v in ProductCatalog.MDF_BOARDS.values()
            )
            return f"**MDF Boards — Available Colours**\n\n  • {lines}"
        elif aspect == "size_only":
            lines = "\n  • ".join(
                f"**{v['product_name']}:** {', '.join(v['sizes'])}"
                for v in ProductCatalog.MDF_BOARDS.values()
            )
            return f"**MDF Boards — Available Sizes**\n\n  • {lines}"
        elif aspect == "size_color":
            lines = "\n  • ".join(
                f"**{v['product_name']}** — Sizes: {', '.join(v['sizes'])} | Colours: {', '.join(v['colors'])}"
                for v in ProductCatalog.MDF_BOARDS.values()
            )
            return f"**MDF Boards — Sizes & Colours**\n\n  • {lines}"
        elif aspect == "pricing_moq":
            return (
                "**MDF Boards — Pricing & MOQ**\n\n"
                "Pricing is dynamic. Share your board type, size, and quantity for a quote.\n\n"
                f"**Custom Branding Note:** {ProductCatalog.MDF_BRANDING['note']}"
            )
        else:
            first_sizes = list(ProductCatalog.MDF_BOARDS.values())[0]["sizes"]
            board_names = ", ".join(v["product_name"] for v in ProductCatalog.MDF_BOARDS.values())
            return ResponseGenerator._overview_menu(
                "MDF Boards (Cake Bases / Cake Boards)",
                f"Flat rigid cake bases available as: {board_names}. "
                f"Sizes from {first_sizes[0]} to {first_sizes[-2]}. "
                "Custom branding (logo, name, insta handle) available."
            )

    # ── drum boards ───────────────────────────────────────────────────────────

    @staticmethod
    def _drum_boards_response(aspect: str) -> str:
        if aspect == "design_features":
            return (
                "**Drum Boards — Design & Features**\n\n"
                "Extra-thick, double-layered cake bases for premium presentation. "
                "Square format with a sturdy build — ideal for multi-tier cakes and display use."
            )
        elif aspect == "color_only":
            lines = "\n  • ".join(
                f"**{v['product_name']}:** {', '.join(v['colors'])}"
                for v in ProductCatalog.DRUM_BOARDS.values()
            )
            return f"**Drum Boards — Available Colours**\n\n  • {lines}"
        elif aspect == "size_only":
            sizes = ", ".join(v["product_name"] for v in ProductCatalog.DRUM_BOARDS.values())
            return f"**Drum Boards — Available Sizes**\n\n{sizes}"
        elif aspect == "size_color":
            lines = "\n  • ".join(
                f"**{v['product_name']}** — Colours: {', '.join(v['colors'])}"
                for v in ProductCatalog.DRUM_BOARDS.values()
            )
            return f"**Drum Boards — Sizes & Colours**\n\n  • {lines}"
        elif aspect == "pricing_moq":
            return (
                "**Drum Boards — Pricing & MOQ**\n\n"
                "Pricing is dynamic. Share your size and quantity requirements for a quote."
            )
        else:
            sizes = ", ".join(v["product_name"] for v in ProductCatalog.DRUM_BOARDS.values())
            return ResponseGenerator._overview_menu(
                "Drum Boards",
                f"Extra-thick double-layered cake bases. Available: {sizes}. "
                "Ideal for multi-tier cakes and premium display."
            )

    # ── cutlery kits ──────────────────────────────────────────────────────────

    @staticmethod
    def _cutlery_kits_response(aspect: str) -> str:
        kit = ProductCatalog.CUTLERY_KITS["STANDARD_KIT"]
        if aspect == "design_features":
            return (
                "**Cutlery Kits — Design & Features**\n\n"
                f"**Contents:** {', '.join(kit['contents'])}\n"
                f"**Ideal For:** {', '.join(kit['suitable_for'])}\n\n"
                f"{kit['description']}"
            )
        elif aspect == "color_only":
            return (
                "**Cutlery Kits — Colours**\n\n"
                "Cutlery Kits come in standard packaging — no specific colour variants available."
            )
        elif aspect == "size_only":
            return (
                "**Cutlery Kits — Size**\n\n"
                "Kits come in a standard size suitable for single-serve use."
            )
        elif aspect == "size_color":
            return (
                "**Cutlery Kits — Sizes & Packaging**\n\n"
                "Kits come in a standard size. "
                "Custom branding (logo printing) is available on the packaging."
            )
        elif aspect == "pricing_moq":
            return (
                "**Cutlery Kits — Pricing & MOQ**\n\n"
                f"**MOQ for Custom Branding:** {kit['customization']['moq_for_branding']} kits\n"
                f"**Branding Options:** {', '.join(kit['customization']['options'])}\n\n"
                "Share your quantity requirements for a quote."
            )
        else:
            return ResponseGenerator._overview_menu(
                "Cutlery Kits",
                f"Standard kits containing {', '.join(kit['contents'])}. "
                f"Suitable for {', '.join(kit['suitable_for'][:2])} and more. "
                "Custom branding available."
            )

    # ── tray boxes ────────────────────────────────────────────────────────────

    @staticmethod
    def _tray_boxes_response(aspect: str) -> str:
        if aspect == "design_features":
            return (
                "**Tray Boxes — Design & Features**\n\n"
                "**Structure:** Flat cardboard tray base with full-height clear PVC/acetate lid.\n"
                "  • **With Handle** — 9 inch, rope handle on lid\n"
                "  • **Without Handle** — 11 inch, clean lid\n\n"
                "**Suitable For:** Sweets, Mithai, Dry fruits, Bakery items, Gifts\n\n"
                f"**Key Features:**\n  • {(chr(10) + '  • ').join(ProductCatalog.TRAY_BOX_FEATURES)}"
            )
        elif aspect == "color_only":
            wh_colors = ", ".join(v["color"] for _, v in ProductCatalog.TRAY_BOXES.items() if v.get("handle"))
            woh_colors = ", ".join(v["color"] for _, v in ProductCatalog.TRAY_BOXES.items() if not v.get("handle"))
            return (
                "**Tray Boxes — Available Colours**\n\n"
                f"**With Handle (9 inch):** {wh_colors}\n"
                f"**Without Handle (11 inch):** {woh_colors}"
            )
        elif aspect == "size_only":
            return (
                "**Tray Boxes — Available Sizes**\n\n"
                "  • **With Handle:** 9 inch\n"
                "  • **Without Handle:** 11 inch"
            )
        elif aspect == "size_color":
            wh = [(k, v) for k, v in ProductCatalog.TRAY_BOXES.items() if v.get("handle")]
            woh = [(k, v) for k, v in ProductCatalog.TRAY_BOXES.items() if not v.get("handle")]
            wh_lines = "\n    ".join(f"{v['product_name']} — {v['color']}" for _, v in wh)
            woh_lines = "\n    ".join(f"{v['product_name']} — {v['color']}" for _, v in woh)
            return (
                "**Tray Boxes — Sizes & Colours**\n\n"
                f"**With Handle (9 inch):**\n    {wh_lines}\n\n"
                f"**Without Handle (11 inch):**\n    {woh_lines}"
            )
        elif aspect == "pricing_moq":
            return (
                "**Tray Boxes — Pricing & MOQ**\n\n"
                "Pricing is dynamic. Share your variant (with/without handle), "
                "colour, and quantity for a quote."
            )
        else:
            wh_count = sum(1 for v in ProductCatalog.TRAY_BOXES.values() if v.get("handle"))
            woh_count = sum(1 for v in ProductCatalog.TRAY_BOXES.values() if not v.get("handle"))
            return ResponseGenerator._overview_menu(
                "Tray Boxes",
                f"Clear PVC-lid tray boxes in two variants: "
                f"With Handle (9 inch, {wh_count} colours) and "
                f"Without Handle (11 inch, {woh_count} colours). "
                "Ideal for sweets, mithai, and gifts."
            )

    # ── main router ───────────────────────────────────────────────────────────

    def _get_full_response(self, workflow: fastworkflow.Workflow, input: Signature.Input) -> str:
        """Route to the correct product family and phase based on detail_aspect."""
        session: SupportSession = workflow.command_context_for_response_generation

        # Resolve product category: prefer explicit input, fall back to session context
        raw_category = (input.product_category or "").strip()
        if not raw_category and session.last_product_category:
            raw_category = session.last_product_category
        category = raw_category.lower()
        aspect = (input.detail_aspect or "").lower().strip()

        # Gift boxes — check before generic 'box' to avoid mis-routing
        if ('gift' in category or 'fancy' in category or 'decorative' in category
                or 'sa 0' in category or 'sa0' in category
                or 'hut' in category or 'tree' in category or 'flower shape' in category
                or 'jar box' in category or 'mgi' in category or 'golden leaf' in category):
            session.last_product_category = 'gift boxes'
            return self._gift_boxes_response(aspect)
        elif 'tray' in category:
            session.last_product_category = 'tray boxes'
            return self._tray_boxes_response(aspect)
        elif ('window' in category
              or ('box' in category and 'tray' not in category
                  and 'gift' not in category and 'jar' not in category)):
            session.last_product_category = 'window boxes'
            return self._window_boxes_response(aspect)
        elif ('mdf' in category or 'cake base' in category or 'cake board' in category
              or 'base board' in category
              or ('board' in category and 'drum' not in category)):
            session.last_product_category = 'MDF boards'
            return self._mdf_boards_response(aspect)
        elif 'drum' in category:
            session.last_product_category = 'drum boards'
            return self._drum_boards_response(aspect)
        elif 'cutlery' in category or 'kit' in category:
            session.last_product_category = 'cutlery kits'
            return self._cutlery_kits_response(aspect)
        elif 'all' in category or 'everything' in category or 'product' in category:
            return ProductCatalog.get_all_products_summary()
        elif 'foil' in category or 'stamp' in category or 'custom' in category or 'brand' in category:
            kit = ProductCatalog.CUTLERY_KITS['STANDARD_KIT']
            return f"""**CUSTOMIZATION OPTIONS**

**Foil Stamping on Window Boxes:**
{chr(10).join('   • ' + f for f in ProductCatalog.FOIL_STAMPING['features'])}
   • Minimum Order: {ProductCatalog.FOIL_STAMPING['moq']} boxes
   • Note: {ProductCatalog.FOIL_STAMPING['note']}

**Custom Branding on MDF Boards:**
{chr(10).join('   • ' + o for o in ProductCatalog.MDF_BRANDING['options'])}
   • Note: {ProductCatalog.MDF_BRANDING['note']}

**Custom Branding on Cutlery Kits:**
{chr(10).join('   • ' + o for o in kit['customization']['options'])}
   • Minimum Order: {kit['customization']['moq_for_branding']} kits"""
        else:
            return (
                "I can help with: Window Boxes, MDF Boards (Cake Bases), Drum Boards, "
                "Cutlery Kits, Gift Boxes (Festival Edition), Tray Boxes, and Customization options.\n\n"
                f"Which product would you like to know about, {session.customer_name}?"
            )

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input
    ) -> fastworkflow.CommandOutput:
        """The framework will call this function to process the command"""
        response = self._get_full_response(workflow, command_parameters)

        response += (
            "\n\nINSTRUCTIONS FOR AGENT: Present the information above exactly as formatted. "
            "If the response ends with a 'What do you want to do next?' menu, show that menu as-is "
            "and invite the customer to pick one of those options. Do NOT expand or add extra product details. "
            "If the response contains a specific section (design, sizes, pricing), present it clearly "
            "and end by asking if they would like to know about another aspect or add the product to their cart. "
            "Keep the tone warm and concise."
        )

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
