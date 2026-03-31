"""Query box and product information from the catalog."""
import json
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field
from ..appliation.fetch_data_from_pdf import PDFDataExtractor


class Signature:
    """Query product catalog for boxes, boards, and other items."""
    
    class Input(BaseModel):
        query: str = Field(
            description="Question about products, boxes, sizes, customization, or pricing",
            examples=["what types of boxes are available?", "what sizes do MDF boards come in?", "customization options for window boxes"]
        )
    
    plain_utterances = [
        "what types of boxes do you have",
        "tell me about window boxes",
        "what sizes are available for L window boxes",
        "do you offer customization",
        "what are the MDF board sizes",
        "tell me about drum boards",
        "what colors are available",
        "what's included in the cutlery kit",
        "foil stamping options",
        "minimum order quantity for branding",
        "contact information",
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
        query_lower = query.lower()
        
        # Check for box type queries
        if "type" in query_lower and ("box" in query_lower or "boxes" in query_lower):
            boxes = []
            if "window_boxes" in products:
                wb = products["window_boxes"]
                for box_type, details in wb.get("types", {}).items():
                    boxes.append({
                        "type": box_type.replace("_", " ").title(),
                        "sizes": details.get("sizes", []),
                        "best_for": details.get("best_for", [])
                    })
            
            response = "We have the following types of boxes:\n"
            for box in boxes:
                response += f"\n• {box['type']}\n"
                response += f"  Sizes: {', '.join(box['sizes'])}\n"
                if box.get('best_for'):
                    response += f"  Best for: {', '.join(box['best_for'])}\n"
            return response
        
        # Check for size queries
        if "size" in query_lower:
            for product_key in ["window_boxes", "mdf_boards", "drum_boards"]:
                if any(word in query_lower for word in product_key.replace("_", " ").split()):
                    product = products.get(product_key, {})
                    sizes = []
                    if "types" in product:
                        for type_info in product["types"].values():
                            sizes.extend(type_info.get("sizes", []))
                    elif "standard_sizes" in product:
                        sizes = product["standard_sizes"]
                    elif "sizes" in product:
                        sizes = product["sizes"]
                    return f"Available sizes: {', '.join(sizes)}"
        
        # Check for customization queries
        if "custom" in query_lower or "brand" in query_lower:
            for product_key in ["window_boxes", "mdf_boards", "cutlery_kits"]:
                if any(word in query_lower for word in product_key.replace("_", " ").split()):
                    product = products.get(product_key, {})
                    options = product.get("customization", product.get("branding", {}))
                    return f"Customization options: {json.dumps(options, indent=2)}"
        
        # Check for contact queries
        if "contact" in query_lower or "phone" in query_lower:
            contact = company_info.get("contact", {})
            return f"Contact us at: {', '.join(contact.get('phone', []))}"
        
        # Check for drum board queries (BEFORE generic "board" check)
        if "drum" in query_lower:
            drum = products.get("drum_boards", {})
            return f"Drum Boards:\n{json.dumps(drum, indent=2)}"
        
        # Check for cutlery kit queries
        if "cutlery" in query_lower or "kit" in query_lower:
            kit = products.get("cutlery_kits", {})
            return f"Cutlery Kits:\n{json.dumps(kit, indent=2)}"
        
        # Check for MDF board queries
        if "mdf" in query_lower or "board" in query_lower:
            mdf = products.get("mdf_boards", {})
            return f"MDF Boards:\n{json.dumps(mdf, indent=2)}"
        
        # General product search
        for product_name, product_info in products.items():
            if any(word in query_lower for word in product_name.replace("_", " ").split()):
                return f"{product_name.replace('_', ' ').title()}:\n{json.dumps(product_info, indent=2)}"
        
        return "I couldn't find information about that. Please try asking about our window boxes, cutlery kits, MDF boards, or drum boards."
    
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
