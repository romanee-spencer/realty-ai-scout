"""Known cash-flow fixtures and validation, without market or provider calls."""
import pytest
from src.deal_calculator import calculate_flip
from src.app import app


@pytest.fixture
def deal():
    return dict(purchase_price=200000, resale_value=300000, renovation_budget=30000,
                contingency_percent=10, buying_costs=5000, monthly_carrying_costs=1000,
                holding_months=6, selling_cost_percent=6, loan_amount=160000,
                annual_interest_percent=7.5, loan_fees=2000, target_profit=30000,
                resale_decline_percent=10, renovation_overrun_percent=20, delay_months=3)


def test_known_deal_and_combined_downside(deal):
    results = calculate_flip(deal)['scenarios']
    base = results[0]
    assert base['total_project_cost'] == 270000
    assert base['cash_required_before_sale'] == 92000
    assert base['profit_before_tax'] == 30000
    assert base['purchase_ceiling_for_target_profit'] == 200000
    assert base['interest_cost'] == 6000
    assert base['selling_costs'] == 18000
    assert base['meets_target_profit'] is True
    assert results[1]['profit_before_tax'] == 1800
    assert results[2]['profit_before_tax'] == 17400
    assert results[3]['profit_before_tax'] == -10800
    assert results[3]['meets_target_profit'] is False


def test_all_cash_and_break_even_identity(deal):
    deal.update(loan_amount=0, loan_fees=0)
    base = calculate_flip(deal)['scenarios'][0]
    assert base['interest_cost'] == 0
    assert base['cash_required_before_sale'] == 244000
    deal['resale_value'] = base['break_even_resale']
    assert abs(calculate_flip(deal)['scenarios'][0]['profit_before_tax']) <= 0.01


@pytest.mark.parametrize('value', [None, '', -1, 'NaN', 'Infinity', True, [], 'abc'])
def test_invalid_numbers(deal, value):
    deal['renovation_budget'] = value
    with pytest.raises(ValueError):
        calculate_flip(deal)


@pytest.mark.parametrize('key,value', [('selling_cost_percent', 100), ('purchase_price', 0),
                                     ('resale_value', 0), ('loan_amount', 200001)])
def test_invalid_model_assumptions(deal, key, value):
    deal[key] = value
    with pytest.raises(ValueError):
        calculate_flip(deal)


def test_deal_endpoint_and_page(deal):
    with app.test_client() as client:
        assert client.get('/investor').status_code == 200
        response = client.post('/deal-analysis', json=deal)
        assert response.status_code == 200
        assert response.get_json()['scenarios'][0]['profit_before_tax'] == 30000
        assert client.post('/deal-analysis', json={}).status_code == 400
        assert client.post('/deal-analysis', data='bad', content_type='application/json').status_code == 400


@pytest.fixture
def rental(deal):
    return dict(deal, monthly_rent=2400, vacancy_percent=5, monthly_property_taxes=400,
                monthly_insurance=150, monthly_maintenance=150, monthly_hoa_utilities=50,
                management_percent=8, monthly_capex_reserve=150, rental_loan_amount=160000,
                rental_interest_percent=6.5, rental_loan_years=30, rental_loan_fees=2000,
                rental_setup_carrying_costs=3000, rent_decline_percent=10, extra_vacancy_points=5)


def test_rental_known_operating_income_and_debt(rental):
    from src.deal_calculator import calculate_rental
    base, downside = calculate_rental(rental)['scenarios']
    assert base['annual_effective_rent'] == 27360
    assert base['annual_operating_expenses'] == 11188.80
    assert base['annual_noi'] == 16171.20
    assert base['monthly_debt_payment'] == 1011.31
    assert base['annual_cash_flow_before_tax'] == 2235.49
    assert base['cash_to_stabilize'] == 83000
    assert downside['monthly_cash_flow_before_tax'] < 0


def test_zero_interest_and_cash_purchase(rental):
    from src.deal_calculator import calculate_rental
    rental['rental_interest_percent'] = 0
    base = calculate_rental(rental)['scenarios'][0]
    assert base['monthly_debt_payment'] == 444.44
    rental.update(rental_loan_amount=0, rental_loan_years=0)
    base = calculate_rental(rental)['scenarios'][0]
    assert base['dscr'] is None
    assert base['annual_cash_flow_before_tax'] == 14371.20


def test_rental_break_even(rental):
    from src.deal_calculator import calculate_rental
    base = calculate_rental(rental)['scenarios'][0]
    rental['monthly_rent'] = base['break_even_monthly_rent']
    assert abs(calculate_rental(rental)['scenarios'][0]['annual_cash_flow_before_tax']) < 0.1


@pytest.mark.parametrize('key,value', [('rental_loan_years', 0), ('rental_loan_years', 1.5),
                                     ('extra_vacancy_points', 95), ('monthly_rent', 0),
                                     ('rental_loan_amount', 200001)])
def test_rental_invalid_assumptions(rental, key, value):
    from src.deal_calculator import calculate_rental
    rental[key] = value
    with pytest.raises(ValueError):
        calculate_rental(rental)


def test_both_strategies_endpoint(rental):
    with app.test_client() as client:
        response = client.post('/strategy-comparison', json=rental)
        assert response.status_code == 200
        data = response.get_json()
        assert data['flip']['scenarios'][0]['profit_before_tax'] == 30000
        assert data['rental']['scenarios'][0]['cash_to_stabilize'] == 83000
        assert client.post('/strategy-comparison', json=[]).status_code == 400
