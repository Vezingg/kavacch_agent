# ⚠️ IMPORTANT: How to Run the Agent Correctly

## Critical Issue Identified

If you run the agent WITHOUT the startup action, it will:
- ❌ Not automatically initialize the session
- ❌ Show generic system commands
- ❌ Potentially hallucinate wrong product information
- ❌ Not present itself as Kalash Packaging support

## ✅ CORRECT Way to Run

### Always use the startup_action flag:

```bash
fastworkflow run \
    ./box_support_agent \
    ./box_support_agent/fastworkflow.env \
    ./box_support_agent/fastworkflow.passwords.env \
    --startup_action ./box_support_agent/startup_action.json
```

### Or simply use the provided script:

```bash
./run.sh
```

The `run.sh` script automatically includes the `--startup_action` flag.

## ❌ WRONG Way to Run

**DON'T run like this:**

```bash
# This is WRONG - missing --startup_action flag
fastworkflow run ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env
```

## What the Startup Action Does

The `startup_action.json` file tells fastWorkflow to automatically:
1. Initialize a customer support session
2. Set up the Kalash Packaging context
3. Display the proper welcome message with product catalog
4. Make the agent context-aware from the start

Without it, the agent starts in a generic "global" context and doesn't know it's Kalash Packaging support.

## Recent Improvements

We've added the following new commands:

### 1. Remove from Cart
```
User > remove item 1 from cart
User > delete the second item
```

### 2. Clear Cart
```
User > clear my cart
User > empty my cart
```

### 3. Better Conversational Flow
- Agent is now less pushy about adding items to cart
- More helpful and informative responses
- Better guidance at each step

## Expected Correct Flow

### Correct Startup (with --startup_action)

```
User > [Agent starts automatically]

🤖 Welcome to Kalash Packaging, Customer! 👋

I'm your customer support assistant. I'm here to help you with all your packaging needs.

**Welcome to Kalash Packaging!**

We are a manufacturer based in Ahmedabad, specializing in:

**1. WINDOW BOXES**
   • Top Window Range: 8x8x5 inch, 10x10x5 inch, 12x12x5 inch
   • L Window Range: 10x10x5 inch, 8x8x8 inch, 10x10x8 inch, 12x12x8 inch
   ...
```

### Incorrect Startup (without --startup_action)

```
User > Hello what can i do here?

❌ Shows generic system commands
❌ No Kalash Packaging context
❌ Agent doesn't know what products to talk about
```

## Available Commands After Proper Startup

Once properly initialized, users can:

1. **Ask about products**
   - "tell me about window boxes"
   - "what MDF board sizes do you have"
   - "show me customization options"

2. **Add to cart**
   - "I want 500 window boxes 8x8x5"
   - "add 1000 MDF boards 12 inch black"

3. **Manage cart**
   - "show my cart"
   - "remove item 1"
   - "clear my cart"

4. **Checkout**
   - "I'm ready to checkout"
   - "proceed with order"

## Testing Checklist

Before considering the agent ready for production:

- [ ] Run with `--startup_action` flag
- [ ] Verify welcome message shows Kalash Packaging
- [ ] Verify product information is correct (not electronics/appliances)
- [ ] Test add to cart
- [ ] Test remove from cart
- [ ] Test clear cart
- [ ] Test checkout flow
- [ ] Verify order summary shows contact info

## Summary

**ALWAYS RUN:**
```bash
./run.sh
```

**OR:**
```bash
fastworkflow run ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env --startup_action ./box_support_agent/startup_action.json
```

**NEVER RUN:**
```bash
fastworkflow run ./box_support_agent ./box_support_agent/fastworkflow.env ./box_support_agent/fastworkflow.passwords.env
# ❌ Missing --startup_action
```

---

**Questions?** Check [README.md](README.md) or [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for more details.
