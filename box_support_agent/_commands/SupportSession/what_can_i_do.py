"""Override what_can_i_do to return a user-friendly help message instead of internal command list"""

import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel


class Signature:
    """List what the assistant can help with"""

    class Input(BaseModel):
        pass

    plain_utterances = [
        "what can you do",
        "what commands do you have",
        "show me your commands",
        "what are your features",
        "help me understand what you can do",
        "what can I ask you",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input,
    ) -> fastworkflow.CommandOutput:
        response = """Here's what I can help you with:

📦 *Product Info* — Ask about window boxes, MDF boards, drum boards, or cutlery kits
📏 *Sizes* — "What sizes are available?"
🎨 *Colors* — "What colors do you have?"
✨ *Customization* — "Do you offer branding or foil stamping?"
🛒 *Add to Cart* — "Add 500 window boxes to my cart"
👁 *View Cart* — "Show me my cart"
🗑 *Remove Item* — "Remove item 2 from my cart"
❌ *Clear Cart* — "Clear my cart"
✅ *Checkout* — "I'm ready to checkout"
🔄 *Reset* — Say "reset" to start a fresh conversation

Just type naturally — I'll understand!"""

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
