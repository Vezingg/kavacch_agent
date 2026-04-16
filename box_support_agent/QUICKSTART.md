# Quick Start Guide

## Step 1: Install fastWorkflow

```bash
pip install fastworkflow
```

## Step 2: Add Your API Key

Edit the file `fastworkflow.passwords.env` and replace `your-mistral-api-key-here` with your actual API key.

Get a free API key from:
- **Mistral AI**: https://mistral.ai
- **OpenRouter**: https://openrouter.ai

```bash
nano fastworkflow.passwords.env
```

## Step 3: Train the Agent

```bash
fastworkflow train ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env
```

This will take a few minutes to generate training data and train the models.

## Step 4: Run the Agent

```bash
fastworkflow run ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env --startup_action ./box_support_agent/startup_action.json
```

## Step 5: Try It Out!

Once running, try these commands:

```
User > tell me about window boxes
User > what MDF board sizes do you have
User > I want to order 500 window boxes 8x8x5 inch
User > add 1000 MDF boards 12 inch black with foil stamping
User > show my cart
User > checkout
```

## Example Session

```
Welcome to Kalash Packaging, Customer! 👋

I'm your customer support assistant...

User > tell me about window boxes

**WINDOW BOXES**
[Details about top window and L window boxes...]

User > I want 500 top window boxes 10x10x5 with foil stamping

✅ Added 500 x Window Box (10x10x5 Top Window) to your cart!
   📝 Notes: with foil stamping
...

User > checkout

**ORDER SUMMARY FOR CUSTOMER**
==================================================

1. Window Box: 10x10x5 Top Window x 500 (Notes: with foil stamping)

==================================================
**Total Items:** 1
**Total Quantity:** 500

**NEXT STEPS:**
Thank you for your interest in Kalash Packaging! 🎉

Our team will contact you shortly with:
   • Detailed pricing for your order
   • Available customization options
   • Delivery timeline
   • Any additional information you may need

**Contact Information:**
   📞 9106845371
   📞 7600337948

We look forward to serving you!
- Kalash Packaging Team
```

## Troubleshooting

### "No module named 'fastworkflow'"
Install fastworkflow: `pip install fastworkflow`

### Training fails
Make sure you've added a valid API key in `fastworkflow.passwords.env`

### Commands not recognized
The agent learns from training data. Make sure training completed successfully.

## Need Help?

Check the [README.md](README.md) for detailed documentation.
