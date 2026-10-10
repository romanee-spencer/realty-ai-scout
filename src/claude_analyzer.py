"""
Claude AI analyzer for comprehensive real estate analysis
Handles ALL analysis: market research, comparable analysis, property insights, and pricing strategies
Replaces the need for separate market research APIs
"""

import os
import json
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude AI client"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
    
    def analyze_property_value(self, property_data: Dict, comparables: List[Dict], market_data: Optional[Dict] = None) -> Dict:
        """Analyze property value using comparable sales and market data"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        As a professional real estate appraiser and market researcher, analyze this property and provide comprehensive insights:

        SUBJECT PROPERTY:
        {json.dumps(property_data, indent=2)}

        COMPARABLE SALES:
        {json.dumps(comparables, indent=2)}

        MARKET DATA:
        {json.dumps(market_data or {}, indent=2)}

        Please provide a comprehensive analysis including:

        1. MARKET RESEARCH:
           - Current market trends in this area
           - Average days on market
           - Price per square foot trends
           - Inventory levels (buyer's vs seller's market)

        2. PROPERTY VALUATION:
           - Estimated market value with confidence range
           - Price per square foot analysis
           - Comparable analysis and adjustments

        3. COMPARABLE ANALYSIS:
           - Rate each comparable (A/B/C grade)
           - Explain adjustments needed
           - Identify best/worst comparables and why

        4. MARKET STRATEGY:
           - Suggested list price and reasoning
           - Best time to sell
           - Marketing recommendations

        5. INVESTMENT ANALYSIS:
           - Potential rental income
           - Appreciation prospects
           - Risk factors

        6. PROPERTY INSIGHTS:
           - Condition assessment
           - Upgrade recommendations
           - Potential issues or red flags

        Format your response as structured JSON with clear sections.
        Use your knowledge of real estate markets to provide insights even with limited data.
        """
        
        return self._make_request(prompt)
    
    def comprehensive_property_analysis(self, scraped_data: Dict) -> Dict:
        """Perform complete property analysis using scraped data"""
        if not self.client:
            return {"error": "Claude API key not configured"}

        property_data = scraped_data.get('property', {})
        comparables = scraped_data.get('comparables', [])

        prompt = f"""
        You are a licensed real estate appraiser performing a Comparative Market Analysis (CMA).
        You must follow standard appraisal methodology and provide defensible valuations.

        CRITICAL RULES FOR COMPARABLE SELECTION & ANALYSIS:
        1. EXCLUDE any sale that appears to be: foreclosure, probate, short sale, bank-owned/REO,
           estate sale, auction, tax sale, sheriff sale, or any non-arm's-length transaction.
           These distressed sales do NOT reflect fair market value.
        2. Only use standard arm's-length transactions between willing buyer and seller.
        3. Comps should be:
           - Within 1 mile (ideal) to 3 miles (maximum) of subject
           - Sold within last 6 months (ideal) to 12 months (maximum)
           - Similar size: within 20-25% of subject sqft
           - Similar bed/bath count: within +-1 bed, +-1 bath
           - Same property type (single family vs condo vs townhouse)
        4. Apply standard adjustments for differences:
           - Location (neighborhood quality, street, lot)
           - Size (price per sqft adjustment)
           - Condition and age
           - Bed/bath count differences
           - Garage, basement, lot size, upgrades
        5. Weight adjusted comp values by quality (best comps get more weight).
        6. Use your knowledge of {property_data.get('address', 'this area')} to supplement
           the provided comps with your understanding of local market conditions.

        IMPORTANT - FINISHED BASEMENT / BELOW-GRADE LIVING SPACE:
        - Zillow's listed sqft often only reflects ABOVE-GRADE living area
        - Finished basements add significant value but are NOT always in the sqft count
        - If a property has a finished basement, the total living space may be 30-60% larger
          than the listed sqft, which dramatically affects $/sqft and overall value
        - When comparing comps, adjust for whether comps include or exclude basement sqft
        - A property with finished basement is worth MORE than one without, even at same listed sqft
        - Do NOT undervalue properties just because comps without basements sold for less

        VALUATION BIAS CHECK:
        - Do NOT assume asking price is overpriced. Many properties sell AT or ABOVE asking.
        - If comps are smaller, older, or inferior quality, adjust UPWARD for the subject property
        - Consider the full picture: location, condition, upgrades, finished space, lot size
        - When data is limited, lean on market knowledge but acknowledge uncertainty rather
          than defaulting to a lower valuation

        SUBJECT PROPERTY:
        Address: {property_data.get('address', 'Unknown')}
        Listed/Asking Price: ${property_data.get('price', 'Unknown')}
        Beds: {property_data.get('beds', 'Unknown')}
        Baths: {property_data.get('baths', 'Unknown')}
        Square Feet (above grade): {property_data.get('sqft', 'Unknown')}
        Finished Basement Sqft: {property_data.get('sqft_finished_basement', 'Unknown')}
        Total Living Sqft (incl basement): {property_data.get('total_living_sqft', 'Unknown')}
        Basement: {property_data.get('basement', 'Unknown')}
        Zestimate: {property_data.get('zestimate', 'Unknown')}
        Year Built: {property_data.get('year_built', 'Unknown')}
        Description: {(property_data.get('description') or 'No description available')[:300]}

        SCRAPED COMPARABLE SALES (pre-filtered to remove obvious distressed sales):
        {self._format_comparables_for_analysis(comparables)}

        NOTE: If the provided comps are insufficient (too few, too different, or suspicious),
        use your knowledge of the local market to provide additional context and adjust accordingly.
        State clearly when you are supplementing with market knowledge vs using provided data.
        If the property has a finished basement, factor that into valuation - it adds real value.

        Respond in JSON format with these exact keys:

        {{
            "executive_summary": "2-3 sentence overview with key finding on value vs asking price",
            "property_overview": {{
                "condition_assessment": "Based on description, age, and price signals",
                "key_features": ["Notable features"],
                "property_type": "Single family/Condo/etc"
            }},
            "market_analysis": {{
                "market_trend": "Specific trend for this neighborhood/city with data points",
                "median_price_area": "Median home price for this area",
                "avg_price_per_sqft": "Average $/sqft for comparable homes in area",
                "avg_days_on_market": "Estimated DOM for this area",
                "inventory_level": "buyer's/seller's/balanced market with reasoning",
                "market_position": "How this property compares (above/below/at market)"
            }},
            "comparable_analysis": {{
                "comps_used": [
                    {{
                        "address": "comp address",
                        "sale_price": "price",
                        "sale_type": "arm's-length / EXCLUDED-reason",
                        "similarity_grade": "A/B/C",
                        "adjustments": "specific $ adjustments applied and why",
                        "adjusted_value": "price after adjustments"
                    }}
                ],
                "comps_excluded": ["list any comps excluded and why (distressed, too different, etc.)"],
                "comp_quality_score": "A/B/C rating for overall comp set quality with reasoning"
            }},
            "valuation": {{
                "estimated_fair_market_value": "Your FMV estimate as a number",
                "value_range_low": "Conservative estimate",
                "value_range_high": "Optimistic estimate",
                "price_vs_value": "Is asking price above/below/at FMV and by how much %",
                "confidence_level": "High/Medium/Low with specific reasoning",
                "methodology": "Brief explanation of how you arrived at this value"
            }},
            "pricing_strategy": {{
                "suggested_list_price": "Recommended listing price if selling",
                "pricing_rationale": "Why this price - reference comps and market",
                "days_to_sell_estimate": "Estimated days on market at this price"
            }},
            "investment_analysis": {{
                "rental_potential": "Estimated monthly rent with reasoning",
                "cap_rate_estimate": "Estimated cap rate",
                "appreciation_outlook": "1-3-5 year outlook with reasoning",
                "investment_grade": "A-F rating with explanation"
            }},
            "recommendations": ["3-5 specific, actionable items"],
            "risk_factors": ["Specific risks with this property/market"],
            "data_quality_notes": "Note any limitations in the analysis due to missing data"
        }}

        Be precise with dollar amounts. Do not hedge excessively - give your best professional estimate.
        """

        return self._make_request(prompt)
    
    def _format_comparables_for_analysis(self, comparables: List[Dict]) -> str:
        """Format comparable properties for Claude analysis with quality indicators"""
        if not comparables:
            return "No comparable properties found from scraping. Use your market knowledge to provide analysis."

        formatted = []
        for i, comp in enumerate(comparables[:8], 1):
            sale_type = comp.get('sale_type', 'unknown')
            comp_text = f"""
            Comp {i}:
            - Address: {comp.get('address', 'Unknown')}
            - Sale Price: ${comp.get('sale_price', 'Unknown')}
            - Beds: {comp.get('beds', 'Unknown')}
            - Baths: {comp.get('baths', 'Unknown')}
            - Sqft: {comp.get('sqft', 'Unknown')}
            - Sale Type: {sale_type}
            - Distance: {comp.get('distance_miles', 'Unknown')} miles
            - Sale Date: {comp.get('sale_date', 'Unknown')}
            """
            formatted.append(comp_text.strip())

        formatted.append(f"\nTotal comps provided: {len(comparables)} (pre-filtered to exclude distressed sales)")
        return "\n".join(formatted)
    
    def generate_listing_description(self, property_data: Dict, analysis: Dict) -> Dict:
        """Generate compelling listing description"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        Create a compelling real estate listing description for this property:

        PROPERTY DATA:
        {json.dumps(property_data, indent=2)}

        ANALYSIS DATA:
        {json.dumps(analysis, indent=2)}

        Generate:
        1. HEADLINE - catchy 1-line summary
        2. DESCRIPTION - 2-3 paragraph compelling description highlighting key features
        3. KEY FEATURES - bullet points of main selling points
        4. NEIGHBORHOOD HIGHLIGHTS - local amenities and attractions
        5. CALL TO ACTION - motivating closing statement

        Style: Professional but engaging, emphasize unique selling points, avoid superlatives without substance.
        """
        
        return self._make_request(prompt)
    
    def assess_property_condition(self, photos: List[str], property_data: Dict) -> Dict:
        """Assess property condition from photos (when available)"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        # Note: This would require Claude's vision capabilities
        # For now, implement text-based condition assessment
        
        prompt = f"""
        Assess property condition based on available data:

        PROPERTY INFORMATION:
        {json.dumps(property_data, indent=2)}

        Based on year built, price relative to area, and any description text, assess:
        1. OVERALL CONDITION - Excellent/Good/Fair/Poor
        2. LIKELY UPDATES NEEDED - kitchen, bathrooms, systems, etc.
        3. CONDITION ADJUSTMENTS - how condition affects value vs comparables
        4. RENOVATION RECOMMENDATIONS - priority improvements for value
        5. INVESTMENT POTENTIAL - fix-up costs vs value increase

        Provide reasoning for each assessment.
        """
        
        return self._make_request(prompt)
    
    def create_market_report(self, address: str, analysis_data: Dict) -> Dict:
        """Create comprehensive market report"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        Create a comprehensive market report for {address}:

        ANALYSIS DATA:
        {json.dumps(analysis_data, indent=2)}

        Generate a professional market report including:
        1. EXECUTIVE SUMMARY
        2. PROPERTY VALUATION SUMMARY
        3. COMPARABLE SALES ANALYSIS
        4. MARKET CONDITIONS OVERVIEW
        5. PRICING RECOMMENDATIONS
        6. MARKETING STRATEGY
        7. RISK FACTORS AND CONSIDERATIONS

        Format as a professional report suitable for real estate professionals.
        """
        
        return self._make_request(prompt)
    
    def analyze_investment_potential(self, property_data: Dict, market_data: Dict) -> Dict:
        """Analyze property as an investment opportunity"""
        if not self.client:
            return {"error": "Claude API key not configured"}
        
        prompt = f"""
        Analyze this property's investment potential:

        PROPERTY DATA:
        {json.dumps(property_data, indent=2)}

        MARKET DATA:
        {json.dumps(market_data, indent=2)}

        Provide investment analysis:
        1. CASH FLOW ANALYSIS - estimated rental income vs expenses
        2. APPRECIATION POTENTIAL - market trends and growth factors
        3. RISK ASSESSMENT - market volatility, location factors
        4. INVESTMENT SCORE - rate 1-10 with reasoning
        5. COMPARABLE INVESTMENTS - how this compares to alternatives
        6. EXIT STRATEGY - resale potential and timeline

        Include specific numbers and calculations where possible.
        """
        
        return self._make_request(prompt)
    
    def analyze_flip_potential(self, property_data: Dict, comparables: List[Dict]) -> Dict:
        """Analyze property for flip/investment potential with financial metrics"""
        if not self.client:
            return {"error": "Claude API key not configured"}

        # No resale estimate or profit is inferred from the asking price.
        # Deterministic deal metrics live in deal_calculator.py and require
        # explicit exit, repair, carrying and financing assumptions.
        flip_metrics = {}

        prompt = f"""
        You are an experienced real estate investor analyzing a potential flip deal.
        Provide a realistic, numbers-driven analysis. Do NOT use distressed sale prices as ARV targets.

        CRITICAL: ARV (After Repair Value) must be based on:
        - Recent arm's-length sales of RENOVATED/UPDATED properties in the same area
        - NOT foreclosures, probate, short sales, or distressed transactions
        - Properties in good/excellent condition (post-renovation comparable)
        - Similar size, bed/bath count, and location to subject

        SUBJECT PROPERTY:
        Address: {property_data.get('address', 'Unknown')}
        Asking Price: ${property_data.get('price', 'Unknown')}
        Beds: {property_data.get('beds', 'Unknown')}
        Baths: {property_data.get('baths', 'Unknown')}
        Square Feet (above grade): {property_data.get('sqft', 'Unknown')}
        Finished Basement Sqft: {property_data.get('sqft_finished_basement', 'Unknown')}
        Total Living Sqft: {property_data.get('total_living_sqft', 'Unknown')}
        Basement: {property_data.get('basement', 'Unknown')}
        Year Built: {property_data.get('year_built', 'Unknown')}
        Description: {(property_data.get('description') or 'No description')[:300]}

        Keep above-grade and basement space distinct. Any value adjustment must be
        supported by supplied comparable evidence; do not invent a local adjustment rate.

        COMPARABLE SALES (pre-filtered, distressed sales removed):
        {self._format_comparables_for_analysis(comparables)}

        PRELIMINARY CALCULATED METRICS (verify and adjust these):
        {json.dumps(flip_metrics, indent=2)}

        The metrics are intentionally empty when underwriting assumptions are absent.
        Do not derive ARV from purchase price or fabricate sold comparables, rents, or costs.
        Use null for unsupported dollar amounts, financial outputs, and scores.
        If adequate comparable evidence is absent, return recommendation="insufficient_data"
        and list the missing evidence. Do not issue a buy recommendation without evidence.

        Provide flip analysis in JSON format:
        {{
            "flip_score": "1-10 rating with justification",
            "recommendation": "strong_buy / buy / consider / pass",
            "arv_assessment": {{
                "estimated_arv": "Your ARV as a dollar amount",
                "arv_per_sqft": "Target $/sqft for renovated property in this area",
                "arv_methodology": "How you determined ARV - which comps, what adjustments",
                "arv_confidence": "High/Medium/Low"
            }},
            "acquisition_analysis": {{
                "max_allowable_offer": "Maximum you should pay using 70% rule",
                "is_asking_price_viable": "Yes/No with reasoning",
                "negotiation_target": "What to offer and why"
            }},
            "renovation_scope": {{
                "estimated_cost_low": "Conservative reno budget",
                "estimated_cost_high": "Full renovation budget",
                "priority_items": ["specific renovation items with estimated costs"],
                "timeline_months": "realistic timeline",
                "scope_level": "cosmetic / moderate / full gut"
            }},
            "financial_summary": {{
                "total_cost_in": "Purchase + reno + holding + closing",
                "expected_arv": "After repair value",
                "expected_profit": "Most likely profit",
                "best_case_profit": "optimistic scenario with assumptions",
                "worst_case_profit": "conservative scenario with assumptions",
                "expected_roi": "ROI percentage",
                "cash_needed": "Total cash required"
            }},
            "deal_breakers": ["Any absolute no-go factors"],
            "market_factors": "Local market conditions affecting this flip - be specific",
            "risks": ["Specific risk factors ranked by severity"],
            "exit_strategies": ["Ranked exit options if flip doesn't work"]
        }}

        Use dollar amounts only when supported by the supplied evidence and explicit
        assumptions. Identify source gaps and unverified facts in risks.
        """

        result = self._make_request(prompt)
        if result.get("success"):
            result["flip_metrics"] = flip_metrics
        return result

    def _make_request(self, prompt: str) -> Dict:
        """Make request to Claude API"""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=6000,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return {
                "success": True,
                "content": message.content[0].text,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    analyzer = ClaudeAnalyzer()
    
    # Test property analysis
    sample_property = {
        "address": "123 Main St, Anytown, CA",
        "price": 750000,
        "sqft": 2100,
        "beds": 3,
        "baths": 2,
        "year_built": 1995
    }
    
    sample_comps = [
        {"address": "125 Main St", "price": 725000, "sqft": 2000, "beds": 3, "baths": 2},
        {"address": "127 Oak Ave", "price": 780000, "sqft": 2200, "beds": 3, "baths": 2}
    ]
    
    sample_market = {"trend": "rising", "avg_dom": 25, "inventory": "low"}
    
    result = analyzer.analyze_property_value(sample_property, sample_comps, sample_market)
    
    if result.get("success"):
        print("Property Analysis:")
        print(result["content"])
    else:
        print(f"Error: {result.get('error')}")