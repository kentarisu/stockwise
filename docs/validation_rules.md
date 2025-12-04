# Product Validation Rules

- Unique identity: name + variant + quantity_unit must be unique for inventory items.
- Case-insensitive match for duplicates and quantity_unit values.
- Quantity input:
  - Box: numeric, non-negative, supports decimals.
  - kg: no numeric value required; stored as "kg".
- Pricing: price must be at least cost × 1.10; cost and price non-negative.
- Stock: non-negative; FIFO used for deductions.
- Server-side checks run on add and edit; client-side checks guide input.
- Logging: duplicate entry attempts are recorded in the audit log with details.