"""Deterministic flip scenarios. All money uses the user's single currency."""
from decimal import Decimal, InvalidOperation


def calculate_flip(inputs):
    if not isinstance(inputs, dict):
        raise ValueError('A JSON object is required')

    def number(key, maximum=Decimal("1000000000000")):
        value = inputs.get(key)
        if value is None or value == '' or isinstance(value, bool):
            raise ValueError(f'{key} is required and must be a nonnegative number')
        try:
            parsed = Decimal(str(value))
        except InvalidOperation:
            raise ValueError(f'{key} must be a number') from None
        if not parsed.is_finite() or parsed < 0 or (maximum is not None and parsed > maximum):
            raise ValueError(f'{key} is outside its allowed range')
        return parsed

    purchase = number('purchase_price')
    resale = number('resale_value')
    renovation = number('renovation_budget')
    contingency_pct = number('contingency_percent', 100)
    closing = number('buying_costs')
    monthly = number('monthly_carrying_costs')
    months = number('holding_months', 120)
    selling_pct = number('selling_cost_percent', 99)
    loan = number('loan_amount')
    interest_pct = number('annual_interest_percent', 100)
    loan_fees = number('loan_fees')
    target = number('target_profit')
    downside_pct = number('resale_decline_percent', 100)
    overrun_pct = number('renovation_overrun_percent', 100)
    delay = number('delay_months', 120)
    if purchase <= 0 or resale <= 0:
        raise ValueError('Purchase price and resale value must be greater than zero')
    if loan > purchase:
        raise ValueError('Loan amount cannot exceed purchase price in this model')

    def money(value):
        return float(value.quantize(Decimal('0.01')))

    def scenario(name, sale, repair, duration):
        contingency = repair * contingency_pct / 100
        holding = monthly * duration
        interest = loan * interest_pct / 100 * duration / 12
        selling = sale * selling_pct / 100
        before_sale = purchase + repair + contingency + closing + holding + interest + loan_fees
        total = before_sale + selling
        cash = before_sale - loan
        profit = sale - total
        return {
            'name': name,
            'resale_value': money(sale),
            'renovation_budget': money(repair),
            'contingency': money(contingency),
            'holding_months': float(duration),
            'carrying_costs': money(holding),
            'interest_cost': money(interest),
            'selling_costs': money(selling),
            'total_project_cost': money(total),
            'cash_required_before_sale': money(cash),
            'profit_before_tax': money(profit),
            'cash_return_percent': money(profit / cash * 100) if cash > 0 else None,
            'break_even_resale': money(before_sale / (1 - selling_pct / 100)),
            'purchase_ceiling_for_target_profit': money(sale - selling - (before_sale - purchase) - target),
            'meets_target_profit': profit >= target,
        }

    return {
        'assumptions': {key: inputs[key] for key in (
            'purchase_price', 'resale_value', 'renovation_budget', 'contingency_percent',
            'buying_costs', 'monthly_carrying_costs', 'holding_months', 'selling_cost_percent',
            'loan_amount', 'annual_interest_percent', 'loan_fees', 'target_profit',
            'resale_decline_percent', 'renovation_overrun_percent', 'delay_months')},
        'scenarios': [
            scenario('Base case', resale, renovation, months),
            scenario('Lower resale', resale * (1 - downside_pct / 100), renovation, months),
            scenario('Repairs and delay', resale, renovation * (1 + overrun_pct / 100), months + delay),
            scenario('Combined downside', resale * (1 - downside_pct / 100),
                     renovation * (1 + overrun_pct / 100), months + delay),
        ],
        'model_notes': [
            'Resale value is a user assumption, not an appraisal or verified comparable estimate.',
            'Interest-only loan at a constant balance; repairs and costs paid in cash; no refinance.',
            'Carrying costs exclude interest, calculated separately. Buying and selling costs must include applicable local charges.',
            'Profit is before income taxes. Cash required assumes costs funded before sale and selling costs paid at closing.',
            'Purchase ceiling holds all other inputs, including loan amount and fees, fixed. Recalculate financing for a revised offer.',
        ],
    }


def calculate_rental(inputs):
    """Annual stabilized rental cash flow; fixed-rate fully amortizing debt."""
    import math

    def number(key, maximum=1e12):
        value = inputs.get(key)
        if value is None or value == '' or isinstance(value, bool):
            raise ValueError(f'{key} is required and must be a nonnegative number')
        try:
            result = float(value)
        except (ValueError, TypeError):
            raise ValueError(f'{key} must be a number') from None
        if not math.isfinite(result) or not 0 <= result <= maximum:
            raise ValueError(f'{key} is outside its allowed range')
        return result

    purchase = number('purchase_price')
    repair = number('renovation_budget') * (1 + number('contingency_percent', 100) / 100)
    basis = purchase + repair + number('buying_costs') + number('rental_loan_fees')
    loan = number('rental_loan_amount')
    rate = number('rental_interest_percent', 100) / 100 / 12
    term = number('rental_loan_years', 50)
    rent = number('monthly_rent')
    vacancy = number('vacancy_percent', 100) / 100
    management = number('management_percent', 100) / 100
    capex = number('monthly_capex_reserve') * 12
    fixed = sum(number(key) for key in (
        'monthly_property_taxes', 'monthly_insurance', 'monthly_maintenance',
        'monthly_hoa_utilities')) * 12
    setup_carry = number('rental_setup_carrying_costs')
    decline = number('rent_decline_percent', 100) / 100
    extra_vacancy = number('extra_vacancy_points', 100) / 100
    if purchase <= 0 or rent <= 0:
        raise ValueError('Purchase price and monthly rent must be greater than zero')
    if loan > purchase:
        raise ValueError('Rental loan cannot exceed purchase price in this model')
    if loan and term < 1:
        raise ValueError('Rental loan term must be at least one year')
    if term != int(term):
        raise ValueError('Rental loan term must be a whole number of years')
    if vacancy + extra_vacancy >= 1:
        raise ValueError('Base and additional vacancy must total less than 100%')
    periods = term * 12
    # Stable for very small positive rates as well as zero-interest loans.
    payment = (loan * rate / (-math.expm1(-periods * math.log1p(rate)))
               if loan and rate else loan / periods if loan else 0)
    cash_invested = basis + setup_carry - loan

    def money(value):
        return round(value, 2)

    def scenario(name, gross_rent, vacancy_rate):
        effective = gross_rent * 12 * (1 - vacancy_rate)
        expenses = fixed + effective * management
        noi = effective - expenses
        annual_debt = payment * 12
        cash_flow = noi - annual_debt - capex
        return {
            'name': name,
            'monthly_rent': money(gross_rent),
            'vacancy_percent': money(vacancy_rate * 100),
            'annual_effective_rent': money(effective),
            'annual_operating_expenses': money(expenses),
            'annual_noi': money(noi),
            'monthly_debt_payment': money(payment),
            'annual_capex_reserve': money(capex),
            'annual_cash_flow_before_tax': money(cash_flow),
            'monthly_cash_flow_before_tax': money(cash_flow / 12),
            'cash_to_stabilize': money(cash_invested),
            'cash_on_cash_percent': money(cash_flow / cash_invested * 100) if cash_invested > 0 else None,
            'yield_on_cost_percent': money(noi / basis * 100),
            'dscr': money(noi / annual_debt) if annual_debt > 0 else None,
            'break_even_monthly_rent': money((fixed + annual_debt + capex) /
                (12 * (1 - vacancy_rate) * (1 - management))) if management < 1 else None,
        }

    return {
        'scenarios': [scenario('Stabilized base', rent, vacancy),
                      scenario('Rental downside', rent * (1 - decline), vacancy + extra_vacancy)],
        'model_notes': [
            'Rental results cover one stabilized year, with no appreciation, sale, refinance, income taxes, or rent growth.',
            'Taxes, insurance, maintenance, and owner-paid HOA/utilities are explicit monthly inputs. Management applies to collected rent.',
            'NOI excludes debt payments and capital reserves; cash flow deducts both. Yield on cost uses purchase, repairs, contingency, buying costs and loan fees.',
            'Cash to stabilize includes your setup carrying budget. Include interest and other costs during repairs and lease-up in that budget.',
            'Fixed-rate amortizing rental loan. Flip financing is modeled separately. DSCR is NOI divided by annual debt service.',
        ],
    }


def compare_strategies(inputs):
    flip = calculate_flip(inputs)
    rental = calculate_rental(inputs)
    return {'assumptions': inputs, 'flip': flip, 'rental': rental,
            'comparison_note': 'Flip profit is a one-time outcome; rental cash flow is annual. Compare capital, timing, and downside separately.'}
