#!/usr/bin/env python
# coding: utf-8

# In[1]:


import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import panel as pn
import hvplot.pandas
from datetime import datetime
import param
from panel import Spacer
import yaml
import sqlite3
pn.extension('tabulator')

# imports data
from bbva import *
from amex import *
from banamex import *
from cetes import *

tooltip_css = """
<style>
.tooltip {
  position: relative;
  display: inline-block;
  cursor: help;
  font-size: 20px;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 200px;
  background-color: #333;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px;
  position: absolute;
  z-index: 999;
  bottom: 125%;
  left: 50%;
  margin-left: -100px;
  opacity: 0;
  transition: opacity 0.3s;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}
</style>
"""

pn.extension()
pn.config.raw_css.append(tooltip_css)


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

now = datetime.now()
default_month = now.month     # e.g., 4 for April
default_year = now.year       # e.g., 2025

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

def execute_sql(query, db_path='db/database.db'):
    """
    Execute a write operation (DELETE, INSERT, UPDATE, etc.) on the SQLite database.

    :param query: SQL query to execute.
    :param db_path: Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()


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

month_slider = pn.widgets.DiscreteSlider(
    name='Month Slider',
    options=months,
    value=default_month  # 👈 Set to current month
)

year_slider = pn.widgets.IntSlider(
    name='Year Slider',
    start=2024,
    end=2026,
    value=default_year   # 👈 Set to current year
)

sort_columns = list(df_transactions.columns)

df_transactions = pd.merge(df_transactions, budget_df, on='tag', how='left')
df_transactions.drop(columns=['budget'], inplace=True)
tags


# In[5]:


### Widgets
tag_check_box = pn.widgets.CheckBoxGroup(name='Tags', options=tags, value=tags)
select_all_button = pn.widgets.Button(name='Select All', button_type='primary')
clear_all_button = pn.widgets.Button(name='Clear All', button_type='warning')
refresh_buton= pn.widgets.Button(name='Refresh Data', button_type='primary')
reset_button = pn.widgets.Button(name='Reset Data', button_type='primary')

def select_all(event):
    tag_check_box.value = tags  

def clear_all(event):
    tag_check_box.value = []

def reset_all(event):
    refresh_buton.name = "⏳ Loading..."
    refresh_buton.button_type = "default"
    refresh_buton.disabled = True

    try:
        execute_sql("DELETE FROM transactions")
        execute_sql("DELETE FROM imports")
    finally:
        refresh_buton.name = "Reset Data"
        refresh_buton.button_type = "primary"
        refresh_buton.disabled = False


def refresh_data(event):
    refresh_buton.name = "⏳ Loading..."
    refresh_buton.button_type = "default"
    refresh_buton.disabled = True

    try:
        import_bbva_credit()
        import_bbva_debit()
        import_amex()
        import_banamex()
        import_cetes()
    finally:
        refresh_buton.name = "Refresh Data"
        refresh_buton.button_type = "primary"
        refresh_buton.disabled = False

select_all_button.on_click(select_all)
clear_all_button.on_click(clear_all)
refresh_buton.on_click(refresh_data)
reset_button.on_click(reset_all)

class FilterParams(param.Parameterized):
    year = param.Integer(default=default_year, bounds=(2020, 2030)) 
    month = param.Integer(default=default_month, bounds=(1, 12))
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
    select_all_button, clear_all_button, tag_check_box
)

trefresh_widget = pn.Column(
    refresh_buton, reset_button
)


# In[6]:


PAGE_SIZE = 25

@pn.depends(filter_params.param.month, filter_params.param.year, filter_params.param.tags)
def update_tag_pipeline(month, year, tags):
    filtered_data = df_transactions[
        (df_transactions['slider_value'] == month) &
        (df_transactions['date'].dt.year == year) &
        (df_transactions['tag'].isin(tags))
    ]
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


@pn.depends(filter_params.param.month, filter_params.param.year)
def update_imports(month, year):
    filtered_data = df_imports[
        (df_imports['slider_value'] == month) &
        (df_imports['date'].dt.year == year)
    ]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    return pn.pane.DataFrame(filtered_data, sizing_mode='stretch_width', index=False)

@pn.depends(filter_params.param.month, filter_params.param.year, filter_params.param.tags)
def total_amount_display(month, year, tags):
    filtered_data = df_transactions[(df_transactions['slider_value'] == month) & (df_transactions['date'].dt.year == year) & (df_transactions['tag'].isin(tags))]
    total_expense = filtered_data[filtered_data['category'] != 'Investment']['amount'].sum()
    total_invested = filtered_data[filtered_data['category'] == 'Investment']['amount'].sum()
    total = filtered_data['amount'].sum()
    
    diff = total_expense - total_expenses_per_month
    overspent = diff if total_expense > total_expenses_per_month else 0

    income = df_imports[(df_imports['slider_value'] == month) & (df_imports['date'].dt.year == year)]['amount'].sum()
    saved = income - total_expense
    bankdelta = saved
    saved = max(0, saved)

    def with_tooltip(label, value, tooltip):
        return f'''
        <div style="font-size: 22px; margin-bottom: 8px; text-align: center;">
            <span class="tooltip">❓
                <span class="tooltiptext">{tooltip}</span>
            </span>
            <b>{label}:</b> ${value:,.2f}
        </div>
        '''

    html_content = "".join([
        with_tooltip("Total", total, "Total de dinero que gastaste en gastos e inversiones"),
        with_tooltip("Total Spent", total_expense, "Total de dinero que gastaste en gastos"),
        with_tooltip("Budget Overspent", overspent, "Lo que gastaste de mas segun tu budget del mes, incluyendo inversiones"),
        "<br>",
        with_tooltip("Total Income", income, "Total de ingresos"),
        with_tooltip("Total Invested", total_invested, "Total de dinero gastado en inversiones"),
        with_tooltip("Saved cash this month", saved, "Dinero sobrante que no fue transferido a inversiones y se quedo en la cuenta bancaria"),
        with_tooltip("Remaining in bank", bankdelta, f"Ahora tienes {bankdelta:,.2f} mas o {bankdelta:,.2f} menos en tu cuenta bancaria, si tienes mas, deberias de invertirlos, si tienes menos, tu esquema de gastos/inversiones son insostenibles"),
        with_tooltip(
            f"{total_invested:,.2f}/m for 5 years (no interest)",
            total_invested*5*12,
            f"Dinero que tendrias si ahorraras {total_invested:,.2f} cada mes por 5 años"
        ),
        with_tooltip(
            f"{total_invested:,.2f}/m for 5 years at 10% compounded",
            calculate_compound_interest_with_monthly_addition(total_invested, .1, 5, total_invested),
            f"Dinero que tendrias si ahorraras {total_invested:,.2f} cada mes por 5 años invertidos en alguna inversion con tasa de %10"
        ),
        with_tooltip(
            f"{total_invested:,.2f}/m for 5 years at 20% compounded",
            calculate_compound_interest_with_monthly_addition(total_invested, .2, 5, total_invested),
            f"Dinero que tendrias si ahorraras {total_invested:,.2f} cada mes por 5 años invertidos en alguna inversion con tasa de %10"
        ),
    ])

    return pn.pane.HTML(f'''
<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; width: 100%;">
    {html_content}
</div>
''', sizing_mode='stretch_both')



@pn.depends(filter_params.param.month, filter_params.param.year, filter_params.param.tags)
def update_budget_usage(month, year, tags):
    filtered_data = df_transactions[
        (df_transactions['slider_value'] == month) & 
        (df_transactions['date'].dt.year == year) & 
        (df_transactions['tag'].isin(tags))
    ]
    spending_summary = filtered_data.groupby('tag')['amount'].sum().reset_index()

    merged_data = pd.merge(spending_summary, budget_df, on='tag', how='left')
    merged_data['percentage_used'] = (merged_data['amount'] / merged_data['budget']) * 100

    # Add a column for color: red if >100%, else blue
    merged_data['color'] = merged_data['percentage_used'].apply(lambda x: 'yellow' if x < 130 and x > 100 else 'red' if x > 100 else 'green')

    bar_plot = merged_data.hvplot.bar(
        x='tag',
        y='percentage_used',
        color='color',  # 👈 use the color column
        ylim=(0, 200),
        height=400,
        width=700,
        xlabel='Tag',
        ylabel='Percentage of Budget Used (%)',
        title='Budget Usage by Tag',
        legend=False
    )
    return bar_plot

@pn.depends(filter_params.param.month)
def update_cetes(month):
    padded_month = f"{month:02d}"
    query = f"""
        SELECT * FROM cetes
        WHERE strftime('%m', date) = '{padded_month}'
    """
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
        #pn.pane.Markdown("### “You’ve learned the lessons well...”"),
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
        sort_order_selector,
        trefresh_widget
    ],
    main=[layout_desktop],
    theme='dark'
)


template.servable()
# panel serve Visualize.py


# In[ ]:




