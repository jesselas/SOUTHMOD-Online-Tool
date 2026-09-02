# SOUTHMOD Online Tool - DEVMOD Dashboard

A web application built with Dash and Plotly for tax-benefit microsimulation analysis. It simulates and analyses policy reforms using the **DEVMOD synthetic microsimulation model**. DEVMOD is developed under the [UNU-WIDER SOUTHMOD project](https://www.wider.unu.edu/project/southmod-simulating-tax-and-benefit-policies-development-phase-3), runs on the EUROMOD platform, and uses artificial data for training and experimentation, mirroring real SOUTHMOD models.

The tool allows users to:

* run the baseline 2023 DEVMOD policy system
* define policy reform scenarios by modifying parameters, or apply a predefined reform
* compare the distributional and budgetary impacts of the reform against the baseline
* explore results through interactive tables and graphs

It serves as a web-based interface for analysis, particularly useful for the DEVMOD model taught in the [SOUTHMOD online course](https://www.wider.unu.edu/about/southmod-online-course). The outputs replicate what DEVMOD produces when run and analysed in EUROMOD with the SOUTHMOD Statistics Presenter.

---

## Features

* **Reform simulation:** Runs the pre-defined 2023 DEVMOD policy system and allows parameter modification for PIT, SIC, presumptive taxes, VAT (rate and exemptions via checklist), social assistance, senior grants, and school meals. Parameter inputs enforce sensible hard limits, and every parameter that differs from the baseline is highlighted.
* **Predefined reforms:** "Raise taxes" and "Increase benefits" apply ready-made parameter packages that can be combined and layered on top of manual edits; hovering over either shows what it changes.
* **Comparative analysis:** Displays results for both baseline and reform scenarios, including differences.
* **Multiple analysis dimensions:** Presents results across tabs covering budgetary impacts, household/individual counts, poverty, inequality, benefit/tax incidence, policy effects, and gainers/losers.
* **Distribution statistic choice:** Allows analysis based on different concepts (consumption/income, pre/post indirect taxes).
* **Simplified tab set:** Five result tabs are shown by default; "Show additional tabs" reveals the full set.
* **EUROMOD-consistent statistics:** Deciles, Gini, and redistribution measures replicate the algorithms of EUROMOD's open-source statistics engine.
* **Hover help:** Explanations for each step, the run button, the predefined reforms, DEVMOD background and every results tab appear as cards in the results area; parameter units appear as small tooltips.
* **Policy change summary:** Modal summarizing parameter changes made.
* **Responsive design:** Adapts layout for different screen sizes.

---

## Technology stack

* **Language:** Python 3
* **Web Framework:** Dash
* **UI Components:** Dash Bootstrap Components
* **Charting:** Plotly
* **Data Manipulation:** Pandas, NumPy

---

## Setup and installation

1.  **Prerequisites:**
    * Python (version 3.9 or higher recommended)
    * pip (Python package installer)

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/jesselas/SOUTHMOD-Online-Tool.git
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Input Data:**
    * Ensure the synthetic input microdata file `dv_2020_a1.txt` is present in the root directory (included in this repository)

6.  **Run the Application:**
    ```bash
    python app.py
    ```

7.  **Access the Dashboard:**
    * Open your web browser to `http://127.0.0.1:8051` (or the address provided)

---

## Usage guide

1.  **Configure reform:** Modify parameters in the accordions, or apply one of the predefined reforms below them. Changed parameters are highlighted, and hovering a parameter label shows its units.
2.  Select the desired **distribution statistic** for analysis.
3.  Click **Run simulation** to generate outputs. A run needs at least one changed parameter.
4.  Explore results via the tabs. "Show additional indicators" reveals the remaining tabs, and "Policy changes" lists the parameter changes behind the results.
5.  Hovering the numbered steps, the run button, "DEVMOD info" or "Description of tab's indicators" opens an explanation in the results area; hovering a predefined reform shows exactly what it changes.

---

## Validation

`validation/` contains scripts used to verify the app against DEVMOD v1.1 run in EUROMOD (person-level microdata comparison and headline-statistics assertions). They require local reference files that are not part of this repository.
