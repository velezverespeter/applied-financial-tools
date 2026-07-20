# Applied Financial Tools

A collection of independent personal finance and everyday automation tools, each in its own subfolder with a dedicated README, dataset, and source code. Built with open-source tools for applied learning and personal use.

## Tools

| Tool | Description | Status |
|---|---|---|
| [`retirement-withdrawal-simulator`](./retirement-withdrawal-simulator) | Monte Carlo safe withdrawal rate analysis (Trinity Study methodology) — simulates portfolio survival probability across withdrawal rates and allocations | Complete |
| `budget-dashboard` | Personal transaction categorization and monthly cash flow dashboard | Planned |
| `net-worth-tracker` | Automated net worth tracking and projection across accounts | Planned |

Each subfolder is self-contained: its own `README.md`, `requirements.txt`, and `src/` directory, so any tool can be run independently without needing the others installed.

## Repository Structure

```
applied-financial-tools/
├── README.md                              (this file)
├── LICENSE
├── .gitignore
└── retirement-withdrawal-simulator/
    ├── README.md
    ├── requirements.txt
    ├── src/
    └── outputs/
```

## License

MIT (see LICENSE) — applies repo-wide unless a subfolder specifies otherwise.

---

<sub>This repository contains independent personal finance planning and automation tools. It does not constitute investment advice, financial planning advice, or a recommendation regarding any specific financial decision.</sub>
