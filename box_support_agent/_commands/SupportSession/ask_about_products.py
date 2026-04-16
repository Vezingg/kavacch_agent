"""Ask about products in the catalog"""

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
            examples=['window boxes', 'MDF boards', 'drum boards', 'cutlery kits', 'all products', 'foil stamping'],
        )

    plain_utterances = [
        "tell me about window boxes",
        "what are your MDF board options",
        "I want to know about drum boards",
        "do you have cutlery kits",
        "what products do you offer",
        "show me all products",
        "what sizes of window boxes do you have",
        "what colors are available for MDF boards",
        "can you do custom branding",
        "tell me about foil stamping",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Provide detailed product information based on the category"""

    def _process_command(self, workflow: fastworkflow.Workflow, input: Signature.Input) -> str:
        session: SupportSession = workflow.command_context_for_response_generation

        category = input.product_category.lower()

        # Determine which product info to return
        if 'window' in category or 'box' in category:
            return ProductCatalog.get_window_boxes_info()
        elif 'mdf' in category or 'board' in category and 'drum' not in category:
            return ProductCatalog.get_mdf_boards_info()
        elif 'drum' in category:
            return ProductCatalog.get_drum_boards_info()
        elif 'cutlery' in category or 'kit' in category:
            return ProductCatalog.get_cutlery_kits_info()
        elif 'all' in category or 'everything' in category or 'product' in category:
            return ProductCatalog.get_all_products_summary()
        elif 'foil' in category or 'stamp' in category or 'custom' in category or 'brand' in category:
            return f"""**CUSTOMIZATION OPTIONS**

**Foil Stamping on Window Boxes:**
{chr(10).join('   • ' + f for f in ProductCatalog.FOIL_STAMPING['features'])}
   • Minimum Order: {ProductCatalog.FOIL_STAMPING['moq']} boxes
   • Note: {ProductCatalog.FOIL_STAMPING['note']}

**Custom Branding on MDF Boards:**
{chr(10).join('   • ' + o for o in ProductCatalog.MDF_BRANDING['options'])}
   • Note: {ProductCatalog.MDF_BRANDING['note']}

**Custom Branding on Cutlery Kits:**
{chr(10).join('   • ' + o for o in ProductCatalog.CUTLERY_KIT_CONTENTS['customization']['options'])}
   • Minimum Order: {ProductCatalog.CUTLERY_KIT_CONTENTS['customization']['moq_for_branding']} kits"""
        else:
            return f"""I can provide information about:
• Window Boxes (Top Window and L Window ranges)
• MDF Boards
• Drum Boards
• Cutlery Kits
• Customization options (Foil Stamping, Branding)

Please specify which product you'd like to learn more about, {session.customer_name}!"""

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input
    ) -> fastworkflow.CommandOutput:
        """The framework will call this function to process the command"""
        response = self._process_command(workflow, command_parameters)

        additional_info = "\n\n**Need more details?** Feel free to ask about specific sizes, colors, customization options, or any other questions you might have!"

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response + additional_info)
            ]
        )
