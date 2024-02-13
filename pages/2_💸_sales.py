import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from matplotlib.colors import to_hex
import plotly.express as px
import matplotlib.pyplot as plt
import branca 
from branca.colormap import linear
from plotly.subplots import make_subplots
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point, Polygon
from folium import Choropleth, Circle, Marker
from folium.plugins import HeatMap, MarkerCluster
import plotly.graph_objects as go
from streamlit_folium import folium_static
import locale
from pinotdb import connect

# Global variables
product_items = ['Blouse', 'Jewelry', 'Pants', 'Shirt', 'Dress', 'Sweater',\
    'Jacket', 'Belt', 'Sunglasses', 'Coat', 'Sandals', 'Socks',\
    'Skirt', 'Shorts', 'Scarf', 'Hat', 'Handbag', 'Hoodie', 'Shoes',\
    'T-shirt', 'Sneakers', 'Boots', 'Backpack', 'Gloves', 'Jeans']
if "selected_items" not in st.session_state:
    st.session_state['selected_items'] = product_items
us_lat_center =  47.751076
us_lon_center = -120.740135
locale.setlocale( locale.LC_ALL, 'en_CA.UTF-8' )

sales_columns = [
    'age','category','color','customer_id','discount_applied','frequency_of_purchases',
    'gender','item_purchased','location','payment_method','previous_purchases','promo_code_used',
    'purchase_amount_usd','purchase_time','review_rating','season','shipping_type','size','subscription_status'
]

# Load data
class SalesData():

    def __init__(self):

        # Read data from Pinot DB
        conn = connect(host='localhost', port=8000, path='/query/sql', scheme='http')
        curs = conn.cursor()
        curs.execute("""SELECT * FROM SalesTxs limit 4000""")
        self.sales_df = pd.DataFrame(
            curs.fetchall(),
            columns=sales_columns
        )
        # Filter data based on the items selected
        self.selected_items = st.session_state['selected_items']
        
        # Filter data based on the items selected
        self.sales_df = self.sales_df.loc[self.sales_df['item_purchased'].isin(self.selected_items)]
        
        # Update Global Numbers
        amount = self.sales_df['purchase_amount_usd'].sum()
        self.total_revenue = locale.currency(amount, symbol=True, grouping=True)
        self.avg_rating = round(self.sales_df['review_rating'].mean(),3)
        self.total_customers = self.sales_df['customer_id'].count()

    def get_total_revenue(self):
        return (self.total_revenue)
    
    def get_avg_rating(self):
        return (self.avg_rating)
    
    def get_total_customers(self):
        return (self.total_customers)
    
    def get_selected_items(self):
        return (self.selected_items)

# Set layout
st.set_page_config(layout="wide")

# Import CSS
# Importar o conteúdo do arquivo CSS na streamlit tag style
with open ("./styles.css") as f:
    st.markdown (f"<style>{f.read()}</style>",unsafe_allow_html=True)

# Page Layout
# Items Selector
with st.expander("Select Items", expanded=True):
    o_selected_items = st.multiselect(
        'Item',
        product_items,
        product_items
    )
    st.session_state['selected_items'] = o_selected_items

salesData = SalesData()

# Clothing Size, Gender, Promocode and Shipping Type distribution
with st.expander("Distributions", expanded=True):
    c_size_col, gender_col, promoc_col, shipping_col = st.columns([2.5,2.5,2.5,2.5])
    with c_size_col:
        with st.container(border=True):
            disp_df = salesData.sales_df.groupby(['size'])['customer_id'].agg("count").reset_index()
            fig_c_size = px.pie(
                disp_df,
                values = "customer_id",
                names = "size",
                title="Clothing Size Distribution"
            )
            c_size_col.plotly_chart(fig_c_size,use_container_width=True)
            
    with gender_col:
        with st.container(border=True):
            disp_df = salesData.sales_df.groupby(['gender'])['customer_id'].agg("count").reset_index()
            fig_c_gender = px.pie(
                disp_df,
                values = "customer_id",
                names="gender",
                title="Gender Distribution"
            )
            gender_col.plotly_chart(fig_c_gender,use_container_width=True)
            
    with promoc_col:
            disp_df = salesData.sales_df.groupby(['promo_code_used'])['customer_id'].agg("count").reset_index()
            fig_c_promoc = px.pie(
                disp_df,
                values = "customer_id",
                names="promo_code_used",
                title="Promocode Distribution",
            )
            promoc_col.plotly_chart(fig_c_promoc,use_container_width=True)
            
    with shipping_col:
            disp_df = salesData.sales_df.groupby(['shipping_type'])['customer_id'].agg("count").reset_index()
            fig_c_shipping = px.bar(
                disp_df,
                y = "customer_id",
                x = "shipping_type",
                title="Shipping Type Distribution"
            )
            fig_c_shipping.update_layout(xaxis_title=None)
            shipping_col.plotly_chart(fig_c_shipping, use_container_width=True)

# Revenue/Location (Map) and Age Distribution
with st.expander("Location and Age", expanded=True):
    rev_location_col, age_distrib_col = st.columns(2,gap="small")
    with rev_location_col:
        sales_location = pd.DataFrame(salesData.sales_df[['location','purchase_amount_usd']])
        us_states_df = pd.read_json("./data/us_json.json")
        us_states_df = us_states_df.rename(columns={'name':'location'})
        sales_location = pd.merge(sales_location, us_states_df ,how='left', on='location')
        sales_location = sales_location.groupby(["abbreviation"])['purchase_amount_usd'].sum().reset_index()
        # sales_map = folium.Map(location=(us_lat_center, us_lon_center), zoom_start=4, tiles="cartodb positron")
        
        fig_map = go.Figure(
            data=go.Choropleth(
                locations=sales_location['abbreviation'], # Spatial coordinates
                z = sales_location.groupby(["abbreviation"])['purchase_amount_usd'].sum(),
                locationmode = 'USA-states', # set of locations match entries in `locations`
                colorscale = 'Reds',
                colorbar_title = "USD",
                )
            )
        PAPER_BGCOLOR=st.get_option('theme.backgroundColor')
        # PAPER_BGCOLOR="#0E1117"
        fig_map.update_layout(
            title_text = 'State Sales',
            geo_scope='usa', # limite map scope to USA
            geo_bgcolor=PAPER_BGCOLOR
        )

        #folium_static(fig_map,width=map_width, height=map_height)
        st.plotly_chart(fig_map,use_container_width=True)
            
    with age_distrib_col:
        # Age distribution
        fig_age = px.histogram(
            salesData.sales_df['age'], 
            nbins=20,
            title="Age Distribution"
        )

        age_distrib_col.plotly_chart(fig_age, use_container_width=True)