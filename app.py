import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# -----------------------------
# 1. Page configuration
# -----------------------------
st.set_page_config(page_title="India Economic Dashboard", layout="wide")

st.title("🇮🇳 India Economic Intelligence Dashboard")
st.markdown("Interactive state-level dashboard for GDP and scores")

# -----------------------------
# 2. Load shapefile
# -----------------------------
@st.cache_data
def load_shapefile():
    gdf = gpd.read_file("data/raw/india_states/StateBoundary.shp")
    gdf = gdf.to_crs(epsg=4326)  # Convert to lat/lon
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
    return gdf

india_map = load_shapefile()

# -----------------------------
# 3. Load GDP + Scores
# -----------------------------
@st.cache_data
def load_gdp():
    # Example GDP data
    df = pd.read_csv("data/raw/economic/state_gdp.csv")
    # Ensure uppercase for merge
    df['State'] = df['State'].str.upper()
    india_map['state_upper'] = india_map['state'].str.upper()
    
    # Example: add dummy scores if not present
    df['infrastructure_score'] = 0.5
    df['education_score'] = 0.5
    df['healthcare_score'] = 0.5
    df['population_score'] = 0.5
    
    merged = india_map.merge(df, left_on='state_upper', right_on='State', how='left')
    
    # Economic score = weighted sum (default weights)
    merged['economic_score'] = (
        0.25*merged['infrastructure_score'] +
        0.25*merged['education_score'] +
        0.25*merged['healthcare_score'] +
        0.25*merged['population_score']
    )
    return merged

merged_map = load_gdp()

# -----------------------------
# 4. Sidebar sliders for weights
# -----------------------------
st.sidebar.title("Adjust Economic Score Weights")

infra_w = st.sidebar.slider("Infrastructure", 0.0, 1.0, 0.25)
edu_w = st.sidebar.slider("Education", 0.0, 1.0, 0.25)
health_w = st.sidebar.slider("Healthcare", 0.0, 1.0, 0.25)
pop_w = st.sidebar.slider("Population", 0.0, 1.0, 0.25)

total_w = infra_w + edu_w + health_w + pop_w
if total_w == 0:
    total_w = 1  # avoid division by zero

merged_map['economic_score'] = (
    (infra_w*merged_map['infrastructure_score'] +
     edu_w*merged_map['education_score'] +
     health_w*merged_map['healthcare_score'] +
     pop_w*merged_map['population_score']) / total_w
)

# -----------------------------
# 5. Create Folium map
# -----------------------------
m = folium.Map(location=[22.5937, 78.9629], zoom_start=5)

folium.Choropleth(
    geo_data=merged_map,
    data=merged_map,
    columns=['state', 'economic_score'],
    key_on='feature.properties.state',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name='Economic Score'
).add_to(m)

# Add tooltips with GDP and scores
for _, row in merged_map.iterrows():
    folium.Marker(
        location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
        popup=(
            f"<b>{row['state']}</b><br>"
            f"GDP: ₹{row['GDP_Crore_2024_25']} Cr<br>"
            f"Infrastructure: {row['infrastructure_score']}<br>"
            f"Education: {row['education_score']}<br>"
            f"Healthcare: {row['healthcare_score']}<br>"
            f"Population: {row['population_score']}<br>"
            f"Economic Score: {row['economic_score']:.2f}"
        ),
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

# -----------------------------
# 6. Display map in Streamlit
# -----------------------------
st.subheader("India Economic Map")
st_data = st_folium(m, width=1200, height=700, returned_objects=[])

# -----------------------------
# 7. Display dataframe
# -----------------------------
st.subheader("State-wise Economic Data")
st.dataframe(merged_map[['state', 'GDP_Crore_2024_25', 'infrastructure_score',
                         'education_score','healthcare_score','population_score','economic_score']])