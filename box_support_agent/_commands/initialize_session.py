"""Initialize customer support session"""

import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ..application.support_session import SupportSession
from ..application.product_catalog import ProductCatalog


class Signature:
    """Initialize the customer support session"""

    class Input(BaseModel):
        customer_phone: str = Field(
            description="Phone number of the customer (injected by system from WhatsApp)",
            examples=['918469933233', '917600337948'],
            default=''
        )

    plain_utterances = [
        "start support session",
        "I need help with boxes",
        "hello, I want to order boxes",
        "hi there",
        "I'm looking for packaging solutions",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Create a SupportSession instance and attach it as the root command context"""

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input,
    ) -> fastworkflow.CommandOutput:
        # Initialize the root command context
        workflow.root_command_context = SupportSession(command_parameters.customer_phone)

        response = f"""**Welcome to Kavacch!** 👋

I'm your customer support assistant. I'm here to help you with all your packaging needs.

{ProductCatalog.get_all_products_summary()}

**How can I assist you today?**

You can ask me about:
• Specific product details (window boxes, MDF boards, drum boards, cutlery kits)
• Available sizes and colors
• Customization options
• Or add items to your cart when you're ready!"""

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
