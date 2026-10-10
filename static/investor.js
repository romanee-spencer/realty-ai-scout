const groups = {
  purchaseFields: [
    ["purchase_price", "Purchase price"],
    [
      "resale_value",
      "Resale value / ARV",
      "Use recent sold comparables; this tool does not verify this value.",
    ],
    ["buying_costs", "Buying & closing costs"],
    [
      "selling_cost_percent",
      "Selling costs (%)",
      "Fees and charges as a percentage of sale price.",
      99,
    ],
    ["target_profit", "Target profit before tax"],
  ],
  repairFields: [
    ["renovation_budget", "Repair budget"],
    [
      "contingency_percent",
      "Repair contingency (%)",
      "Added to the repair budget.",
      100,
    ],
    [
      "monthly_carrying_costs",
      "Monthly carrying costs",
      "Exclude loan interest; include taxes, insurance and utilities.",
    ],
    ["holding_months", "Months until sale", "Allows partial months.", 120],
  ],
  financeFields: [
    [
      "loan_amount",
      "Purchase loan amount",
      "Enter 0 for an all-cash purchase.",
    ],
    [
      "annual_interest_percent",
      "Annual interest (%)",
      "Interest-only, constant loan balance.",
      100,
    ],
    ["loan_fees", "Loan fees"],
    [
      "resale_decline_percent",
      "Downside resale decline (%)",
      "Your stress-test assumption.",
      100,
    ],
    [
      "renovation_overrun_percent",
      "Downside repair overrun (%)",
      "Applied before contingency.",
      100,
    ],
    [
      "delay_months",
      "Additional holding months",
      "Your stress-test delay.",
      120,
    ],
  ],
};
groups.rentalFields = [
  ["monthly_rent", "Monthly gross rent", "Use supported rent comparables."],
  [
    "vacancy_percent",
    "Base vacancy (%)",
    "Annual uncollected rent allowance.",
    99,
  ],
  ["monthly_property_taxes", "Monthly property taxes"],
  ["monthly_insurance", "Monthly insurance"],
  ["monthly_maintenance", "Monthly maintenance reserve"],
  ["monthly_hoa_utilities", "Monthly HOA & owner utilities"],
  [
    "management_percent",
    "Management fee (%)",
    "Percentage of collected rent.",
    100,
  ],
  [
    "monthly_capex_reserve",
    "Monthly capital reserve",
    "For future major replacements.",
  ],
  ["rental_loan_amount", "Rental loan amount", "Enter 0 for an all-cash hold."],
  [
    "rental_interest_percent",
    "Rental annual interest (%)",
    "Fixed rate over the loan term.",
    100,
  ],
  [
    "rental_loan_years",
    "Rental loan term (years)",
    "Whole years for an amortizing loan.",
    50,
  ],
  ["rental_loan_fees", "Rental loan fees"],
  [
    "rental_setup_carrying_costs",
    "Costs before rental stabilizes",
    "Include financing, carrying costs and lease-up costs.",
  ],
  [
    "rent_decline_percent",
    "Downside rent decline (%)",
    "Your stress-test assumption.",
    100,
  ],
  [
    "extra_vacancy_points",
    "Additional vacancy points",
    "Added to base vacancy in the downside case.",
    99,
  ],
];
for (const [id, fields] of Object.entries(groups)) {
  for (const [key, title, hint, max] of fields) {
    const label = document.createElement("label");
    label.textContent = title;
    const input = document.createElement("input");
    Object.assign(input, {
      id: key,
      name: key,
      type: "number",
      min: "0",
      step: "any",
      required: true,
    });
    if (max !== undefined) input.max = String(max);
    if (["purchase_price", "resale_value"].includes(key)) input.min = "0.01";
    label.append(input);
    if (hint) {
      const small = document.createElement("small");
      small.textContent = hint;
      label.append(small);
    }
    document.getElementById(id).append(label);
  }
}
let lastResult = null;
let isExample = false;
const sample = {
  purchase_price: 200000,
  resale_value: 300000,
  buying_costs: 5000,
  selling_cost_percent: 6,
  target_profit: 30000,
  renovation_budget: 30000,
  contingency_percent: 10,
  monthly_carrying_costs: 1000,
  holding_months: 6,
  loan_amount: 160000,
  annual_interest_percent: 7.5,
  loan_fees: 2000,
  resale_decline_percent: 10,
  renovation_overrun_percent: 20,
  delay_months: 3,
  monthly_rent: 2400,
  vacancy_percent: 5,
  monthly_property_taxes: 400,
  monthly_insurance: 150,
  monthly_maintenance: 150,
  monthly_hoa_utilities: 50,
  management_percent: 8,
  monthly_capex_reserve: 150,
  rental_loan_amount: 160000,
  rental_interest_percent: 6.5,
  rental_loan_years: 30,
  rental_loan_fees: 2000,
  rental_setup_carrying_costs: 3000,
  rent_decline_percent: 10,
  extra_vacancy_points: 5,
};
document.getElementById("sample").addEventListener("click", () => {
  for (const [k, v] of Object.entries(sample))
    document.getElementById(k).value = v;
  document.querySelector("[name=deal_name]").value = "Illustrative example";
  document.querySelector("[name=resale_evidence]").value =
    "Example only — no verified comparable sales";
  document.querySelector("[name=rent_evidence]").value =
    "Example only — no verified rent comparables";
  isExample = true;
  document.getElementById("results").hidden = true;
  document.getElementById("error").textContent =
    "Example loaded. These are illustrative assumptions, not market data.";
});
document.getElementById("dealForm").addEventListener("input", () => {
  document.getElementById("results").hidden = true;
  lastResult = null;
  document.getElementById("error").textContent = "";
});
const format = (n) =>
  n === null
    ? "—"
    : Number(n).toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      });
document
  .getElementById("dealForm")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const error = document.getElementById("error");
    error.textContent = "";
    document.getElementById("results").hidden = true;
    lastResult = null;
    const inputs = Object.fromEntries(new FormData(event.target));
    const button = event.target.querySelector("[type=submit]");
    button.disabled = true;
    try {
      const response = await fetch("/strategy-comparison", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(inputs),
      });
      const data = await response.json();
      if (!response.ok) throw Error(data.error || "Calculation failed");
      lastResult = data;
      document.getElementById("resultTitle").textContent =
        inputs.deal_name || "Strategy comparison";
      const summary = document.getElementById("summaryCards");
      summary.replaceChildren();
      for (const [title, value, caption] of [
        [
          "Flip profit before tax",
          data.flip.scenarios[0].profit_before_tax,
          "One-time base case",
        ],
        [
          "Rental annual cash flow",
          data.rental.scenarios[0].annual_cash_flow_before_tax,
          "One stabilized year, before tax",
        ],
        [
          "Rental cash to stabilize",
          data.rental.scenarios[0].cash_to_stabilize,
          "Purchase, repairs and setup",
        ],
      ]) {
        const card = document.createElement("div");
        card.style.cssText =
          "padding:18px;background:#f0f5ef;border-radius:10px";
        const small = document.createElement("small");
        small.textContent = title;
        const strong = document.createElement("h2");
        strong.textContent = format(value);
        const sub = document.createElement("small");
        sub.textContent = caption;
        card.append(small, strong, sub);
        summary.append(card);
      }
      const head = document.getElementById("tableHead");
      head.replaceChildren();
      const hr = document.createElement("tr");
      for (const title of [
        "Metric",
        ...data.flip.scenarios.map((s) => s.name),
      ]) {
        const th = document.createElement("th");
        th.textContent = title;
        th.scope = "col";
        hr.append(th);
      }
      head.append(hr);
      const body = document.getElementById("tableBody");
      body.replaceChildren();
      const rows = [
        ["resale_value", "Resale value"],
        ["renovation_budget", "Repair budget"],
        ["contingency", "Contingency"],
        ["holding_months", "Holding months"],
        ["carrying_costs", "Carrying costs"],
        ["interest_cost", "Loan interest"],
        ["selling_costs", "Selling costs"],
        ["total_project_cost", "Total project cost"],
        ["cash_required_before_sale", "Cash needed before sale"],
        ["profit_before_tax", "Profit before tax"],
        ["cash_return_percent", "Return on cash (%)"],
        ["break_even_resale", "Break-even resale"],
        [
          "purchase_ceiling_for_target_profit",
          "Purchase ceiling for target profit",
        ],
        ["meets_target_profit", "Meets profit target"],
      ];
      for (const [key, title] of rows) {
        const tr = document.createElement("tr");
        const label = document.createElement("th");
        label.scope = "row";
        label.textContent = title;
        tr.append(label);
        for (const s of data.flip.scenarios) {
          const td = document.createElement("td");
          td.textContent =
            key === "meets_target_profit"
              ? s[key]
                ? "Yes"
                : "No"
              : format(s[key]);
          if (key === "profit_before_tax")
            td.className = s[key] < 0 ? "bad" : "good";
          tr.append(td);
        }
        body.append(tr);
      }
      const rentalHead = document.getElementById("rentalHead");
      rentalHead.replaceChildren();
      const rentalHr = document.createElement("tr");
      for (const title of [
        "Metric",
        ...data.rental.scenarios.map((s) => s.name),
      ]) {
        const th = document.createElement("th");
        th.textContent = title;
        th.scope = "col";
        rentalHr.append(th);
      }
      rentalHead.append(rentalHr);
      const rentalBody = document.getElementById("rentalBody");
      rentalBody.replaceChildren();
      for (const [key, title] of [
        ["monthly_rent", "Gross monthly rent"],
        ["vacancy_percent", "Vacancy (%)"],
        ["annual_effective_rent", "Collected annual rent"],
        ["annual_operating_expenses", "Annual operating expenses"],
        ["annual_noi", "Annual net operating income"],
        ["monthly_debt_payment", "Monthly debt payment"],
        ["annual_capex_reserve", "Annual capital reserve"],
        ["monthly_cash_flow_before_tax", "Monthly cash flow before tax"],
        ["annual_cash_flow_before_tax", "Annual cash flow before tax"],
        ["cash_to_stabilize", "Cash to stabilize"],
        ["cash_on_cash_percent", "Annual return on cash (%)"],
        ["yield_on_cost_percent", "NOI yield on cost (%)"],
        ["dscr", "Debt service coverage ratio"],
        ["break_even_monthly_rent", "Break-even monthly gross rent"],
      ]) {
        const tr = document.createElement("tr");
        const th = document.createElement("th");
        th.scope = "row";
        th.textContent = title;
        tr.append(th);
        for (const scenario of data.rental.scenarios) {
          const td = document.createElement("td");
          td.textContent = format(scenario[key]);
          if (key === "monthly_cash_flow_before_tax")
            td.className = scenario[key] < 0 ? "bad" : "good";
          tr.append(td);
        }
        rentalBody.append(tr);
      }
      const notes = document.getElementById("notes");
      notes.replaceChildren();
      for (const note of [
        ...data.flip.model_notes,
        ...data.rental.model_notes,
      ]) {
        const li = document.createElement("li");
        li.textContent = note;
        notes.append(li);
      }
      document.getElementById("exampleNote").textContent = isExample
        ? "Contains illustrative example assumptions. Review every input before assessing a property."
        : "Results reflect your inputs. Keep sold comparable evidence and quotes with your deal.";
      document.getElementById("results").hidden = false;
    } catch (e) {
      error.textContent = e.message;
    } finally {
      button.disabled = false;
    }
  });
document.getElementById("export").addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob(
    [
      JSON.stringify(
        {
          ...lastResult,
          example_assumptions_loaded: isExample,
          exported_at: new Date().toISOString(),
        },
        null,
        2,
      ),
    ],
    { type: "application/json" },
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "investor-deal.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
