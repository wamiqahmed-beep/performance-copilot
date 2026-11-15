# Performance & variance copilot — assignment note

**Purpose.** Explain illustrative monthly revenue and gross margin versus budget and the same month last year. The analysis is descriptive and contains no forecasting, machine learning or optimisation.

**Pages.** Overview presents six KPIs, the 12-month trend and markets ranked by revenue variance. Variance drivers explains the revenue gap with a budget-to-actual waterfall. Countries compares markets and provides a searchable, sortable table. Country detail drills into a selected market, its brands and channels. Definitions & data documents calculations and downloads the underlying CSV. Global filters apply to the selected month, country, brand and channel.

**Data.** Synthetic monthly P&L observations cover 2023–2025, six countries, three brands and three channels. They are generated deterministically for teaching and do not represent Arçelik results. Columns: `date`, `country`, `currency`, `brand`, `channel`, `budget_units`, `actual_units`, `budget_revenue_local`, `actual_revenue_local`, `budget_cogs_local`, `actual_cogs_local`, `budget_fx`, `actual_fx`. FX rates are illustrative euros per local currency unit. Download the dataset using the button on the Definitions & data page.

**Measures.** Revenue in EUR = local revenue × corresponding FX rate. Gross profit = revenue − cost of goods sold; gross margin rate = gross profit / revenue. Revenue variance = (actual − comparison) / comparison. Last year means the same month in the preceding year. Margin-rate differences are in percentage points. Missing comparisons or zero denominators are unavailable.

**Bridge.** For each country and month, volume = change in total units × budget weighted-average EUR price; mix = actual total units × change in each segment's unit share × its budget EUR price; price = actual segment units × change in local unit price × budget FX; FX = actual segment units × actual local unit price × change in FX. Summing across segments yields the budget-to-actual revenue difference. This ordered decomposition describes arithmetic contributions, not causal effects.

**Flag.** A country is flagged when its revenue is more than 5% above or below budget. Exactly ±5% is within range. Green denotes above budget; red denotes below budget.

**Five-minute demo.** Introduce the overview and change a filter; explain the bridge; rank and search the countries; open a country; finish with the flag and methodology.
