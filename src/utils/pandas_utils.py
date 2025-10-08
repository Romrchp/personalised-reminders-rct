import pandas as pd


def print_df_shape(df, rows=5):
    print(f"The dataframe has this shape: {df.shape}")


def delete_empty_rows(df):
    df = df.dropna(subset=['food_name','product_name'], how="all")
    return df


def get_json_from_df_row(row):

    #key_mapping = {
    #'energy_kcal': ('calories', ''),
    #'water': ('water_ml', 'ml'),
    #'protein': ('protein_g', 'g'),
    #'carbohydrates': ('carbs_g', 'g'),
    #'starch': ('starch_g', 'g'),
    #'sugar': ('sugar_g', 'g'),
    #'salt': ('salt_g', 'g'),
    #'fiber': ('fiber_g', 'g'),
    #'fat': ('fat_g', 'g'),
    #'fatty_acids_saturated': ('sat_fat_g', 'g'),
    #'fatty_acids_polyunsaturated': ('poly_unsat_fat_g', 'g'),
    #'fatty_acids_monounsaturated': ('mono_unsat_fat_g', 'g'),
    #'cholesterol': ('cholesterol_mg', 'mg'),
    #'calcium': ('calcium_mg', 'mg'),
    #'iron': ('iron_mg', 'mg'),
    #'zinc': ('zinc_mg', 'mg'),
    #'phosphorus': ('phosphorus_mg', 'mg'),
    #'sodium': ('sodium_mg', 'mg'),
    #'alcohol': ('alcohol_g', 'g')
    #}
    wanted_nutrients = {
        'energy_kcal', 'water', 'protein', 'carbohydrates', 'starch', 'sugar', 'salt', 'fiber', 'fat', 
        'fatty_acids_saturated', 'fatty_acids_polyunsaturated', 'fatty_acids_monounsaturated', 'cholesterol', 
        'calcium', 'iron', 'zinc', 'phosphorus', 'sodium', 'alcohol'
    }

    formatted_nutrients = {}
    for key, value in row.items():
        if key in wanted_nutrients and pd.notna(value):
            formatted_nutrients[key] = round(value, 2)
    return formatted_nutrients

