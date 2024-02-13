import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import datetime as dt
from datetime import timedelta
import numpy as np
import plotly.graph_objects as go
import locale
from pinotdb import connect

# Global variables
product_items = ['Blouse', 'Jewelry', 'Pants', 'Shirt', 'Dress', 'Sweater',\
    'Jacket', 'Belt', 'Sunglasses', 'Coat', 'Sandals', 'Socks',\
    'Skirt', 'Shorts', 'Scarf', 'Hat', 'Handbag', 'Hoodie', 'Shoes',\
    'T-shirt', 'Sneakers', 'Boots', 'Backpack', 'Gloves', 'Jeans']
if "selected_items" not in st.session_state:
    st.session_state['selected_items'] = product_items
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
        
        # Filter out unselected items
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

# Total Revenue, Average Rating and Total Customers
with st.expander("Global Numbers", expanded=True):
    total_revenue_col, avg_rating_col, total_customers_col = st.columns([3.3,3.3,3.4])
    with total_revenue_col:
        with st.container(border=True):
            st.title("Total Revenue", anchor="totaL-revenue")
            st.write(str(salesData.get_total_revenue()))
    with avg_rating_col:
        with st.container(border=True):
            st.title("Average Rating", anchor="average-rating")
            st.write(str(salesData.get_avg_rating()))
    with total_customers_col:
        with st.container(border=True):
            st.title("Total Customers", anchor="total-customers")
            st.write(str(salesData.get_total_customers()))

# Revenue/Product (Vertical Bar) and Revenue/Category (Horizontal Bar) in one expander
# besides #Customers and Revenue per Category-Item
with st.expander("Revenue Details", expanded=True):
    rev_pro_cat_col, cus_rev_cat_ite_col = st.columns(2,gap="small")
    with rev_pro_cat_col:
        with st.container(border=True):
            # Revenue/Product (Vertical Bar)
            disp_df = salesData.sales_df.groupby(['item_purchased'])['purchase_amount_usd'].agg(sum).nlargest(100).reset_index()
            fig_rev_pro = px.bar(
                disp_df,
                x="item_purchased",
                y="purchase_amount_usd",
                title="Revenue/Product",
            )
            rev_pro_cat_col.plotly_chart(fig_rev_pro,use_container_width=True)

        with st.container(border=True):
            # Revenue/Category (Horizontal Bar)
            disp_df = salesData.sales_df.groupby(['category'])['purchase_amount_usd'].agg(sum).nlargest(100).reset_index()
            fig_rev_cat = px.bar(
                disp_df,
                x="purchase_amount_usd",
                y="category",
                title="Revenue/Category",
                orientation='h'
            )
            fig_rev_cat.update_layout(yaxis=dict(autorange="reversed"))
            rev_pro_cat_col.plotly_chart(fig_rev_cat,use_container_width=True)
            
    with cus_rev_cat_ite_col:
        # Customers and Revenue per Category-Item
        display_df = salesData.sales_df.groupby(['category','item_purchased'])[['customer_id','purchase_amount_usd']].agg(
            count_cust=("customer_id","count"),
            sum_rev=("purchase_amount_usd","sum"))
        display_df['sum_rev'] = display_df['sum_rev'].map(lambda v: locale.currency(v, symbol=True, grouping=True))
        st.table(display_df)
            