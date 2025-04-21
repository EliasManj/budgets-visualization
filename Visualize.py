#!/usr/bin/env python
# coding: utf-8

# In[1]:


import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import panel as pn
import hvplot.pandas
import param
from panel import Spacer
import yaml
import sqlite3
pn.extension('tabulator')
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

#calculate_compound_interest_with_monthly_addition(saved, .1, 1, 5, saved)
months = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

# In[2]:


# https://www.nerdwallet.com/calculator/compound-interest-calculator
# http://www.moneychimp.com/calculator/compound_interest_calculator.htm
def calculate_compound_interest_with_yearly_addition(P, r, n, t, M):
    """
    Calculate compound interest with yearly contributions.
    
    :param P: Initial principal amount
    :param r: Annual interest rate (decimal, so 10% = 0.10)
    :param n: Number of compounding periods per year (12 for monthly, 1 for annually)
    :param t: Time in years
    :param M: Yearly contribution amount
    :return: Total accumulated amount
    """
    # Calculate the compound interest for the principal amount
    compound_interest = P * (1 + r/n) ** (n*t)
    
    # Calculate the compound interest for the monthly additions
    compound_interest_additions = M * (((1 + r/n) ** (n*t) - 1) / (r/n))
    
    # Total accumulated amount
    total_amount = compound_interest + compound_interest_additions
    
    return total_amount

def calculate_compound_interest_with_monthly_addition(P, r, t, M):
    """
    Calculate compound interest with monthly contributions.

    :param P: Initial principal amount
    :param r: Annual interest rate (decimal, so 10% = 0.10)
    :param t: Time in years
    :param M: Monthly contribution amount
    :return: Total accumulated amount
    """
    n = 12  # Compounding periods per year (12 for monthly)
    monthly_rate = r / n  # Monthly interest rate
    
    # Calculate the compound interest for the principal amount
    compound_interest = P * (1 + monthly_rate) ** (n * t)
    
    # Calculate the compound interest for the monthly additions
    compound_interest_additions = M * (((1 + monthly_rate) ** (n * t) - 1) / monthly_rate)
    
    # Total accumulated amount
    total_amount = compound_interest + compound_interest_additions
    
    return total_amount


def fetch_data(query, db_path='db/database.db'):
    """
    Fetch data from the SQLite database and return it as a pandas DataFrame.

    :param query: SQL query to execute.
    :param db_path: Path to the SQLite database file. Default is 'database.db'.
    :return: pandas DataFrame containing the query results.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # Use pandas to execute the query and fetch the data
    df = pd.read_sql_query(query, conn)
    
    # Close the connection
    conn.close()
    
    return df


# In[3]:


df_transactions = fetch_data("SELECT * FROM transactions")
df_imports = fetch_data("SELECT * FROM imports")
df_accumulations = fetch_data("SELECT * FROM budget_accumulations")
df_transactions = df_transactions.sort_values(by='tag')
df_transactions['date'] = pd.to_datetime(df_transactions['date'], format='%Y-%m-%d', errors='coerce')
df_imports['date'] = pd.to_datetime(df_imports['date'], format='%Y-%m-%d', errors='coerce')
df_accumulations['date'] = pd.to_datetime(df_accumulations['date'], format='%Y-%m-%d', errors='coerce')

with open('budgets.yaml', 'r') as file:
    yaml_data = yaml.safe_load(file)

budget_df = pd.DataFrame(yaml_data['budgets'])
total_budget_per_month = budget_df['amount'].sum()
total_expenses_per_month = budget_df[ budget_df['category'] == 'Expense' ]['amount'].sum()
total_investments_per_month = budget_df[ budget_df['category'] != 'Expense' ]['amount'].sum()
budget_df.columns = ['tag','category','budget']


# In[4]:


start_date = pd.Timestamp('2024-01-01')
tags = list(budget_df['tag'])
sort_direction = ['Ascending', 'Descending']
drop_columns = ['slider_value']

def date_to_slider_value(date):
    return date.month

df_transactions['slider_value'] = df_transactions['date'].apply(date_to_slider_value)
df_imports['slider_value'] = df_imports['date'].apply(date_to_slider_value)
df_accumulations['slider_value'] = df_accumulations['date'].apply(date_to_slider_value)

month_slider = pn.widgets.DiscreteSlider(name='Month Slider', options=months, value=1)
sort_columns = list(df_transactions.columns)

# Define year slider with a range of years
year_slider = pn.widgets.IntSlider(
    name='Year Slider', 
    start=2024,  # Adjust start year as needed
    end=2026,    # Adjust end year as needed
    value=2024   # Default value
)

df_transactions = pd.merge(df_transactions, budget_df, on='tag', how='left')
df_transactions.drop(columns=['budget'], inplace=True)
tags


# In[5]:


### Widgets
tag_check_box = pn.widgets.CheckBoxGroup(name='Tags', options=tags, value=tags)
select_all_button = pn.widgets.Button(name='Select All', button_type='primary')
clear_all_button = pn.widgets.Button(name='Clear All', button_type='warning')

def select_all(event):
    tag_check_box.value = tags  

def clear_all(event):
    tag_check_box.value = []

select_all_button.on_click(select_all)
clear_all_button.on_click(clear_all)

class FilterParams(param.Parameterized):
    year = param.Integer(default=2024, bounds=(2020, 2030)) 
    month = param.Integer(default=1, bounds=(1, 12))
    tags = param.ListSelector(default=tags)
    sort_column = param.ObjectSelector(default='date', objects=sort_columns)
    sort_order = param.Selector(default='Ascending', objects=sort_direction)

filter_params = FilterParams()

month_slider.link(filter_params, value='month')
year_slider.link(filter_params, value='year')
tag_check_box.link(filter_params, value='tags')

sort_column_selector = pn.widgets.Select(name='Sort Column', options=sort_columns, value='date')
sort_order_selector = pn.widgets.RadioBoxGroup(name='Sort Order', options=sort_direction, inline=True)

sort_column_selector.link(filter_params, value='sort_column')
sort_order_selector.link(filter_params, value='sort_order')

tag_selection_widget = pn.Column(
    pn.pane.Markdown("### Filter by Tags"),
    select_all_button, clear_all_button, tag_check_box
)

# In[6]:


PAGE_SIZE = 25

@pn.depends(filter_params.param.month, filter_params.param.tags)
def update_tag_pipeline(month, tags):
    filtered_data = df_transactions[(df_transactions['slider_value'] == month) & (df_transactions['tag'].isin(tags))]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    filtered_data = filtered_data.groupby('tag')['amount'].sum().reset_index()
    merged_df = pd.merge(filtered_data, budget_df, on='tag', how='inner')
    desired_order = ['tag', 'category', 'budget', 'amount']
    merged_df = merged_df[desired_order]
    return pn.pane.DataFrame(merged_df, sizing_mode='stretch_width', index=False)


@pn.depends(filter_params.param.month, filter_params.param.year, filter_params.param.tags, filter_params.param.sort_column, filter_params.param.sort_order)
def update_pipeline(month, year, tags, sort_column, sort_order):
    print(f'month {month}, year {year}')
    filtered_data = df_transactions[
        (df_transactions['slider_value'] == month) & 
        (df_transactions['date'].dt.year == year) & 
        (df_transactions['tag'].isin(tags))
    ]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    filtered_data = filtered_data.sort_values(by=sort_column, ascending=(sort_order == 'Ascending'))
    filtered_data['date'] = filtered_data['date'].dt.strftime('%Y-%m-%d')

    column_widths = {
        'date': 100,
        'description': 250,
        'amount': 100,
        'tag': 100,
        'card': 100,
        'category': 200
    }
    
    return pn.widgets.Tabulator(filtered_data, pagination='local', page_size=PAGE_SIZE, sizing_mode='stretch_width', show_index=False, widths=column_widths)


@pn.depends(filter_params.param.month)
def update_imports(month):
    filtered_data = df_imports[df_imports['slider_value'] == month]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    return pn.pane.DataFrame(filtered_data, sizing_mode='stretch_width', index=False)


@pn.depends(filter_params.param.month)
def update_accumulations(month):
    filtered_data = df_accumulations[df_accumulations['slider_value'] == month]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    return pn.pane.DataFrame(filtered_data, sizing_mode='stretch_width', index=False)

@pn.depends(filter_params.param.month, filter_params.param.tags)
def total_amount_display(month, tags):
    filtered_data = df_transactions[(df_transactions['slider_value'] == month) & (df_transactions['tag'].isin(tags))]
    total_expense = filtered_data[filtered_data['category'] != 'Investment']['amount'].sum()
    total_invested = filtered_data[filtered_data['category'] == 'Investment']['amount'].sum()
    total = filtered_data['amount'].sum()
    
    diff = total_expense - total_expenses_per_month
    overspent = diff if total_expense > total_expenses_per_month else 0

    income = df_imports[df_imports['slider_value'] == month]['amount'].sum()
    saved = max(0, income - total_expense)

    def with_tooltip(label, value, tooltip):
        return f'''
        <div style="font-size: 22px; margin-bottom: 6px; text-align: center;">
            <span title="{tooltip}" style="cursor: help; font-size: 20px;">❓</span> <b>{label}:</b> ${value:,.2f}
        </div>
        '''

    html_content = "".join([
        with_tooltip("Total", total, "Total amount spent and invested combined"),
        with_tooltip("Total Spent", total_expense, "Amount spent on expenses this month"),
        with_tooltip("Budget Overspent", overspent, "Amount over your monthly budget"),
        "<br>",
        with_tooltip("Total Income", income, "Total income received this month"),
        with_tooltip("Total Invested", total_invested, "Amount invested this month"),
        with_tooltip("Saved cash this month", saved, "Remaining cash after expenses"),
        with_tooltip(
            f"{total_invested:,.2f}/y for 5 years (no interest)",
            total_invested*5*12,
            "Straightforward savings without compounding"
        ),
        with_tooltip(
            f"{total_invested:,.2f}/y for 5 years at 10% compounded",
            calculate_compound_interest_with_monthly_addition(total_invested, .1, 5, total_invested),
            "Compound interest scenario for 5 years at 10% annually"
        ),
    ])

    return pn.pane.HTML(f'''
<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; width: 100%;">
    {html_content}
</div>
''', sizing_mode='stretch_both')



@pn.depends(filter_params.param.month, filter_params.param.tags)
def update_budget_usage(month, tags):
    filtered_data = df_transactions[(df_transactions['slider_value'] == month) & (df_transactions['tag'].isin(tags))]
    spending_summary = filtered_data.groupby('tag')['amount'].sum().reset_index()

    merged_data = pd.merge(spending_summary, budget_df, on='tag', how='left')
    merged_data['percentage_used'] = (merged_data['amount'] / merged_data['budget']) * 100

    bar_plot = merged_data.hvplot.bar(
        x='tag',
        y='percentage_used',
        ylim=(0, 200),
        height=400,
        width=700,
        xlabel='Tag',
        ylabel='Percentage of Budget Used (%)',
        title='Budget Usage by Tag'
    )
    return bar_plot

@pn.depends(filter_params.param.month)  # Example dependency for month; adjust as needed
def update_cetes(month):
    query = "SELECT * FROM cetes"
    cetes_data = fetch_data(query)
    return pn.pane.DataFrame(cetes_data, sizing_mode='stretch_width', index=False)

# In[7]:


custom_style_total = {'text-align': 'center', 'font-size': '30px'}
custom_style_tables = {'text-align': 'center', 'border': '1px solid black', 'box-shadow': '5px 5px 5px #bcbcbc', 'padding': '10px'}

title_data_p = pn.pane.Markdown("## Monthly Transaction Summary")
title_tag_pipeline = pn.pane.Markdown("## Transactions Grouped by Tag")
budget = f"### Budget: ${total_budget_per_month:,.2f}"
budget_expenses = f"Expenses: ${total_expenses_per_month:,.2f}"
budget_inv = f"Investments: ${total_investments_per_month:,.2f}"
budget_detail = pn.pane.Markdown(f"{budget}    {budget_expenses}    {budget_inv}\n")
budget_title = pn.pane.Markdown(f"## Budget")

image_path = "/home/eliasmanj/code/python/budgets-visualization/img/image.png"

layout_desktop = pn.GridSpec(sizing_mode='stretch_both')
layout_desktop[0:3, 0] = pn.Column(title_data_p, update_pipeline)
layout_desktop[3, 0] = pn.Column(
    pn.pane.Markdown("## CETES Data", align='center'),
    update_cetes,
    styles={'text-align': 'center', 'border': '1px solid black', 'padding': '10px'},
    sizing_mode='stretch_both'
)

layout_desktop[0:2, 1] = pn.Column(title_tag_pipeline, update_tag_pipeline, budget_detail, styles=custom_style_tables)
layout_desktop[2:4, 1] = pn.Column(
    pn.layout.VSpacer(),  # Spacer to push content down
    pn.pane.Markdown("## Budget Usage Visualization", align='center'),  # Title aligned to center
    pn.Row(  # Row for centering the plot
        pn.layout.HSpacer(),  # Spacer on the left to center horizontally
        update_budget_usage,  # The plot
        pn.layout.HSpacer()   # Spacer on the right to center horizontally
    ),
    pn.layout.VSpacer(),  # Spacer to push content up
    styles=custom_style_tables,
    sizing_mode='stretch_both'  # Ensure the entire column expands
)

layout_desktop[0:2, 2] = pn.Column("## Income", update_imports, styles=custom_style_tables)
layout_desktop[2:4, 2] = total_amount_display  # ✅ Correct

template = pn.template.FastListTemplate(
    title='Spending Dashboard',
    sidebar=[
        pn.pane.Markdown("# Transactions"),
        pn.pane.Markdown("### “You’ve learned the lessons well...”"),
        pn.pane.PNG(image_path, width=300),
        pn.pane.Markdown("## Settings"),
        pn.pane.Markdown("### Filter by Year"),
        year_slider,  # Add the year slider here
        pn.pane.Markdown("### Filter by Month"),
        month_slider,
        pn.Spacer(height=20),
        pn.pane.Markdown("### Filter by Tags"),
        tag_selection_widget,
        pn.Spacer(height=20),
        pn.pane.Markdown("### Sort by"),
        sort_column_selector,
        sort_order_selector
    ],
    main=[layout_desktop],
    theme='dark'
)


template.servable()
# panel serve Visualize.py


# In[ ]:




