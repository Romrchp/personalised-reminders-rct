import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

from src.utils.localization_utils import get_localized_summary_element

# from hei_calculator_v2 import HEICalculator


def assign_meal_period(eaten_amount, eaten_time, eaten_amount_threshold=10):
    if (eaten_amount < eaten_amount_threshold) or (15 <= eaten_time < 18) :
        return "Snack"
    elif 4 <= eaten_time < 11:
        return "Breakfast"
    elif 11 <= eaten_time < 15:
        return "Lunch"
    elif 18 <= eaten_time < 23:
        return "Dinner"
    else:
        #print("eaten_time:", eaten_time, "eaten_amount:", eaten_amount)
        return "Late Night"


# def calculate_HEI_score(user_df, food_category):
#     """Calculates the HEI score for a given day (in format YYYY-MM-DD)"""

#     # Create calculator instance
#     calculator = HEICalculator(
#         base_path="data/cross_verification_food_categories_HEI", nutrition_data=user_df
#     )
#     all_scores = calculator.calculate_scores()

#     new_foods = user_df[user_df["food_group_cname"] == "custom"]

#     # Handle custom food categories if provided
#     if food_category is not None and new_foods.shape[0] > 0:
#         food_quantities = calculator.get_food_quantities()
#         for category in food_category.keys():
#             if food_category[category] or food_category[category] == 1:

#                 new_foods_category_quantity = calculator.calculate_quantity(
#                     new_foods, category
#                 )
#                 print("new_foods_category_quantity", new_foods_category_quantity)
#                 print(
#                     "food_quantities for category", category, food_quantities[category]
#                 )
#                 food_quantities[category] = (
#                     food_quantities[category] + new_foods_category_quantity
#                 )
#                 calculator.modify_food_quantity(category, food_quantities[category])
#         all_scores = calculator.calculate_scores()

#     return all_scores

def plot_macronutrient_and_energy(user_language, user_df, figsize=(12, 6), ax=None, panel_label=None):

    GUIDELINES = {
        'protein': {'min': 10, 'max': 35, 'name': 'Protein'},
        'carbs': {'min': 45, 'max': 60, 'name': 'Carbohydrates'},
        'fat': {'min': 20, 'max': 35, 'name': 'Fat'}
    }

    plot_data = user_df.groupby("eaten_date").sum(numeric_only=True).reset_index()
    plot_data["carbohydrates_kcal"] = plot_data["carbohydrates"] * 4
    plot_data["fat_kcal"] = plot_data["fat"] * 9
    plot_data["protein_kcal"] = plot_data["protein"] * 4

    plot_data["total_macro_kcal"] = (
        plot_data["carbohydrates_kcal"] + plot_data["fat_kcal"] + plot_data["protein_kcal"]
    )
    plot_data["carbs_pct"] = (plot_data["carbohydrates_kcal"] / plot_data["total_macro_kcal"]) * 100
    plot_data["fat_pct"] = (plot_data["fat_kcal"] / plot_data["total_macro_kcal"]) * 100
    plot_data["protein_pct"] = (plot_data["protein_kcal"] / plot_data["total_macro_kcal"]) * 100

    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    colors = {
        'carbohydrates_kcal': '#4A90E2',
        'fat_kcal': '#F5A623',
        'protein_kcal': '#E94B3C'
    }

    sns.barplot(
        x="eaten_date",
        y="carbohydrates_kcal",
        data=plot_data,
        color=colors['carbohydrates_kcal'],
        label=f"{get_localized_summary_element('panel_a.legend-carbs', user_language)} (kcal)",
        ax=ax, alpha=0.8, edgecolor='white', linewidth=0.5
    )
    sns.barplot(
        x="eaten_date",
        y="fat_kcal",
        data=plot_data,
        color=colors['fat_kcal'],
        label=f"{get_localized_summary_element('panel_a.legend-fat', user_language)} (kcal)",
        bottom=plot_data["carbohydrates_kcal"],
        ax=ax, alpha=0.8, edgecolor='white', linewidth=0.5
    )
    sns.barplot(
        x="eaten_date",
        y="protein_kcal",
        data=plot_data,
        color=colors['protein_kcal'],
        label=f"{get_localized_summary_element('panel_a.legend-protein', user_language)} (kcal)",
        bottom=plot_data["carbohydrates_kcal"] + plot_data["fat_kcal"],
        ax=ax, alpha=0.8, edgecolor='white', linewidth=0.5
    )

    total_energy_color = "#7B68EE"
    ax.plot(
        range(len(plot_data)),
        plot_data["energy_kcal"],
        color=total_energy_color,
        marker="o",
        linestyle="-",
        linewidth=2.5,
        markersize=6,
        label=f"{get_localized_summary_element('panel_a.legend-energy', user_language)} (kcal)",
        markerfacecolor='white',
        markeredgecolor=total_energy_color,
        markeredgewidth=2
    )

    avg_carbs_pct = plot_data["carbs_pct"].mean()
    avg_fat_pct = plot_data["fat_pct"].mean()
    avg_protein_pct = plot_data["protein_pct"].mean()

    def check_guidelines(pct, macro_type):
        guidelines = GUIDELINES[macro_type]
        if pct < guidelines['min']:
            return 'low', f"below {guidelines['min']}%"
        elif pct > guidelines['max']:
            return 'high', f"above {guidelines['max']}%"
        else:
            return 'good', f"within {guidelines['min']}-{guidelines['max']}%"

    def get_status_color(status):
        return {'good': '#28a745', 'low': '#ffc107', 'high': '#dc3545'}[status]
    

    # Title for the info box (move to top right)
    ax.text(
        1.15, 0.98, get_localized_summary_element("panel_a.avg-macros", user_language), 
        transform=ax.transAxes, fontsize=8, fontweight='bold',
        verticalalignment='top', horizontalalignment='right'
    )

    macros_display = [
        ("panel_a.legend-protein", avg_protein_pct, "protein", colors['protein_kcal']),
        ("panel_a.legend-fat", avg_fat_pct, "fat", colors['fat_kcal']),
        ("panel_a.legend-carbs-short", avg_carbs_pct, "carbs", colors['carbohydrates_kcal'])
    ]

    base_y = 0.92
    y_step = 0.06

    for i, (label, avg_pct, macro_key, color) in enumerate(macros_display):
        status, msg = check_guidelines(avg_pct, macro_key)
        y_pos = base_y - i * y_step

        # Colored circle indicator (move to right)
        ax.scatter(0.97, y_pos, s=30, color=color, alpha=0.9, 
                   transform=ax.transAxes, zorder=10)

        # Name and percentage (move to right)
        ax.text(1.15, y_pos, f"{get_localized_summary_element(label, user_language)}: {avg_pct:.0f}%", 
                transform=ax.transAxes, fontsize=8, fontweight='medium',
                color=get_status_color(status),
                verticalalignment='center', horizontalalignment='right')

        # Guidelines range (move to right, smaller font)
        ax.text(1.25, y_pos, f"({GUIDELINES[macro_key]['min']}-{GUIDELINES[macro_key]['max']}%)", 
                transform=ax.transAxes, fontsize=7, color='gray',
                verticalalignment='center', horizontalalignment='right')

    # Lower the legend position to avoid overlap with title
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.075),
              frameon=True, fancybox=True, shadow=True,
              facecolor='white', edgecolor='lightgray')

    ax.set_ylabel(get_localized_summary_element("panel_a.y-axis", user_language), fontsize=11, fontweight='medium')
    ax.set_title(get_localized_summary_element("panel_a.panel-title", user_language),
                 fontsize=13, fontweight='bold', pad=20)

    formatted_labels = []
    for date_str in plot_data["eaten_date"]:
        date_obj = pd.to_datetime(date_str) if isinstance(date_str, str) else date_str
        month_key = f"months.{date_obj.month:02d}"
        month_name = get_localized_summary_element(month_key, user_language)
        formatted_labels.append(f"{month_name} {date_obj.day:02d}")

    ax.set_xticks(range(len(plot_data)))
    ax.set_xticklabels(formatted_labels, rotation=45, ha="right")
    ax.set_xlabel(get_localized_summary_element("panel_a.x-axis", user_language))

    if panel_label:
        ax.text(
            -0.2,
            1.15,
            panel_label,
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7)
        )

    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    sns.despine(right=True, top=True)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)

    plt.tight_layout()

    macros_display = [
        ("Protein", avg_protein_pct, "protein", colors['protein_kcal']),
        ("Fat", avg_fat_pct, "fat", colors['fat_kcal']),
        ("Carbs", avg_carbs_pct, "carbs", colors['carbohydrates_kcal'])
    ]

    energy_percentages = {}

    for i, (label, avg_pct, macro_key, color) in enumerate(macros_display):
        energy_percentages[label] = (avg_pct,f"({GUIDELINES[macro_key]['min']}-{GUIDELINES[macro_key]['max']}%)")

    return ax, energy_percentages, plot_data




def plot_eaten_hour_distribution(user_language,df_food, ax=None, panel_label=None, color="#4A90E2"):
    """
    Plot the distribution of meal times by hour of day as a radial plot,
    styled to match the macronutrient and meal period plots.
    """

    df = df_food.copy()
    # Ensure local_time is datetime and extract hour
    df["local_time"] = pd.to_datetime(df["local_time"])
    df["eaten_hour"] = df["local_time"].dt.hour

    # Count occurrences for each hour (0-23)
    all_hours = pd.Series(0, index=range(24))
    hour_counts = df["eaten_hour"].value_counts()
    all_hours.update(hour_counts)
    all_hours = all_hours.sort_index()

    # Angles for each hour
    theta = np.linspace(0, 2 * np.pi, 24, endpoint=False)

    # Create polar plot if needed
    if ax is None:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.add_subplot(111, polar=True)

    # Improved bar styling matching other functions
    bars = ax.bar(
        theta,
        all_hours.values,
        width=2 * np.pi / 24,
        alpha=0.8,
        color=color,
        edgecolor='white',
        linewidth=0.5
    )

    # Add value labels at the end of each bar with improved styling
    #for i, bar in enumerate(bars):
    #    if bar.get_height() > 0:
    #        ax.text(
    #            bar.get_x() + bar.get_width() / 2,
    #            bar.get_height() + max(all_hours.values) * 0.05,  # Better relative positioning
    #            f"{int(bar.get_height())}",
    #            ha="center",
    #            va="bottom",
    #            fontsize=9,
    #            fontweight='medium',
    #            color="#333333"
    #        )

    # Set zero hour to top and clockwise
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    # Set hour labels with improved styling
    ax.set_xticks(theta)
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], fontsize=10)

    # Improved radial tick styling
    ax.tick_params(axis='y', labelsize=9, colors='#666666')
    
    # Set radial label position to avoid overlap
    ax.set_rlabel_position(45)

    # Title styling matching other functions
    ax.set_title(
        get_localized_summary_element("panel_c.panel-title",user_language),
        fontsize=13,
        fontweight='bold',
        pad=20
    )

    # Improved grid matching other functions
    ax.grid(True, linestyle="-", alpha=0.3, linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Style the radial grid lines
    ax.yaxis.grid(True, linestyle="-", alpha=0.3, linewidth=0.5)
    ax.xaxis.grid(True, linestyle="-", alpha=0.3, linewidth=0.5)

    # Clean up spines for better appearance
    ax.spines["polar"].set_linewidth(0.8)
    ax.spines["polar"].set_alpha(0.3)

    # Panel label with styling matching other functions
    if panel_label:
        ax.text(
            -0.4,
            1.15,
            panel_label,
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7)
        )

    # Add a subtle background circle for better visual appeal
    circle = plt.Circle((0, 0), max(all_hours.values) * 1.1, 
                       transform=ax.transData._b, 
                       fill=False, edgecolor='lightgray', 
                       linewidth=1, alpha=0.3, zorder=0)
    
    plt.tight_layout()
    return ax, all_hours


def plot_meal_size_vs_time_correlation(
    user_language, df, ax=None, figsize=(6, 4), panel_label=None, size_metric='energy_kcal'
):
    """
    Plot meal size vs time correlation showing eating patterns throughout the day.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Aggregated user data with meal periods, eaten_hour, and size metrics
    ax : matplotlib.axes, optional
        Axes to plot on
    figsize : tuple, optional
        Figure size if creating new plot
    panel_label : str, optional
        Text to display at the top left of the plot
    size_metric : str, optional
        Column name to use for meal size ('energy_kcal' or 'consumed_quantity')
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Prepare the data
    plot_data = df.copy()
    
    # Ensure we have the required columns
    if size_metric not in plot_data.columns:
        print(f"Warning: {size_metric} not found, using 'consumed_quantity'")
        size_metric = 'consumed_quantity'
    
    # Remove any rows with missing data
    plot_data = plot_data.dropna(subset=['eaten_time', size_metric, 'meal_period'])
    plot_data['eaten_time'] = plot_data['eaten_time'].apply(
    lambda t: t.hour + t.minute / 60 + t.second / 3600 if isinstance(t, datetime.time) else t
        )
    
    # Define colors for each meal period (matching your existing palette)
    meal_colors = {
        'Breakfast': "#1BA043",     # Professional blue
        'Lunch': "#DFCF40",        # Warm amber  
        'Dinner': "#8A5423",       # Vibrant red
        'Snack': '#7B68EE',        # Medium slate blue
        'Late Night': '#9B59B6'    # Purple
    }
    
    # Define meal period order for legend
    meal_period_order = ["Breakfast", "Lunch", "Dinner", "Snack", "Late Night"]
    
    # Create scatter plot for each meal period
    for meal_period in meal_period_order:
        meal_data = plot_data[plot_data['meal_period'] == meal_period]
        
        if len(meal_data) > 0:
            ax.scatter(
                meal_data['eaten_time'],
                meal_data[size_metric],
                c=meal_colors.get(meal_period, '#666666'),
                label=get_localized_summary_element(f"panel_d.{meal_period}",user_language),
                alpha=0.7,
                s=60,
                edgecolors='white',
                linewidth=0.5
            )
    
    # Add trend line to show overall pattern
    if len(plot_data) >= 2:
        # Calculate polynomial fit (degree 2 for gentle curve)
        coeffs = np.polyfit(plot_data['eaten_time'], plot_data[size_metric], 5)
        trend_line = np.poly1d(coeffs)
        
        # Create smooth line
        x_smooth = np.linspace(plot_data['eaten_time'].min(), 
                              plot_data['eaten_time'].max(), 100)
        y_smooth = trend_line(x_smooth)
        
        ax.plot(x_smooth, y_smooth, '--', color='#333333', alpha=0.6, 
                linewidth=2, label=get_localized_summary_element("panel_d.trend",user_language))
    
    # Customize the plot
    ax.set_xlabel(get_localized_summary_element("panel_d.x-axis",user_language), fontsize=11, fontweight='medium')
    
    # Set appropriate y-label based on metric
    if size_metric == 'energy_kcal':
        ax.set_ylabel(get_localized_summary_element("panel_d.y-axis-kcal",user_language), fontsize=11, fontweight='medium')
        title_suffix = get_localized_summary_element("panel_d.kcal-title-suffix",user_language)
    else:
        ax.set_ylabel(get_localized_summary_element("panel_d.y-axis-grams",user_language), fontsize=11, fontweight='medium')
        title_suffix = get_localized_summary_element("panel_d.grams-title-suffix",user_language)
    
    ax.set_title(f'{get_localized_summary_element("panel_d.panel-title",user_language)} - {title_suffix}', 
                fontsize=13, fontweight='bold', pad=20)
    
    # Set x-axis to show all hours with nice formatting
    ax.set_xlim(-0.5, 23.5)
    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 3)], 
                       fontsize=10)
    
    # Ensure y-axis starts at 0 for better interpretation
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(0, y_max * 1.05)
    
    # Add legend with improved styling
    ax.legend(loc='upper left', frameon=True, fancybox=True,
              shadow=True, facecolor='white', edgecolor='lightgray',
              fontsize=10, ncol=2 if len(meal_period_order) > 3 else 1)
    
    # Add statistical information box
    avg_size = plot_data[size_metric].mean()
    max_size = plot_data[size_metric].max()
    peak_hour = plot_data.loc[plot_data[size_metric].idxmax(), 'eaten_hour']
    #
    #unit = 'kcal' if size_metric == 'energy_kcal' else 'g'
    #stats_text = f'Avg meal size: {avg_size:.0f} {unit}\nLargest meal: {max_size:.0f} {unit} at {peak_hour:02.0f}:00'
    
    #props = dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9,
    #            edgecolor='lightgray', linewidth=1)
    #ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
    #        fontsize=9, verticalalignment="top", horizontalalignment="left",
    #        bbox=props, fontweight='medium')
    
    # Add subtle background shading for typical meal times
    meal_time_ranges = {
        'Breakfast': (4, 11, '#1BA043'),
        'Lunch': (11, 15, '#DFCF40'), 
        'Dinner': (18, 23, '#8A5423')
    }
    
    for meal_name, (start, end, color) in meal_time_ranges.items():
        ax.axvspan(start, end, alpha=0.1, color=color, zorder=0)
    
    # Improved grid styling
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    
    # Improve tick styling
    ax.tick_params(axis='both', labelsize=10)
    
    # Panel label with styling matching other functions
    if panel_label:
        ax.text(
            -0.1,
            1.15,
            panel_label,
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7)
        )
    
    # Improve layout spacing
    plt.tight_layout()
    
    # Return summary statistics for text generation
    summary_stats = {
        'average_meal_size': avg_size,
        'largest_meal_size': max_size,
        'peak_eating_hour': peak_hour,
        'total_meals': len(plot_data),
        'meal_period_distribution': plot_data['meal_period'].value_counts().to_dict(),
        'hourly_average': plot_data.groupby('eaten_hour')[size_metric].mean().to_dict()
    }
    
    return ax, summary_stats





#def plot_eaten_amount_distribution(
#    df, ax=None, figsize=(6, 4), color="steelblue", panel_label=None
#):
#    """
#    Plot the distribution of eaten counts by meal period.
#    """
#
#    # Create a figure if ax is not provided
#    if ax is None:
#        fig = plt.figure(figsize=figsize)
#        ax = fig.add_subplot(111)
#
#    # Define the order of meal periods
#    meal_period_order = ["Breakfast", "Lunch", "Dinner", "Snack", "Late Night"]
#
#    # Create a Series with all meal periods and fill with zeros for missing meal periods
#    all_meal_periods = pd.Series(0, index=meal_period_order)
#
#    # Count the occurrences of each meal period in the DataFrame
#    period_counts = df["meal_period"].value_counts()
#
#    # Update the counts for meal periods that exist in the data
#    all_meal_periods.update(period_counts)
#
#    # Use the predefined order instead of sorting alphabetically
#    all_meal_periods = all_meal_periods[meal_period_order]
#
#    # Plot the bars
#    bars = ax.bar(
#        all_meal_periods.index,
#        all_meal_periods.values,
#        alpha=0.7,
#        width=0.5,
#        color=color,
#    )
#
#    # Add values on top of bars
#    for bar in bars:
#        height = bar.get_height()
#        ax.text(
#            bar.get_x() + bar.get_width() / 2.0,
#            height + 0.1,
#            f"{int(height)}",
#            ha="center",
#            va="bottom",
#        )
#
#    ax.set_title("Distribution of Eaten counts by Meal Period")
#
#    # Add labels
#    ax.set_xlabel("Meal Period")
#    ax.set_ylabel("Count")
#
#    # Add grid
#    ax.grid(True, axis="y", linestyle="--", alpha=0.7)
#
#    if ax.get_figure() is not None:
#        plt.tight_layout()
#
#    if panel_label:
#        ax.text(
#            -0.1,
#            1.1,
#            panel_label,
#            transform=ax.transAxes,
#            fontsize=12,
#            fontweight="bold",
#            va="top",
#            ha="left",
#        )
#
#    return ax, all_meal_periods


def plot_macronutrients_by_meal_period(user_language, user_df_agg, ax=None, panel_label=None):
    """
    Plot average macronutrient energy intake (in kcal) by meal period as horizontal bars.

    Parameters:
    -----------
    user_df_agg : DataFrame
        Aggregated user data with meal periods
    ax : matplotlib.axes, optional
        Axes to plot on
    panel_label : str, optional
        Text to display at the top left of the plot
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))


    # Get mean macronutrient grams per meal period
    meal_data = user_df_agg.groupby("meal_period").mean(numeric_only=True)[
        ["carbohydrates", "fat", "protein"]
    ]

    # Convert grams to kcal
    meal_data["carbohydrates"] *= 4
    meal_data["fat"] *= 9
    meal_data["protein"] *= 4

    # Rename columns to reflect kcal
    meal_data.columns = [get_localized_summary_element("panel_b.legend-carbs",user_language), 
                         get_localized_summary_element("panel_b.legend-fat",user_language), 
                         get_localized_summary_element("panel_b.legend-protein",user_language)]

    # Updated meal period labels
    meal_periods_with_hours = {
        "Breakfast": get_localized_summary_element("panel_b.breakfast",user_language),
        "Lunch": get_localized_summary_element("panel_b.lunch",user_language) ,
        "Dinner": get_localized_summary_element("panel_b.dinner",user_language),
        "Late Night": get_localized_summary_element("panel_b.late-night-snack",user_language),
        "Snack": get_localized_summary_element("panel_b.snack",user_language),
    }

    plot_data = meal_data.copy()
    new_index = [
        meal_periods_with_hours.get(meal, meal) for meal in plot_data.index
    ]
    plot_data.index = new_index

    # Define colors
    colors = {
        get_localized_summary_element("panel_b.legend-carbs",user_language): '#4A90E2',
        get_localized_summary_element("panel_b.legend-fat",user_language): '#F5A623',
        get_localized_summary_element("panel_b.legend-protein",user_language): '#E94B3C'
    }

    # Plotting
    bars = plot_data.plot(
        kind="barh",
        color=[colors[col] for col in plot_data.columns],
        ax=ax,
        alpha=0.8,
        edgecolor='white',
        linewidth=0.5
    )

    # Add labels
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", fontsize=9, padding=3, fontweight='medium')

    if panel_label:
        ax.text(
            -0.2,
            1.15,
            panel_label,
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7)
        )

    ax.set_title(get_localized_summary_element("panel_b.panel-title",user_language),
                 fontsize=13, fontweight='bold', pad=20)
    ax.set_xlabel(get_localized_summary_element("panel_b.x-axis",user_language), fontsize=11, fontweight='medium')
    ax.set_ylabel("")

    ax.legend(ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, 1.07), frameon=True, fancybox=True,
              shadow=True, facecolor='white', edgecolor='lightgray',
              title_fontsize=10, fontsize=10)

    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='x')
    ax.set_axisbelow(True)

    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)

    plt.tight_layout()
    return ax, plot_data


def plot_hei_score_over_time(
    user_language,
    hei_scores_df,
    low_energy_days=None,
    column_name="total_HEI_score",
    ax=None,
    panel_label=None,
):

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))

    # Get the data series and sort by date
    data_series = hei_scores_df.T[column_name].sort_index()

    # Create the base line plot with improved styling
    line_color = "#4A90E2"  # Professional blue matching other functions
    ax.plot(
        data_series.index,
        data_series.values,
        color=line_color,
        linewidth=2.5,
        alpha=0.8,
        zorder=2,
    )

    # Add markers with different colors for weekdays and weekends
    weekday_dates = []
    weekend_dates = []
    weekday_values = []
    weekend_values = []
    
    for date, value in data_series.items():
        # Check if the date is a weekend (Saturday=5 or Sunday=6)
        is_weekend = pd.to_datetime(date).weekday() >= 5
        if is_weekend:
            weekend_dates.append(date)
            weekend_values.append(value)
        else:
            weekday_dates.append(date)
            weekday_values.append(value)

    # Plot markers in batches for better legend handling
    if weekday_dates:
        ax.scatter(
            weekday_dates,
            weekday_values,
            color="#4A90E2",  # Same blue as line
            s=80,
            zorder=3,
            label=get_localized_summary_element("panel_e.weekday",user_language),
            edgecolors='white',
            linewidth=1.5,
            alpha=0.9
        )
    
    if weekend_dates:
        ax.scatter(
            weekend_dates,
            weekend_values,
            color="#E94B3C",  # Red for weekends
            s=80,
            zorder=3,
            label=get_localized_summary_element("panel_e.weekend",user_language),
            edgecolors='white',
            linewidth=1.5,
            alpha=0.9
        )

    # Add vertical dashed lines for skipped dates (low energy days) with improved styling
    if low_energy_days is not None:
        for date in low_energy_days:
            ax.axvline(
                x=pd.to_datetime(date),
                color="#999999",
                linestyle="--",
                alpha=0.6,
                linewidth=1.5,
                zorder=1,
            )

    # Improved date formatting for x-axis
    formatted_labels = []
    tick_positions = []
    
    # Get reasonable number of ticks
    dates = pd.to_datetime(data_series.index)
    n_ticks = min(len(dates), 8)  # Limit to 8 ticks for readability
    step = max(1, len(dates) // n_ticks)
    
    for i in range(0, len(dates), step):
        tick_positions.append(dates[i])
        month_key = f"months.{dates[i].month:02d}"
        month_name = get_localized_summary_element(month_key, user_language)
        day = dates[i].day
        formatted_labels.append(f"{month_name} {day}")
    
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(formatted_labels, rotation=35, ha="right", fontsize=10)

    # Improved axis styling
    ax.set_xlabel(get_localized_summary_element("panel_e.x-axis",user_language), fontsize=11, fontweight='medium')
    ax.set_ylabel(get_localized_summary_element("panel_e.y-axis",user_language), fontsize=11, fontweight='medium')

    # Set y-axis range from 0 to 100 with better ticks
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 20))
    ax.tick_params(axis='y', labelsize=10)
    ax.tick_params(axis='x', labelsize=10)

    # Improved title
    ax.set_title(get_localized_summary_element("panel_e.panel-title",user_language), 
                fontsize=13, fontweight='bold', pad=20)

    # Add legend with improved styling
    if len(weekday_dates) > 0 or len(weekend_dates) > 0:
        ax.legend(loc="upper right", frameon=True, fancybox=True, 
                 shadow=True, facecolor='white', edgecolor='lightgray',
                 fontsize=10)

    # Improved textbox with information about skipped days and average score
    num_skipped_days = 0 if low_energy_days is None else len(low_energy_days)
    avg_score = data_series.mean()
    if low_energy_days is not None:
        textstr = f"{get_localized_summary_element('panel_e.days-skipped',user_language)}: {num_skipped_days}\n {get_localized_summary_element('panel_e.avg-hei-score',user_language)}: {avg_score:.1f}/100"
    else:
        textstr = f"{get_localized_summary_element('panel_e.avg-hei-score',user_language)}: {avg_score:.1f}/100"
    
    props = dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, 
                edgecolor='lightgray', linewidth=1)
    ax.text(
        0.02,
        0.98,
        textstr,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=props,
        fontweight='medium'
    )

    # Improved grid styling matching other functions
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)

    # Panel label with styling matching other functions
    if panel_label:
        ax.text(
            -0.1,
            1.15,
            panel_label,
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7)
        )

    # Improve layout spacing
    plt.tight_layout()

    return ax, data_series


def plot_hei_components_heatmap(
    user_language,
    hei_scores_df,
    ax1=None,
    ax2=None,
    figsize=(10, 4),
    panel_label=None,
):
    """
    Plot a heatmap of HEI component scores split into two panels.

    Parameters:
    -----------
    hei_scores_df : pandas.DataFrame
        DataFrame containing HEI component scores
    ax1 : matplotlib.axes.Axes, optional
        Axes object for the first heatmap. If None, new figure and axes are created.
    ax2 : matplotlib.axes.Axes, optional
        Axes object for the second heatmap. If None, new figure and axes are created.
    figsize : tuple, optional
        Figure size (width, height) in inches, default is (10, 4).
        Only used if ax1 and ax2 are None.

    Returns:
    --------
    fig : matplotlib figure or None if axes were provided
    """
    if ax1 is None and ax2 is None:
        fig, ax = plt.subplots(ncols=2, figsize=figsize, gridspec_kw={'wspace': 0.3})
        ax1, ax2 = ax[0], ax[1]
        return_fig = fig
    else:
        # Get the figure from one of the provided axes
        return_fig = None

    # First panel - fruits, vegetables, and proteins
    plot_data_1 = hei_scores_df[
        hei_scores_df.index.isin(
            [
                "total_fruits",
                "whole_fruits",
                "total_vegetables",
                "greens_and_beans",
                "protein_foods",
                "seafood_plant_proteins",
            ]
        )
    ]

    plot_data_2 = hei_scores_df[
        hei_scores_df.index.isin(
            [
                "whole_grains",
                "dairy",
                "fatty_acids",
                "saturated_fats",
                "refined_grains",
                "sodium",
                "added_sugars",
            ]
        )
    ]

    # Improved heatmap styling for first panel
    im1 = sns.heatmap(
        plot_data_1,
        linewidths=0.8,
        linecolor='white',
        cmap="RdYlGn",
        alpha=0.9,
        ax=ax1,
        cbar_kws={
            "label": get_localized_summary_element("panel_f1.scale",user_language),
            "shrink": 0.8,
            "aspect": 20,
            "pad": 0.02
        },
        square=False,
        xticklabels=True,
        yticklabels=True
    )
    # Style the first panel
    #ax1.set_title("Adequacy Components", fontsize=12, fontweight='bold', pad=15)
    
    # Format x-axis labels for dates
    import pandas as pd
    x_labels = plot_data_1.columns
    formatted_x_labels = []
    for label in x_labels:
        try:
            date_obj = pd.to_datetime(label)
            month_key = f"months.{date_obj.month:02d}"
            month_name = get_localized_summary_element(month_key, user_language)
            formatted_x_labels.append(f"{month_name} {date_obj.day}")
        except:
            formatted_x_labels.append(str(label))
    
    ax1.set_xticklabels(formatted_x_labels, rotation=35, ha='right', fontsize=9)
    
    # Format y-axis labels
    
    y_labels_1 = [get_localized_summary_element(f'panel_f_1.{label}',user_language) for label in plot_data_1.index]
    ax1.set_yticklabels(y_labels_1, rotation=0, fontsize=10, va='center')
    ax1.set_ylabel(get_localized_summary_element("panel_f_1.y-axis",user_language), fontsize=10, fontweight='medium')

    # Style colorbar for first panel
    cbar1 = ax1.collections[0].colorbar
    cbar1.ax.tick_params(labelsize=9)
    cbar1.set_label(get_localized_summary_element("panel_f_1.scale",user_language), fontsize=10, fontweight='medium')

    ax1.set_title(get_localized_summary_element("panel_f_1.panel-title",user_language), 
                fontsize=13, fontweight='bold', pad=20)

    # Improved heatmap styling for second panel
    im2 = sns.heatmap(
        plot_data_2,
        linewidths=0.8,
        linecolor='white',
        cmap="RdYlGn",
        alpha=0.9,
        ax=ax2,
        cbar_kws={
            "label": get_localized_summary_element("panel_f_2.scale",user_language),
            "shrink": 0.8,
            "aspect": 20,
            "pad": 0.02
        },
        square=False,
        xticklabels=True,
        yticklabels=True
    )

    # Style the second panel
    #ax2.set_title("Moderation Components", fontsize=12, fontweight='bold', pad=15)
    
    # Format x-axis labels for second panel
    x_labels_2 = plot_data_2.columns
    formatted_x_labels_2 = []
    for label in x_labels_2:
        try:
            date_obj = pd.to_datetime(label)
            month_key = f"months.{date_obj.month:02d}"
            month_name = get_localized_summary_element(month_key, user_language)
            formatted_x_labels_2.append(f"{month_name} {date_obj.day}")
        except:
            formatted_x_labels_2.append(str(label))

    
    ax2.set_xticklabels(formatted_x_labels_2, rotation=35, ha='right', fontsize=9)
    
    # Format y-axis labels for second panel
    y_labels_2 = [get_localized_summary_element(f'panel_f_2.{label}',user_language) for label in plot_data_2.index]
    ax2.set_yticklabels(y_labels_2, rotation=0, fontsize=10, va='center')
    ax2.set_xlabel(get_localized_summary_element("panel_f_2.x-axis",user_language), fontsize=10, fontweight='medium')
    ax2.set_ylabel(get_localized_summary_element("panel_f_2.y-axis",user_language), fontsize=10, fontweight='medium')

    # Style colorbar for second panel
    cbar2 = ax2.collections[0].colorbar
    cbar2.ax.tick_params(labelsize=9)
    cbar2.set_label(get_localized_summary_element("panel_f_2.scale",user_language), fontsize=10, fontweight='medium')

    # Add subtle borders around heatmaps
    for spine in ax1.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_edgecolor('lightgray')
    
    for spine in ax2.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_edgecolor('lightgray')

    # Panel label with styling matching other functions
    if panel_label:
        ax1.text(
            -0.25,
            1.3,
            panel_label,
            transform=ax1.transAxes,
            fontsize=14,
            fontweight="bold",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7)
        )

    # Improve layout spacing
    if return_fig:
        plt.tight_layout()

    return return_fig, plot_data_1, plot_data_2
