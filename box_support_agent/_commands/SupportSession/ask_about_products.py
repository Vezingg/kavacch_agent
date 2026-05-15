"""Ask about products in the catalog"""

import os
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ...application.support_session import SupportSession
from ...application.product_catalog import ProductCatalog


class Signature:
    """Ask about specific product categories or get detailed information"""

    class Input(BaseModel):
        product_category: str = Field(
            description="The product category to learn about",
            examples=['window boxes', 'MDF boards', 'drum boards', 'cutlery kits', 'all products', 'foil stamping', 'gift boxes', 'tray boxes'],
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
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:

    def _get_full_response(self, workflow: fastworkflow.Workflow, input: Signature.Input) -> str:
        """Route to the correct ProductCatalog method and return the full product data."""
        session: SupportSession = workflow.command_context_for_response_generation
        category = input.product_category.lower()

        # Gift boxes — check before generic 'box' to avoid mis-routing
        if ('gift' in category or 'fancy' in category or 'decorative' in category
                or 'sa 0' in category or 'sa0' in category
                or 'hut' in category or 'tree' in category or 'flower shape' in category
                or 'jar box' in category or 'mgi' in category or 'golden leaf' in category):
            return ProductCatalog.get_gift_boxes_info()
        elif 'tray' in category:
            return ProductCatalog.get_tray_boxes_info()
        elif ('window' in category
              or ('box' in category and 'tray' not in category
                  and 'gift' not in category and 'jar' not in category)):
            return ProductCatalog.get_window_boxes_info()
        elif ('mdf' in category or 'cake base' in category or 'cake board' in category
              or 'base board' in category
              or ('board' in category and 'drum' not in category)):
            return ProductCatalog.get_mdf_boards_info()
        elif 'drum' in category:
            return ProductCatalog.get_drum_boards_info()
        elif 'cutlery' in category or 'kit' in category:
            return ProductCatalog.get_cutlery_kits_info()
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

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
