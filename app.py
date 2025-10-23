import dash
import gc
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL, MATCH
import pandas as pd
import numpy as np
import base64
import io
import textwrap
import re
import html as html_utils
from datetime import datetime
from io import BytesIO
import openpyxl
import json
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

# --- APPLICATION INITIALIZATION ---
# Use a Bootstrap theme for a clean layout
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# --- DATA LOADING ---
INPUT_FILE = 'dv_2020_a1.txt'

try:
    INPUT_DF = pd.read_csv(INPUT_FILE, sep=r'\s+', low_memory=False)
except FileNotFoundError:
    INPUT_DF = None
BASELINE_CACHE = {}

# --- VAT ITEM DEFINITIONS ---
# Dictionary mapping item codes to labels and baseline status
VAT_ITEM_MAP = {
    'x0111': {'label': 'Bread and cereals', 'baseline_vattable': False},
    'x0112': {'label': 'Meat', 'baseline_vattable': True},
    'x0113': {'label': 'Fish and seafood', 'baseline_vattable': True},
    'x0114': {'label': 'Milk, cheese and eggs', 'baseline_vattable': True},
    'x0115': {'label': 'Oils and fats', 'baseline_vattable': True},
    'x0116': {'label': 'Fruit', 'baseline_vattable': False},
    'x0117': {'label': 'Vegetables', 'baseline_vattable': False},
    'x0118': {'label': 'Sugar, jam, honey, chocolate', 'baseline_vattable': True},
    'x0119': {'label': 'Food products n.e.c.', 'baseline_vattable': True},
    'x0121': {'label': 'Coffee, tea and cocoa', 'baseline_vattable': True},
    'x0122': {'label': 'Mineral waters, soft drinks, juices', 'baseline_vattable': True},
    'x0211': {'label': 'Spirits', 'baseline_vattable': True},
    'x0212': {'label': 'Wine', 'baseline_vattable': True},
    'x0213': {'label': 'Beer', 'baseline_vattable': True},
    'x0230': {'label': 'Narcotics', 'baseline_vattable': True},
    'x0311': {'label': 'Clothing materials', 'baseline_vattable': True},
    'x0312': {'label': 'Garments', 'baseline_vattable': True},
    'x0313': {'label': 'Other clothing, clothing accessories', 'baseline_vattable': True},
    'x0314': {'label': 'Cleaning, repair and hire of clothing', 'baseline_vattable': True},
    'x0321': {'label': 'Shoes and other footwear', 'baseline_vattable': True},
    'x0322': {'label': 'Repair and hire of footwear', 'baseline_vattable': True},
    'x0411': {'label': 'Actual rentals paid by tenants', 'baseline_vattable': True},
    'x0412': {'label': 'Other actual rentals', 'baseline_vattable': True},
    'x0431': {'label': 'Dwelling repair and maintenance materials', 'baseline_vattable': True},
    'x0432': {'label': 'Services for dwelling repair and maintenance', 'baseline_vattable': True},
    'x0441': {'label': 'Water supply', 'baseline_vattable': True},
    'x0442': {'label': 'Refuse collection', 'baseline_vattable': True},
    'x0443': {'label': 'Sewerage collection', 'baseline_vattable': True},
    'x0444': {'label': 'Other dwelling-related services', 'baseline_vattable': True},
    'x0451': {'label': 'Electricity', 'baseline_vattable': True},
    'x0452': {'label': 'Gas', 'baseline_vattable': True},
    'x0453': {'label': 'Liquid fuels', 'baseline_vattable': True},
    'x0454': {'label': 'Solid fuels', 'baseline_vattable': True},
    'x0455': {'label': 'Heat energy', 'baseline_vattable': True},
    'x0511': {'label': 'Furniture and furnishings', 'baseline_vattable': True},
    'x0512': {'label': 'Carpets, other floor coverings', 'baseline_vattable': True},
    'x0513': {'label': 'Repair of furniture and floor coverings', 'baseline_vattable': True},
    'x0531': {'label': 'Major household appliances', 'baseline_vattable': True},
    'x0532': {'label': 'Small electric household appliances', 'baseline_vattable': True},
    'x0533': {'label': 'Repair of household appliances', 'baseline_vattable': True},
    'x0551': {'label': 'Major tools and equipment', 'baseline_vattable': True},
    'x0552': {'label': 'Small tools and misc accessories', 'baseline_vattable': True},
    'x0561': {'label': 'Non-durable household goods', 'baseline_vattable': True},
    'x0562': {'label': 'Domestic services, household services', 'baseline_vattable': True},
    'x0611': {'label': 'Pharmaceutical products', 'baseline_vattable': False},
    'x0612': {'label': 'Other medical products', 'baseline_vattable': False},
    'x0613': {'label': 'Therapeutic appliances and equipment', 'baseline_vattable': False},
    'x0621': {'label': 'Medical services', 'baseline_vattable': False},
    'x0622': {'label': 'Dental services', 'baseline_vattable': False},
    'x0623': {'label': 'Paramedical services', 'baseline_vattable': False},
    'x0711': {'label': 'Motor cars', 'baseline_vattable': True},
    'x0712': {'label': 'Motor cycles', 'baseline_vattable': True},
    'x0713': {'label': 'Bicycles', 'baseline_vattable': True},
    'x0714': {'label': 'Animal drawn vehicles', 'baseline_vattable': True},
    'x0721': {'label': 'Accessories for personal transport equipment (PTE)', 'baseline_vattable': True},
    'x0722': {'label': 'Fuels and lubricants for PTE', 'baseline_vattable': True},
    'x0723': {'label': 'Maintenance and repair of PTE', 'baseline_vattable': True},
    'x0724': {'label': 'Other services in respect of PTE', 'baseline_vattable': True},
    'x0731': {'label': 'Passenger transport by railway', 'baseline_vattable': True},
    'x0732': {'label': 'Passenger transport by road', 'baseline_vattable': True},
    'x0733': {'label': 'Passenger transport by air', 'baseline_vattable': True},
    'x0734': {'label': 'Passenger transport by water', 'baseline_vattable': True},
    'x0735': {'label': 'Combined passenger transport', 'baseline_vattable': True},
    'x0810': {'label': 'Postal services', 'baseline_vattable': True},
    'x0911': {'label': 'Equipment relating to sound and picture', 'baseline_vattable': True},
    'x0912': {'label': 'Photographic and cinematographic equipment', 'baseline_vattable': True},
    'x0921': {'label': 'Major durables for outdoor recreation', 'baseline_vattable': True},
    'x0922': {'label': 'Instruments and durables for indoor recreation', 'baseline_vattable': True},
    'x0923': {'label': 'Maintenance of other durables for recreation', 'baseline_vattable': True},
    'x0931': {'label': 'Games, toys and hobbies', 'baseline_vattable': True},
    'x0932': {'label': 'Equipment for sports and open-air recreation', 'baseline_vattable': True},
    'x0941': {'label': 'Recreational and sporting services', 'baseline_vattable': True},
    'x0951': {'label': 'Books', 'baseline_vattable': True},
    'x0960': {'label': 'Package holidays', 'baseline_vattable': True},
    'x1111': {'label': 'Restaurants and cafés', 'baseline_vattable': True},
    'x1112': {'label': 'Canteens', 'baseline_vattable': True},
    'x1211': {'label': 'Hairdressing salons and similar', 'baseline_vattable': True},
    'x1212': {'label': 'Electrical appliances for personal care', 'baseline_vattable': True},
    'x1213': {'label': 'Other products for personal care', 'baseline_vattable': True},
}

# Baseline list of vatable items, derived from the map
TOTAL_VAT_ITEMS = len(VAT_ITEM_MAP)
BASELINE_VAT_STD_RATE_ITEMS = [k for k, v in VAT_ITEM_MAP.items() if v['baseline_vattable']]


# --- BASELINE PARAMETERS (2023) ---
BASELINE_PARAMS = {
    'basic_pov_line': 120, 'upper_pov_line': 150,
    'basic_pov_line_pf': 109, 'upper_pov_line_pf': 136,
    'tscee_rate': 0.05, 'tscer_rate': 0.10, 'tva_rate': 0.16,
    'presumptive_turnover_1': 200, 'presumptive_tax_1': 0,
    'presumptive_turnover_2': 400, 'presumptive_tax_2': 12,
    'presumptive_turnover_3': 1200, 'presumptive_tax_3': 24,
    'presumptive_rate_4': 0.03,
    'pit_yse_turnover_threshold': 5000, 'pit_yag_exemption': 300,
    'pit_bracket1_thresh': 0, 'pit_bracket1_rate': 0.0,
    'pit_bracket2_thresh': 500, 'pit_bracket2_rate': 0.05,
    'pit_bracket3_thresh': 1000, 'pit_bracket3_rate': 0.10,
    'pit_bracket4_thresh': 1500, 'pit_bracket4_rate': 0.20,
    'pit_bracket5_thresh': 2000, 'pit_bracket5_rate': 0.25,
    'bsa_income_threshold': 441, 'bsa_1_person': 165, 'bsa_2_person': 276,
    'bsa_3_plus_person': 386, 'bsa_disabled_topup': 80,
    'senior_grant_age': 55, 'senior_grant_income_threshold': 221, 'senior_grant_amount': 76,
    'school_meal_value': 80, 'school_meal_age': 18,
    'vat_items_list': BASELINE_VAT_STD_RATE_ITEMS
}

PARAM_INPUT_META = {
    'tva_rate': {'precision': 3, 'step': 0.01},
    'tscee_rate': {'precision': 3, 'step': 0.01},
    'tscer_rate': {'precision': 3, 'step': 0.01},
    'presumptive_rate_4': {'precision': 3, 'step': 0.01},
    'pit_bracket1_rate': {'precision': 3, 'disabled': True, 'step': 0.01},
    'pit_bracket2_rate': {'precision': 3, 'step': 0.01},
    'pit_bracket3_rate': {'precision': 3, 'step': 0.01},
    'pit_bracket4_rate': {'precision': 3, 'step': 0.01},
    'pit_bracket5_rate': {'precision': 3, 'step': 0.01},
    'pit_bracket1_thresh': {'precision': 0, 'thousands': True, 'disabled': True, 'step': 1},
    'pit_bracket2_thresh': {'precision': 2, 'thousands': True, 'step': 1},
    'pit_bracket3_thresh': {'precision': 2, 'thousands': True, 'step': 1},
    'pit_bracket4_thresh': {'precision': 2, 'thousands': True, 'step': 1},
    'pit_bracket5_thresh': {'precision': 2, 'thousands': True, 'step': 1},
    'pit_yse_turnover_threshold': {'precision': 2, 'thousands': True, 'step': 1},
    'pit_yag_exemption': {'precision': 2, 'thousands': True, 'step': 1},
    'presumptive_turnover_1': {'precision': 2, 'thousands': True, 'step': 1},
    'presumptive_turnover_2': {'precision': 2, 'thousands': True, 'step': 1},
    'presumptive_turnover_3': {'precision': 2, 'thousands': True, 'step': 1},
    'presumptive_tax_2': {'precision': 2, 'thousands': True, 'step': 1},
    'presumptive_tax_3': {'precision': 2, 'thousands': True, 'step': 1},
    'bsa_income_threshold': {'precision': 2, 'thousands': True, 'step': 1},
    'bsa_1_person': {'precision': 2, 'thousands': True, 'step': 1},
    'bsa_2_person': {'precision': 2, 'thousands': True, 'step': 1},
    'bsa_3_plus_person': {'precision': 2, 'thousands': True, 'step': 1},
    'bsa_disabled_topup': {'precision': 2, 'thousands': True, 'step': 1},
    'senior_grant_age': {'precision': 0, 'thousands': False, 'force_int': True, 'step': 1},
    'senior_grant_income_threshold': {'precision': 2, 'thousands': True, 'step': 1},
    'senior_grant_amount': {'precision': 2, 'thousands': True, 'step': 1},
    'school_meal_value': {'precision': 2, 'thousands': True, 'step': 1},
}

def get_param_meta(param_id: str) -> dict:
    base_meta = {
        'precision': 2,
        'thousands': False,
        'allow_negative': False,
        'strip_trailing': True,
        'force_int': False,
        'disabled': False,
        'step': 1,
    }
    base_meta.update(PARAM_INPUT_META.get(param_id, {}))
    return base_meta

def format_param_value(param_id: str, raw_value) -> str:
    if raw_value is None or raw_value == "":
        return ""
    meta = get_param_meta(param_id)
    if isinstance(raw_value, str):
        candidate = raw_value.replace(",", "").strip()
    else:
        candidate = str(raw_value)
    try:
        numeric_value = float(candidate)
    except (TypeError, ValueError):
        return str(raw_value)
    precision = meta['precision']
    thousands = meta['thousands']
    if precision is None:
        formatted = f"{int(round(numeric_value))}"
    else:
        pattern = f"{{:,.{precision}f}}" if thousands else f"{{:.{precision}f}}"
        formatted = pattern.format(numeric_value)
        if meta['strip_trailing'] and '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
    if thousands and '.' not in formatted and precision == 0:
        formatted = f"{int(round(numeric_value)):,}"
    return formatted

def parse_param_input_value(param_id: str, value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    cleaned = value.replace(",", "").strip()
    if cleaned in {"", ".", "-"}:
        return None
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    meta = get_param_meta(param_id)
    if meta.get('force_int'):
        return int(round(parsed))
    return parsed

def create_param_input_component(param_id: str, value, disabled: bool = False):
    meta = get_param_meta(param_id)
    formatted_value = format_param_value(param_id, value)
    input_kwargs = {
        'id': {'type': 'param-input', 'index': param_id},
        'value': formatted_value,
        'type': 'text',
        'style': {'width': '100%'},
        'className': "form-control form-control-sm param-input-field",
        'inputmode': 'decimal' if meta.get('precision', 0) and meta['precision'] > 0 else 'numeric',
        'disabled': disabled or meta.get('disabled'),
    }
    input_element = dbc.Input(**input_kwargs)
    if input_kwargs['disabled']:
        return input_element

    dec_button = dbc.Button(
        "−",
        id={'type': 'param-step', 'index': param_id, 'direction': 'dec'},
        color="light",
        size="sm",
        className="param-step-btn"
    )
    inc_button = dbc.Button(
        "+",
        id={'type': 'param-step', 'index': param_id, 'direction': 'inc'},
        color="light",
        size="sm",
        className="param-step-btn"
    )

    return html.Div(
        [
            dec_button,
            input_element,
            inc_button,
        ],
        className="param-input-wrapper"
    )

# --- INFO MODAL CONTENT ---
INFO_MODAL_CONTENT = {
    'taxbenpol': {
        'title': 'About: Tax-benefit policy',
        'body': '''<p style="line-height:1.5">This tab presents an overview of government revenues and expenditures as included in the model, shown in two tables. The first table presents the yearly revenue and expenditure amounts in millions of national currency. The second table shows revenue by source and expenditure by type as shares of total revenue and expenditure (%). In addition to the baseline results, each reform scenario includes the corresponding outcomes and their absolute differences from the baseline values.</p>
<p style="line-height:1.5"><b><span style='color:#0070C0'>Sum of government revenue:</span></b> The total of direct taxes, social insurance contributions, and indirect taxes.</p>
<p style="line-height:1.5"><b><span style='color:#0070C0'>By source:</span></b> Breakdown of revenue components. This categorization is mutually exclusive.</p>
<p style="line-height:1.2; margin-left:20px;"><b>Direct taxes:</b> Taxes levied directly on income or wealth (e.g., personal income tax). Refer to income list <i>ils_tax</i> in DEVMOD.</p>
<p style="line-height:1.2; margin-left:20px;"><b>Social insurance contributions:</b> Contributions from employees, employers, and self-employed. Refer to income list <i>ils_sic</i>.</p>
<p style="line-height:1.2; margin-left:20px;"><b>Indirect taxes:</b> Taxes on goods and services (e.g., VAT and excise duties). Refer to income list <i>ils_taxco</i>.</p>
<p style="line-height:1.5"><b><span style='color:#0070C0'>Sum of government expenditure:</span></b> The total of cash benefits, in-kind benefits, and indirect subsidies.</p>
<p style="line-height:1.5"><b><span style='color:#0070C0'>By type:</span></b> Breakdown of expenditure by the type of the transfer. This categorization is mutually exclusive.</p>
<p style="line-height:1.2; margin-left:20px;"><b>Cash benefits:</b> Direct monetary transfers to households/individuals. Refer to income list <i>ils_ben</i>.</p>
<p style="line-height:1.2; margin-left:20px;"><b>In-kind benefits:</b> Benefits provided as goods or services rather than cash. Refer to income list <i>ils_benki</i>. Please note that in-kind benefits are not modelled in all countries.</p>
<p style="line-height:1.2; margin-left:20px;"><b>Indirect subsidies:</b> Subsidies that reduce the price of goods/services (e.g., fuel subsidies). Refer to income list <i>ils_benco</i>. Please note that indirect subsidies are not modelled in all countries.</p>
<p style="line-height:0.1"><b><span style='color:#ffffff'>_</span></b></p>'''
    },
    'poverty': {
        'title': 'About: Poverty',
        'body': '''<p style="line-height:1.5">This tab shows poverty rates and gaps for the total population and for individuals living in different types of households. All calculations are performed at the individual level. In addition to the baseline results, each reform scenario includes the corresponding outcomes and their absolute differences from the baseline values.</p>
      <p style="line-height:1.5"><b><span style='color:#0070C0'>Poverty rate:</span></b> An individual is defined as poor if their household’s disposable income or consumption (an equivalized value calculated for each individual) falls below the poverty line. This measure is also known as the poverty headcount ratio, or the Foster-Greer-Thorbecke (FGT) index for alpha=0, FGT(0).</p>
      <p style="line-height:1.5"><b><span style='color:#0070C0'>Poverty gap:</span></b> This measures the average intensity of poverty. For each poor individual, the distance to the poverty line is calculated as a percentage of that line. The final index is the average of these values over the entire population (both poor and non-poor). This corresponds to the Foster-Greer-Thorbecke (FGT) index for alpha=1, FGT(1).</p>
      <p style="line-height:1.5"><b><span style='color:#0070C0'>Household structure:</span></b> These categories classify households based on their composition of adults (aged 18 and over) and children (under 18):</p>
	  <p style="line-height:1.2; margin-left:20px;"><b>Single person:</b> A household with exactly one person of any age.</p>
      <p style="line-height:1.2; margin-left:20px;"><b>Single parent:</b> A household with one adult (aged 18+) and at least one child (&lt;18).</p>
      <p style="line-height:1.2; margin-left:20px;"><b>2 adults without children:</b> A household with exactly two adults and no children.</p>
      <p style="line-height:1.2; margin-left:20px;"><b>2 adults with children:</b> Households with exactly two adults, categorized by the number of children (1-2, 3-4, or 5+).</p>
      <p style="line-height:1.2; margin-left:20px;"><b>3 or more adults without children:</b> A household with three or more adults and no children.</p>
      <p style="line-height:1.2; margin-left:20px;"><b>3 or more adults with children:</b> A household with three or more adults and at least one child.</p>
      <p style="line-height:1.5"><b><span style='color:#0070C0'>Vulnerable households:</span></b> These categories identify households containing at least one member with a specific characteristic:</p>
	  <p style="line-height:1.2; margin-left:20px;"><b>Young child (aged 0-2):</b> Households with at least one child aged two or younger.</p>
      <p style="line-height:1.2; margin-left:20px;"><b>Elderly member:</b> Households with at least one member aged 65 or older.</p>
      <p style="line-height:1.2; margin-left:20px;"><b>Member with a disability:</b> Households with at least one member reported as having a disability (based on variable <i>ddi</i>).</p>
      <p style="line-height:1.2; margin-left:20px;"><b>No male adults:</b> Households without any male members aged 18 or older.</p>
      <p style="line-height:1.5"><b><span style='color:#0070C0'>Labour market status:</span></b> These categories classify households based on their connection to the labour market: </p>
      <p style="line-height:1.2; margin-left:20px;"><b>No labour market income:</b> No household member has positive labour market income (based on income list <i>ils_earns</i>).</p>
      <p style="line-height:1.2; margin-left:20px;"><b>Informal adult:</b> The household includes at least one adult member identified as an informal worker (based on variable <i>lfo</i>).</p>
      <p style="line-height:1.2; margin-left:20px;"><b>No informal adults:</b> The household does not include any adults identified as informal workers.</p>
      <p style="line-height:1.5"><b><span style='color:#0070C0'>Absolute national poverty line, yearly:</span></b> The annual poverty line used for the calculations, shown in national currency.</p>'''
    },
    'households': {
        'title': 'About: Households',
        'body': '''<p style="line-height:1.5">This tab shows counts of households, grouped by different characteristics. In addition to the baseline counts, each reform scenario includes the corresponding counts and their absolute differences from the baseline values.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Taxpayer and benefit recipient households:</span></b> This table shows the weighted number of households where at least one member pays a specific tax/contribution or receives a specific benefit. Please note that in-kind benefits and indirect subsidies are not modelled in all countries.</p>
	      <p style="line-height:1.5"><b><span style='color:#0070C0'>Household categories:</span></b> This table shows the total number of households for various demographic and economic subgroups. These categories classify households by their structure of adults (18+), children (&lt;18), and other characteristics; see the "Poverty" tab description for full details. Please note that the sum of the categories under "Household structure" may not equal the total if the dataset contains multi-person households composed exclusively of children (persons under 18), as this rare household type is not separately categorized.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Household decile distribution:</span></b> This table shows the number of households in each decile. These deciles are calculated at the household level, meaning the population of households (not individuals) has been ranked and divided into ten equal-sized groups based on the selected income/consumption concept. The user's selection of "Distribution statistics" (consumption-based or income-based, and whether net of indirect taxes/benefits) determines the underlying ranking variable used for forming deciles. In the case of income-based results, deciles and decile-specific outcomes need to be carefully interpreted for countries where more than 10% of the households has zero income; those households will all be grouped in the bottom decile in that case.</p>'''
    },
    'individuals': {
        'title': 'About: Individuals',
        'body': '''<p style="line-height:1.5">This tab shows counts of individuals, grouped by different characteristics. In addition to the baseline counts, each reform scenario includes the corresponding counts and their absolute differences from the baseline values.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Taxpayer and benefit recipient individuals:</span></b> This table shows the weighted number of individuals who pay a specific tax/contribution or receive a specific benefit. For taxes/benefits that are recorded at the household level, only the household head will be counted as an individual payer/recipient for that specific item. Please note that in-kind benefits and indirect subsidies are not modelled in all countries.</p>
	      <p style="line-height:1.5"><b><span style='color:#0070C0'>Household categories:</span></b> This table shows the total number of individuals living in households with the specified demographic and economic characteristics; see the "Poverty" tab description for full details. Please note that the sum of the categories under "Household structure" may not equal the total if the dataset contains multi-person households composed exclusively of children (persons under 18), as this rare household type is not separately categorized.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Individual decile distribution:</span></b> This table shows the number of individuals in each decile. Deciles are calculated at the individual level by ranking all persons based on their household's equivalised disposable income or consumption. The user's selection of "Distribution statistics" (consumption-based or income-based, and whether net of indirect taxes/benefits) determines the underlying ranking variable used for forming deciles. In the case of income-based results, deciles and decile-specific outcomes need to be carefully interpreted for countries where more than 10% of the population has zero income; those individuals will all be grouped in the bottom decile in that case.</p>'''
    },
    'inequality': {
        'title': 'About: Inequality',
        'body': '''<p style="line-height:1.5">This tab shows measures of inequality and the distribution of household resources. All distributional statistics (e.g., percentiles) are calculated by ranking all individuals according to their household's equivalised disposable income or consumption possibilities (based on the user's selection). In addition to the baseline results, each reform scenario includes the corresponding outcomes and their absolute differences from the baseline values.</p>
	  
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Inequality indices:</span></b> The Gini and Atkinson indices measure inequality on a scale from 0 (perfect equality) to 100 (perfect inequality). The P80/P20 and mean/median ratios compare different points of the distribution.</p>
          
		  <p style="line-height:1.5"><b><span style='color:#0070C0'>Percentiles of distribution and median, yearly:</span></b> This table presents annual amounts in national currency (unless this setting is changed by the user). It shows the level of equivalised disposable income or consumption at various points (percentiles) of the distribution. For example, the 10th percentile shows the level below which the poorest 10% of individuals fall. The 50th percentile represents the median. The user's selection of "Distribution statistics" (consumption-based or income-based, and whether net of indirect taxes/benefits) determines the underlying ranking variable used for forming percentiles and calculating levels.</p>
          
		  <p style="line-height:1.5"><b><span style='color:#0070C0'>Absolute national poverty line, yearly:</span></b> The annual poverty line is also shown in national currency for comparison with the percentile distribution.</p>
          
		  <p style="line-height:1.5"><b><span style='color:#0070C0'>Distribution of total income/consumption across deciles, %:</span></b> This shows the percentage of total income/consumption held by each decile (10% group) of the population. For reforms, the distribution is calculated over the deciles as defined in the baseline scenario to ensure comparability. The user's selection of "Distribution statistics" determines the underlying ranking variable used for forming deciles and calculating levels. In the case of income-based results, decile-specific outcomes need to be carefully interpreted for countries where more than 10% of the population has zero income; those individuals will all be grouped in the bottom decile in that case.</p>'''
    },
    'benefits': {
        'title': 'About: Benefits',
        'body': '''<p style="line-height:1.5">This tab shows the distribution of cash benefits (<i>ils_ben</i>) and in-kind benefits (<i>ils_benki</i>). Note that indirect subsidies are not included in this tab's results, and in-kind benefits are not modelled in all countries. In addition to the baseline results, each reform scenario includes the corresponding outcomes and their absolute differences from the baseline values.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Receipt of benefits by household type, % of households:</span></b> These tables show the percentage of households in a specific category that receive any benefit, cash benefits, or in-kind benefits. For reforms, household categories are fixed to their baseline characteristics.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Targeting of poor households, % of benefits:</span></b> These rows show what percentage of the total benefit expenditure (of a specific type) is received by households who were defined as poor in the baseline scenario.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Per-capita adequacy:</span></b> These rows show the mean yearly benefit amount per beneficiary. This amount is calculated at the individual level after equivalising the household benefit amount, making it comparable to the individual-level poverty line. It is also shown as a share of the baseline yearly median individual consumption and disposable income (before indirect taxes and benefits) in the population.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Distribution across deciles, %:</span></b> These tables show the percentage of total cash or in-kind benefits received by each decile of the population. For reforms, the distribution is calculated over the deciles as defined in the baseline scenario to ensure comparability. The user's selection of "Distribution statistics" (consumption-based or income-based, and whether net of indirect taxes/benefits) determines the underlying ranking variable used for forming deciles. In the case of income-based results, decile-specific outcomes need to be carefully interpreted for countries where more than 10% of the population has zero income; those individuals will all be grouped in the bottom decile in that case.</p>'''
    },
    'taxes': {
        'title': 'About: Taxes',
        'body': '''<p style="line-height:1.5">This tab shows the distribution of direct taxes, indirect taxes, and social contributions across different household groups and income/consumption deciles. In addition to the baseline results, each reform scenario includes the corresponding outcomes and their absolute differences from the baseline values.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Payment by household type, % of households:</span></b> These tables show what percentage of households with specific characteristics pay any amount of direct tax, indirect tax, or social contributions. "Social contributions" here refers to the sum of employee and self-employed contributions (from income lists <i>ils_sicee</i> and <i>ils_sicse</i>). For reforms, household categories are fixed to their baseline characteristics.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Effective tax rates (ETR), %:</span></b> This table shows various average effective tax rates, calculated as the total amount of taxes (and social insurance contributions, SIC) paid, divided by total original income across the entire population.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Distribution across deciles, %:</span></b> These tables show the percentage of the total tax or contribution burden that is paid by each decile of the population. For reforms, the distribution is calculated over the deciles as defined in the baseline scenario to ensure comparability. The user's selection of "Distribution statistics" (consumption-based or income-based, and whether net of indirect taxes/benefits) determines the underlying ranking variable used for forming deciles. In the case of income-based results, decile-specific outcomes need to be carefully interpreted for countries where more than 10% of the population has zero income; those individuals will all be grouped in the bottom decile in that case.</p>'''
    },
    'policy-effects': {
        'title': 'About: Policy effects',
        'body': '''<p style="line-height:1.5">This tab illustrates the redistributive impact of the tax-benefit system by comparing key poverty and inequality indicators "before" and "after" taxes and benefits. In addition to the baseline results, each reform scenario includes the corresponding outcomes and their absolute differences from the baseline values.</p>

          <p style="line-height:1.5"><b><span style='color:#0070C0'>"Before taxes and benefits" measures:</span></b></p>
          <p style="line-height:1.2; margin-left:20px;"><b>Income based distribution statistics:</b> If the user selected "Income based" or "Income based, net of indirect taxes and benefits", the measures are computed based on original market income (income list <i>ils_origy</i>) and imputed home produce (variable <i>xivot</i>, if available).</p>
          <p style="line-height:1.2; margin-left:20px;"><b>Consumption based distribution statistics:</b> If the user selected "Consumption based" or "Consumption based, net of indirect taxes and benefits", a proxy for resources available before direct taxes and cash benefits is used for computing the measures. It is calculated as <i>ils_con - ils_ben + ils_tax + ils_sicee + ils_sicse</i>.</p>
          <p style="line-height:1.2; margin-left:20px;"><b>Poverty line:</b> For all "before" poverty and poverty gap measures, the standard poverty line (variable <i>spl</i>) is used, ensuring consistency with the "before" income/consumption concepts, which are also prior to indirect fiscal effects.</p>
          <p style="line-height:1.2; margin-left:20px;"><b>Reform values:</b> For all "Before taxes and benefits" indicators shown in the reform scenario columns, the values correspond to the baseline system to keep the "Effects" comparable.</p>

          <p style="line-height:1.5"><b><span style='color:#0070C0'>"After taxes and benefits" measures:</span></b></p>
          <p style="line-height:1.2; margin-left:20px;">Indicators are calculated in the same way as on the "Poverty" and "Inequality" tabs, using the user's selected income/consumption concept.</p>

          <p style="line-height:1.5"><b><span style='color:#0070C0'>Effects of tax-benefit system:</span></b></p>
          <p style="line-height:1.2; margin-left:20px;"><b>Percentage points (pp.):</b> The absolute difference, After - Before.</p>
          <p style="line-height:1.2; margin-left:20px;"><b>Percentages (%):</b> The relative percentage change, 100 * ((After - Before) / Before).</p>'''
    },
    'gainers-losers': {
        'title': 'About: Gainers and losers',
        'body': '''<p style="line-height:1.5">This tab shows the share of individuals (as a % of the population in the respective group) who are gainers or losers due to the reform. The change is measured for individuals based on their household's equivalised disposable income or consumption relative to the baseline scenario. All groupings are based on the individual's situation in the baseline.</p>

          <p style="line-height:1.5">Only figures are displayed directly. Tables can be accessed by exporting results to Excel via the button in the top-right corner.</p>

          <p style="line-height:1.5"><b><span style='color:#0070C0'>Gainers:</span></b> Individuals whose household resources increase by more than 1% or 5% due to the reform.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Losers:</span></b> Individuals whose household resources decrease by more than 1% or 5% due to the reform.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Deciles:</span></b> Calculated at the individual level based on equivalised disposable income or consumption. In income-based runs, interpret carefully if many individuals have zero income, as they will cluster in the bottom decile.</p>
          <p style="line-height:1.5"><b><span style='color:#0070C0'>Household structure, vulnerable households, labour market status:</span></b> Groupings follow the definitions outlined in the "Poverty" tab description.</p>'''
    },
    'default': {
        'title': 'Info',
        'body': 'No information available for this tab.'
    }
}


def normalize_html_text(raw_html: str) -> str:
    if not isinstance(raw_html, str):
        return ""
    cleaned_lines = [line.lstrip() for line in raw_html.splitlines()]
    cleaned = textwrap.dedent("\n".join(cleaned_lines)).strip()
    return cleaned


def html_to_plain_text(raw_html: str) -> str:
    normalized = normalize_html_text(raw_html)
    if not normalized:
        return ""
    text = re.sub(r'<\s*br\s*/?>', '\n', normalized, flags=re.IGNORECASE)
    text = re.sub(r'</p\s*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?span[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?b[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?i[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?u[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_utils.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


TABLE_HEADER_LABELS = {"By source", "By type", "By area, excl. indirect subsidies", "Household structure", "Vulnerable households", "Labour market status"}
TABLE_STRONG_LABELS = {"Sum of government revenue", "Sum of government expenditure", "All individuals"}


def strip_tags(html_text: str) -> str:
    text = re.sub(r'<[^>]+>', '', html_text)
    return html_utils.unescape(text)


def extract_description_lines(info_key: str):
    content = INFO_MODAL_CONTENT.get(info_key)
    if not content:
        return []
    body = normalize_html_text(content.get('body', ''))
    if not body:
        return []
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', body, flags=re.IGNORECASE | re.DOTALL)
    lines = []
    for para in paragraphs:
        segment = para.strip()
        if not segment:
            continue
        match = re.match(r'\s*<b>\s*<span[^>]*>(.*?)</span>\s*</b>\s*(.*)', segment, flags=re.IGNORECASE | re.DOTALL)
        if match:
            header_html = match.group(1)
            remainder_html = match.group(2)
            header_text = strip_tags(header_html).strip()
            body_text = strip_tags(remainder_html).strip()
            if header_text:
                lines.append(('header', header_text))
            if body_text:
                lines.append(('body', body_text))
        else:
            plain_text = strip_tags(segment).strip()
            if plain_text:
                lines.append(('body', plain_text))
    return lines


def ensure_input_dataframe():
    """
    Loads the input micro-data once and reuses it across requests to avoid
    repeated disk I/O on resource-constrained hosts (e.g. Render free tier).
    """
    global INPUT_DF
    if INPUT_DF is None:
        df = pd.read_csv(INPUT_FILE, sep=r'\s+', low_memory=False)
        int_cols = df.select_dtypes(include=['int64', 'int32', 'int16', 'int']).columns
        float_cols = df.select_dtypes(include=['float64']).columns

        if len(int_cols) > 0:
            df[int_cols] = df[int_cols].apply(pd.to_numeric, downcast='integer')
        if len(float_cols) > 0:
            df[float_cols] = df[float_cols].apply(pd.to_numeric, downcast='float')

        obj_cols = df.select_dtypes(include=['object']).columns
        for col in obj_cols:
            unique_values = df[col].nunique(dropna=False)
            if 0 < unique_values < 256 and unique_values / len(df) < 0.5:
                df[col] = df[col].astype('category')

        INPUT_DF = df
    return INPUT_DF


def get_baseline_artifacts(df: pd.DataFrame, analysis_choice: int):
    """
    Returns cached baseline simulation results for the selected distribution statistic.
    This prevents recomputing the heavy baseline run on every callback.
    """
    cache_key = analysis_choice
    if cache_key in BASELINE_CACHE:
        return BASELINE_CACHE[cache_key]

    baseline_sim_df = run_simulation(df, BASELINE_PARAMS)
    baseline_results, baseline_analysis_df = run_analysis(baseline_sim_df, analysis_choice)

    cols_to_keep = ['idperson', 'deciles']
    cols_to_keep.extend([col for col in baseline_analysis_df.columns if col.startswith('is') and 'HH' in col])
    baseline_merge_df = baseline_analysis_df.loc[:, cols_to_keep].copy()

    artifacts = {
        'results': baseline_results,
        'merge_df': baseline_merge_df,
    }
    BASELINE_CACHE[cache_key] = artifacts

    del baseline_sim_df, baseline_analysis_df
    gc.collect()

    return artifacts


# --- SIMULATION ENGINE ---
def run_simulation(df, params):
    sim_df = df.copy()
    
    # Ensure required identification columns are present
    required = ['idhh', 'dhh', 'idperson']
    missing = [c for c in required if c not in sim_df.columns]
    if missing:
        raise ValueError(f"Missing required id columns: {', '.join(missing)}")

    # 'ses' is no longer in this list, as we will simulate it.
    # Initialize missing columns together to keep the frame compact
    cols_to_add = {}
    for col in ['lfo', 'ddi', 'xivot', 'dec', 'ytn']:
        if col not in sim_df.columns:
            cols_to_add[col] = 0
    if cols_to_add:
        sim_df = sim_df.assign(**cols_to_add)

    # Ensure key monetary variables exist and contain no missing values
    for var in ['yem', 'yse', 'yag', 'yds', 'xhh']:
        if var not in sim_df.columns:
            sim_df[var] = 0
        else:
            sim_df[var] = sim_df[var].fillna(0)

    uprating_factors = {
        'f_CPI_Overall': 1.2092, 'f_CPI_Food': 1.1797, 'f_CPI_Non_Food': 1.2746,
        'f_CPI_Alcohol': 1.2089, 'f_CPI_Tobacco': 1.1842, 'f_CPI_Energy': 1.1275,
        'f_CPI_Earnings': 1.3197
    }

    for var in ['yem', 'yse', 'yag']:
        if var in sim_df.columns:
            sim_df[var] *= uprating_factors['f_CPI_Earnings']

    # Uprate 'yds'
    for var in ['yds','ytn']:
        if var in sim_df.columns:
            sim_df[var] *= uprating_factors['f_CPI_Overall']
            
    # Clip individual labour incomes at zero
    for col in ['yem', 'yse']:
        if col in sim_df.columns:
            sim_df[col] = sim_df[col].clip(lower=0)
    
    if 'yag' in sim_df.columns:
        yag_hh_sum = sim_df.groupby('idhh')['yag'].transform('sum')
        # If household-level YAG <= 0, set all members' yag to 0
        sim_df.loc[yag_hh_sum <= 0, 'yag'] = 0
        # Otherwise, drop only negative individual values
        sim_df.loc[sim_df['yag'] < 0, 'yag'] = 0

    # Apply category-specific uprating factors to expenditure variables
    food_vars = [
        'x0111', 'x0112', 'x0113', 'x0114', 'x0115', 'x0116', 'x0117', 'x0118', 'x0119',
        'x0121', 'x0122', 'x1111', 'x1112'
    ]
    alcohol_vars = ['x0211', 'x0212', 'x0213']
    energy_vars = ['x0451', 'x0452', 'x0453', 'x0454', 'x0455']
    non_food_vars = [
        'x0311', 'x0312', 'x0313', 'x0314', 'x0321', 'x0322', 'x0411', 'x0412',
        'x0431', 'x0432', 'x0441', 'x0442', 'x0443', 'x0444', 'x0511', 'x0512',
        'x0513', 'x0531', 'x0532', 'x0533', 'x0551', 'x0552', 'x0561', 'x0562',
        'x0611', 'x0612', 'x0613', 'x0621', 'x0622', 'x0623', 'x0711', 'x0712',
        'x0713', 'x0714', 'x0721', 'x0722', 'x0723', 'x0724', 'x0731', 'x0732',
        'x0733', 'x0734', 'x0735', 'x0810', 'x0911', 'x0912', 'x0921', 'x0922',
        'x0923', 'x0931', 'x0932', 'x0941', 'x0951', 'x0960', 'x1211', 'x1212',
        'x1213'
    ]
    # List of non-monetary 'x' vars to skip in loop
    x_skip_vars = ['xivot', 'xhh'] 

    for col in sim_df.columns:
        if col.startswith('x') and col not in x_skip_vars:
            factor = uprating_factors['f_CPI_Overall'] # Default
            if col in food_vars: 
                factor = uprating_factors['f_CPI_Food']
            elif col in alcohol_vars: 
                factor = uprating_factors['f_CPI_Alcohol']
            elif col in energy_vars: 
                factor = uprating_factors['f_CPI_Energy']
            elif col in non_food_vars:
                factor = uprating_factors['f_CPI_Non_Food']
            # Note: x0230 (Narcotics) is correctly mapped to f_CPI_Overall by default
            sim_df[col] *= factor

    # Uprate xhh (if it exists) by the overall factor
    if 'xhh' in df.columns:
        sim_df['xhh'] *= uprating_factors['f_CPI_Overall']


    # Uprate poverty lines (monthly values) and align names
    sim_df['spl'] = params['basic_pov_line'] * uprating_factors['f_CPI_Overall']
    sim_df['splpf'] = params['basic_pov_line_pf'] * uprating_factors['f_CPI_Overall']
    sim_df['spl_u'] = params['upper_pov_line'] * uprating_factors['f_CPI_Overall']
    sim_df['splpf_u'] = params['upper_pov_line_pf'] * uprating_factors['f_CPI_Overall']

    # --- Equivalence Scale (ses) Calculation ---
    # Calculate individual 'ses' based on age bins
    bins = [-np.inf, 3, 7, 12, 17, 29, 39, 59, np.inf]
    labels = [0.30, 0.50, 0.70, 0.95, 1.10, 0.95, 0.90, 0.80]
    
    # Ensure 'dag' column exists
    if 'dag' not in sim_df.columns:
        sim_df['dag'] = 0 # Default age to 0 if missing
        
    sim_df['ses_person'] = pd.cut(sim_df['dag'], bins=bins, labels=labels, right=True, ordered=False).astype(float)
    
    # Sum individual 'ses' values to get the household total
    hh_ses_total = sim_df.groupby('idhh')['ses_person'].transform('sum')
    
    # Assign this total 'ses' value *only to the household head*
    sim_df['ses'] = 0.0
    is_head = sim_df['dhh'] == 1
    sim_df.loc[is_head, 'ses'] = hh_ses_total[is_head]
    sim_df = sim_df.drop(columns=['ses_person'])
    # --- End of Equivalence Scale Calculation ---

    # Continue with simulation logic
    
    # Store uprated sums of COICOP items as a fallback consumption measure
    x_cols = sim_df.filter(regex='^x[0-9]').columns
    # Calculate sum of x-cols at individual level first
    xhh_uprated_fallback_indiv = sim_df.loc[:, x_cols].sum(axis=1)
    # Then, create the household-level sum, broadcast to all members
    xhh_uprated_fallback_hh = xhh_uprated_fallback_indiv.groupby(sim_df['idhh']).transform('sum')

    # 'yds' is now the uprated version from the data.
    # This value is used to calculate the change in disposable income.
    yds_hh_uprated = sim_df.groupby('idhh')['yds'].transform('sum')

    # Prefer the dataset xhh column when available, otherwise use the COICOP fallback
    if 'xhh' in df.columns and not sim_df['xhh'].eq(0).all():
        # Use uprated 'xhh' from data (assumed to be HH total repeated for members)
        xhh_base = sim_df['xhh'] 
    else:
        # Use uprated HH-level sum-of-cols fallback
        xhh_base = xhh_uprated_fallback_hh

    # Initialize policy columns in a single assign call
    policy_cols = ['tscee_s', 'tscer_s', 'ttn_s', 'tin_s', 'tva_s', 'bsa_s', 'boa_s', 'bed_s']
    sim_df = sim_df.assign(**{col: 0.0 for col in policy_cols})

    formal_workers = sim_df['lfo'] == 1
    sim_df.loc[formal_workers, 'tscee_s'] = sim_df.loc[formal_workers, 'yem'] * params['tscee_rate']
    sim_df.loc[formal_workers, 'tscer_s'] = sim_df.loc[formal_workers, 'yem'] * params['tscer_rate']

    # Presumptive tax logic (using yearly params from UI, dividing by 12)
    cond1 = (sim_df['ytn'] > params['presumptive_turnover_1'] / 12) & (sim_df['ytn'] <= params['presumptive_turnover_2'] / 12)
    cond2 = (sim_df['ytn'] > params['presumptive_turnover_2'] / 12) & (sim_df['ytn'] <= params['presumptive_turnover_3'] / 12)
    cond3 = (sim_df['ytn'] > params['presumptive_turnover_3'] / 12) & (sim_df['ytn'] <= params['pit_yse_turnover_threshold'] / 12)
    sim_df.loc[cond1, 'ttn_s'] = params['presumptive_tax_2'] / 12
    sim_df.loc[cond2, 'ttn_s'] = params['presumptive_tax_3'] / 12
    sim_df.loc[cond3, 'ttn_s'] = sim_df['ytn'] * params['presumptive_rate_4']
    
    # PIT logic (calculated on an annual basis, then converted to monthly)
    
    # 1. Annualize monthly incomes
    yem_y = sim_df['yem'] * 12
    yse_y = sim_df['yse'] * 12
    yag_y = sim_df['yag'] * 12
    ytn_y = sim_df['ytn'] * 12
    tscee_y = sim_df['tscee_s'] * 12
    
    # 2. Calculate annual tax base (ttb_y)
    ttb01_y = np.where(ytn_y > params['pit_yse_turnover_threshold'], yse_y, 0) + np.maximum(0, yag_y - params['pit_yag_exemption'])
    ttb02_y = np.where(sim_df['lfo'] == 1, yem_y, 0)
    ttb_y = (ttb01_y + ttb02_y - tscee_y).clip(lower=0)

    # Store monthly versions for output
    sim_df['ttb01_s'] = ttb01_y / 12
    sim_df['ttb02_s'] = ttb02_y / 12
    sim_df['ttb_s'] = ttb_y / 12

    # 3. Get annual thresholds and rates from params
    b2_y, b3_y, b4_y, b5_y = params['pit_bracket2_thresh'], params['pit_bracket3_thresh'], params['pit_bracket4_thresh'], params['pit_bracket5_thresh']
    r2, r3, r4, r5 = params['pit_bracket2_rate'], params['pit_bracket3_rate'], params['pit_bracket4_rate'], params['pit_bracket5_rate']
    
    # 4. Calculate annual tax (tax_y)
    tax_y = pd.Series(0.0, index=sim_df.index)
    tax_y += (ttb_y.clip(upper=b3_y) - b2_y).clip(lower=0) * r2
    tax_y += (ttb_y.clip(upper=b4_y) - b3_y).clip(lower=0) * r3
    tax_y += (ttb_y.clip(upper=b5_y) - b4_y).clip(lower=0) * r4
    tax_y += (ttb_y - b5_y).clip(lower=0) * r5
    
    # 5. Convert annual tax back to monthly flow (tin_s)
    sim_df['tin_s'] = tax_y / 12

    # VAT logic (calculated for head only)
    # Get the list of vatable items from the params
    vatable_item_list = params.get('vat_items_list', []) 
    # Filter this list to only include columns that actually exist in the dataframe
    vatable_cols = [col for col in vatable_item_list if col in sim_df.columns]
    
    vat_base = sim_df.loc[is_head, vatable_cols].sum(axis=1)

    sim_df['il_exp_vat'] = 0.0
    sim_df.loc[is_head, 'il_exp_vat'] = vat_base

    # Apply the VAT rate directly to the consumption base
    sim_df.loc[is_head, 'tva_s'] = vat_base * params['tva_rate']

    # Benefit logic (using monthly params from UI)
    sim_df['ils_origy'] = sim_df['yem'] + sim_df['yse'] + sim_df['yag']
    hh_origy = sim_df.groupby('idhh')['ils_origy'].transform('sum')
    hh_size = sim_df.groupby('idhh')['idperson'].transform('count')
    hh_disabled_count = sim_df.groupby('idhh')['ddi'].transform('sum')
    eligible_hh_mask = hh_origy < params['bsa_income_threshold']
    amount = pd.Series(0.0, index=sim_df.index)
    amount.loc[hh_size == 1] = params['bsa_1_person']
    amount.loc[hh_size == 2] = params['bsa_2_person']
    amount.loc[hh_size >= 3] = params['bsa_3_plus_person']
    amount += hh_disabled_count * params['bsa_disabled_topup']
    sim_df.loc[is_head & eligible_hh_mask, 'bsa_s'] = amount[is_head & eligible_hh_mask]

    eligible_seniors = (sim_df['dag'] >= params['senior_grant_age']) & (sim_df['ils_origy'] < params['senior_grant_income_threshold'])
    sim_df.loc[eligible_seniors, 'boa_s'] = params['senior_grant_amount']

    eligible_children = (sim_df['dag'] < params['school_meal_age']) & (sim_df['dec'].isin([2, 3, 4]))
    sim_df.loc[eligible_children, 'bed_s'] = params['school_meal_value'] * (10 / 12) # Averaging 10-month benefit over 12 months

    # Final resource definitions
    ils_tax_indiv = sim_df['tin_s'] + sim_df['ttn_s']
    ils_ben_indiv = sim_df['bsa_s'] + sim_df['boa_s'] # Note: bsa_s is only on head
    ils_dispy_indiv = sim_df['ils_origy'] + ils_ben_indiv - ils_tax_indiv - sim_df['tscee_s']
    ils_benki_indiv = sim_df['bed_s']
    ils_dispyki_indiv = ils_dispy_indiv + ils_benki_indiv
    sim_dispyki_hh = ils_dispyki_indiv.groupby(sim_df['idhh']).transform('sum')
    
    # Calculate the change in disposable income
    delta = sim_dispyki_hh - yds_hh_uprated

    # Apply a floor when income falls
    xhh_s_raw = xhh_base + delta
    floor = xhh_base * 0.25
    xhh_s = np.where(delta < 0, np.maximum(xhh_s_raw, floor), xhh_s_raw)

    # Store xhh_s and ils_con, assigning the HH total only to the head
    
    # First, create xhh_s and set to 0 for everyone
    sim_df['xhh_s'] = 0.0
    # Then, assign the calculated xhh_s value ONLY to the household head
    sim_df.loc[is_head, 'xhh_s'] = pd.Series(xhh_s, index=sim_df.index)[is_head].fillna(0) 

    # Do the same for ils_con (which uses the same xhh_s value)
    sim_df['ils_con'] = 0.0
    sim_df.loc[is_head, 'ils_con'] = pd.Series(xhh_s, index=sim_df.index)[is_head].fillna(0) # HH consumption assigned to head

    # Aggregating variables for analysis
    # Use assign to avoid fragmenting the dataframe
    new_analysis_cols = {
        'ils_head': (sim_df['dhh'] == 1).astype(int),
        'ils_earns': sim_df.get('yem', 0) + sim_df.get('yse', 0) + sim_df.get('yag', 0),
        'ils_dispyki': ils_dispyki_indiv,
        'ils_tax': ils_tax_indiv,
        'ils_sicee': sim_df['tscee_s'],
        'ils_sicse': 0.0,
        'ils_sicer': sim_df['tscer_s'],
        'ils_pen': 0.0,
        'ils_benmt': sim_df['bsa_s'] + sim_df['boa_s'],
        'ils_bennt': 0.0,
        'ils_benki': sim_df['bed_s'],
        'ils_benco': 0.0,
        'ils_bch': sim_df['bed_s'],
        'ils_bsu': 0.0,
        'ils_bdi': 0.0,
        'ils_bun': 0.0,
        'ils_bag': 0.0
    }
    sim_df = sim_df.assign(**new_analysis_cols)
    
    sim_df['ils_sic'] = sim_df['ils_sicee'] + sim_df['ils_sicse'] + sim_df['ils_sicer']
    sim_df['ils_ben'] = sim_df['ils_benmt'] + sim_df['ils_bennt'] + sim_df['ils_pen']
    sim_df['ils_bsa'] = sim_df['bsa_s'] + sim_df['boa_s']
    sim_df['ils_dispy'] = ils_dispy_indiv
    
    # Keep VAT totals stored on the household head only
    tva_s_hh = sim_df.groupby('idhh')['tva_s'].transform('sum')
    sim_df['ils_taxco'] = 0.0 # Clear for everyone
    sim_df.loc[is_head, 'ils_taxco'] = tva_s_hh[is_head] # Assign HH total to head
    
    # These lines are now correct because ils_taxco is 0 for non-heads
    sim_df['ils_dispy_pf'] = sim_df['ils_dispy'] - sim_df['ils_taxco'] + sim_df['ils_benco']
    sim_df['ils_con_pf'] = sim_df['ils_con'] - sim_df['ils_taxco'] + sim_df['ils_benco']
    sim_df['ils_dispyx'] = sim_df['ils_dispy'] + sim_df['xivot']
    sim_df['ils_dispyx_pf'] = sim_df['ils_dispyx'] - sim_df['ils_taxco'] + sim_df['ils_benco']
    
    # Return a compact copy
    return sim_df.copy()

# --- ANALYSIS HELPER FUNCTIONS ---
def weighted_sum(df, column_name, weight_col='dwt'):
    if column_name not in df.columns or weight_col not in df.columns or df.empty: return 0
    return (df[column_name] * df[weight_col]).sum()

def weighted_average(df, column_name, weight_col='dwt'):
    if df.empty: return 0
    if column_name not in df.columns or weight_col not in df.columns: return 0
    weights = df[weight_col]
    if weights.sum() == 0: return 0
    return np.average(df[column_name], weights=weights)

def add_analysis_flags(df):
    
    # Create individual-level flags in one assign call
    flag_cols = {
        'isPers': 1,
        'isChild': (df['dag'] < 18).astype(int),
        'isElderly': (df['dag'] > 64).astype(int),
        'isAdult': (df['dag'] >= 18).astype(int),
        'isMaleAdult': ((df.get('dgn', 0) > 0) & (df['dag'] >= 18)).astype(int),
        'isYoungChild': (df['dag'] <= 2).astype(int),
        'isInformalWorker': (df.get('lfo', 0) == 0).astype(int)
    }
    df = df.assign(**flag_cols)
    
    # Create 'isInformalAdults' based on new columns
    df['isInformalAdults'] = ((df['isInformalWorker'] > 0) & (df['isAdult'] > 0)).astype(int)

    # Group once to create household totals for each flag
    hh_flag_cols = ['isChild', 'isElderly', 'isAdult', 'isMaleAdult', 'isPers', 'isYoungChild', 'ddi', 'isInformalWorker', 'isInformalAdults']
    
    # Ensure all columns exist before grouping
    for col in hh_flag_cols:
        if col not in df.columns:
            df[col] = 0
            
    # Create a DataFrame of the HH sums
    hh_sums_df = df.groupby('idhh')[hh_flag_cols].transform('sum')
    
    # Rename columns to 'n...InHH' format
    hh_sums_df.columns = [f'n{col.replace("is", "")}InHH' for col in hh_flag_cols]
    
    # Join the new count columns back to the main df
    df = df.join(hh_sums_df)
    
    # Create final household flags based on the new count columns
    hh_type_cols = {
        'isHHWithChild': (df['nChildInHH'] > 0).astype(int),
        'isAtLeastOneElderlyHH': (df['nElderlyInHH'] > 0).astype(int),
        'isAtLeastOneDisabledHH': (df['nddiInHH'] > 0).astype(int),
        'isSinglePersonHH': (df['nPersInHH'] == 1).astype(int),
        'is1AdultWithChildrenHH': ((df['nAdultInHH'] == 1) & (df['nChildInHH'] >= 1)).astype(int),
        'is2AdultsNoChildrenHH': ((df['nAdultInHH'] == 2) & (df['nChildInHH'] == 0)).astype(int),
        'is2Adults1_2ChildrenHH': ((df['nAdultInHH'] == 2) & (df['nChildInHH'].between(1, 2))).astype(int),
        'is2Adults3_4ChildrenHH': ((df['nAdultInHH'] == 2) & (df['nChildInHH'].between(3, 4))).astype(int),
        'is2Adults5plusChildrenHH': ((df['nAdultInHH'] == 2) & (df['nChildInHH'] >= 5)).astype(int),
        'is3plusAdultsNoChildrenHH': ((df['nAdultInHH'] >= 3) & (df['nChildInHH'] == 0)).astype(int),
        'is3plusAdultsWithChildrenHH': ((df['nAdultInHH'] >= 3) & (df['nChildInHH'] >= 1)).astype(int),
        'isYoungChildHH': (df['nYoungChildInHH'] > 0).astype(int),
        'isNoMaleAdultHH': (df['nMaleAdultInHH'] == 0).astype(int),
        'isInformalAdultHH': (df['nInformalAdultsInHH'] > 0).astype(int),
        'isNoInformalAdultsHH': (df['nInformalAdultsInHH'] == 0).astype(int),
        'ils_earns': df.get('yem', 0) + df.get('yse', 0) + df.get('yag', 0)
    }
    df = df.assign(**hh_type_cols)
    
    df['TotalHHEarnings'] = df.groupby('idhh')['ils_earns'].transform('sum')
    df['isNoTotalHHEarningsHH'] = (df['TotalHHEarnings'] <= 0).astype(int)
    
    return df

# --- MAIN ANALYSIS ENGINE ---
def run_analysis(sim_df, user_choice, baseline_analysis_df=None):
    results = {}
    analysis_df = sim_df.copy()
    
    # 1. DEFINE RESOURCE AND POVERTY LINE
    base_resource_map = {1: 'ils_con', 2: 'ils_dispyx', 3: 'ils_con_pf', 4: 'ils_dispyx_pf'}
    povline_map = {1: 'spl', 2: 'spl', 3: 'splpf', 4: 'splpf'}
    
    base_resource_col = base_resource_map[user_choice]
    analysis_df['ilsRank'] = analysis_df.get(base_resource_col, 0) # Use .get for safety
    analysis_df['povLine_raw'] = analysis_df.get(povline_map[user_choice], 0)
    
    # 2. CALCULATE TOTAL HOUSEHOLD RESOURCE (ilsRankHH)
    analysis_df['ilsRankHH'] = analysis_df.groupby('idhh')['ilsRank'].transform('sum')
    

    # 3. CALCULATE EQUIVALENCE SCALE (eqScale)
    head_ses = analysis_df.loc[analysis_df['dhh'] == 1, ['idhh', 'ses']].set_index('idhh')['ses']
    analysis_df['eqScale'] = analysis_df['idhh'].map(head_ses).fillna(0)

    # 4. CALCULATE EQUIVALIZED RESOURCE (eqRank)
    valid_eq_rank_mask = (analysis_df['ilsRankHH'] >= 0) & (analysis_df['eqScale'] > 0)
    analysis_df['eqRank'] = 0.0
    analysis_df.loc[valid_eq_rank_mask, 'eqRank'] = analysis_df.loc[valid_eq_rank_mask, 'ilsRankHH'] / analysis_df.loc[valid_eq_rank_mask, 'eqScale']

    # 5. DEFINE ANALYSIS GROUPS (DECILES, HH TYPES)
    if baseline_analysis_df is not None:
        # REFORM run
        cols_to_merge = ['deciles'] + [col for col in baseline_analysis_df if col.startswith('is') and 'HH' in col]
        analysis_df = analysis_df.drop(columns=cols_to_merge, errors='ignore').merge(
            baseline_analysis_df[['idperson'] + cols_to_merge], on='idperson', how='left'
        )
    else:
        # BASELINE run
        analysis_df = add_analysis_flags(analysis_df)
        analysis_df_sorted = analysis_df.sort_values('eqRank')
        
        # Ensure dwt exists
        if 'dwt' not in analysis_df_sorted.columns:
             analysis_df_sorted['dwt'] = 1 # Default to 1 if missing
             
        analysis_df_sorted['cum_w'] = analysis_df_sorted['dwt'].cumsum()
        total_w = analysis_df_sorted['dwt'].sum()
        if total_w > 0:
            analysis_df_sorted['deciles'] = pd.cut(analysis_df_sorted['cum_w'], bins=np.linspace(0, total_w, 11), labels=range(1, 11), right=False, include_lowest=True)
        else:
            analysis_df_sorted['deciles'] = 1
        analysis_df = analysis_df_sorted.sort_index()

    # 6. CALCULATE POVERTY INDICATORS
    povLine = weighted_average(analysis_df, 'povLine_raw')
    
    analysis_df['isPoor'] = (analysis_df['eqRank'] < povLine).astype(int)
    
    analysis_df['povGap'] = 0.0
    if povLine > 0:
        analysis_df['povGap'] = np.maximum(0, (povLine - analysis_df['eqRank']) / povLine) * analysis_df['isPoor']
    
    is_head_df = analysis_df[analysis_df['dhh']==1]
    
    # 7. AGGREGATE RESULTS
    results['taxbenpol_abs'] = {
        'Direct taxes': weighted_sum(analysis_df, 'ils_tax'),
        'Social insurance contributions': weighted_sum(analysis_df, 'ils_sic'),
        'Indirect taxes': weighted_sum(is_head_df, 'tva_s'), # tva_s is HH total on head
        'Cash benefits': weighted_sum(analysis_df, 'ils_ben'),
        'In-kind benefits': weighted_sum(analysis_df, 'ils_benki'),
        'Indirect subsidies': weighted_sum(analysis_df, 'ils_benco'),
        'Child benefits': weighted_sum(analysis_df, 'ils_bch'),
        'Social assistance': weighted_sum(analysis_df, 'ils_bsa'),
    }
    
    total_rev = sum(results['taxbenpol_abs'][name] for name in ['Direct taxes', 'Social insurance contributions', 'Indirect taxes'])
    total_exp = sum(results['taxbenpol_abs'][name] for name in ['Cash benefits', 'In-kind benefits', 'Indirect subsidies'])
    results['taxbenpol_abs']['Sum of government revenue'] = total_rev
    results['taxbenpol_abs']['Sum of government expenditure'] = total_exp

    results['taxbenpol_share'] = {
        name: (results['taxbenpol_abs'][name] / total_rev * 100) if total_rev > 0 else 0 for name in ['Direct taxes', 'Social insurance contributions', 'Indirect taxes']
    }
    results['taxbenpol_share'].update({
        name: (results['taxbenpol_abs'][name] / total_exp * 100) if total_exp > 0 else 0 for name in ['Cash benefits', 'In-kind benefits', 'Indirect subsidies']
    })

    results['poverty'] = {}
    # Include header markers alongside subgroup flags
    subgroup_flags = [
        'All individuals', 
        'header_hh_structure', 'isSinglePersonHH', 'is1AdultWithChildrenHH', 'is2AdultsNoChildrenHH',
        'is2Adults1_2ChildrenHH', 'is2Adults3_4ChildrenHH', 'is2Adults5plusChildrenHH',
        'is3plusAdultsNoChildrenHH', 'is3plusAdultsWithChildrenHH', 
        'header_vulnerable', 'isYoungChildHH', 'isAtLeastOneElderlyHH', 'isAtLeastOneDisabledHH', 
        'isNoMaleAdultHH',
        'header_labor', 'isNoTotalHHEarningsHH', 'isInformalAdultHH', 'isNoInformalAdultsHH'
    ]
    
    for flag in subgroup_flags:
        # Treat header markers separately
        if flag.startswith('header_'):
            results['poverty'][flag] = {'Poverty rate (%)': None, 'Poverty gap (%)': None}
            continue
            
        if flag == 'All individuals':
             sub_df = analysis_df
        elif flag in analysis_df.columns:
            sub_df = analysis_df[analysis_df[flag] == 1]
        else:
            sub_df = pd.DataFrame(columns=analysis_df.columns) # Empty df
            
        results['poverty'][flag] = {
            'Poverty rate (%)': weighted_average(sub_df, 'isPoor') * 100,
            'Poverty gap (%)': weighted_average(sub_df, 'povGap') * 100,
        }
    results['poverty']['povline'] = povLine

    return results, analysis_df

# --- UI HELPER FUNCTIONS ---
# Helper for building parameter rows with consistent styling
def make_param_input(label, param_id, value, step=None, label_width=7, input_width=5, disabled=False):
    """Creates a neatly formatted row for a parameter input."""
    return dbc.Row([
        dbc.Label(label, html_for=param_id, width=label_width, style={'font-size': '0.9rem'}),
        dbc.Col(
            create_param_input_component(param_id, value, disabled=disabled),
            width=input_width
        ),
    ], className="param-input-row align-items-center")

# Helper for rendering the PIT bracket table
def make_pit_table(params):
    """Creates a table for PIT brackets."""
    header = [html.Thead(html.Tr([
        html.Th("Bracket", style={'font-size': '0.9rem'}), 
        html.Th("Lower limit, yearly", style={'font-size': '0.9rem'}), 
        html.Th("Marginal rate, %/100", style={'font-size': '0.9rem'})
    ]))]
    
    body = html.Tbody([
        html.Tr([
            html.Td("1"),
            html.Td(create_param_input_component('pit_bracket1_thresh', params['pit_bracket1_thresh'], disabled=True)),
            html.Td(create_param_input_component('pit_bracket1_rate', params['pit_bracket1_rate'], disabled=True))
        ]),
        html.Tr([
            html.Td("2"),
            html.Td(create_param_input_component('pit_bracket2_thresh', params['pit_bracket2_thresh'])),
            html.Td(create_param_input_component('pit_bracket2_rate', params['pit_bracket2_rate']))
        ]),
        html.Tr([
            html.Td("3"),
            html.Td(create_param_input_component('pit_bracket3_thresh', params['pit_bracket3_thresh'])),
            html.Td(create_param_input_component('pit_bracket3_rate', params['pit_bracket3_rate']))
        ]),
        html.Tr([
            html.Td("4"),
            html.Td(create_param_input_component('pit_bracket4_thresh', params['pit_bracket4_thresh'])),
            html.Td(create_param_input_component('pit_bracket4_rate', params['pit_bracket4_rate']))
        ]),
        html.Tr([
            html.Td("5"),
            html.Td(create_param_input_component('pit_bracket5_thresh', params['pit_bracket5_thresh'])),
            html.Td(create_param_input_component('pit_bracket5_rate', params['pit_bracket5_rate']))
        ]),
    ])
    
    return dbc.Table(header + [body], bordered=True, size="sm", responsive=True)

def make_control_step(step_number: str, title: str) -> html.Div:
    """Creates a highlighted heading for the controls panel."""
    return html.Div(
        [
            html.Span(step_number, className="control-step-number"),
            html.Span(title, className="control-step-title"),
        ],
        className="control-step-header d-flex align-items-center gap-2 mb-2"
    )

# Render tables with consistent styling
def create_styled_table(data_dict, title, subtitle):
    if data_dict:
        original_keys = list(data_dict.keys())
        replace_first = original_keys[0] in ('Component', 'Household category')
        table_dict = {}
        for idx, key in enumerate(original_keys):
            new_key = '' if replace_first and idx == 0 else key
            table_dict[new_key] = data_dict[key]
    else:
        table_dict = data_dict

    max_len = 0
    if table_dict:
         max_len = max(len(v) for v in table_dict.values() if v is not None)
         
    for col in table_dict:
        if table_dict[col] is None: table_dict[col] = []
        if len(table_dict[col]) < max_len:
            table_dict[col].extend([None] * (max_len - len(table_dict[col]))) # Use None, not ''

    header_cells = []
    for idx, col in enumerate(table_dict.keys()):
        th_classes = "table-header-cell"
        if idx > 0:
            th_classes += " text-end"
        header_cells.append(html.Th(col, className=th_classes))
    header = [html.Thead(html.Tr(header_cells))]
    
    body_rows = []
    if not table_dict:
        return [html.P("No data for table.")]
        
    row_titles_col_name = next(iter(table_dict))
    
    # Header row labels used for styling
    header_rows = ["By source", "By type", "By area, excl. indirect subsidies", 
                   "Household structure", "Vulnerable households", "Labour market status"]
    
    for i, row_title in enumerate(table_dict[row_titles_col_name]):
        if row_title is None:
            continue # Should not happen, but good to check

        row_title_str = str(row_title)
        display_title = row_title_str[1:].strip() if row_title_str.startswith('-') else row_title_str
        is_header_row = row_title_str in header_rows
        is_sub_row = row_title_str.startswith('-')
        is_strong_row = row_title_str in {"Sum of government revenue", "Sum of government expenditure", "All individuals"}

        row_classes = []
        if any(x in row_title_str for x in ["Sum of government expenditure", "By type", "By source"]):
            row_classes.append("table-section-divider")
        if is_header_row:
            row_classes.append("table-section-header-row")
        if is_strong_row:
            row_classes.append("table-row-strong")
        if is_sub_row:
            row_classes.append("table-sub-row")

        first_cell_classes = ["table-first-column"]
        if is_header_row:
            first_cell_classes.append("table-first-column-header")
        if is_sub_row:
            first_cell_classes.append("table-first-column-child")
        if is_strong_row:
            first_cell_classes.append("table-row-strong")

        row_cells = [html.Td(display_title, className=" ".join(first_cell_classes))]

        for col_name in list(table_dict.keys())[1:]:
            val = table_dict[col_name][i]
            formatted_val = f"{val:,.2f}" if pd.notna(val) and isinstance(val, (int, float)) else ("" if pd.isna(val) else val)
            cell_classes = ["text-end", "table-data-cell"]
            if is_header_row:
                cell_classes.append("table-data-header")
            if is_strong_row:
                cell_classes.append("table-row-strong")
            if is_sub_row:
                cell_classes.append("table-data-sub")
            row_cells.append(html.Td(formatted_val, className=" ".join(cell_classes)))

        row_classes_for_render = list(row_classes)
        if not is_header_row and not is_sub_row:
            row_classes_for_render.append("table-main-row")
        body_rows.append(html.Tr(row_cells, className=" ".join(row_classes_for_render)))

    body = [html.Tbody(body_rows)]
    
    return [
        html.Div(
            [
                html.H5(title, className="mb-0"),
                html.Span(subtitle, className="text-muted small ms-2 table-subtitle"),
            ],
            className="table-title-row d-flex align-items-center gap-2 mt-4"
        ),
        dbc.Table(header + body, bordered=True, hover=True, responsive=True, className="table-sm")
    ]


def format_signed_value(val):
    if pd.isna(val):
        return val
    if val > 0:
        return f"+{val:,.2f}"
    if val < 0:
        return f"{val:,.2f}"
    return "0.00"

# Helper for building baseline parameter modal sections
def create_baseline_param_section(title, params_dict):
    """Creates a formatted section for the baseline parameters modal."""
    def format_value(value):
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not value.is_integer():
                formatted = f"{value:,.2f}".rstrip('0').rstrip('.')
                return formatted if formatted else "0"
            return f"{int(round(value)):,}"
        return value
    
    # 1. Create the list of dbc.Row components
    rows = [
        dbc.Row([
            dbc.Col(html.Span(format_value(value), className="baseline-param-value"), width="auto"),
            dbc.Col(html.Strong(label, className="baseline-param-label"), width=True)
        ], className="align-items-center mb-1 baseline-param-row") for label, value in params_dict.items()
    ]
    
    # 2. Return a single, flat list using list concatenation
    return [html.H5(title, className="mt-3")] + rows + [html.Hr()]

# Helper to create consistent output dataframes
def create_output_dataframe(sim_df):
    """Selects, orders, and formats columns for the output file."""
    output_columns = [
        'idhh', 'idperson', 'idmother', 'idfather', 'idpartner', 'xhh_s', 'xhh', 
        'dag', 'dgn', 'dec', 'dwt', 'dms', 'dhh', 'ddi', 'deh', 'dct', 'dcz', 
        'dur', 'les', 'loc', 'lfo', 'lcs', 'lindi', 'yem', 'yse', 
        'yag', 'ytn', 'yds', 'bsa_s', 'boa_s', 'bed_s', 'tscee_s', 'tscer_s', 
        'ttn_s', 'ttb01_s', 'ttb02_s', 'ttb_s', 'tin_s', 'tva_s', 'arf', 'aec', 
        'spl', 'splpf', 'ses', 'ils_head', 'ils_earns', 'ils_origy', 'ils_tax', 
        'ils_sicee', 'ils_sicse', 'ils_sicer', 'ils_pen', 'ils_benmt', 'ils_bennt', 
        'ils_benki', 'ils_ben', 'ils_dispy', 'ils_dispy_pf', 'ils_dispyki', 
        'ils_taxco', 'ils_sic', 'ils_benco', 'ils_bch', 'ils_bsa', 'ils_dispyx', 
        'ils_dispyx_pf', 'ils_con', 'ils_con_pf', 'il_exp_vat'
    ]
    
    monetary_cols = [
        'xhh_s', 'xhh', 'yem', 'yse', 'yag', 'ytn', 'yds', 'bsa_s', 
        'boa_s', 'bed_s', 'tscee_s', 'tscer_s', 'ttn_s', 'ttb01_s', 
        'ttb02_s', 'ttb_s', 'tin_s', 'tva_s', 'spl', 'splpf', 'ses', 
        'ils_earns', 'ils_origy', 'ils_tax', 'ils_sicee', 'ils_sicse', 
        'ils_sicer', 'ils_pen', 'ils_benmt', 'ils_bennt', 'ils_benki', 
        'ils_ben', 'ils_dispy', 'ils_dispy_pf', 'ils_dispyki', 'ils_taxco', 
        'ils_sic', 'ils_benco', 'ils_bch', 'ils_bsa', 'ils_dispyx', 
        'ils_dispyx_pf', 'ils_con', 'ils_con_pf', 'il_exp_vat'
    ]

    df_out = pd.DataFrame()
    for col in output_columns:
        if col in sim_df.columns:
            df_out[col] = sim_df[col]
        else:
            df_out[col] = np.nan 

    # Reorder to be certain and round
    df_out = df_out[output_columns]
    for col in monetary_cols:
        if col in df_out.columns:
            df_out[col] = df_out[col].round(2)
            
    return df_out

def make_tab(label_text: str, info_index: str, content_div_id: str) -> dbc.Tab:
    """Create a Tab with a string label and an in-tab info button header."""
    return dbc.Tab(
        label=label_text,  # <-- string only
        children=[
            html.Div(
                dbc.Button(
                    "Description of tab's indicators",
                    id={'type': 'info-button', 'index': info_index},
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="info-button btn-description",
                ),
                className="tab-info-wrapper d-flex justify-content-start mb-2"
            ),
            html.Div(id=content_div_id),
        ],
        className="modern-tab"
    )

# --- APP LAYOUT ---
app.layout = dbc.Container([
    dcc.Download(id='download-simulation-output'),

    # Baseline Parameters Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Baseline parameters (2023)")),
        dbc.ModalBody([
            *create_baseline_param_section("Indirect taxes", {
                'Standard VAT rate, %/100': BASELINE_PARAMS['tva_rate'],
            }),
            *create_baseline_param_section("Personal income tax", {
                'Self-employment income threshold (presumptive maximum), annual': BASELINE_PARAMS['pit_yse_turnover_threshold'],
                'Exemption on agricultural income, annual': BASELINE_PARAMS['pit_yag_exemption'],
                'Bracket 2 (non-zero tax) lower threshold, annual': BASELINE_PARAMS['pit_bracket2_thresh'],
                'Bracket 2 progressive rate, %/100': BASELINE_PARAMS['pit_bracket2_rate'],
                'Bracket 3 lower threshold, annual': BASELINE_PARAMS['pit_bracket3_thresh'],
                'Bracket 3 progressive rate, %/100': BASELINE_PARAMS['pit_bracket3_rate'],
                'Bracket 4 lower threshold, annual': BASELINE_PARAMS['pit_bracket4_thresh'],
                'Bracket 4 progressive rate, %/100': BASELINE_PARAMS['pit_bracket4_rate'],
                'Bracket 5 lower threshold, annual': BASELINE_PARAMS['pit_bracket5_thresh'],
                'Bracket 5 progressive rate, %/100': BASELINE_PARAMS['pit_bracket5_rate'],
            }),
            *create_baseline_param_section("Social insurance contributions", {
                'Employee contribution rate, %/100': BASELINE_PARAMS['tscee_rate'],
                'Employer contribution rate, %/100': BASELINE_PARAMS['tscer_rate'],
            }),
            *create_baseline_param_section("Presumptive tax for micro enterprises", {
                'Band 2 (non-zero tax) lower threshold, annual': BASELINE_PARAMS['presumptive_turnover_1'],
                'Band 2 tax amount, annual': BASELINE_PARAMS['presumptive_tax_2'],
                'Band 3 lower threshold, annual': BASELINE_PARAMS['presumptive_turnover_2'],
                'Band 3 tax amount, annual': BASELINE_PARAMS['presumptive_tax_3'],
            }),
            *create_baseline_param_section("Presumptive tax for small enterprises", {
                'Lower threshold, annual': BASELINE_PARAMS['presumptive_turnover_3'],
                'Tax rate, %/100': BASELINE_PARAMS['presumptive_rate_4'],
            }),
            *create_baseline_param_section("Social assistance benefit", {
                'Income threshold, monthly': BASELINE_PARAMS['bsa_income_threshold'],
                'Benefit amount (1-person household), monthly': BASELINE_PARAMS['bsa_1_person'],
                'Benefit amount (2-person household), monthly': BASELINE_PARAMS['bsa_2_person'],
                'Benefit amount (3+-person household), monthly': BASELINE_PARAMS['bsa_3_plus_person'],
                'Disability top-up, monthly': BASELINE_PARAMS['bsa_disabled_topup'],
            }),
             *create_baseline_param_section("Senior citizens' grant", {
                'Age limit': BASELINE_PARAMS['senior_grant_age'],
                'Income threshold, monthly': BASELINE_PARAMS['senior_grant_income_threshold'],
                'Grant amount, monthly': BASELINE_PARAMS['senior_grant_amount'],
            }),
             *create_baseline_param_section("School meals", {
                'Maximum age': BASELINE_PARAMS['school_meal_age'],
                'Meal value, monthly': BASELINE_PARAMS['school_meal_value'],
            }),
            *create_baseline_param_section("Poverty lines", {
                'Basic poverty line, monthly': BASELINE_PARAMS['basic_pov_line'],
                'Basic post-fiscal poverty line, monthly': BASELINE_PARAMS['basic_pov_line_pf'],
            }),
        ]),
        dbc.ModalFooter(dbc.Button("Close", id="close-baseline-modal", className="ms-auto", n_clicks=0)),
    ], id="baseline-modal", is_open=False, size="lg", scrollable=True, className="baseline-modal"), # Made modal scrollable
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("About DEVMOD")),
        dbc.ModalBody(html.Div([
            html.P([
                "DEVMOD is a synthetic tax-benefit microsimulation model developed under UNU-WIDER’s ",
                html.A("SOUTHMOD project", href="https://www.wider.unu.edu/project/southmod-simulating-tax-and-benefit-policies-development-phase-3", target="_blank"),
                ". The model runs on the EUROMOD platform and mirrors real SOUTHMOD country models. It uses artificial data, so you can learn and experiment without handling sensitive micro data. The model is taught and used in the ",
                html.A("SOUTHMOD online course", href="https://www.wider.unu.edu/about/southmod-online-course", target="_blank"),
                ", delivered through UNU-WIDER’s learning platform at ",
                html.A("learning.wider.unu.edu", href="https://learning.wider.unu.edu/group/2", target="_blank"),
                "."
            ], style={"lineHeight": 1.5}),
        
            html.P("This simulator allows you to run DEVMOD on the web. The outputs correspond to what DEVMOD produces when run and analysed in EUROMOD. Based on the model’s synthetic input dataset, you can run a baseline policy system for 2023, change parameters to create reform scenarios, and compare baseline and reform indicators for various distributional and budgetary outcomes – similar to the SOUTHMOD Statistics Presenter in EUROMOD. You can also export the results to Excel.", style={"lineHeight": 1.5}),
            html.P([
                "DEVMOD follows standard SOUTHMOD conventions for identifiers, income variables, and policy functions, and supports simulations of direct and indirect taxes, social contributions, and cash benefits. It is maintained by UNU-WIDER as an accompanion to the SOUTHMOD bundle. Refer to the ",
                html.A("SOUTHMOD User Manual", href="https://www.wider.unu.edu/sites/default/files/Projects/PDF/SOUTHMOD_UserManual_20250718.pdf", target="_blank"),
                " for details."
            ], style={"lineHeight": 1.5}),

            html.P([
                "To run DEVMOD in the standard EUROMOD environment, download the model from ",
                html.A("here (zip file)", href="https://www.wider.unu.edu/sites/default/files/About/DEVMOD%20v1.0.zip", target="_blank"),
                ", optionally review its data requirement document from ",
                html.A("here (Excel file)", href="https://www.wider.unu.edu/sites/default/files/About/DRD%20DEVMOD%20for%20dataset%20dv_2020_a1.xlsx", target="_blank"),
                ", and install EUROMOD software from  ",
                html.A("here (zip file)", href="https://euromod-web.jrc.ec.europa.eu/sites/default/files/EUROMOD_installer_64bit_latest_version.zip", target="_blank"),
                ". Finally open the DEVMOD model folder in EUROMOD, click on the DV flag, and edit or run the model as needed. For background on the modelling platform itself, see ",
                html.A("What is EUROMOD?", href="https://euromod-web.jrc.ec.europa.eu/overview/what-is-euromod", target="_blank"),
                 " by the Joint Research Centre, the European Commission’s science and knowledge service that develops and maintains EUROMOD.",
            ], style={"lineHeight": 1.5})

        ])),
        dbc.ModalFooter(dbc.Button("Close", id="close-devmod-modal", className="ms-auto"))
    ], id="devmod-modal", is_open=False, size="lg", scrollable=True, className="baseline-modal"),
    
    # Info Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="info-modal-title")),
        dbc.ModalBody(dcc.Markdown(id="info-modal-body", dangerously_allow_html=True), className="info-modal-body"),
        dbc.ModalFooter(dbc.Button("Close", id="close-info-modal", className="ms-auto"))
    ], id="info-modal", is_open=False, size="lg", scrollable=True),

    # Primary layout: controls column and results column
    dbc.Row([
        dbc.Col(
            html.Div([
                html.Div([
                    html.H1("SOUTHMOD Online Tool", className="app-title-heading"),
                    html.P("DEVMOD reform analysis dashboard", className="app-title-subheading")
                ], className="app-title"),
                dbc.Card([
                    dbc.CardBody([
                html.Div([
                    dbc.Row([
                        dbc.Col(dbc.Button("DEVMOD info", id="view-devmod-button", color="secondary", outline=True, size="sm", className="w-100 btn-baseline"), width=6),
                        dbc.Col(dbc.Button("Baseline parameters", id="view-baseline-button", color="secondary", outline=True, size="sm", className="w-100 btn-baseline"), width=6),
                    ], className="g-2 mb-3"),
                    html.Div([
                        make_control_step("1", "Name your reform scenario"),
                        dcc.Input(id='reform-name-input', placeholder='Enter reform scenario name...', value='My reform', type='text', className="form-control modern-input"),
                    ], className="mb-3"),
                ]),
                        
                        make_control_step("2", "Configure reform parameters"),
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.P("Personal income tax", className="accordion-section-title"),
                                make_param_input("Self-employment income threshold (presumptive maximum), annual", 'pit_yse_turnover_threshold', BASELINE_PARAMS['pit_yse_turnover_threshold']), 
                                make_param_input("Exemption on agricultural income, annual", 'pit_yag_exemption', BASELINE_PARAMS['pit_yag_exemption']), 
                                html.Hr(),
                                make_pit_table(BASELINE_PARAMS),
                                html.Hr(), 
                                html.P("Social insurance contributions", className="accordion-section-title"),
                                make_param_input("Employee SIC rate, %/100", 'tscee_rate', BASELINE_PARAMS['tscee_rate'], 0.01), 
                                make_param_input("Employer SIC rate, %/100", 'tscer_rate', BASELINE_PARAMS['tscer_rate'], 0.01),
                                html.Hr(),
                                html.P("Presumptive tax for micro enterprises", className="accordion-section-title"),
                                make_param_input("Band 2 (non-zero tax) lower threshold, annual", 'presumptive_turnover_1', BASELINE_PARAMS['presumptive_turnover_1']), 
                                make_param_input("Band 2 tax amount, annual", 'presumptive_tax_2', BASELINE_PARAMS['presumptive_tax_2']), 
                                make_param_input("Band 3 lower threshold, annual", 'presumptive_turnover_2', BASELINE_PARAMS['presumptive_turnover_2']), 
                                make_param_input("Band 3 tax amount, annual", 'presumptive_tax_3', BASELINE_PARAMS['presumptive_tax_3']), 
                                html.Hr(),
                                html.P("Presumptive tax for small enterprises", className="accordion-section-title"),
                                make_param_input("Lower threshold, annual", 'presumptive_turnover_3', BASELINE_PARAMS['presumptive_turnover_3']), 
                        make_param_input("Tax rate, %/100", 'presumptive_rate_4', BASELINE_PARAMS['presumptive_rate_4'], 0.01)
                            ], title="Direct taxes"),
                            dbc.AccordionItem([
                        html.P("Value-added tax (VAT)", className="accordion-section-title"),
                        make_param_input("Standard VAT rate, %/100", 'tva_rate', BASELINE_PARAMS['tva_rate'], 0.01),
                        html.Hr(),
                                dbc.Label("Select standard-rated goods", className="fw-bold", style={"font-size": "0.92rem"}),
                                dbc.Row([
                                    dbc.Col(dbc.Button("Select all", id="vat-select-all", color="link", size="sm", className="p-0 me-2"), width="auto"),
                                    dbc.Col(dbc.Button("Exempt all", id="vat-deselect-all", color="link", size="sm", className="p-0 me-2"), width="auto"),
                                    dbc.Col(dbc.Button("Back to baseline", id="vat-baseline", color="link", size="sm", className="p-0"), width="auto"),
                                ], className="mb-2 vat-button-row align-items-center"),
                                dcc.Checklist(
                                    id='vat-checklist',
                                    options=[{'label': v['label'], 'value': k} for k, v in VAT_ITEM_MAP.items()],
                                    value=BASELINE_VAT_STD_RATE_ITEMS,
                                    className="dbc_checklist",
                                    style={'height': '180px', 'overflowY': 'auto', 'border': '1px solid #ccc', 'padding': '8px', 'border-radius': '5px'},
                                    labelStyle={'display': 'block', 'font-size': '0.9rem', 'marginLeft': '0.4rem'}
                                )
                            ], title="Indirect taxes"),
                            dbc.AccordionItem([
                                html.P("Social assistance", className="accordion-section-title"),
                                make_param_input("Eligibility income threshold, monthly", 'bsa_income_threshold', BASELINE_PARAMS['bsa_income_threshold']), 
                                make_param_input("1-person benefit amount, monthly", 'bsa_1_person', BASELINE_PARAMS['bsa_1_person']), 
                                make_param_input("2-person benefit amount, monthly", 'bsa_2_person', BASELINE_PARAMS['bsa_2_person']), 
                                make_param_input("3+ person benefit amount, monthly", 'bsa_3_plus_person', BASELINE_PARAMS['bsa_3_plus_person']), 
                                make_param_input("Disability top-up, monthly", 'bsa_disabled_topup', BASELINE_PARAMS['bsa_disabled_topup']), 
                                html.Hr(), 
                                html.P("Senior citizens' grant", className="accordion-section-title"),
                                make_param_input("Eligibility age threshold", 'senior_grant_age', BASELINE_PARAMS['senior_grant_age']), 
                                make_param_input("Eligibility income threshold, monthly", 'senior_grant_income_threshold', BASELINE_PARAMS['senior_grant_income_threshold']), 
                                make_param_input("Senior grant amount, monthly", 'senior_grant_amount', BASELINE_PARAMS['senior_grant_amount']), 
                                html.Hr(), 
                                html.P("In-kind benefits", className="accordion-section-title"),
                                make_param_input("School meal value, monthly", 'school_meal_value', BASELINE_PARAMS['school_meal_value'])
                            ], title="Benefit policies"),
                        ], start_collapsed=True, className="mb-3"),

                        html.Div([
                            make_control_step("3", "Select distribution statistic"),
                        dbc.Select(
                            id='analysis-choice',
                            options=[
                                {'label': 'Consumption based', 'value': '1'},
                                {'label': 'Income based', 'value': '2'},
                                {'label': 'Consumption based, net of indirect taxes', 'value': '3'},
                                {'label': 'Income based, net of indirect taxes', 'value': '4'}
                            ],
                            value='3',
                            className="modern-select"
                        ),
                        ], className="mb-3"),
                        
                        dbc.Switch(id='generate-excel-switch', label="Generate Excel output file", value=False, className="my-2 modern-switch"),
                        
                        dbc.Button("Run simulation", id='run-button', color="primary", size="lg", className="w-100 btn-run-simulation"),
                        dcc.Loading(id="loading-icon", children=[html.Div(id="loading-output", className="text-center mt-4")], type="default")
                    ], className="modern-card-body")
                ], className="modern-card shadow-sm border-0 control-card")
            ], className="left-column d-flex flex-column gap-3"),
            width=4
        ),

        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-main",
                        children=[
                            html.H4(id='results-title', className="mt-1 mb-3 text-center results-title"),
                            dbc.Tabs(
                                id='results-tabs',
                                children=[
                                    make_tab("Tax-benefit policy", "taxbenpol", "tab-taxbenpol"),
                                    make_tab("Poverty", "poverty", "tab-poverty"),
                                    make_tab("Households", "households", "tab-households"),
                                    make_tab("Individuals", "individuals", "tab-individuals"),
                                    make_tab("Poverty graphs", "poverty-graphs", "tab-poverty-graphs"),
                                    make_tab("Inequality", "inequality", "tab-inequality"),
                                    make_tab("Inequality graphs", "inequality-graphs", "tab-inequality-graphs"),
                                    make_tab("Benefits", "benefits", "tab-benefits"),
                                    make_tab("Taxes", "taxes", "tab-taxes"),
                                    make_tab("Policy effects", "policy-effects", "tab-policy-effects"),
                                    make_tab("Gainers & losers", "gainers-losers", "tab-gainers-losers"),
                                ],
                                className="modern-tabs"
                            ),
                        ],
                        type="default",
                        className="results-loading"
                    )
                ], className="modern-card-body"),
                className="modern-card shadow-sm border-0 results-card"
            ),
            width=8,
            className="modern-results-panel"
        )
    ], className="g-4 align-items-start")
], fluid=True, className="app-shell py-4")

# --- CALLBACKS ---


def warm_baseline_cache():
    try:
        df = ensure_input_dataframe()
    except Exception:
        return

    for choice in (1, 2, 3, 4):
        try:
            get_baseline_artifacts(df, choice)
        except Exception:
            continue


warm_baseline_cache()

# Baseline parameters modal callback
@app.callback(
    Output("baseline-modal", "is_open"),
    [Input("view-baseline-button", "n_clicks"), Input("close-baseline-modal", "n_clicks")],
    [State("baseline-modal", "is_open")],
)
def toggle_baseline_modal(n_view, n_close, is_open):
    if n_view or n_close:
        return not is_open
    return is_open

@app.callback(
    Output("devmod-modal", "is_open"),
    [Input("view-devmod-button", "n_clicks"), Input("close-devmod-modal", "n_clicks")],
    [State("devmod-modal", "is_open")],
)
def toggle_devmod_modal(n_view, n_close, is_open):
    if n_view or n_close:
        return not is_open
    return is_open

# Callback for VAT checklist buttons
@app.callback(
    Output('vat-checklist', 'value'),
    Input('vat-select-all', 'n_clicks'),
    Input('vat-deselect-all', 'n_clicks'),
    Input('vat-baseline', 'n_clicks'),
    prevent_initial_call=True
)
def update_vat_checklist(select_all, deselect_all, baseline_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'vat-select-all':
        return list(VAT_ITEM_MAP.keys())
    elif trigger_id == 'vat-deselect-all':
        return []
    elif trigger_id == 'vat-baseline':
        return BASELINE_VAT_STD_RATE_ITEMS
    
    return dash.no_update

@app.callback(
    Output({'type': 'param-input', 'index': MATCH}, 'value'),
    Input({'type': 'param-input', 'index': MATCH}, 'value'),
    Input({'type': 'param-step', 'index': MATCH, 'direction': 'dec'}, 'n_clicks'),
    Input({'type': 'param-step', 'index': MATCH, 'direction': 'inc'}, 'n_clicks'),
    State({'type': 'param-input', 'index': MATCH}, 'id'),
    prevent_initial_call=True
)
def normalize_param_inputs(current_value, dec_clicks, inc_clicks, component_id):
    param_id = component_id.get('index') if isinstance(component_id, dict) else None
    if not param_id:
        return dash.no_update
    meta = get_param_meta(param_id)
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    triggered_id = getattr(ctx, "triggered_id", None)
    if isinstance(triggered_id, dict) and 'direction' in triggered_id:
        direction = triggered_id.get('direction')
        if direction not in {'inc', 'dec'}:
            return dash.no_update
        step = meta.get('step', 1)
        parsed = parse_param_input_value(param_id, current_value)
        if parsed is None:
            parsed = BASELINE_PARAMS.get(param_id, 0)
        if direction == 'inc':
            new_value = parsed + step
        else:
            new_value = parsed - step
        if not meta.get('allow_negative', False) and new_value < 0:
            new_value = 0
        return format_param_value(param_id, new_value)
    trigger = ctx.triggered[0]['prop_id']
    if isinstance(current_value, str):
        stripped = current_value.strip()
        if stripped == "":
            return ""
        normalized_for_pattern = stripped.replace(',', '')
        if stripped.endswith('.'):
            return stripped
        numeric_pattern = r'^-?\d*(?:\.\d*)?$'
        if re.fullmatch(numeric_pattern, normalized_for_pattern):
            if normalized_for_pattern in {"-", "-0", "+", "+0"}:
                return stripped
            if '.' in normalized_for_pattern:
                decimals = normalized_for_pattern.split('.', 1)[1]
                if len(decimals) <= meta.get('precision', 2):
                    return stripped
    if current_value in (None, ""):
        return ""
    parsed = parse_param_input_value(param_id, current_value)
    if parsed is None:
        cleaned = ''.join(ch for ch in str(current_value) if ch in "0123456789.,-")
        if cleaned == str(current_value):
            return dash.no_update
        return cleaned
    formatted = format_param_value(param_id, parsed)
    if formatted == str(current_value):
        return dash.no_update
    return formatted

# Callback for tab information modals
@app.callback(
    Output("info-modal", "is_open"),
    Output("info-modal-title", "children"),
    Output("info-modal-body", "children"),
    Input({'type': 'info-button', 'index': ALL}, 'n_clicks'),
    Input("close-info-modal", "n_clicks"),
    State("info-modal", "is_open"),
)
def toggle_info_modal(info_clicks, close_click, is_open):
    ctx = dash.callback_context
    
    # Check if any button was clicked
    if not ctx.triggered or all(c is None for c in info_clicks) and close_click is None:
        return False, "", ""
    
    trigger_id_str = ctx.triggered[0]['prop_id']
    
    if "close-info-modal" in trigger_id_str:
        return False, "", ""
    
    if "info-button" in trigger_id_str:
        # Extract index from the triggered component's ID
        try:
            trigger_id_dict = json.loads(trigger_id_str.split('.')[0])
            trigger_index = trigger_id_dict['index']
        except Exception:
            return False, "", "" # Failed to parse ID
        
        content = INFO_MODAL_CONTENT.get(trigger_index, INFO_MODAL_CONTENT['default'])
        body = content.get('body', '') if isinstance(content, dict) else ''
        body = normalize_html_text(body)
        return True, content.get('title', ''), body
        
    return is_open, "", ""


# Main simulation and results callback
@app.callback(
    [Output(f'tab-{tab_name}', 'children') for tab_name in 
     ['taxbenpol', 'poverty', 'households', 'individuals', 'poverty-graphs', 
      'inequality', 'inequality-graphs', 'benefits', 'taxes', 
      'policy-effects', 'gainers-losers']],
    Output('loading-output', 'children'),
    Output('results-title', 'children'),  # Title for the results card
    Output('download-simulation-output', 'data'),  # Excel download payload
    Input('run-button', 'n_clicks'),
    State('analysis-choice', 'value'),
    State('reform-name-input', 'value'),  # Reform name input
    State('generate-excel-switch', 'value'),  # Excel export toggle
    State({'type': 'param-input', 'index': ALL}, 'id'),
    State({'type': 'param-input', 'index': ALL}, 'value'),
    State('vat-checklist', 'value')  # Selected VAT checklist values
)
def run_and_display_results(n_clicks, analysis_choice, reform_name, generate_excel, 
                            param_ids, param_values, vat_checklist_value):    
    dev_placeholder = html.Div(dbc.Alert("Output for this tab is under development.", color="info"), className="p-4")
    run_placeholder = html.Div(dbc.Alert("Run a simulation to see results.", color="info"), className="p-4")
    if not n_clicks:
        return [run_placeholder, run_placeholder] + [dev_placeholder] * 9 + ["", "", dash.no_update]

    try:
        analysis_choice = int(analysis_choice)
    except (TypeError, ValueError):
        analysis_choice = 3

    try:
        try:
            df = ensure_input_dataframe()
        except FileNotFoundError:
            error_msg = dbc.Alert(
                f"Error: Input file '{INPUT_FILE}' not found in the application folder.",
                color="danger"
            )
            return [error_msg] * 11 + ["Error", "", dash.no_update]
        except Exception as e:
            error_msg = dbc.Alert(f"Error loading '{INPUT_FILE}': {e}", color="danger")
            return [error_msg] * 11 + ["Error", "", dash.no_update]

        baseline_artifacts = get_baseline_artifacts(df, analysis_choice)
        baseline_results = baseline_artifacts['results']
        baseline_analysis_df = baseline_artifacts['merge_df']

        reform_params = BASELINE_PARAMS.copy()
        user_reform_values = {}
        for pid, raw_val in zip(param_ids, param_values):
            param_key = pid.get('index') if isinstance(pid, dict) else None
            if not param_key:
                continue
            parsed_val = parse_param_input_value(param_key, raw_val)
            if parsed_val is None:
                continue
            user_reform_values[param_key] = parsed_val
        reform_params.update(user_reform_values)
        reform_params['vat_items_list'] = vat_checklist_value
        
        reform_sim_df = run_simulation(df, reform_params)
        reform_results, reform_analysis_df = run_analysis(reform_sim_df, analysis_choice, baseline_analysis_df)

    except Exception as e:
        import traceback
        print(f"Error during simulation: {e}")
        traceback.print_exc()
        error_msg = dbc.Alert([
            html.H5("An error occurred during simulation:", className="alert-heading"),
            html.P(f"Error: {e}"),
            html.P("Please check your input data. Common issues include missing 'dag' column or 0 weights.")
        ], color="danger")
        return [error_msg] * 11 + ["Simulation failed.", "Error", dash.no_update]

    # --- Generate TaxBenPol Tab Content ---
    tbp_rows = ['Sum of government revenue', 'By source', '- Direct taxes', '- Social insurance contributions', '- Indirect taxes',
                'Sum of government expenditure', 'By type', '- Cash benefits', '- In-kind benefits', '- Indirect subsidies']
    
    abs_data = {'Component': tbp_rows, 'Baseline': [], 'Reform': []}
    for row in tbp_rows:
        key = row.replace('- ','')
        if key in baseline_results['taxbenpol_abs']:
            # Multiply monthly totals by 12 to get yearly totals (in millions)
            abs_data['Baseline'].append(baseline_results['taxbenpol_abs'][key] * 12 / 1e6)
            abs_data['Reform'].append(reform_results['taxbenpol_abs'][key] * 12 / 1e6)
        else:
            abs_data['Baseline'].append(None) # Use None for blank rows
            abs_data['Reform'].append(None)

    abs_df = pd.DataFrame(abs_data)
    if 'Component' in abs_df.columns:
        abs_df = abs_df.rename(columns={'Component': ''})
    abs_df['Difference'] = abs_df.apply(lambda row: row['Reform'] - row['Baseline'] if pd.notna(row['Reform']) and pd.notna(row['Baseline']) else None, axis=1)
    abs_df_excel = abs_df.copy()
    abs_df['Difference'] = abs_df['Difference'].apply(format_signed_value)
    tab1_part1 = create_styled_table(abs_df.to_dict('list'), "Total revenue and expenditure", "(yearly, millions of national currency)")

    share_rows = ['By source', '- Direct taxes', '- Social insurance contributions', '- Indirect taxes',
                  'By type', '- Cash benefits', '- In-kind benefits', '- Indirect subsidies']
    share_data = {'Component': share_rows, 'Baseline (%)': [], 'Reform (%)': []}
    for row in share_rows:
        key = row.replace('- ','')
        if key in baseline_results['taxbenpol_share']:
            share_data['Baseline (%)'].append(baseline_results['taxbenpol_share'][key])
            share_data['Reform (%)'].append(reform_results['taxbenpol_share'][key])
        else:
            share_data['Baseline (%)'].append(None)
            share_data['Reform (%)'].append(None)
            
    share_df = pd.DataFrame(share_data)
    if 'Component' in share_df.columns:
        share_df = share_df.rename(columns={'Component': ''})
    share_df['Difference (pp.)'] = share_df.apply(lambda row: row['Reform (%)'] - row['Baseline (%)'] if pd.notna(row['Reform (%)']) and pd.notna(row['Baseline (%)']) else None, axis=1)
    share_df_excel = share_df.copy()
    share_df['Difference (pp.)'] = share_df['Difference (pp.)'].apply(format_signed_value)
    tab1_part2 = create_styled_table(share_df.to_dict('list'), "Shares of total revenue and expenditure", "(%)")
    tab1_content = tab1_part1 + tab1_part2

    # --- Generate Poverty Tab Content ---
    pov_row_map = {
        'All individuals': 'All individuals',
        'header_hh_structure': 'Household structure',
        'isSinglePersonHH': '- Single person',
        'is1AdultWithChildrenHH': '- Single parent',
        'is2AdultsNoChildrenHH': '- 2 adults without children',
        'is2Adults1_2ChildrenHH': '- 2 adults with 1-2 children',
        'is2Adults3_4ChildrenHH': '- 2 adults with 3-4 children',
        'is2Adults5plusChildrenHH': '- 2 adults with 5+ children',
        'is3plusAdultsNoChildrenHH': '- 3+ adults without children',
        'is3plusAdultsWithChildrenHH': '- 3+ adults with children',
        'header_vulnerable': 'Vulnerable households',
        'isYoungChildHH': '- HH with young child (0-2)',
        'isAtLeastOneElderlyHH': '- HH with elderly member',
        'isAtLeastOneDisabledHH': '- HH with disabled member',
        'isNoMaleAdultHH': '- HH with no male adults',
        'header_labor': 'Labour market status',
        'isNoTotalHHEarningsHH': '- HH with no labour income',
        'isInformalAdultHH': '- HH with informal adult(s)',
        'isNoInformalAdultsHH': '- HH with no informal adults'
    }
    
    pov_rate_data = {'Household category': [], 'Baseline (%)': [], 'Reform (%)': []}
    pov_gap_data = {'Household category': [], 'Baseline (%)': [], 'Reform (%)': []}
    
    for k, v in pov_row_map.items():
        pov_rate_data['Household category'].append(v)
        pov_gap_data['Household category'].append(v)
        
        # This is a data row
        if not k.startswith('header_'):
            pov_rate_data['Baseline (%)'].append(baseline_results['poverty'][k]['Poverty rate (%)'])
            pov_rate_data['Reform (%)'].append(reform_results['poverty'][k]['Poverty rate (%)'])
            pov_gap_data['Baseline (%)'].append(baseline_results['poverty'][k]['Poverty gap (%)'])
            pov_gap_data['Reform (%)'].append(reform_results['poverty'][k]['Poverty gap (%)'])
        # This is a header row
        else:
            for data_dict in [pov_rate_data, pov_gap_data]:
                data_dict['Baseline (%)'].append(None) # Use None for blanks
                data_dict['Reform (%)'].append(None)
    
    pov_rate_df = pd.DataFrame(pov_rate_data)
    pov_gap_df = pd.DataFrame(pov_gap_data)
    if 'Household category' in pov_rate_df.columns:
        pov_rate_df = pov_rate_df.rename(columns={'Household category': ''})
    if 'Household category' in pov_gap_df.columns:
        pov_gap_df = pov_gap_df.rename(columns={'Household category': ''})

    def calc_diff(row):
        if pd.notna(row['Reform (%)']) and pd.notna(row['Baseline (%)']):
            return row['Reform (%)'] - row['Baseline (%)']
        return None
        
    pov_rate_df['Difference (pp.)'] = pov_rate_df.apply(calc_diff, axis=1)
    pov_gap_df['Difference (pp.)'] = pov_gap_df.apply(calc_diff, axis=1)
    pov_rate_df_excel = pov_rate_df.copy()
    pov_gap_df_excel = pov_gap_df.copy()
    pov_rate_df['Difference (pp.)'] = pov_rate_df['Difference (pp.)'].apply(format_signed_value)
    pov_gap_df['Difference (pp.)'] = pov_gap_df['Difference (pp.)'].apply(format_signed_value)

    # Display poverty line as a yearly value
    povline_text = f"Absolute national poverty line used (yearly): {baseline_results['poverty']['povline']*12:,.2f}"
    
    tab2_content = create_styled_table(pov_rate_df.to_dict('list'), "Poverty rate", "(share of poor population, %)") + \
                   create_styled_table(pov_gap_df.to_dict('list'), "Poverty gap", "(average normalised poverty gap, %)") + \
                   [dbc.Alert(povline_text, color="secondary", className="mt-3")]

    # --- Placeholder tabs ---
    placeholder_content = [dev_placeholder]
    
    # --- Prepare Download Data ---
    download_output = dash.no_update
    
    if generate_excel:
        try:
            generation_dt = datetime.now()
            generation_date = generation_dt.strftime("%Y-%m-%d_%H-%M")
            generation_display = generation_dt.strftime("%Y-%m-%d %H:%M")

            def format_value_display(value):
                if isinstance(value, (int, float)):
                    formatted = f"{value:,.4f}".rstrip('0').rstrip('.')
                    return formatted if formatted else "0"
                return str(value)

            distribution_labels = {
                1: "Consumption based",
                2: "Income based",
                3: "Consumption based, net of indirect taxes",
                4: "Income based, net of indirect taxes",
            }
            distribution_label = distribution_labels.get(analysis_choice, "Income based")

            policy_changes_lines = []
            for key, val in user_reform_values.items():
                if key == 'vat_items_list':
                    continue
                baseline_val = BASELINE_PARAMS.get(key)
                current_display = format_value_display(val)
                baseline_display = format_value_display(baseline_val) if baseline_val is not None else "n/a"
                if baseline_display == current_display:
                    continue
                policy_changes_lines.append(f"{key}: {baseline_display} -> {current_display}")

            selected_vat = vat_checklist_value or []
            policy_changes_lines.append(
                f"Selected standard-rated VAT items (count): {len(selected_vat)}/{TOTAL_VAT_ITEMS} "
                f"(baseline {len(BASELINE_VAT_STD_RATE_ITEMS)}/{TOTAL_VAT_ITEMS})"
            )
            if set(selected_vat) != set(BASELINE_VAT_STD_RATE_ITEMS):
                added = sorted(set(selected_vat) - set(BASELINE_VAT_STD_RATE_ITEMS))
                removed = sorted(set(BASELINE_VAT_STD_RATE_ITEMS) - set(selected_vat))
                if added:
                    policy_changes_lines.append(
                        "  Added: " + "; ".join(VAT_ITEM_MAP.get(item, {}).get('label', item) for item in added)
                    )
                if removed:
                    policy_changes_lines.append(
                        "  Removed: " + "; ".join(VAT_ITEM_MAP.get(item, {}).get('label', item) for item in removed)
                    )

            policy_changes_lines = [line for line in policy_changes_lines if line]

            info_rows = [
                {"Field": "Reform name", "Value": reform_name or "My reform"},
                {"Field": "Distribution statistic", "Value": distribution_label},
                {"Field": "Date/time generated", "Value": generation_display},
                {"Field": "Input file", "Value": INPUT_FILE},
                {"Field": "Baseline system", "Value": "2023"},
            ]
            if policy_changes_lines:
                info_rows.append({"Field": "Policy changes", "Value": policy_changes_lines[0]})
                for line in policy_changes_lines[1:]:
                    info_rows.append({"Field": "", "Value": line})
            else:
                info_rows.append({"Field": "Policy changes", "Value": "None"})

            info_df = pd.DataFrame(info_rows)

            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
                info_df.to_excel(writer, sheet_name='Info', index=False, header=False)

                table_specs = [
                    ('TaxBenPolicy', 'taxbenpol', [
                        (abs_df_excel, "Total revenue and expenditure (yearly, millions of national currency).", ["Difference"]),
                        (share_df_excel, "Shares of total revenue and expenditure (%).", ["Difference (pp.)"]),
                    ]),
                    ('Poverty', 'poverty', [
                        (pov_rate_df_excel, "Poverty rate (share of poor population, %).", ["Difference (pp.)"]),
                        (pov_gap_df_excel, "Poverty gap (average normalised poverty gap, %).", ["Difference (pp.)"]),
                    ]),
                ]

                sheet_meta = {}
                for sheet_name, info_key, tables in table_specs:
                    description_lines = []
                    if info_key and info_key in INFO_MODAL_CONTENT:
                        description_text = html_to_plain_text(INFO_MODAL_CONTENT[info_key].get('body', ''))
                        if description_text:
                            description_lines = [line for line in description_text.split('\n')]
                    sheet_meta[sheet_name] = {
                        'sections': [],
                        'description_lines': description_lines,
                    }
                    start_row = 0
                    for df_excel, note, diff_columns in tables:
                        title_row = start_row + 1
                        subtitle_row = start_row + 2
                        data_start = start_row + 3

                        ws = writer.sheets.get(sheet_name)
                        if ws is None:
                            df_excel.to_excel(writer, sheet_name=sheet_name, index=False, startrow=data_start)
                            ws = writer.sheets[sheet_name]
                        else:
                            df_excel.to_excel(writer, sheet_name=sheet_name, index=False, startrow=data_start)

                        for col_idx, col_name in enumerate(df_excel.columns, start=1):
                            if col_name in diff_columns:
                                for row_idx in range(data_start + 1, data_start + df_excel.shape[0] + 1):
                                    cell = ws.cell(row=row_idx, column=col_idx)
                                    cell.alignment = Alignment(horizontal='right')
                                    cell.number_format = "+0.00;-0.00;0.00"

                        title_cell = ws.cell(row=title_row, column=1, value=note.split(' (')[0])
                        title_cell.font = Font(bold=True, italic=True, size=13, color="000000")
                        subtitle_cell = ws.cell(row=subtitle_row, column=1, value=note)
                        subtitle_cell.font = Font(italic=True, color="1f2937")

                        sheet_meta[sheet_name]['sections'].append({
                            'start_row': data_start,
                            'title_row': title_row,
                            'subtitle_row': subtitle_row,
                            'col_count': df_excel.shape[1],
                            'row_count': df_excel.shape[0] + 1,
                            'note': note,
                        })
                        start_row = data_start + df_excel.shape[0] + 4

                # Placeholder tabs
                placeholder_sheets = ['Households', 'Individuals', 'Poverty_Graphs', 
                                      'Inequality', 'Inequality_Graphs', 'Benefits', 
                                      'Taxes', 'Policy_Effects', 'Gainers_Losers']
                placeholder_df = pd.DataFrame(["Output for this tab is under development."])
                for sheet in placeholder_sheets:
                    placeholder_df.to_excel(writer, sheet_name=sheet, index=False, header=False)

                wb = writer.book
                info_ws = wb['Info']
                info_ws.column_dimensions['A'].width = 24
                info_ws.column_dimensions['B'].width = 70
                for row in info_ws.iter_rows(min_row=1, max_col=1):
                    for cell in row:
                        cell.font = Font(bold=True)

                for sheet_name, meta in sheet_meta.items():
                    if sheet_name not in wb.sheetnames:
                        continue
                    ws = wb[sheet_name]
                    max_cols = max(section['col_count'] for section in meta['sections'])
                    ws.column_dimensions['A'].width = 44
                    for col_idx in range(2, max_cols + 1):
                        col_letter = get_column_letter(col_idx)
                        ws.column_dimensions[col_letter].width = 18
                    for section in meta['sections']:
                        start_row = section['start_row']
                        col_count = section['col_count']
                        row_count = section['row_count']
                        note = section['note']

                        header_row = start_row + 1
                        for col_idx in range(2, col_count + 1):
                            header_cell = ws.cell(row=header_row, column=col_idx)
                            header_cell.alignment = Alignment(horizontal='right', vertical='center')
                            header_cell.font = Font(bold=True)
                            for data_row in range(header_row + 1, header_row + row_count):
                                cell = ws.cell(row=data_row, column=col_idx)
                                if isinstance(cell.value, (int, float)):
                                    cell.number_format = '#,##0.00'
                                    cell.alignment = Alignment(horizontal='right', vertical='center')
                        last_row = header_row + row_count - 1
                        for data_row in range(header_row + 1, header_row + row_count):
                            first_cell = ws.cell(row=data_row, column=1)
                            first_val = (first_cell.value or "").strip()
                            if first_val in TABLE_HEADER_LABELS or first_val in TABLE_STRONG_LABELS:
                                for col_idx in range(1, col_count + 1):
                                    ws.cell(row=data_row, column=col_idx).font = Font(bold=True)
                            if first_val in TABLE_HEADER_LABELS or first_val in TABLE_STRONG_LABELS:
                                first_cell.alignment = Alignment(horizontal='left', vertical='center')

                        section['last_row'] = last_row

                    description_lines = extract_description_lines(info_key)
                    if description_lines:
                        last_used_row = max(sec.get('last_row', sec['start_row'] + sec['row_count'] - 1) for sec in meta['sections'])
                        desc_row = last_used_row + 2
                        ws.cell(row=desc_row, column=1, value="Description:").font = Font(bold=True)
                        desc_row += 1
                        for style, text in description_lines:
                            cell = ws.cell(row=desc_row, column=1, value=text)
                            if style == 'header':
                                cell.font = Font(bold=True, color="1D4ED8")
                            else:
                                cell.font = Font(italic=False)
                            desc_row += 1

            excel_data = output_stream.getvalue()
            download_output = dcc.send_bytes(excel_data, f"DEVMOD_online_output_{generation_date}.xlsx")
            
        except Exception as e:
            print(f"Error generating Excel file: {e}")
            # If Excel fails, don't crash the whole app
            download_output = dash.no_update 
            # Optionally, update the loading message to show an error
            # ...

    # Set dynamic results title
    results_title_text = f"Baseline vs. Reform ({reform_name})"

    return (
        tab1_content, 
        tab2_content, 
        *([placeholder_content] * 9), 
        "Simulation complete.", 
        results_title_text,
        download_output
    )


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
