import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="CarDekho Analytics", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
/* Enhance the top KPI cards */
div.stMetric[data-testid="metric-container"] {
    background-color: #1e293b;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0px 8px 16px rgba(0,0,0,0.15);
    border: 1px solid #3c3c54;
    transition: transform 0.2s ease-in-out;
}
div.stMetric[data-testid="metric-container"]:hover {
    transform: translateY(-5px);
}
/* Title & subtitle adjustments */
h1 {
    color: #00f2fe;
    font-weight: 700;
}
h2, h3 {
    color: #ffffff;
    border-left: 5px solid #00f2fe;
    padding-left: 12px;
    background: linear-gradient(90deg, rgba(0,242,254,0.15) 0%, rgba(0,0,0,0) 100%);
    border-radius: 4px;
    padding-top: 8px;
    padding-bottom: 8px;
}
/* Hide the Deploy button and Main Menu */
.stDeployButton {
    display: none;
}
#MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Read the dataset and drop the unnamed index column if it exists
    df = pd.read_csv("cardekho_dataset.csv")
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    return df

df_full = load_data()

# Clean some data, ensure proper types if necessary
# e.g., mapping transmission, fuel_type etc.
# Some processing if `selling_price` is missing or something, but the dataset looks clean.

st.title("CarDekho Analytics Dashboard")
st.markdown("Analyze used car prices, depreciation trends, and filter by top-selling brands.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

# Brand Filter
brands = df_full['brand'].unique().tolist()
selected_brands = st.sidebar.multiselect("Select Brand(s)", sorted(brands), default=[])

# Model Filter (Depends on Brand)
if selected_brands:
    models = df_full[df_full['brand'].isin(selected_brands)]['model'].unique().tolist()
else:
    models = df_full['model'].unique().tolist()
selected_models = st.sidebar.multiselect("Select Model(s)", sorted(models), default=[])

# Fuel Type
fuel_types = df_full['fuel_type'].unique().tolist()
selected_fuel = st.sidebar.multiselect("Fuel Type", fuel_types, default=fuel_types)

# Transmission
transmissions = df_full['transmission_type'].unique().tolist()
selected_transmission = st.sidebar.multiselect("Transmission", transmissions, default=transmissions)

# Year/Age Slider
min_age = int(df_full['vehicle_age'].min())
max_age = int(df_full['vehicle_age'].max())
selected_age_range = st.sidebar.slider("Vehicle Age (Years)", min_value=min_age, max_value=max_age, value=(min_age, max_age))

# Apply Filters
df = df_full.copy()
if selected_brands:
    df = df[df['brand'].isin(selected_brands)]
if selected_models:
    df = df[df['model'].isin(selected_models)]
if selected_fuel:
    df = df[df['fuel_type'].isin(selected_fuel)]
if selected_transmission:
    df = df[df['transmission_type'].isin(selected_transmission)]

df = df[(df['vehicle_age'] >= selected_age_range[0]) & (df['vehicle_age'] <= selected_age_range[1])]

# --- TOP SUMMARY CARDS (KPIs) ---
st.markdown("### Key Performance Indicators")
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

total_cars = len(df)
avg_price = df['selling_price'].mean() if total_cars > 0 else 0
highest_price = df['selling_price'].max() if total_cars > 0 else 0
lowest_price = df['selling_price'].min() if total_cars > 0 else 0
avg_mileage = df['mileage'].mean() if total_cars > 0 else 0
total_brands_available = df['brand'].nunique()

def format_currency(val):
    if val >= 10000000:
        return f"₹{val/10000000:.2f} Cr"
    elif val >= 100000:
        return f"₹{val/100000:.2f} L"
    return f"₹{val:,.0f}"

with kpi1:
    st.metric(label="Total Cars Listed", value=f"{total_cars:,}")
with kpi2:
    st.metric(label="Average Price", value=format_currency(avg_price))
with kpi3:
    st.metric(label="Highest Price", value=format_currency(highest_price))
with kpi4:
    st.metric(label="Lowest Price", value=format_currency(lowest_price))
with kpi5:
    st.metric(label="Average Mileage", value=f"{avg_mileage:.1f} kmpl")
with kpi6:
    st.metric(label="Total Brands", value=total_brands_available)

st.markdown("<hr/>", unsafe_allow_html=True)

# --- INTERACTIVE VISUALIZATIONS ---
col1, col2 = st.columns([1, 1])

# Chart 1: Price Trend by Year/Age
with col1:
    st.subheader("Price Depreciation by Age")
    # Group by age and get avg price
    price_by_age = df.groupby('vehicle_age')['selling_price'].mean().reset_index()
    fig1 = px.line(price_by_age, x='vehicle_age', y='selling_price', markers=True, 
                   labels={'vehicle_age':'Vehicle Age (Years)', 'selling_price': 'Average Price (₹)'},
                   color_discrete_sequence=['#00f2fe'])
    fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Average Price by Brand
with col2:
    st.subheader("Average Price by Brand")
    top_brands = df['brand'].value_counts().head(10).index # Focus on top 10 populated
    brand_avg_price = df[df['brand'].isin(top_brands)].groupby('brand')['selling_price'].mean().sort_values(ascending=False).reset_index()
    fig2 = px.bar(brand_avg_price, x='brand', y='selling_price',
                  labels={'brand': 'Brand', 'selling_price': 'Average Price (₹)'},
                  color_discrete_sequence=['#ff9a44'])
    fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)


col3, col4 = st.columns([1, 1])

# Chart 3: Fuel Type Distribution
with col3:
    st.subheader("Fuel Type Distribution")
    fuel_counts = df['fuel_type'].value_counts().reset_index()
    fuel_counts.columns = ['fuel_type', 'count']
    fig3 = px.pie(fuel_counts, values='count', names='fuel_type', hole=0.4,
                  color_discrete_sequence=px.colors.sequential.Teal)
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Mileage vs Price Scatter
with col4:
    st.subheader("Mileage vs Price")
    # Sample data slightly to prevent lag on big scatters if needed (but 15k is okay for plotly)
    fig4 = px.scatter(df, x='mileage', y='selling_price', color='fuel_type', opacity=0.6,
                      labels={'mileage': 'Mileage (kmpl)', 'selling_price': 'Price (₹)'},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# --- CAR COMPARISON MODULE ---
st.markdown("### Compare Two Cars Side-by-Side")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    car1_search = st.selectbox("Search First Car", df_full['car_name'].unique(), key="car1_select")
    car1_data = df_full[df_full['car_name'] == car1_search].iloc[0] if not df_full[df_full['car_name'] == car1_search].empty else None

with filter_col2:
    car2_search = st.selectbox("Search Second Car", df_full['car_name'].unique(), index=min(1, len(df_full['car_name'].unique())-1), key="car2_select")
    car2_data = df_full[df_full['car_name'] == car2_search].iloc[0] if not df_full[df_full['car_name'] == car2_search].empty else None

if car1_data is not None and car2_data is not None:
    comp_c1, comp_c2 = st.columns(2)
    
    def compare_metric(label, v1, v2, suffix="", reverse_good=False, is_currency=False):
        d1 = format_currency(v1) if is_currency else f"{v1}{suffix}"
        d2 = format_currency(v2) if is_currency else f"{v2}{suffix}"
        
        # Determine color
        c1, c2 = "white", "white"
        if v1 != v2:
            if type(v1) in [int, float] and type(v2) in [int, float]:
                better_is_higher = not reverse_good
                if (v1 > v2 and better_is_higher) or (v1 < v2 and not better_is_higher):
                    c1 = "#00f2fe" # Winner color
                else:
                    c2 = "#00f2fe"

        with comp_c1:
            st.markdown(f"<div style='padding: 10px; background: #1e293b; border-radius: 8px; margin-bottom: 5px; color:{c1}'><small>{label}</small><br/><b>{d1}</b></div>", unsafe_allow_html=True)
        with comp_c2:
            st.markdown(f"<div style='padding: 10px; background: #1e293b; border-radius: 8px; margin-bottom: 5px; color:{c2}'><small>{label}</small><br/><b>{d2}</b></div>", unsafe_allow_html=True)

    compare_metric("Price", car1_data['selling_price'], car2_data['selling_price'], reverse_good=True, is_currency=True)
    compare_metric("Mileage", car1_data['mileage'], car2_data['mileage'], suffix=" kmpl")
    compare_metric("Vehicle Age", car1_data['vehicle_age'], car2_data['vehicle_age'], suffix=" Years", reverse_good=True)
    compare_metric("Engine", car1_data['engine'], car2_data['engine'], suffix=" CC")
    compare_metric("Max Power", float(car1_data['max_power']) if str(car1_data['max_power']).replace('.', '', 1).isdigit() else 0, 
                   float(car2_data['max_power']) if str(car2_data['max_power']).replace('.', '', 1).isdigit() else 0, suffix=" bhp")


st.markdown("<hr/>", unsafe_allow_html=True)

# --- DETAILED INSIGHTS ---
st.markdown("### Detailed Insights")
i_col1, i_col2 = st.columns(2)

with i_col1:
    st.markdown("#### Top 5 Most Expensive Cars")
    top_exp = df.nlargest(5, 'selling_price')[['car_name', 'selling_price', 'year', 'mileage']] if 'year' in df.columns else df.nlargest(5, 'selling_price')[['car_name', 'selling_price', 'vehicle_age', 'mileage']]
    st.dataframe(top_exp, use_container_width=True, hide_index=True)

with i_col2:
    st.markdown("#### Top 5 Value Deals (Low Price + High Mileage)")
    # Simple value score: Mileage / Price (Higher is better)
    # Just avoiding divide by zero
    temp_df = df[df['selling_price'] > 50000].copy() # Ensure realistic cars
    temp_df['Value Score'] = temp_df['mileage'] / temp_df['selling_price']
    top_value = temp_df.nlargest(5, 'Value Score')[['car_name', 'selling_price', 'mileage', 'vehicle_age']]
    st.dataframe(top_value, use_container_width=True, hide_index=True)

