# Agent Issues

## 1) Checkout Confirmation Is Bypassed for Window Box Variants

The agent correctly recognizes that there are two different window box types:
- L window box
- Top window box

However, during checkout, it sometimes auto-selects one variant without asking the user to confirm which one they want. This happens even though there is existing logic intended to require order confirmation before placing the order.

Expected behavior:
- At checkout, the agent should explicitly ask the user to choose between the two window box variants.
- The order should not proceed until this choice is confirmed.

## 2) Size Values Are Misinterpreted as Quantity

When users specify sizes like `8'` or `10'`, the agent sometimes treats these values as quantity instead of size.

Expected behavior:
- Values such as `8'` and `10'` should be parsed and stored as size attributes, not item counts.

## 3) Product Detail Retrieval Fails Across Multiple Products

If a user asks for details of one product, the agent can usually return them correctly. But when the user then asks for details of another product, the agent struggles and often cannot provide the full details available in `product_data.json`.

Expected behavior:
- The agent should reliably fetch complete details for each requested product, even across consecutive product-detail queries in the same conversation.

## 4) Product Size Is Sometimes Forgotten

In some flows, the agent loses or forgets the selected product size.

Expected behavior:
- Once size is provided and confirmed, the agent should retain it consistently through the rest of the conversation and checkout flow.
