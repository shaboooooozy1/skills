# TCOR inputs.json

## Shape

```json
{
  "client": "Client name",
  "exposure_base": {"name": "revenue", "per": 1000},
  "periods": [
    {
      "label": "2025-26 Guaranteed cost (current)",
      "kind": "actual",
      "exposure": 48000000,
      "premiums": {"WC": 146000, "GL": 51000, "AL": 251000, "Umbrella": 38000, "Taxes and fees": 4200},
      "retained_losses": {"Uninsured losses": 6000},
      "admin": {"Internal safety coordinator (25%)": 21000},
      "risk_control": {"Telematics": 14000},
      "collateral": {"amount": 0, "cost_rate": 0, "fees": 0},
      "source": "Policies and FY2025 GL detail",
      "notes": ""
    }
  ]
}
```

## Fields

| Field | Meaning |
|---|---|
| `exposure_base.name` | `revenue`, `payroll`, `headcount`, `vehicles`, or another base the client tracks |
| `exposure_base.per` | Divisor for the unit rate. 1000 gives "per $1,000 of revenue." Use 1 for per vehicle or per employee. |
| `periods[].label` | Shown in every table. Name the year and the structure. |
| `periods[].kind` | `actual` for booked figures, `scenario` for anything using a quote or a replay estimate |
| `periods[].exposure` | Exposure for that period. Omit if unknown; unit rate shows n/a. |
| `premiums`, `retained_losses`, `admin`, `risk_control` | An object of named line items, or a single number |
| `collateral.amount` | Collateral posted (LOC face, cash, trust) |
| `collateral.cost_rate` | Annual cost as a decimal: LOC fee or the client's cost of capital. 0.015 = 1.5%. |
| `collateral.fees` | Flat fees (LOC issuance, trust admin) |
| `source` | Where the numbers came from. Required in practice for the review. |

## Scenario example

A large-deductible alternative on auto, using a carrier indication and the replay:

```json
{
  "label": "2026-27 AL $100K deductible (scenario)",
  "kind": "scenario",
  "exposure": 50000000,
  "premiums": {"WC": 146000, "GL": 51000, "AL": "[carrier quote]", "Umbrella": 38000},
  "retained_losses": {"AL deductible losses (replay, mature-years avg)": "[from retention.json]"},
  "admin": {"Deductible claims handling": "[carrier quote]"},
  "collateral": {"amount": "[carrier requirement]", "cost_rate": "[client LOC rate]"},
  "source": "Carrier indication dated [date]; retention replay at $100K, AL, incurred basis"
}
```

Bracketed placeholders are not numbers. The script will stop on them. Replace each with a real figure, or drop the scenario until the quote arrives.
