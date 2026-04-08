"""Query box and product information from the catalog."""
import json
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field
from ..appliation.fetch_data_from_pdf import PDFDataExtractor


class Signature:
    """
    Answer ANY question about Kalash Packaging products, sizes, colors, customization,
    pricing, or company information. ALWAYS invoke this command immediately — do NOT
    ask the user for clarification or more details. Pass the user's question as-is.
    This includes follow-up questions like "what about X?", "tell me more", "more details",
    "what else?", "and cutlery kits?", "what about drum boards?" etc.
    """

    class Input(BaseModel):
        query: str = Field(
            description="The user's question about products, boxes, sizes, colors, customization, pricing, or company info. Pass the full question exactly as asked.",
            examples=[
                "what types of boxes are available?",
                "what sizes do MDF boards come in?",
                "tell me more about cutlery kits",
                "what about drum boards?",
                "tell me more",
                "what colors are available for drum boards?",
                "customization options for window boxes",
            ]
        )
    
    plain_utterances = [
        "what types of boxes do you have",
        "tell me about window boxes",
        "tell me more about bakery boxes",
        "what sizes are available for L window boxes",
        "do you offer customization",
        "what are the MDF board sizes",
        "tell me about drum boards",
        "what about drum boards",
        "what about cutlery kits",
        "what about cake boards",
        "what about MDF boards",
        "tell me more",
        "tell me more about that",
        "more details please",
        "what else do you have",
        "what colors are available",
        "what colors do drum boards come in",
        "what sizes do drum boards come in",
        "what's included in the cutlery kit",
        "tell me about the cutlery kit",
        "foil stamping options",
        "minimum order quantity for branding",
        "contact information",
        "what are the available sizes",
        "what are your products",
        "product information",
        "give me details about",
        "I want to know about",
    ]
    
    @staticmethod
    def generate_utterances(
        workflow: fastworkflow.Workflow, 
        command_name: str
    ) -> list[str]:
        return [
            command_name.split("/")[-1].lower().replace("_", " ")
        ] + generate_diverse_utterances(
            Signature.plain_utterances, 
            command_name
        )


class ResponseGenerator:
    """Fetch and format product information from the catalog."""
    
    def _get_fresh_data(self) -> dict:
        """Fetch fresh data from PDF every time."""
        extractor = PDFDataExtractor()
        return extractor.get_data()
    
    def _answer_query(self, query: str, data: dict) -> str:
        """Answer a natural language query about products."""
        products = data.get("products", {})
        company_info = data.get("company_info", {})
        q = query.lower()

        # ── COMPANY INFO ──────────────────────────────────────────────────────

        if any(w in q for w in ["contact", "phone", "number", "call", "reach"]):
            phones = company_info.get("contact", {}).get("phone", [])
            return f"You can reach us at: {', '.join(phones)}"

        if any(w in q for w in ["location", "where", "based", "city"]):
            return f"{company_info.get('name', '')} is located in {company_info.get('location', '')}."

        if any(w in q for w in ["speciali", "what do you sell", "what do you offer"]):
            specs = company_info.get("specializations", [])
            return f"{company_info.get('name', '')} specializes in: {', '.join(specs)}."

        if any(w in q for w in ["focus", "commitment", "timely", "consistency"]):
            focus = company_info.get("focus", [])
            return f"Our key focus areas: {', '.join(focus)}."

        if any(w in q for w in ["who are you", "about you", "about kalash", "company"]):
            specs = company_info.get("specializations", [])
            focus = company_info.get("focus", [])
            return (
                f"{company_info.get('name', '')} — based in {company_info.get('location', '')}.\n"
                f"• Specializes in: {', '.join(specs)}\n"
                f"• Focus: {', '.join(focus)}"
            )

        # ── WINDOW BOXES ──────────────────────────────────────────────────────

        if "window" in q or "bakery" in q or ("box" in q and "drum" not in q and "mdf" not in q):
            wb = products.get("window_boxes", {})

            # full overview — "tell me more", "more about", "all about", "overview", "details"
            if any(w in q for w in ["more", "all", "overview", "detail", "full", "everything", "tell me about"]):
                description = wb.get("description", "")
                features = wb.get("features", [])
                types = wb.get("types", {})
                foil = wb.get("customization", {}).get("foil_stamping", {})
                lines = [
                    f"Window Boxes (Bakery Boxes): {description}",
                    "",
                    "Key features:",
                ]
                lines += [f"• {f}" for f in features]
                lines.append("")
                lines.append("Types & sizes:")
                tw = types.get("top_window", {})
                lines.append(f"• Top Window — Sizes: {', '.join(tw.get('sizes', []))}")
                lw = types.get("l_window", {})
                lines.append(f"• L Window — Sizes: {', '.join(lw.get('sizes', []))}")
                lines.append(f"  Best for: {', '.join(lw.get('best_for', []))}")
                lines.append("")
                lines.append("Customization (Foil Stamping):")
                for detail in foil.get("details", []):
                    lines.append(f"• {detail}")
                lines.append(f"• MOQ: {foil.get('moq', '')}")
                lines.append(f"• Note: {foil.get('note', '')}")
                return "\n".join(lines)

            # top window specific
            if "top" in q:
                tw = wb.get("types", {}).get("top_window", {})
                return (
                    f"Top Window Box:\n"
                    f"• {tw.get('description', '')}\n"
                    f"• Sizes: {', '.join(tw.get('sizes', []))}"
                )

            # l window specific
            if any(w in q for w in ["l window", "l-window"]):
                lw = wb.get("types", {}).get("l_window", {})
                return (
                    f"L Window Box:\n"
                    f"• Sizes: {', '.join(lw.get('sizes', []))}\n"
                    f"• Best for: {', '.join(lw.get('best_for', []))}"
                )

            # features / highlights
            if any(w in q for w in ["highlight", "feature", "key"]):
                features = wb.get("features", [])
                return "Key highlights of Window Boxes:\n" + "\n".join(f"• {f}" for f in features)

            # types
            if "type" in q:
                lines = ["Window Box types available:"]
                for box_type, details in wb.get("types", {}).items():
                    lines.append(f"\n• {box_type.replace('_', ' ').title()}")
                    lines.append(f"  Sizes: {', '.join(details.get('sizes', []))}")
                    if details.get("best_for"):
                        lines.append(f"  Best for: {', '.join(details['best_for'])}")
                return "\n".join(lines)

            # sizes
            if "size" in q:
                sizes = []
                for type_info in wb.get("types", {}).values():
                    sizes.extend(type_info.get("sizes", []))
                return f"Window Box sizes: {', '.join(sizes)}"

            # colors
            if any(w in q for w in ["color", "colour"]):
                return "Window Boxes are available in a Premium Pastel colour range."

            # customization / foil stamping / MOQ
            if any(w in q for w in ["custom", "brand", "foil", "stamp", "moq", "minimum order", "design charge"]):
                foil = wb.get("customization", {}).get("foil_stamping", {})
                lines = ["Window Box Foil Stamping / Customization:"]
                for detail in foil.get("details", []):
                    lines.append(f"• {detail}")
                if foil.get("moq"):
                    lines.append(f"• MOQ: {foil['moq']}")
                if foil.get("note"):
                    lines.append(f"• Note: {foil['note']}")
                return "\n".join(lines)

            # description / general overview (fallback within window boxes)
            description = wb.get("description", "")
            features = wb.get("features", [])
            lines = [f"Window Boxes: {description}", "Key features:"]
            lines += [f"• {f}" for f in features]
            return "\n".join(lines)

        # ── DRUM BOARDS ───────────────────────────────────────────────────────

        if "drum" in q:
            drum = products.get("drum_boards", {})

            if any(w in q for w in ["color", "colour"]):
                return f"Drum Board colors: {', '.join(drum.get('colors', []))}"

            if "size" in q:
                return f"Drum Board sizes: {', '.join(drum.get('sizes', []))}"

            if any(w in q for w in ["describe", "what is", "about", "overview"]):
                return drum.get("description", "")

            # general / fallback
            return (
                f"Drum Boards: {drum.get('description', '')}\n"
                f"• Sizes: {', '.join(drum.get('sizes', []))}\n"
                f"• Colors: {', '.join(drum.get('colors', []))}"
            )

        # ── CUTLERY KITS ──────────────────────────────────────────────────────

        if "cutlery" in q or "kit" in q:
            kit = products.get("cutlery_kits", {})
            contents = kit.get("standard_kit_contents", {})
            custom = kit.get("customization", {})

            if any(w in q for w in ["target", "who", "customer", "audience"]):
                return f"Target customers for Cutlery Kits: {', '.join(kit.get('target_customers', []))}"

            if any(w in q for w in ["benefit", "advantage", "why"]):
                return f"Benefits of Cutlery Kits: {', '.join(kit.get('benefits', []))}"

            if any(w in q for w in ["include", "content", "what's in", "contain", "inside"]):
                items = ", ".join(f"{v} {k}" for k, v in contents.items())
                return f"Standard Cutlery Kit includes: {items}"

            if any(w in q for w in ["ideal for", "best for", "suited for"]):
                return f"Cutlery Kits are ideal for: {', '.join(custom.get('ideal_for', []))}"

            if any(w in q for w in ["custom", "brand", "print", "moq", "minimum order"]):
                lines = ["Cutlery Kit Customization:"]
                for opt in custom.get("options", []):
                    lines.append(f"• {opt}")
                lines.append(f"• Ideal for: {', '.join(custom.get('ideal_for', []))}")
                lines.append(f"• MOQ for custom branding: {custom.get('moq_custom_branding', 'N/A')}")
                return "\n".join(lines)

            if any(w in q for w in ["describe", "what is", "about"]):
                return kit.get("description", "")

            # general / fallback
            items = ", ".join(f"{v} {k}" for k, v in contents.items())
            return (
                f"Cutlery Kits: {kit.get('description', '')}\n"
                f"• Standard kit includes: {items}\n"
                f"• Benefits: {', '.join(kit.get('benefits', []))}\n"
                f"• Target customers: {', '.join(kit.get('target_customers', []))}"
            )

        # ── MDF BOARDS ────────────────────────────────────────────────────────

        if "mdf" in q or "board" in q:
            mdf = products.get("mdf_boards", {})
            prem = mdf.get("premium_options", {})
            brand = mdf.get("branding", {})

            if "size" in q:
                return f"MDF Board sizes: {', '.join(mdf.get('standard_sizes', []))}"

            if any(w in q for w in ["color", "colour"]):
                return f"MDF Board colors: {', '.join(prem.get('colors', []))}"

            if "shape" in q:
                return f"MDF Board shapes: {', '.join(prem.get('shapes', []))}"

            if any(w in q for w in ["premium", "option", "finish"]):
                return (
                    f"MDF Board premium options:\n"
                    f"• Colors: {', '.join(prem.get('colors', []))}\n"
                    f"• Shapes: {', '.join(prem.get('shapes', []))}"
                )

            if any(w in q for w in ["brand", "custom", "logo", "moq", "minimum order", "design"]):
                lines = ["MDF Board Branding options:"]
                for opt in brand.get("options", []):
                    lines.append(f"• {opt}")
                if brand.get("note"):
                    lines.append(f"• Note: {brand['note']}")
                return "\n".join(lines)

            if any(w in q for w in ["describe", "what is", "about", "overview"]):
                return mdf.get("description", "")

            # general / fallback
            return (
                f"MDF Boards: {mdf.get('description', '')}\n"
                f"• Sizes: {', '.join(mdf.get('standard_sizes', []))}\n"
                f"• Colors: {', '.join(prem.get('colors', []))}\n"
                f"• Shapes: {', '.join(prem.get('shapes', []))}\n"
                f"• Branding: {', '.join(brand.get('options', []))}"
            )

        return "I couldn't find information about that. Please try asking about our window boxes, cutlery kits, MDF boards, drum boards, or company info."
    
    def process_command(
        self,
        workflow: fastworkflow.Workflow,
        input: Signature.Input
    ) -> str:
        # Fetch fresh data from PDF
        data = self._get_fresh_data()
        
        query = input.query.strip()
        if not query:
            return "Please ask a question about our products (window boxes, cutlery kits, MDF boards, or drum boards)."
        
        return self._answer_query(query, data)
    
    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input,
    ) -> fastworkflow.CommandOutput:
        response = self.process_command(workflow, command_parameters)
        
        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
