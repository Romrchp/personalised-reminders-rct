import pandas as pd
import time
import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, 
    PageBreak, NextPageTemplate, Table, TableStyle, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable

from src.data_manager.meal import get_recent_meals_string_for_user
from src.utils.localization_utils import prompt_language_formatting, get_localized_summary_element, get_hei_translations

from ...utils.health_plot_utils import (
    assign_meal_period,
    plot_macronutrient_and_energy,
    plot_macronutrients_by_meal_period,
    plot_eaten_hour_distribution,
    #plot_eaten_amount_distribution,
    plot_meal_size_vs_time_correlation,
    plot_hei_score_over_time,
    plot_hei_components_heatmap,
)

from src.openai_client import OpenAIChatClient
from src.constants import DATA_FOLDER_NAME, FOODS_CATEGORIES_FILENAME, FOODS_EXPORT_FILENAME, PRODUCTS_CATEGORIES_FILENAME, PRODUCTS_FILENAME, SYSTEM_ROLE, GPT_4_O, USER_ROLE, FIGURE_OUTPUT_FOLDER,TEXT_OUTPUT_FOLDER,OUTPUT_FOLDER
from src.prompts.prompts_templates import PANEL_A_PROMPT, PANEL_B_PROMPT, PANEL_C_PROMPT, PANEL_D_PROMPT, PANEL_E_PROMPT, PANEL_F1_PROMPT, PANEL_F2_PROMPT
from src.data_manager.health_summary.hei_calculator import HEICalculator
from src.services.meal_grouping import aggregate_by_time_window
from src.utils.health_formatting_utils import clean_text_for_paragraph, create_hei_footnotes, draw_full_page_image, create_info_box, create_hei_table, create_enhanced_hei_explanation_box, create_enhanced_disclaimer_box, create_section_header, draw_header_footer


def set_plot_style():
    """Set consistent plot styling for better visualization."""
    font_list = [f.name for f in fm.fontManager.ttflist]
    if "Arial" in font_list:
        plt.rcParams["font.family"] = "Arial"
    else:
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Helvetica", "Verdana"]

    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["axes.labelsize"] = 10
    plt.rcParams["xtick.labelsize"] = 9
    plt.rcParams["ytick.labelsize"] = 9
    plt.rcParams["legend.fontsize"] = 9
    plt.rcParams["figure.titlesize"] = 14

def load_data(user_food_df):
    """
    Load and prepare the food and category data.
    
    Args:
        user_food_df (pd.DataFrame): The user's food data
        
    Returns:
        pd.DataFrame: Prepared user data with categories
    """
    
    project_dir = os.getcwd()
    data_dir = os.path.join(project_dir, DATA_FOLDER_NAME)
    
    foods_export_path = os.path.join(data_dir, FOODS_EXPORT_FILENAME)
    category_list_path = os.path.join(data_dir, FOODS_CATEGORIES_FILENAME)   
    products_path = os.path.join(data_dir, PRODUCTS_FILENAME)
    products_category_list_path = os.path.join(data_dir, PRODUCTS_CATEGORIES_FILENAME)
    
    food_export = pd.read_csv(foods_export_path)
    product_export = pd.read_csv(products_path)
    
    category_list = pd.read_csv(category_list_path)
    products_category_list = pd.read_csv(products_category_list_path)
    
    food_categories = [col for col in category_list.columns if col != "food_name"]
    
    product_export["name_combined"] = (
        product_export["name_en"]
        .fillna(product_export["name_fr"])
        .fillna(product_export["name_de"])
    )

    products_with_categories = pd.merge(
        product_export, 
        products_category_list, 
        how='left', #left join to keep all products
        left_on='name_combined', 
        right_on='food_name',
        suffixes=('_product', '_category')
    )
    
    # Prepare foods with categories - merge category list with food export
    foods_with_categories = pd.merge(
        food_export,
        category_list,
        left_on="display_name_en", 
        right_on="food_name", 
        how="left",
        suffixes=('_food', '_category')
    )
    
    # user data
    user_df = user_food_df.copy()
    user_df["local_time"] = pd.to_datetime(user_df["local_time"], errors='coerce')
    user_df["eaten_date"] = user_df["local_time"].dt.date
    user_df["eaten_hour"] = user_df["local_time"].dt.hour
    user_df["eaten_time"] = user_df["local_time"].dt.time
    
    #print("Initial user_df shape:", user_df.shape)
    
    # Initialize category columns
    for category in food_categories:
        user_df[category] = False
    
    # Track matching statistics
    food_matches = 0
    product_matches = 0
    total_foods = 0
    total_products = 0
    
    # Process each row individually -- handles foods and products correctly
    for idx, row in user_df.iterrows():
        # Check if this row has a food_id (it's a food item)
        if pd.notna(row.get('food_id')) and pd.notna(row.get('food_name')):
            total_foods += 1
            # Try to match with foods_with_categories using food_name
            food_match = foods_with_categories[
                foods_with_categories['food_name_en'] == row['food_name']
            ]
            
            
            if not food_match.empty:
                #print(f"Matched: {row['food_name']}")
                food_matches += 1
                # Update category columns for this food
                for category in food_categories:
                    if category in food_match.columns:
                        category_value = food_match.iloc[0][category]
                        if pd.notna(category_value):
                            user_df.at[idx, category] = category_value
        
        # Check if this row has a product_id (it's a product item)
        elif pd.notna(row.get('product_id')) and pd.notna(row.get('product_name')):
            total_products += 1
            # Try to match with products_with_categories using product_name
            product_match = products_with_categories[
                products_with_categories['name_combined'] == row['product_name']
            ]
            
            if not product_match.empty:
                product_matches += 1
                # Update category columns for this product
                for category in food_categories:
                    if category in product_match.columns:
                        category_value = product_match.iloc[0][category]
                        if pd.notna(category_value):
                            user_df.at[idx, category] = category_value
    
        #print(f"Final user_df shape: {user_df.shape}")
        #print(f"Food matching: {food_matches}/{total_foods} foods matched")
        #print(f"Product matching: {product_matches}/{total_products} products matched")
        #print("Available category columns:", [col for col in food_categories if col in user_df.columns])
    
    # Display some sample matches for debugging
    #matched_foods = user_df[user_df[food_categories].any(axis=1)]
    #print(f"Total rows with category matches: {len(matched_foods)}")
    
    #if len(matched_foods) > 0:
    #    #print("\nSample of matched items:")
    #    sample_cols = ['food_name', 'product_name'] + food_categories[:5] if len(food_categories) >= 5 else food_categories
    #    #print(matched_foods[sample_cols].head())
    
    return user_df

def calculate_hei_scores(user_df,user_id):
    """
    Calculate HEI scores for each day in the user data.
    
    Args:
        user_df (pd.DataFrame): User food data with categories
        
    Returns:
        tuple: (HEI scores DataFrame, list of low energy days)
    """
    rename_col_dict = {
        "consumed_quantity": "eaten_quantity_in_gram",
        "energy_kcal": "energy_kcal_eaten",
        "fat": "fat_eaten",
        "carbohydrates": "carbohydrates_eaten",
        "protein": "protein_eaten",
    }
    
    low_energy_days = []
    res_hei_scores_df = pd.DataFrame()
    
    for e, date in enumerate(user_df.sort_values("eaten_date")["eaten_date"].unique()):
        #print(e, date)
        daywise_df = user_df[user_df["eaten_date"] == date]
        daywise_df = daywise_df.rename(columns=rename_col_dict)
        
        total_energy_kcal_eaten = daywise_df["energy_kcal_eaten"].sum()
        daywise_df.to_csv(f"{user_id}_testing.csv")
        if total_energy_kcal_eaten < 1000:
            low_energy_days.append(date)
            continue
        calculator = HEICalculator(nutrition_data=daywise_df)
        all_scores = calculator.calculate_scores()
        daywise_hei_scores = pd.DataFrame(all_scores).loc["points"]
        
        res_hei_scores_df = pd.concat(
            [res_hei_scores_df, daywise_hei_scores.to_frame(name=date)], axis=1
        )
    
    #print("skipped", len(low_energy_days), "\ndays", low_energy_days)
    
    return res_hei_scores_df, low_energy_days


def create_aggregated_data(user_df):
    """
    Create aggregated data from user food data.
    
    Args:
        user_df (pd.DataFrame): User food data with categories
        
    Returns:
        pd.DataFrame: Aggregated user data
    """
    timestamp_columns = ['consumed_at','local_time']
    value_columns = ['energy_kcal','fat','carbohydrates','protein', 'consumed_quantity']

    meal_windowed_user_df_agg = aggregate_by_time_window(user_df,
                                                         columns_to_sum=value_columns,
                                                         columns_to_min=timestamp_columns)

    user_df_agg = meal_windowed_user_df_agg.groupby("local_time").sum(numeric_only=True).reset_index()
    user_df_agg["eaten_hour"] = pd.to_datetime(user_df_agg["local_time"]).dt.hour
    user_df_agg["meal_period"] = user_df_agg.apply(
        lambda row: assign_meal_period(
            row["consumed_quantity"],
            row["eaten_hour"],
            eaten_amount_threshold=10,
        ),
        axis=1,
    )
    user_df_agg["eaten_date"] = pd.to_datetime(user_df_agg["local_time"]).dt.date
    user_df_agg["eaten_time"] = pd.to_datetime(user_df_agg["local_time"]).dt.time
    
    return user_df_agg


def create_nutrition_dashboard(user_language, user_df, user_df_agg, res_hei_scores_df, output_path):
    """
    Create a nutrition dashboard figure with multiple panels.
    """
    import matplotlib.gridspec as gridspec

    # Determine if we have HEI data
    has_hei_data = len(res_hei_scores_df) > 0
    
    # Use consistent aspect ratio
    if has_hei_data:
        fig = plt.figure(figsize=(14, 16))  # Keep original size for HEI data
        gs = gridspec.GridSpec(nrows=3, ncols=2, figure=fig, height_ratios=[1, 1, 1])
    else:
        #Same width but adjust height to maintain reasonable proportions
        fig = plt.figure(figsize=(14, 10)) 
        gs = gridspec.GridSpec(nrows=2, ncols=2, figure=fig, height_ratios=[1, 1])
    
    panel_results = {}

    # Panel A and B
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _, panel_results['panel_a_macro_percentages'], panel_results['panel_a'] = plot_macronutrient_and_energy(user_language,user_df, ax=ax_a, panel_label="Panel A")
    _, panel_results['panel_b'] = plot_macronutrients_by_meal_period(user_language,user_df_agg, ax=ax_b, panel_label="Panel B")

    # Panel C and D 
    ax_c = fig.add_subplot(gs[1, 0], polar=True)
    ax_d = fig.add_subplot(gs[1, 1])
    _, panel_results['panel_c'] = plot_eaten_hour_distribution(user_language,user_df_agg, ax=ax_c, panel_label="Panel C", color="dimgray")
    _, panel_results['panel_d'] = plot_meal_size_vs_time_correlation(user_language,user_df_agg, ax=ax_d, panel_label="Panel D", size_metric='energy_kcal')

    # HEI panels (E, F1, F2) (only if data is available)
    if has_hei_data:
        # Bottom row for Panel E and F
        bottom_gs = gs[2, :].subgridspec(1, 2, width_ratios=[0.5, 0.5], wspace=0.5)
        right_gs = bottom_gs[1].subgridspec(2, 1)

        hei_time_ax = fig.add_subplot(bottom_gs[0])
        hei_heat1_ax = fig.add_subplot(right_gs[0])
        hei_heat2_ax = fig.add_subplot(right_gs[1])

        _, panel_results['panel_e'] = plot_hei_score_over_time(
            user_language,
            res_hei_scores_df,
            low_energy_days=None,
            column_name="total_HEI_score",
            ax=hei_time_ax,
            panel_label="Panel E",
        )
        _, panel_results['panel_f_1'], panel_results['panel_f_2'] = plot_hei_components_heatmap(
            user_language,
            res_hei_scores_df,
            ax1=hei_heat1_ax,
            ax2=hei_heat2_ax,
            panel_label="Panel F",
        )

    # Final layout
    plt.tight_layout(pad=1.0)
    plt.savefig(output_path, dpi=300, bbox_inches="tight", 
                facecolor='white', edgecolor='none')
    plt.close() 
    return panel_results



def generate_text_summary(panel_results, phone_number, user_key, user_diet_goal, user_language, output_path):
    """
    Generate text summaries for each panel using OpenAI API.
    
    Args:
        panel_results (dict): Dictionary containing panel results
        output_path (str): Path to save the text summary
        phone_number (str): Phone number to associate with the chat
        
    Returns:
        dict: Dictionary containing text summaries for each panel
    """
    chat_client = OpenAIChatClient(os.environ.get('OPENAI_API_KEY'))
    user_meals = get_recent_meals_string_for_user(user_key)
    user_language = prompt_language_formatting(user_language)
    
    system_message = (
        "You are a helpful assistant that summarizes the nutritional data of a user's diet."
    )
    
    chat_client.add_message_from_phone_number(
        phone_number,
        SYSTEM_ROLE,
        system_message,
        twilio_message_id=None,
        reminder_id=None
    )
    
    panel_configs = [
        {
            'panel_key': 'panel_a',
            'prompt': PANEL_A_PROMPT.format(
                panel_results_summary=panel_results['panel_a'][["carbohydrates", "fat", "protein", "energy_kcal"]].describe().to_dict(),
                panel_a_df=panel_results['panel_a'],
                macro_percentages = panel_results['panel_a_macro_percentages'],
                user_language = user_language,
                user_diet_goal = user_diet_goal,
                recent_meals = user_meals
            )
        },
        {
            'panel_key': 'panel_b',
            'prompt': PANEL_B_PROMPT.format(panel_b_df=panel_results['panel_b'],
                user_diet_goal = user_diet_goal,
                user_language = user_language,
                recent_meals = user_meals)
        },
        {
            'panel_key': 'panel_c',
            'prompt': PANEL_C_PROMPT.format(panel_c_df=panel_results['panel_c'],
                                            user_language = user_language,
                                            user_diet_goal = user_diet_goal)
        },
        {
            'panel_key': 'panel_d',
            'prompt': PANEL_D_PROMPT.format(panel_d_df=panel_results['panel_d'],
                                            user_language = user_language,
                                            user_diet_goal = user_diet_goal)
        }
    ]

    if 'panel_e' in panel_results:
        panel_configs.append({
            'panel_key': 'panel_e',
            'prompt': PANEL_E_PROMPT.format(panel_e_df=panel_results['panel_e'],
                average_hei_score = panel_results['panel_e'].mean(),
                user_language = user_language,
                user_diet_goal = user_diet_goal,
                recent_meals = user_meals)
        })
    if 'panel_f_1' in panel_results:
            panel_configs.append({
                'panel_key': 'panel_f_1',
                'prompt': PANEL_F1_PROMPT.format(panel_f1_df=panel_results['panel_f_1'],
                user_language = user_language,                                 
                user_diet_goal = user_diet_goal,
                recent_meals = user_meals)
            })
    if 'panel_f_2' in panel_results:
            panel_configs.append({
                'panel_key': 'panel_f_2',
                'prompt': PANEL_F2_PROMPT.format(panel_f2_df=panel_results['panel_f_2'],
                user_language = user_language,
                user_diet_goal = user_diet_goal,
                recent_meals = user_meals)
            })
    
    summaries = {}
    for config in panel_configs:
        chat_client.add_message_from_phone_number(
            phone_number,
            SYSTEM_ROLE,
            config['prompt'],
            twilio_message_id=None,
            reminder_id=None
        )
        
        response = chat_client.create_chat_completion(
            GPT_4_O,
            phone_number,
            temperature=1
        )
        
        summaries[config['panel_key']] = response
        time.sleep(10)


    with open(output_path, "w") as f:
        f.write(summaries.get('panel_a', ''))
        f.write("\n\n")
        
        f.write(summaries.get('panel_b', ''))
        f.write("\n\n")
        
        f.write(summaries.get('panel_c', ''))
        f.write("\n\n")
        
        f.write(summaries.get('panel_d', ''))
        f.write("\n\n")
        
        if 'panel_e' in summaries:
            f.write(summaries.get('panel_e', ''))
            f.write("\n\n")
            
            f.write(summaries.get('panel_f_1', ''))
            f.write("\n\n")
            
            f.write(summaries.get('panel_f_2', ''))
            f.write("\n\n")
    
    return summaries
    


def generate_health_summary(user_id, user_phone_nb,user_key,user_diet_goal, user_language, user_df):
    """
    Process nutrition data for a user and generate summary and visualization.
    This function runs the entire pipeline.
    
    Args:
        user_id (str): User ID to process
        user_df (pd.DataFrame) :  The DataFrame containing the user's ID.
        
    Returns:
        tuple: (user_df, user_df_agg, res_hei_scores_df, panel_results, summaries)
    """

    # Define file paths
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    data_dir = os.path.join(project_dir,OUTPUT_FOLDER)
    figure_dir = os.path.join(data_dir,FIGURE_OUTPUT_FOLDER)
    text_summaries_dir = os.path.join(data_dir,TEXT_OUTPUT_FOLDER)
    figure_output_path = os.path.join(figure_dir,f"{user_id}_nutrition_dashboard.png")
    text_output_path = os.path.join(text_summaries_dir,f"{user_id}_summary_text.txt")
    
    # Load data & calculate HEI scores
    set_plot_style()
    user_df = load_data(user_df)
    res_hei_scores_df, low_energy_days = calculate_hei_scores(user_df,user_id)
    
    # Create aggregated data
    user_df_agg = create_aggregated_data(user_df)
    
    # Create dashboard
    os.makedirs(figure_dir, exist_ok=True)
    panel_results = create_nutrition_dashboard(user_language,
        user_df, user_df_agg, res_hei_scores_df, figure_output_path
    )
    
    # Generate text summaries
    os.makedirs(text_summaries_dir, exist_ok=True)
    summaries = generate_text_summary(panel_results, user_phone_nb,user_key,user_diet_goal,user_language, text_output_path)

    return user_df, user_df_agg, res_hei_scores_df, panel_results, summaries






def build_nutrition_pdf(user_id, summaries_dict, figure_path, output_pdf_path, user_language, ai_disclaimer=None,hei_explanation=None):
    """PDF builder"""
    width, height = A4

    dummy_frame = Frame(0, 0, 1, 1, id="Dummy")
    text_frame = Frame(0.75 * inch, 0.75 * inch, 
                      width - 1.5 * inch, height - 1.5 * inch, 
                      id='Text', leftPadding=0, rightPadding=0)

    image_template = PageTemplate(
        id='ImagePage', 
        frames=[dummy_frame],
        onPage=lambda c, d: draw_full_page_image(c, d, figure_path,user_language)
    )
    
    text_template = PageTemplate(
        id='TextPage', 
        frames=[text_frame],
        onPage=draw_header_footer
    )

    doc = BaseDocTemplate(output_pdf_path, pagesize=A4,
                          pageTemplates=[image_template, text_template],
                          title=get_localized_summary_element("summary-main-title",user_language),
                          author="Nutrition Tracker")

    styles = getSampleStyleSheet()
    
    content_style = ParagraphStyle(
        "ContentStyle",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        fontName="Helvetica",
        textColor=HexColor("#2D3748")
    )

    elements = []

    # Start with text page template after image
    elements.append(NextPageTemplate('TextPage'))
    elements.append(PageBreak())

    # Main title for summaries section
    elements.extend(create_section_header(get_localized_summary_element("summaries_recap.main-title",user_language), is_main=True))
    
    ai_disclaimer = get_localized_summary_element("ai-disclaimer",user_language)
    hei_explanation = get_localized_summary_element("hei-explanation",user_language)

    # Add AI disclaimer if available
    if ai_disclaimer:
        enhanced_disclaimer = create_enhanced_disclaimer_box(ai_disclaimer)
        elements.append(enhanced_disclaimer)
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(HRFlowable(width="80%", thickness=1, 
                              color=HexColor("#E5E7EB"), 
                              spaceBefore=10, spaceAfter=20,
                              hAlign='CENTER'))

    # Check if HEI data exists by looking for HEI-related summaries
    has_hei_data = any(key in summaries_dict for key in ['panel_e', 'panel_f_1', 'panel_f_2'])

    # Define grouped sections structure
    section_groups = [
        {
            "title": get_localized_summary_element("summaries_recap.first-section",user_language),
            "panels": [
                {"key": "panel_a", "title": get_localized_summary_element("summaries_recap.panel-a-section",user_language)},
                {"key": "panel_b", "title": get_localized_summary_element("summaries_recap.panel-b-section",user_language)}
            ]
        },
        {
            "title": get_localized_summary_element("summaries_recap.second-section",user_language),
            "panels": [
                {"key": "panel_c", "title": get_localized_summary_element("summaries_recap.panel-c-section",user_language)},
                {"key": "panel_d", "title": get_localized_summary_element("summaries_recap.panel-d-section",user_language)}
            ]
        }
    ]

    # Only add HEI section if HEI data exists
    if has_hei_data:
        section_groups.append({
            "title": get_localized_summary_element("summaries_recap.third-section",user_language),
            "panels": [
                {"key": "panel_e", "title": get_localized_summary_element("summaries_recap.panel-e-section",user_language)},
                {"key": "panel_f_1", "title": get_localized_summary_element("summaries_recap.panel-f-1-section",user_language)},
                {"key": "panel_f_2", "title": get_localized_summary_element("summaries_recap.panel-f-2-section",user_language)}
            ]
        })

    # Process sections with grouped structure
    for section_idx, section_group in enumerate(section_groups):
        # Main section header
        section_elements = []
        section_elements.extend(create_section_header(section_group["title"]))
        
        # Add HEI explanation before HEI Score Analysis section (as plain text)
        # Only add this if we have HEI data and this is the HEI section
        if (has_hei_data and 
            section_group["title"] == get_localized_summary_element("summaries_recap.third-section",user_language) and 
            hei_explanation):
            enhanced_hei_explanation = create_enhanced_hei_explanation_box(hei_explanation)
            section_elements.append(enhanced_hei_explanation)
            section_elements.append(Spacer(1, 0.25 * inch))
            
            hei_disclaimer_text = get_localized_summary_element("hei-calculation-disclaimer", user_language)
            if hei_disclaimer_text:
                enhanced_hei_disclaimer = create_enhanced_disclaimer_box(hei_disclaimer_text, "hei-calculation")
                section_elements.append(enhanced_hei_disclaimer)
                section_elements.append(Spacer(1, 0.2 * inch))

            section_elements.append(create_hei_table(get_hei_translations(user_language)))
            section_elements.append(Spacer(1, 0.15 * inch))
            section_elements.append(create_hei_footnotes(get_hei_translations(user_language)))
            section_elements.append(Spacer(1, 0.2 * inch))
        
        # Process panels within the section
        for panel in section_group["panels"]:
            panel_key = panel["key"]
            panel_title = panel["title"]
            
            if panel_key in summaries_dict:
                # Subsection header
                section_elements.extend(create_section_header(panel_title, is_subsection=True))
                
                # Content in styled box
                summary = summaries_dict[panel_key]
                clean_text = clean_text_for_paragraph(summary)
                content_para = Paragraph(clean_text, content_style)
                
                section_elements.append(
                    create_info_box(content_para, "info")
                )
                section_elements.append(Spacer(1, 0.2 * inch))
        
        # Keep each section together to avoid page breaks within sections
        elements.append(KeepTogether(section_elements))
        
        # Add page break between major sections (but not after the last one)
        if section_idx < len(section_groups) - 1:
            elements.append(PageBreak())

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(
        Table([[get_localized_summary_element("final-summary-message",user_language),]], 
              colWidths=[6.5 * inch],
              style=TableStyle([
                  ('BACKGROUND', (0, 0), (-1, -1), HexColor("#F0FFF4")),
                  ('TEXTCOLOR', (0, 0), (-1, -1), HexColor("#22543D")),
                  ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                  ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                  ('FONTSIZE', (0, 0), (-1, -1), 12),
                  ('TOPPADDING', (0, 0), (-1, -1), 15),
                  ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                  ('ROUNDEDCORNERS', [10, 10, 10, 10]),
              ]))
    )

    doc.build(elements)