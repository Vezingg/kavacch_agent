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

📦 *Product Info* — Ask about any of our products:
   • Window Boxes (Top Window & L Window, 8×8×5 to 12×12×8)
   • MDF Boards / Cake Bases (6" to 20", Square/Round/Round with Handle)
   • Drum Boards (10×10, 12×12, 14×14)
   • Cutlery Kits (knife + candles, custom branding available)
   • Gift Boxes — Festival Edition (33 variants across 17 design groups:
     Mughal Arch-Top, Floral Dome-Top, House Window, Landscape Bags,
     Hut/3-D shapes, Jar Boxes with MGI Golden Work, and more)
   • Tray Boxes (9" with handle in 3 colors / 11" without handle in 2 colors)

📏 *Sizes* — "What sizes are available for gift boxes?"
🎨 *Colors* — "What colors does SA 001 come in?"
✨ *Customization* — "Do you offer branding or foil stamping?"
🛒 *Add to Cart* — "Add 100 SA 014 hut gift boxes" / "Add 200 tray boxes with handle"
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
