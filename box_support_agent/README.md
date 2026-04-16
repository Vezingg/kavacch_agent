# Kalash Packaging Customer Support Agent

A fastWorkflow-powered AI customer support agent for Kalash Packaging, a box and packaging materials manufacturer based in Ahmedabad.

## About Kalash Packaging

Kalash Packaging specializes in:
- **Bakery Boxes** (Window boxes, Top window, L window)
- **MDF Boards** (Various sizes and colors)
- **Drum Boards**
- **Cutlery Kits**

They focus on quality, consistency, and timely delivery.

## Features

This AI agent helps customers:
- Learn about different product categories
- Get detailed specifications (sizes, colors, customization options)
- Add items to their shopping cart
- View their cart
- Checkout and receive an order summary
- Get connected with the sales team for pricing

## Installation

### Prerequisites

1. Python 3.11+
2. fastWorkflow installed:
```bash
pip install fastworkflow
# or
uv add fastworkflow
```

### Setup

1. **Configure API Keys**

Edit `fastworkflow.passwords.env` and add your API key:

```bash
nano fastworkflow.passwords.env
```

Get a free API key from:
- [Mistral AI](https://mistral.ai) - for mistral-small model
- [OpenRouter](https://openrouter.ai) - for free GPT models

Replace `your-mistral-api-key-here` with your actual API key.

2. **Train the Model**

```bash
fastworkflow train ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env
```

This will:
- Generate synthetic training data
- Train intent detection models
- Create the necessary model files

3. **Run the Agent**

```bash
fastworkflow run ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env --startup_action ./box_support_agent/startup_action.json
```

## Usage

Once the agent is running, you can interact with it naturally. Here are some example interactions:

### Getting Product Information

```
User > tell me about window boxes
User > what sizes of MDF boards do you have
User > do you offer customization
User > show me all products
```

### Adding Items to Cart

```
User > I want to order 500 window boxes 10x10x5
User > add 1000 MDF boards 12 inch black with custom branding
User > I need 200 cutlery kits
```

### Managing Your Order

```
User > show me my cart
User > view my order
User > I'm ready to checkout
```

### Checkout Process

When you checkout, the agent will:
1. Show you a complete order summary
2. Tell you that the team will contact you for pricing
3. Provide contact information for Kalash Packaging
4. Clear your cart for a new session

## Project Structure

```
box_support_agent/
├── application/
│   ├── product_catalog.py      # Product information from brochure
│   └── support_session.py       # Session management and cart
├── _commands/
│   ├── initialize_session.py    # Session initialization
│   ├── SupportSession/
│   │   ├── _SupportSession.py   # Context navigation
│   │   ├── ask_about_products.py # Product inquiry
│   │   ├── add_to_cart.py       # Add items to cart
│   │   ├── view_cart.py         # View cart contents
│   │   └── checkout.py          # Complete order
│   └── context_inheritance_model.json
├── fastworkflow.env             # Environment configuration
├── fastworkflow.passwords.env   # API keys (keep private!)
├── startup_action.json          # Auto-initialize on startup
└── README.md                    # This file
```

## How It Works

This application uses fastWorkflow's class-based approach:

1. **SupportSession Class**: Maintains customer name and shopping cart
2. **ProductCatalog Class**: Contains all product information from the brochure
3. **Commands**: Natural language commands that map to actions
   - `initialize_session` - Start a new customer session
   - `ask_about_products` - Get product information
   - `add_to_cart` - Add items to shopping cart
   - `view_cart` - See current cart
   - `checkout` - Complete order and get summary

## Key Concepts

### Dynamic Pricing
Prices are not included in the brochure and are dynamic. When customers checkout, they receive:
- Complete order summary
- Information that the team will contact them with pricing
- Contact phone numbers

### Product Categories

**Window Boxes:**
- Top Window: 8x8x5, 10x10x5, 12x12x5 inch
- L Window: 10x10x5, 8x8x8, 10x10x8, 12x12x8 inch
- Features: Strong material, clean finish, pastel colors, customization
- Foil Stamping: MOQ 1000 boxes

**MDF Boards:**
- Sizes: 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 14x19 inch
- Colors: White, Black, Golden, Pastel
- Shapes: Square (round corners), Round, Round with handle
- Custom branding available

**Drum Boards:**
- Sizes: 10x10, 12x12, 14x14
- Colors: Black, White, Golden

**Cutlery Kits:**
- Standard: 1 knife, 4 candles
- Ideal for cakes, parties, celebrations
- Custom branding: MOQ 10,000 kits

## Contact Information

Kalash Packaging
- Location: Ahmedabad
- Phone: 9106845371, 7600337948

## Development Notes

Built following fastWorkflow best practices:
- Class-based state management (Article 2)
- Context-aware command routing
- Structured inputs/outputs using Pydantic
- Clean separation of business logic and commands

## License

This is a customer support application for Kalash Packaging.
