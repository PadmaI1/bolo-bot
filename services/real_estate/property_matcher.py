import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class PropertyInventoryMatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Sample property inventory (would integrate with actual property management system)
        self.property_inventory = {
            "bangalore": [
                {
                    "id": "BLR001",
                    "name": "Prestige Sunrise Park",
                    "builder": "Prestige Group",
                    "location": "Electronic City Phase 2",
                    "area_details": {
                        "micro_location": "Electronic City",
                        "nearby_landmarks": ["Infosys", "TCS", "Metro Station"],
                        "connectivity_score": 9
                    },
                    "property_details": {
                        "type": "apartment",
                        "configurations": ["2bhk", "3bhk"],
                        "sizes": {"2bhk": "1200 sqft", "3bhk": "1650 sqft"},
                        "price_range": {"2bhk": "₹72-78 Lakhs", "3bhk": "₹95-105 Lakhs"},
                        "possession": "Ready to Move",
                        "age": "2 years"
                    },
                    "amenities": [
                        "Swimming Pool", "Gym", "Children's Play Area", 
                        "Jogging Track", "24x7 Security", "Power Backup",
                        "Covered Parking", "Landscaped Gardens"
                    ],
                    "investment_metrics": {
                        "rental_yield": "3.2%",
                        "appreciation_forecast": "8-10% annually",
                        "rental_range": {"2bhk": "₹22-25K", "3bhk": "₹32-38K"}
                    },
                    "legal_status": "RERA Approved",
                    "financing": {
                        "loan_approved_banks": ["SBI", "HDFC", "ICICI"],
                        "loan_eligibility": "Up to 90%"
                    }
                },
                {
                    "id": "BLR002", 
                    "name": "Godrej Nest",
                    "builder": "Godrej Properties",
                    "location": "Whitefield",
                    "area_details": {
                        "micro_location": "Whitefield Main Road",
                        "nearby_landmarks": ["ITPL", "Phoenix MarketCity", "Metro Connectivity"],
                        "connectivity_score": 8
                    },
                    "property_details": {
                        "type": "apartment",
                        "configurations": ["1bhk", "2bhk", "3bhk"],
                        "sizes": {"1bhk": "650 sqft", "2bhk": "1100 sqft", "3bhk": "1500 sqft"},
                        "price_range": {"1bhk": "₹45-52 Lakhs", "2bhk": "₹68-78 Lakhs", "3bhk": "₹88-98 Lakhs"},
                        "possession": "Dec 2025",
                        "age": "under_construction"
                    },
                    "amenities": [
                        "Club House", "Swimming Pool", "Gym", "Tennis Court",
                        "Children's Play Area", "Senior Citizen Area", "Multipurpose Hall"
                    ],
                    "investment_metrics": {
                        "rental_yield": "3.8%", 
                        "appreciation_forecast": "12-15% annually",
                        "rental_range": {"1bhk": "₹15-18K", "2bhk": "₹25-30K", "3bhk": "₹35-42K"}
                    },
                    "legal_status": "RERA Approved",
                    "financing": {
                        "loan_approved_banks": ["SBI", "HDFC", "Axis Bank"],
                        "loan_eligibility": "Up to 85%"
                    }
                }
            ],
            "gurgaon": [
                {
                    "id": "GGN001",
                    "name": "DLF New Town Heights",
                    "builder": "DLF Limited",
                    "location": "Sector 90",
                    "area_details": {
                        "micro_location": "New Gurgaon",
                        "nearby_landmarks": ["Dwarka Expressway", "IGI Airport", "Cyber Hub"],
                        "connectivity_score": 9
                    },
                    "property_details": {
                        "type": "apartment",
                        "configurations": ["2bhk", "3bhk", "4bhk"],
                        "sizes": {"2bhk": "1350 sqft", "3bhk": "1800 sqft", "4bhk": "2500 sqft"},
                        "price_range": {"2bhk": "₹95-110 Lakhs", "3bhk": "₹1.35-1.55 Cr", "4bhk": "₹2.1-2.4 Cr"},
                        "possession": "Ready to Move",
                        "age": "1 year"
                    },
                    "amenities": [
                        "Resort-style Swimming Pool", "State-of-art Gym", "Spa", 
                        "Business Center", "Banquet Hall", "Shopping Complex",
                        "School & Medical Center", "Golf Course View"
                    ],
                    "investment_metrics": {
                        "rental_yield": "2.8%",
                        "appreciation_forecast": "10-12% annually", 
                        "rental_range": {"2bhk": "₹35-42K", "3bhk": "₹48-58K", "4bhk": "₹75-90K"}
                    },
                    "legal_status": "RERA Approved",
                    "financing": {
                        "loan_approved_banks": ["HDFC", "ICICI", "Kotak Mahindra"],
                        "loan_eligibility": "Up to 90%"
                    }
                }
            ]
        }
        
        # Location mapping for easier access
        self.location_mapping = {
            "electronic city": "bangalore",
            "whitefield": "bangalore", 
            "btm": "bangalore",
            "koramangala": "bangalore",
            "gurgaon": "gurgaon",
            "sector": "gurgaon",
            "dwarka": "gurgaon"
        }
    
    def find_matching_properties(self, qualification_data: Dict[str, Any], max_results: int = 5) -> List[Dict[str, Any]]:
        """Find properties matching lead qualification criteria"""
        try:
            matches = []
            
            # Get all properties from relevant locations
            locations = qualification_data.get("locations", [])
            budget_range = qualification_data.get("budget_range", "")
            property_type = qualification_data.get("property_type", "")
            
            # Search in relevant cities
            cities_to_search = set()
            for location in locations:
                location_lower = location.lower()
                for mapped_location, city in self.location_mapping.items():
                    if mapped_location in location_lower:
                        cities_to_search.add(city)
                        break
                else:
                    # If no specific mapping found, search all cities
                    cities_to_search.update(["bangalore", "gurgaon"])
            
            if not cities_to_search:
                cities_to_search = ["bangalore", "gurgaon"]  # Default search
            
            # Search properties in identified cities
            for city in cities_to_search:
                city_properties = self.property_inventory.get(city, [])
                for prop in city_properties:
                    match_score = self._calculate_match_score(prop, qualification_data)
                    if match_score >= 5:  # Minimum match threshold
                        enhanced_prop = prop.copy()
                        enhanced_prop["match_score"] = match_score
                        enhanced_prop["match_reasons"] = self._get_match_reasons(prop, qualification_data)
                        matches.append(enhanced_prop)
            
            # Sort by match score and return top results
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            return matches[:max_results]
        
        except Exception as e:
            self.logger.error(f"Property matching error: {e}")
            return []
    
    def _calculate_match_score(self, property_info: Dict[str, Any], qualification_data: Dict[str, Any]) -> int:
        """Calculate how well a property matches lead qualification (1-10 scale)"""
        score = 0
        
        # Budget matching (30% weight)
        budget_score = self._score_budget_match(
            qualification_data.get("budget_range", ""),
            property_info["property_details"]["price_range"]
        )
        score += budget_score * 0.3
        
        # Property type matching (25% weight)
        type_score = self._score_type_match(
            qualification_data.get("property_type", ""),
            property_info["property_details"]["type"]
        )
        score += type_score * 0.25
        
        # Location matching (25% weight)
        location_score = self._score_location_match(
            qualification_data.get("locations", []),
            property_info["location"]
        )
        score += location_score * 0.25
        
        # Timeline matching (10% weight)
        timeline_score = self._score_timeline_match(
            qualification_data.get("timeline", ""),
            property_info["property_details"]["possession"]
        )
        score += timeline_score * 0.1
        
        # Motivation matching (10% weight)
        motivation_score = self._score_motivation_match(
            qualification_data.get("motivation", ""),
            property_info.get("investment_metrics", {})
        )
        score += motivation_score * 0.1
        
        return min(int(score), 10)
    
    def _score_budget_match(self, qual_budget: str, property_prices: Dict[str, str]) -> int:
        """Score budget alignment"""
        if not qual_budget or qual_budget == "not_disclosed":
            return 5  # Neutral score
        
        try:
            # Extract budget number (assuming format like "50-75 lakhs" or "1-2 crores")
            qual_budget_lower = qual_budget.lower()
            
            # Simple budget range extraction
            if "crore" in qual_budget_lower:
                if "1" in qual_budget_lower:
                    budget_min, budget_max = 100, 200  # 1-2 crores in lakhs
                elif "2" in qual_budget_lower:
                    budget_min, budget_max = 200, 300
                else:
                    budget_min, budget_max = 100, 500
            elif "lakh" in qual_budget_lower:
                if "20" in qual_budget_lower or "30" in qual_budget_lower:
                    budget_min, budget_max = 20, 50
                elif "50" in qual_budget_lower:
                    budget_min, budget_max = 50, 100
                elif "80" in qual_budget_lower or "90" in qual_budget_lower:
                    budget_min, budget_max = 80, 120
                else:
                    budget_min, budget_max = 50, 150
            else:
                return 5  # Default if unclear
            
            # Check if any property configuration falls within budget
            for config, price_str in property_prices.items():
                # Extract price range from string like "₹85-95 Lakhs"
                if "lakh" in price_str.lower():
                    # Simple price extraction - in production, use proper parsing
                    if budget_min <= 100 and "85" in price_str:  # Example match
                        return 8
                elif "crore" in price_str.lower():
                    if budget_max >= 100:  # Budget in crore range
                        return 8
            
            return 6  # Partial match
            
        except Exception as e:
            self.logger.error(f"Budget scoring error: {e}")
            return 5
    
    def _score_type_match(self, qual_type: str, property_type: str) -> int:
        """Score property type alignment"""
        if not qual_type or qual_type == "any":
            return 7  # Good default score
        
        if qual_type.lower() == property_type.lower():
            return 10  # Perfect match
        
        # Partial matches
        type_synonyms = {
            "apartment": ["flat", "unit", "residential"],
            "villa": ["house", "independent", "bungalow"],
            "plot": ["land", "site", "investment"]
        }
        
        qual_type_lower = qual_type.lower()
        property_type_lower = property_type.lower()
        
        for main_type, synonyms in type_synonyms.items():
            if (qual_type_lower in synonyms and main_type == property_type_lower) or \
               (property_type_lower in synonyms and main_type == qual_type_lower):
                return 8
        
        return 3  # Low match
    
    def _score_location_match(self, qual_locations: List[str], property_location: str) -> int:
        """Score location preference alignment"""
        if not qual_locations:
            return 7  # Default score when no preference specified
        
        property_location_lower = property_location.lower()
        
        for qual_location in qual_locations:
            qual_location_lower = qual_location.lower()
            
            # Exact match
            if qual_location_lower in property_location_lower or property_location_lower in qual_location_lower:
                return 10
            
            # Partial city matches
            location_mappings = {
                "bangalore": ["bengaluru", "blr", "garden city"],
                "gurgaon": ["gurugram", "ggn", "millennium city"],
                "electronic city": ["e-city", "ec", "tech hub"],
                "whitefield": ["itpl", "brookefield"]
            }
            
            for main_location, alternatives in location_mappings.items():
                if qual_location_lower == main_location and any(alt in property_location_lower for alt in alternatives):
                    return 9
                elif property_location_lower == main_location and any(alt in qual_location_lower for alt in alternatives):
                    return 9
        
        return 4  # No strong location match
    
    def _score_timeline_match(self, qual_timeline: str, property_possession: str) -> int:
        """Score timeline alignment"""
        if not qual_timeline:
            return 7
        
        timeline_lower = qual_timeline.lower()
        possession_lower = property_possession.lower()
        
        if timeline_lower == "immediate" and "ready" in possession_lower:
            return 10
        elif timeline_lower in ["1-3months", "3-6months"]:
            if "ready" in possession_lower:
                return 9
            elif "2025" in possession_lower:
                return 7
        elif timeline_lower in ["6months", "1year", "exploring"]:
            return 8  # Flexible timeline matches most properties
        
        return 6
    
    def _score_motivation_match(self, motivation: str, investment_metrics: Dict[str, Any]) -> int:
        """Score motivation alignment"""
        if not motivation:
            return 7
        
        motivation_lower = motivation.lower()
        
        if motivation_lower == "investment":
            # For investors, focus on rental yield and appreciation
            rental_yield = investment_metrics.get("rental_yield", "0%")
            yield_value = float(rental_yield.replace("%", "")) if rental_yield != "0%" else 0
            
            if yield_value >= 3.5:
                return 9
            elif yield_value >= 3.0:
                return 8
            else:
                return 6
                
        elif motivation_lower in ["self_use", "end_user", "family"]:
            # For self-use, all properties are generally suitable
            return 8
            
        elif motivation_lower == "upgrader":
            # Upgraders typically want better amenities and locations
            return 8 if len(investment_metrics) > 0 else 6
        
        return 7
    
    def _get_match_reasons(self, property_info: Dict[str, Any], qualification_data: Dict[str, Any]) -> List[str]:
        """Get specific reasons why this property matches the lead"""
        reasons = []
        
        # Budget alignment
        budget = qualification_data.get("budget_range", "")
        if budget:
            reasons.append("Budget aligned with your requirements")
        
        # Location preference
        locations = qualification_data.get("locations", [])
        if locations:
            for location in locations:
                if location.lower() in property_info["location"].lower():
                    reasons.append(f"Located in your preferred area: {location}")
                    break
        
        # Property type match
        prop_type = qualification_data.get("property_type", "")
        if prop_type and prop_type.lower() == property_info["property_details"]["type"]:
            reasons.append("Exact property type match")
        
        # Timeline suitability
        timeline = qualification_data.get("timeline", "")
        possession = property_info["property_details"]["possession"]
        if timeline == "immediate" and "Ready" in possession:
            reasons.append("Ready for immediate possession")
        
        # Investment suitability
        motivation = qualification_data.get("motivation", "")
        if motivation == "investment":
            rental_yield = property_info.get("investment_metrics", {}).get("rental_yield", "")
            if rental_yield:
                reasons.append(f"Good rental yield: {rental_yield}")
        
        # Default reasons if none specific found
        if not reasons:
            reasons = ["Good location connectivity", "Premium amenities", "Reputed builder"]
        
        return reasons[:3]  # Return top 3 reasons
    
    def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for specific property"""
        try:
            for city_properties in self.property_inventory.values():
                for prop in city_properties:
                    if prop["id"] == property_id:
                        return prop
            return None
        except Exception as e:
            self.logger.error(f"Property detail retrieval error: {e}")
            return None
    
    def create_property_comparison(self, property_ids: List[str]) -> Dict[str, Any]:
        """Create property comparison for lead decision making"""
        try:
            properties = []
            for prop_id in property_ids:
                prop_details = self.get_property_details(prop_id)
                if prop_details:
                    properties.append(prop_details)
            
            if len(properties) < 2:
                return {"error": "Need at least 2 properties for comparison"}
            
            comparison = {
                "properties": properties,
                "comparison_matrix": self._create_comparison_matrix(properties),
                "recommendation": self._recommend_best_property(properties),
                "decision_factors": self._identify_key_decision_factors(properties)
            }
            
            return comparison
        
        except Exception as e:
            self.logger.error(f"Property comparison error: {e}")
            return {"error": str(e)}
    
    def _create_comparison_matrix(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create detailed comparison matrix"""
        comparison_matrix = {
            "price_comparison": {},
            "location_scores": {},
            "amenity_comparison": {},
            "investment_potential": {},
            "possession_timeline": {}
        }
        
        for prop in properties:
            prop_id = prop["id"]
            
            # Price comparison
            comparison_matrix["price_comparison"][prop_id] = {
                "configurations": prop["property_details"]["price_range"],
                "price_per_sqft": self._calculate_price_per_sqft(prop)
            }
            
            # Location scoring
            comparison_matrix["location_scores"][prop_id] = {
                "connectivity_score": prop["area_details"]["connectivity_score"],
                "landmarks": prop["area_details"]["nearby_landmarks"]
            }
            
            # Amenities
            comparison_matrix["amenity_comparison"][prop_id] = {
                "total_amenities": len(prop["amenities"]),
                "premium_amenities": self._count_premium_amenities(prop["amenities"])
            }
            
            # Investment metrics
            if "investment_metrics" in prop:
                comparison_matrix["investment_potential"][prop_id] = prop["investment_metrics"]
            
            # Possession status
            comparison_matrix["possession_timeline"][prop_id] = prop["property_details"]["possession"]
        
        return comparison_matrix
    
    def _calculate_price_per_sqft(self, property_info: Dict[str, Any]) -> Dict[str, str]:
        """Calculate price per square foot for different configurations"""
        prices = {}
        price_range = property_info["property_details"]["price_range"]
        sizes = property_info["property_details"]["sizes"]
        
        for config in price_range.keys():
            if config in sizes:
                # Simple calculation (would be more sophisticated in production)
                prices[config] = "₹5,500-6,500/sqft"  # Placeholder calculation
        
        return prices
    
    def _count_premium_amenities(self, amenities: List[str]) -> int:
        """Count premium amenities"""
        premium_amenities = ["swimming pool", "gym", "spa", "golf", "tennis", "banquet", "business center"]
        count = 0
        
        for amenity in amenities:
            if any(premium in amenity.lower() for premium in premium_amenities):
                count += 1
        
        return count
    
    def _recommend_best_property(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recommend the best property with reasoning"""
        if not properties:
            return {"error": "No properties to compare"}
        
        # Simple recommendation based on overall score (would use more sophisticated algorithm)
        best_property = max(properties, key=lambda x: x.get("match_score", 0))
        
        return {
            "recommended_property": best_property["id"],
            "property_name": best_property["name"],
            "recommendation_reasons": [
                f"Highest match score: {best_property.get('match_score', 0)}/10",
                f"Excellent {best_property['area_details']['connectivity_score']}/10 connectivity",
                f"Strong investment potential with {best_property.get('investment_metrics', {}).get('rental_yield', 'good')} rental yield"
            ],
            "key_selling_points": [
                f"Prime location in {best_property['location']}",
                f"Ready possession" if "Ready" in best_property["property_details"]["possession"] else "Upcoming possession",
                f"Premium amenities including {', '.join(best_property['amenities'][:3])}"
            ]
        }
    
    def _identify_key_decision_factors(self, properties: List[Dict[str, Any]]) -> List[str]:
        """Identify key factors for decision making"""
        return [
            "Price per square foot and total cost",
            "Location connectivity and future development",
            "Possession timeline and ready-to-move vs under-construction",
            "Builder reputation and RERA compliance",
            "Rental yield potential for investment buyers",
            "Amenities and lifestyle offerings",
            "Home loan eligibility and approved banks"
        ]
    
    def generate_property_pitch_audio(self, property_id: str, personalization_context: Dict[str, Any]) -> bytes:
        """Generate personalized property pitch audio using Murf AI"""
        try:
            property_details = self.get_property_details(property_id)
            if not property_details:
                return b""
            
            # Create personalized pitch based on lead qualification
            motivation = personalization_context.get("motivation", "self_use")
            budget_conscious = personalization_context.get("budget_sensitive", False)
            
            if motivation == "investment":
                pitch_focus = f"""
                This property offers excellent investment potential with {property_details['investment_metrics']['rental_yield']} rental yield
                and {property_details['investment_metrics']['appreciation_forecast']} expected appreciation.
                
                The location in {property_details['location']} is rapidly developing with upcoming infrastructure projects.
                Current rental demand is strong with {property_details['investment_metrics']['rental_range'].get('3bhk', '₹30-35K')} monthly rental.
                """
            else:
                pitch_focus = f"""
                This beautiful home in {property_details['location']} offers the perfect lifestyle for your family.
                
                With {len(property_details['amenities'])} premium amenities including {', '.join(property_details['amenities'][:3])},
                your family will enjoy resort-style living with excellent connectivity to work and schools.
                """
            
            # Add financing information if budget conscious
            if budget_conscious and property_details.get("financing"):
                financing_info = f"""
                
                For financing, this project is approved by {', '.join(property_details['financing']['loan_approved_banks'][:2])}
                with loan eligibility up to {property_details['financing']['loan_eligibility']}.
                """
                pitch_focus += financing_info
            
            return self.tts_service.create_property_presentation(
                property_details, 
                personalization_context.get("language", "english")
            )
        
        except Exception as e:
            self.logger.error(f"Property pitch generation error: {e}")
            return b""
    
    def get_inventory_summary(self, city: Optional[str] = None) -> Dict[str, Any]:
        """Get inventory summary for reporting"""
        try:
            if city:
                city_inventory = self.property_inventory.get(city.lower(), [])
                properties = city_inventory
            else:
                properties = []
                for city_props in self.property_inventory.values():
                    properties.extend(city_props)
            
            summary = {
                "total_properties": len(properties),
                "by_type": {},
                "price_ranges": {},
                "possession_status": {},
                "average_amenities": 0
            }
            
            # Analyze inventory
            for prop in properties:
                # By type
                prop_type = prop["property_details"]["type"]
                summary["by_type"][prop_type] = summary["by_type"].get(prop_type, 0) + 1
                
                # Possession status
                possession = prop["property_details"]["possession"]
                possession_key = "ready" if "Ready" in possession else "under_construction"
                summary["possession_status"][possession_key] = summary["possession_status"].get(possession_key, 0) + 1
            
            # Average amenities
            total_amenities = sum(len(prop["amenities"]) for prop in properties)
            summary["average_amenities"] = round(total_amenities / len(properties), 1) if properties else 0
            
            return summary
        
        except Exception as e:
            self.logger.error(f"Inventory summary error: {e}")
            return {"error": str(e)}
