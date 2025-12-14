---
title: "Token Budget Management"
description: "How Fabra handles prompt budgets: priorities, required items, dropped-item receipts, and diffing budget-driven drift."
keywords: token budget, prompt budget, dropped items, context tetris, priorities
---

# Token Budget Management

Token budgets are an incident source: “why did it miss that doc?” is often “it got dropped.”

Fabra treats budgeting as part of production state and records it.

## Priorities + required items

Build contexts from `ContextItem`s with:
- `priority` (what drops first)
- `required=True/False` (required items must remain)

## Dropped-item receipts

When budgets force drops, Fabra records:
- which items were dropped
- why they were dropped

That’s why `context_id` is a receipt, not a log line.

## Debugging budget drift

Use diffs to see when the budget changed what made it into the final context:

```bash
fabra context diff <id1> <id2>
```

## Next reading

- [Context Assembly](context-assembly.md)
- Blog: Token Budget Management (`/blog/token-budget-management/`)
