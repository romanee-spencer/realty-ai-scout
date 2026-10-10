"""Offline request and scraping lifecycle regression tests."""

import importlib
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

app_module = importlib.import_module('src.app')


@pytest.fixture
def client():
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client


@pytest.fixture
def pipeline(monkeypatch):
    analyzer = Mock()
    result = {'success': True, 'content': '{"estimated_value": 250000}'}
    analyzer.comprehensive_property_analysis.return_value = result
    analyzer.analyze_flip_potential.return_value = result
    factory = Mock(return_value=analyzer)
    monkeypatch.setitem(sys.modules, 'claude_analyzer', SimpleNamespace(ClaudeAnalyzer=factory))
    scrape = Mock(return_value={'property': {'sqft': 1000}, 'comparables': []})
    monkeypatch.setattr(app_module, 'try_scrape', scrape)
    return factory, analyzer, scrape


def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Realty AI Scout' in response.data


@pytest.mark.parametrize('endpoint', ['/analyze', '/flip-analysis'])
@pytest.mark.parametrize('payload', [{}, {'address': ''}, {'address': '   '},
                                     {'address': 123}, {'address': []}, [], 'text'])
def test_invalid_input_does_not_start_pipeline(client, pipeline, endpoint, payload):
    response = client.post(endpoint, json=payload)
    assert response.status_code == 400
    assert 'error' in response.get_json()
    pipeline[0].assert_not_called()
    pipeline[2].assert_not_called()


@pytest.mark.parametrize('endpoint', ['/analyze', '/flip-analysis'])
@pytest.mark.parametrize('body,content_type', [('invalid json', 'application/json'),
                                             ('null', 'application/json'),
                                             ('', 'application/json'),
                                             ('address=test', 'text/plain')])
def test_bad_body_returns_json_error(client, pipeline, endpoint, body, content_type):
    response = client.post(endpoint, data=body, content_type=content_type)
    assert response.status_code == 400
    assert 'error' in response.get_json()
    pipeline[0].assert_not_called()


@pytest.mark.parametrize('endpoint,key', [('/analyze', 'analysis'),
                                          ('/flip-analysis', 'flip_analysis')])
def test_successful_analysis(client, pipeline, endpoint, key):
    response = client.post(endpoint, json={'address': ' 123 Main St ', 'sqft': 1500})
    assert response.status_code == 200
    data = response.get_json()
    assert data['address'] == '123 Main St'
    assert data['property_data']['sqft'] == 1500
    assert data[key]['estimated_value'] == 250000
    pipeline[2].assert_called_once_with('123 Main St')


@pytest.mark.parametrize('endpoint,method', [('/analyze', 'comprehensive_property_analysis'),
                                             ('/flip-analysis', 'analyze_flip_potential')])
def test_provider_failure(client, pipeline, endpoint, method):
    getattr(pipeline[1], method).return_value = {'success': False, 'error': 'Provider unavailable'}
    response = client.post(endpoint, json={'address': '123 Main St'})
    assert response.status_code == 500
    assert 'Provider unavailable' in response.get_json()['error']


@pytest.mark.parametrize('outcome', ['success', 'scrape_error', 'start_failure', 'close_error'])
def test_browser_always_closed(monkeypatch, outcome):
    scraper = Mock()
    scraper.start_driver.return_value = outcome != 'start_failure'
    expected = {'property': {'address': '123 Main St'}, 'comparables': []}
    scraper.scrape_property_and_comps.return_value = expected
    if outcome == 'scrape_error':
        scraper.scrape_property_and_comps.side_effect = RuntimeError('Scraping failed')
    if outcome == 'close_error':
        scraper.close_driver.side_effect = RuntimeError('Closing failed')
    monkeypatch.setitem(sys.modules, 'selenium_scraper',
                        SimpleNamespace(PropertyScraper=Mock(return_value=scraper)))
    assert app_module.try_scrape('123 Main St') == expected
    scraper.close_driver.assert_called_once()


def test_manual_merge_preserves_scraped_input_and_zero_values():
    scraped = {'sqft': 1000, 'beds': 2}
    result = app_module.build_property_data({'address': '123 Main St', 'beds': 0,
                                             'sqft_finished_basement': 0,
                                             'condition': 'Unknown'}, scraped)
    assert scraped == {'sqft': 1000, 'beds': 2}
    assert result['beds'] == 0
    assert result['data_source'] == 'manual'
    assert 'condition' not in result


def test_flip_research_does_not_infer_arv_from_purchase_price(monkeypatch):
    monkeypatch.setitem(sys.modules, 'anthropic', SimpleNamespace(Anthropic=Mock()))
    module = importlib.import_module('src.claude_analyzer')
    analyzer = module.ClaudeAnalyzer.__new__(module.ClaudeAnalyzer)
    analyzer.client = object()
    analyzer._make_request = Mock(return_value={'success': True, 'content': '{}'})
    result = analyzer.analyze_flip_potential({'price': 200000, 'sqft': 1000}, [])
    assert result['flip_metrics'] == {}
    assert 'Do not derive ARV from purchase price' in analyzer._make_request.call_args[0][0]
