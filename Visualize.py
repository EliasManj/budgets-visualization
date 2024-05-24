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
pn.extension('tabulator')


# In[2]:


def calculate_compound_interest(P, r, n, t):
    return P * (1 + r/n) ** (n*t)

def fetch_data(query):
    params = {
        "dbname": "transactions",
        "user": "root",
        "password": "secret",
        "host": "localhost",
        "port": "5432"
    }

    with psycopg2.connect(**params) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return pd.DataFrame(rows)


df_transactions = fetch_data("SELECT * FROM transactions")
df_imports = fetch_data("SELECT * FROM imports")
df_accumulations = fetch_data("SELECT * FROM budget_accumulations")

df_transactions = df_transactions.sort_values(by='tag')
df_transactions['date'] = pd.to_datetime(df_transactions['date'], format='%d-%m-%y', errors='coerce')

with open('budgets.yaml', 'r') as file:
    yaml_data = yaml.safe_load(file)

budget_df = pd.DataFrame(yaml_data['budgets'].items(), columns=['tag', 'budget'])
total_budget_per_month = budget_df['budget'].sum()


# In[3]:


start_date = pd.Timestamp('2024-01-01')
tags = list(yaml_data['budgets'].keys())
sort_direction = ['Ascending', 'Descending']
drop_columns = ['slider_value']

def date_to_slider_value(date):
    if pd.isna(date):
        return None
    return (date.year - start_date.year) * 12 + (date.month - start_date.month) + 1


df_transactions['slider_value'] = df_transactions['date'].apply(date_to_slider_value)
df_imports['slider_value'] = df_imports['date'].apply(date_to_slider_value)
df_accumulations['slider_value'] = df_accumulations['date'].apply(date_to_slider_value)

month_slider = pn.widgets.IntSlider(name='Month Slider', start=1, end=12, step=1, value=1)
sort_columns = list(df_transactions.columns)


# In[4]:


### Widgets
tag_check_box = pn.widgets.CheckBoxGroup(name='Tags', options=tags, value=tags)

class FilterParams(param.Parameterized):
    month = param.Integer(default=1, bounds=(1, 12))
    tags = param.ListSelector(default=tags)
    sort_column = param.ObjectSelector(default='date', objects=sort_columns)
    sort_order = param.Selector(default='Ascending', objects=sort_direction)

filter_params = FilterParams()

month_slider.link(filter_params, value='month')
tag_check_box.link(filter_params, value='tags')

sort_column_selector = pn.widgets.Select(name='Sort Column', options=sort_columns, value='date')
sort_order_selector = pn.widgets.RadioBoxGroup(name='Sort Order', options=sort_direction, inline=True)

sort_column_selector.link(filter_params, value='sort_column')
sort_order_selector.link(filter_params, value='sort_order')


# In[5]:


@pn.depends(filter_params.param.month, filter_params.param.tags)
def update_tag_pipeline(month, tags):
    filtered_data = df_transactions[(df_transactions['slider_value'] == month) & (df_transactions['tag'].isin(tags))]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    return pn.pane.DataFrame(filtered_data.groupby('tag')['amount'].sum().reset_index(), sizing_mode='stretch_width', index=False)


@pn.depends(filter_params.param.month, filter_params.param.tags, filter_params.param.sort_column, filter_params.param.sort_order)
def update_pipeline(month, tags, sort_column, sort_order):
    filtered_data = df_transactions[(df_transactions['slider_value'] == month) & (df_transactions['tag'].isin(tags))]
    filtered_data = filtered_data.drop(columns=drop_columns, axis=1, errors='ignore')
    filtered_data = filtered_data.sort_values(by=sort_column, ascending=(sort_order == 'Ascending'))
    return pn.pane.DataFrame(filtered_data, sizing_mode='stretch_width')


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
    total_amount = filtered_data['amount'].sum()
    diff = total_amount - total_budget_per_month
    overspent = diff if total_amount > total_budget_per_month else 0

    income = df_imports[df_imports['slider_value'] == month]['amount'].sum()
    remaining = income - total_amount

    total_spent = f"Total Spent: ${total_amount:,.2f}"
    budget_overspent = f"Budget Overspent: ${overspent:,.2f}"
    total_income = f"Total Income: ${income:,.2f}"
    remaining_text = f"Remaining: ${remaining:,.2f}"
    compounded = calculate_compound_interest(remaining, .1, 1, 5)
    compounded_text = f"Compounded for 5 years at 10% rate: ${compounded:,.2f}"

    return f"{total_spent}\n{budget_overspent}\n{total_income}\n{remaining_text}\n{compounded_text}"


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


# In[6]:


custom_style_total = {'text-align': 'center', 'font-size': '30px'}
custom_style_tables = {'text-align': 'center', 'border': '1px solid black', 'box-shadow': '5px 5px 5px #bcbcbc', 'padding': '10px'}

total_amount_markdown = pn.pane.Markdown(total_amount_display, sizing_mode='stretch_width', styles=custom_style_total)

title_data_p = pn.pane.Markdown("## Monthly Transaction Summary")
title_tag_pipeline = pn.pane.Markdown("## Transactions Grouped by Tag")
budget_title = pn.pane.Markdown(f"## Budget: ${total_budget_per_month:,.2f}")

image_path = "/home/emanjarrez/code/python/budgets-visualization/img/image.png"

layout = pn.GridSpec(sizing_mode='stretch_both')
layout[0:2, 0] = pn.Column(title_data_p, update_pipeline)
layout[0, 1] = pn.Column(title_tag_pipeline, update_tag_pipeline, styles=custom_style_tables)
layout[0, 2] = pn.Column(budget_title, pn.pane.DataFrame(budget_df, sizing_mode='stretch_width'), styles=custom_style_tables)
layout[1, 3] = total_amount_markdown
layout[1, 1] = pn.Column("## Budget Usage Visualization", update_budget_usage, styles=custom_style_tables)
layout[0, 3] = pn.Column("## Income", update_imports, styles=custom_style_tables)
layout[1, 2] = pn.Column("## Budget Accumulations", update_accumulations, styles=custom_style_tables)

template = pn.template.FastListTemplate(
    title='Spending Dashboard',
    sidebar=[
        pn.pane.Markdown("# Transactions of 2024"),
        pn.pane.Markdown("### “You’ve learned the lessons well. You first learned to live on less than you earn. Next you learned to seek advice from those who are competent. Lastly, you’ve learned to make gold work for you.”"),
        pn.pane.PNG(image_path, width=300),
        pn.pane.Markdown("## Settings"),
        pn.pane.Markdown("### Filter by Month"),
        month_slider,
        pn.Spacer(height=20),
        pn.pane.Markdown("### Filer by Tags"),
        tag_check_box,
        pn.Spacer(height=20),
        pn.pane.Markdown("### Sort by"),
        sort_column_selector,
        sort_order_selector
    ],
    main=[layout],
    accent_base_color="#88d8b0",
    header_background="#88d8b0"
)

template.servable()
# panel serve Visualize.py


# In[ ]:





# In[ ]:




