import numpy as np
import pandas as pd

class HEICalculator:
    def __init__(self, nutrition_data):
        """
        Parameters:
            nutrition_data (DataFrame): Daily nutritional intake data.
        """
        self.nutrition_data = nutrition_data

        # Define nutrient units and conversion factors
        self.nutrient_units = {
            "protein": "g",
            "alcohol": "g",
            "water": "g",
            "carbohydrates": "g",
            "fiber": "g",
            "sugar": "g",
            "fat": "g",
            "fatty_acids_saturated": "g",
            "fatty_acids_monounsaturated": "g",
            "fatty_acids_polyunsaturated": "g",
            "cholesterol": "mg",
            "vitamin_a": "IU",
            "vitamin_c": "mg",
            "beta_carotene": "mcg",
            "vitamin_e": "TAE",
            "vitamin_d": "mcg",
            "vitamin_k": "mcg",
            "thiamin": "mg",
            "riboflavin": "mg",
            "niacin": "mg",
            "vitamin_b6": "mg",
            "folate": "mcg",
            "vitamin_b12": "mcg",
            "calcium": "mg",
            "phosphorus": "mg",
            "magnesium": "mg",
            "iron": "mg",
            "zinc": "mg",
            "copper": "mg",
            "selenium": "mcg",
            "potassium": "mg",
            "sodium": "mg",
            "caffeine": "mg",
            "theobromine": "mg",
            "energy_kcal": "kcal",
            "pantothenic_acid": "mg",
            "vitamin_b1": "mg",
            "vitamin_b2": "mg",
        }
        
        # Salt to sodium conversion factor
        self.salt_to_sodium_factor = 0.4
        
        # Official HEI-2020 Scoring Standards
        self.hei_standards = {
            # Adequacy Components
            "total_fruits": {
                "max_points": 5,
                "min_standard": 0.8,  # cup equiv per 1000 kcal for max score
                "max_standard": 0.0,  # cup equiv per 1000 kcal for min score (0 points)
                "density_factor": 1000,  # per 1000 kcal
                "unit": "cup_equiv"
            },
            "whole_fruits": {
                "max_points": 5,
                "min_standard": 0.4,  # cup equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "cup_equiv"
            },
            "total_vegetables": {
                "max_points": 5,
                "min_standard": 1.1,  # cup equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "cup_equiv"
            },
            "greens_and_beans": {
                "max_points": 5,
                "min_standard": 0.2,  # cup equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "cup_equiv"
            },
            "whole_grains": {
                "max_points": 10,
                "min_standard": 1.5,  # oz equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "oz_equiv"
            },
            "dairy": {
                "max_points": 10,
                "min_standard": 1.3,  # cup equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "cup_equiv"
            },
            "protein_foods": {
                "max_points": 5,
                "min_standard": 2.5,  # oz equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "oz_equiv"
            },
            "seafood_plant_proteins": {
                "max_points": 5,
                "min_standard": 0.8,  # oz equiv per 1000 kcal for max score
                "max_standard": 0.0,
                "density_factor": 1000,
                "unit": "oz_equiv"
            },
            "fatty_acids": {
                "max_points": 10,
                "min_standard": 2.5,  # ratio of (PUFA+MUFA)/SFA for max score
                "max_standard": 1.2,  # ratio for min score (0 points)
                "density_factor": 1,
                "unit": "ratio"
            },
            # Moderation Components (lower intake = higher score)
            "refined_grains": {
                "max_points": 10,
                "min_standard": 1.8,  # oz equiv per 1000 kcal for max score
                "max_standard": 4.3,  # oz equiv per 1000 kcal for min score (0 points)
                "density_factor": 1000,
                "unit": "oz_equiv"
            },
            "sodium": {
                "max_points": 10,
                "min_standard": 1.1,  # g per 1000 kcal for max score
                "max_standard": 2.0,  # g per 1000 kcal for min score (0 points)
                "density_factor": 1000,
                "unit": "g"
            },
            "added_sugars": {
                "max_points": 10,
                "min_standard": 6.5,  # % of energy for max score
                "max_standard": 26.0,  # % of energy for min score (0 points)
                "density_factor": 100,  # percent of energy
                "unit": "percent_energy"
            },
            "saturated_fats": {
                "max_points": 10,
                "min_standard": 8.0,  # % of energy for max score
                "max_standard": 16.0,  # % of energy for min score (0 points)
                "density_factor": 100,  # percent of energy
                "unit": "percent_energy"
            }
        }
        
        # Dictionary to hold any manual modifications to food category quantities
        self.modified_quantities = {}
        
        # Conversion factors for food equivalents (approximate)
        self.conversion_factors = {
            # Cup equivalents (grams to cups)
            "fruits_cup_equiv": 150,  # ~150g = 1 cup equiv for fruits
            "vegetables_cup_equiv": 125,  # ~125g = 1 cup equiv for vegetables
            "dairy_cup_equiv": 244,  # ~244g = 1 cup equiv for dairy
            # Ounce equivalents (grams to oz)
            "grains_oz_equiv": 28,  # ~28g = 1 oz equiv for grains
            "protein_oz_equiv": 28,  # ~28g = 1 oz equiv for protein foods
        }

    def calculate_sodium_from_salt(self, df_safe):
        """
        Calculate sodium content from salt values using the conversion factor.
        Returns sodium in grams.
        """
        # Ensure salt column is numeric and handle missing values
        if "salt" in df_safe.columns:
            salt_grams = pd.to_numeric(df_safe["salt"], errors='coerce').fillna(0).sum()
        else:
            salt_grams = 0
            print("Warning: 'salt' column not found in data. Sodium calculation will be 0.")
        
        # Convert salt to sodium (salt is ~40% sodium by weight)
        sodium_grams = salt_grams * self.salt_to_sodium_factor
        
        return sodium_grams

    def calculate_food_quantities(self, df=None):
        """
        Calculates consumed amounts for each food category in appropriate units.
        Returns quantities in the units needed for HEI scoring.
        """
        if df is None:
            df = self.nutrition_data

        quantities = {}
        
        df_safe = df.copy()
        
        food_category_columns = [
            "total_fruits", "whole_fruits", "total_vegetables", "greens_and_beans",
            "whole_grains", "dairy", "protein_foods", "seafood_plant_proteins", 
            "refined_grains"
        ]
        
        # Fill NaN values with False for food category columns
        for col in food_category_columns:
            if col in df_safe.columns:
                df_safe[col] = df_safe[col].fillna(False).astype(bool)
            else:
                df_safe[col] = False
        
        numeric_columns = ["eaten_quantity_in_gram", "salt", "sugar", 
                          "fatty_acids_saturated", "fatty_acids_monounsaturated", 
                          "fatty_acids_polyunsaturated"]
        
        for col in numeric_columns:
            if col in df_safe.columns:
                df_safe[col] = pd.to_numeric(df_safe[col], errors='coerce').fillna(0)
            else:
                df_safe[col] = 0
        
        # Fruits (convert to cup equivalents)
        fruits_grams = df_safe[df_safe["total_fruits"]]["eaten_quantity_in_gram"].sum()
        quantities["total_fruits"] = fruits_grams / self.conversion_factors["fruits_cup_equiv"]
        
        whole_fruits_grams = df_safe[df_safe["whole_fruits"]]["eaten_quantity_in_gram"].sum()
        quantities["whole_fruits"] = whole_fruits_grams / self.conversion_factors["fruits_cup_equiv"]
        
        # Vegetables (convert to cup equivalents)
        vegetables_grams = df_safe[df_safe["total_vegetables"]]["eaten_quantity_in_gram"].sum()
        quantities["total_vegetables"] = vegetables_grams / self.conversion_factors["vegetables_cup_equiv"]
        
        greens_grams = df_safe[df_safe["greens_and_beans"]]["eaten_quantity_in_gram"].sum()
        quantities["greens_and_beans"] = greens_grams / self.conversion_factors["vegetables_cup_equiv"]
        
        # Grains (convert to oz equivalents)
        whole_grains_grams = df_safe[df_safe["whole_grains"]]["eaten_quantity_in_gram"].sum()
        quantities["whole_grains"] = whole_grains_grams / self.conversion_factors["grains_oz_equiv"]
        
        refined_grains_grams = df_safe[df_safe["refined_grains"]]["eaten_quantity_in_gram"].sum()
        quantities["refined_grains"] = refined_grains_grams / self.conversion_factors["grains_oz_equiv"]
        
        # Dairy (convert to cup equivalents)
        dairy_grams = df_safe[df_safe["dairy"]]["eaten_quantity_in_gram"].sum()
        quantities["dairy"] = dairy_grams / self.conversion_factors["dairy_cup_equiv"]
        
        # Protein foods (convert to oz equivalents)
        protein_grams = df_safe[df_safe["protein_foods"]]["eaten_quantity_in_gram"].sum()
        quantities["protein_foods"] = protein_grams / self.conversion_factors["protein_oz_equiv"]
        
        seafood_plant_grams = df_safe[df_safe["seafood_plant_proteins"]]["eaten_quantity_in_gram"].sum()
        quantities["seafood_plant_proteins"] = seafood_plant_grams / self.conversion_factors["protein_oz_equiv"]
        
        # Fatty acids (calculate ratio)
        pufa_mufa = (
            df_safe["fatty_acids_monounsaturated"].sum() + 
            df_safe["fatty_acids_polyunsaturated"].sum()
        )
        sfa = df_safe["fatty_acids_saturated"].sum()
        quantities["fatty_acids"] = (pufa_mufa, sfa)
        
        # Sodium (calculate from salt column instead of sodium column)
        quantities["sodium"] = self.calculate_sodium_from_salt(df_safe)
        
        # Added sugars (grams - will be converted to % energy in scoring)
        quantities["added_sugars"] = df_safe["sugar"].sum()
        
        # Saturated fats (grams - will be converted to % energy in scoring)
        quantities["saturated_fats"] = df_safe["fatty_acids_saturated"].sum()

        # Apply any manual modifications
        for category, mod_value in self.modified_quantities.items():
            quantities[category] = mod_value

        return quantities

    def get_food_quantities(self):
        """Returns the current food quantities dictionary."""
        return self.calculate_food_quantities()

    def modify_food_quantity(self, category, new_quantity):
        """Modifies the stored quantity for a given food category."""
        self.modified_quantities[category] = new_quantity

    def score_food_category(self, food_quantity, total_energy, category):
        """
        Calculates HEI points for a given food category using official HEI-2020 standards.
        Returns a tuple (points, density_ratio).
        """
        if category not in self.hei_standards:
            raise ValueError(f"Unknown food category: {category}")
        
        standards = self.hei_standards[category]
        max_points = standards["max_points"]
        min_standard = standards["min_standard"]
        max_standard = standards["max_standard"]
        density_factor = standards["density_factor"]
        
        # Calculate density ratio based on category
        if category == "fatty_acids":
            # Special case: ratio of unsaturated to saturated fatty acids
            pufa_mufa, sfa = food_quantity
            density_ratio = pufa_mufa / sfa if sfa > 0 else 0
        elif category in ["added_sugars", "saturated_fats"]:
            energy_from_component = food_quantity * (4 if category == "added_sugars" else 9) 
            density_ratio = (energy_from_component / total_energy) * 100 if total_energy > 0 else 0
        elif category == "sodium":
            density_ratio = (food_quantity * density_factor) / total_energy if total_energy > 0 else 0
        else:
            density_ratio = (food_quantity * density_factor) / total_energy if total_energy > 0 else 0
        
        if category in ["total_fruits", "whole_fruits", "total_vegetables", "greens_and_beans", 
                       "whole_grains", "dairy", "protein_foods", "seafood_plant_proteins", "fatty_acids"]:
            if density_ratio >= min_standard:
                points = max_points
            elif density_ratio <= max_standard:
                points = 0
            else:
                points = max_points * (density_ratio - max_standard) / (min_standard - max_standard)
        else:
            if density_ratio <= min_standard:
                points = max_points
            elif density_ratio >= max_standard:
                points = 0
            else:
                points = max_points * (max_standard - density_ratio) / (max_standard - min_standard)
        
        points = max(0, min(points, max_points))
        
        return round(points, 2), round(density_ratio, 3)

    def calculate_scores(self):
        """
        Calculates HEI scores for all food categories based on the official HEI-2020 standards.
        Returns a dictionary with component scores and total HEI score.
        """
        # Calculate total energy
        if "energy_kcal_eaten" in self.nutrition_data.columns:
            total_energy = pd.to_numeric(self.nutrition_data["energy_kcal_eaten"], errors='coerce').fillna(0).sum()
        elif "energy_kcal" in self.nutrition_data.columns:
            total_energy = pd.to_numeric(self.nutrition_data["energy_kcal"], errors='coerce').fillna(0).sum()
        else:
            total_energy = 2000  # Default assumption if energy data is missing
            
        quantities = self.calculate_food_quantities()
        scores = {}
        total_hei_score = 0

        # Score all 13 HEI-2020 components
        for category in self.hei_standards.keys():
            qty = quantities.get(category, 0)
            points, density_ratio = self.score_food_category(qty, total_energy, category)
            scores[category] = {
                "points": points,
                "density_ratio": density_ratio,
                "max_points": self.hei_standards[category]["max_points"]
            }
            total_hei_score += points

        scores["total_HEI_score"] = round(total_hei_score, 2)
        scores["total_energy"] = total_energy
        
        return scores
    
    def get_component_summary(self):
        """
        Returns a summary of all HEI-2020 components with their scoring standards.
        """
        summary = {}
        for category, standards in self.hei_standards.items():
            summary[category] = {
                "max_points": standards["max_points"],
                "standard_for_max_score": standards["min_standard"],
                "standard_for_min_score": standards["max_standard"],
                "unit": standards["unit"],
                "component_type": "Adequacy" if category in [
                    "total_fruits", "whole_fruits", "total_vegetables", "greens_and_beans",
                    "whole_grains", "dairy", "protein_foods", "seafood_plant_proteins", "fatty_acids"
                ] else "Moderation"
            }
        return summary