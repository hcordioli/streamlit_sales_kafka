import streamlit as st
import pandas as pd
import plotly.express as px
import locale
import plotly.graph_objects as go
from pinotdb import connect

# Global variables
pay_methods = ['PayPal','Credit Card','Cash','Debit Card','Venmo','Bank Transfer']
seasons = ['Spring','Summer','Fall','Winter']

if "pay_methods" not in st.session_state:
    st.session_state['pay_methods'] = pay_methods
if "seasons" not in st.session_state:
    st.session_state['seasons'] = seasons

locale.setlocale( locale.LC_ALL, 'en_CA.UTF-8' )

sales_columns = [
    'age','category','color','customer_id','discount_applied','frequency_of_purchases',
    'gender','item_purchased','location','payment_method','previous_purchases','promo_code_used',
    'purchase_amount_usd','purchase_time','review_rating','season','shipping_type','size','subscription_status'
]

# Load data
class InsightData():

    def __init__(self):

        # Read data from Pinot DB
        conn = connect(host='localhost', port=8000, path='/query/sql', scheme='http')
        curs = conn.cursor()
        curs.execute("""SELECT * FROM SalesTxs limit 4000""")
        self.insights_df = pd.DataFrame(
            curs.fetchall(),
            columns=sales_columns
        )
        # Retirar linha abaixo após mudar tipo da coluna "age" para INT
        self.insights_df['age'] = self.insights_df['age'].astype(int)
        
        self.pay_methods = st.session_state['pay_methods']
        self.seasons = st.session_state['seasons']
        
        # Filter out unselected items
        self.insights_df = self.insights_df.loc[
            (self.insights_df['payment_method'].isin(self.pay_methods)) & 
            (self.insights_df['season'].isin(self.seasons)) 
        ]

# Auxiliary functions
def set_age_bin(age):
    if age < 30:
        return('twenties')
    elif age < 40:
        return('thirties')
    elif age < 50:
        return('forties')
    else:
        return('senior')

# Set layout
st.set_page_config(layout="wide")

# Import CSS
# Importar o conteúdo do arquivo CSS na streamlit tag style
with open ("./styles.css") as f:
    st.markdown (f"<style>{f.read()}</style>",unsafe_allow_html=True)

# Layout
pm_col, seasons_col = st.columns(2,gap="small")
with pm_col:
    pm_expander = st.expander("Payment Methods", expanded=True)
    pm_selected_items = pm_expander.multiselect(
        'Payment Method',
        pay_methods,
        pay_methods
    )
    st.session_state['pay_methods'] = pm_selected_items
    insightData = InsightData()
    
    disp_df = insightData.insights_df.groupby(['payment_method'])[['customer_id']].agg("count").reset_index()
    disp_df = disp_df.rename(columns={'customer_id':'purchases'})
    fig_cus_pm = px.bar(
            disp_df,
            x="payment_method",
            y="purchases",
            title="Purchases per Payment Methods",
        )
    pm_expander.plotly_chart(fig_cus_pm,use_container_width=True)

with seasons_col:
    season_expander = st.expander("Seasons", expanded=True)
    s_selected_seasons = season_expander.multiselect(
        'Season',
        seasons,
        seasons
    )
    st.session_state['seasons'] = s_selected_seasons
    insightData = InsightData()

    disp_df = insightData.insights_df.groupby(['season'])[['purchase_amount_usd']].agg("sum").reset_index()
    fig_usd_s = px.bar(
            disp_df,
            x="season",
            y="purchase_amount_usd",
            title="Purchase Amount (USD) per Season",
        )
    season_expander.plotly_chart(fig_usd_s,use_container_width=True)
    
with st.expander("Purchases Amount x USD", expanded=True):
    qtd_purch = insightData.insights_df.groupby(['item_purchased'])[['customer_id']].agg("count").reset_index()
    qtd_purch = qtd_purch.rename(columns={'customer_id':'purchases'})
    usd_purch = insightData.insights_df.groupby(['item_purchased'])[['purchase_amount_usd']].agg("sum").reset_index()
    fig_p_q_u = go.Figure()

    fig_p_q_u.add_trace(go.Bar(
        x=usd_purch['item_purchased'],
        y=usd_purch['purchase_amount_usd'],
        name="USD"
    ))

    fig_p_q_u.add_trace(go.Scatter(
        x=qtd_purch['item_purchased'],
        y=qtd_purch['purchases'],
        name="Purchases",
        yaxis="y2"
    ))

    fig_p_q_u.update_layout(
        yaxis=dict(
            title="USD",
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )
        ),
        yaxis2=dict(
            title="Purchases",
            titlefont=dict(
                color="#ff7f0e"
            ),
            tickfont=dict(
                color="#ff7f0e"
            ),
            anchor="free",
            overlaying="y",
            side="right",
            position=1
        )
    )
    st.plotly_chart(fig_p_q_u,use_container_width=True)
    
with st.expander("Age, Freq, Paym Method Relationship", expanded=True):
    ap_col, af_col, fp_col = st.columns(3,gap="small")
    insight_df = insightData.insights_df[['age','payment_method','frequency_of_purchases','customer_id']].copy()
    insight_df['age_range'] = insight_df['age'].map(set_age_bin)
    insight_df = insight_df.drop(columns=['age'])
    
    # Age x Payment Method
    display_df =  insight_df.groupby(['age_range','payment_method']).agg("count").reset_index()
    display_df = display_df.drop(['frequency_of_purchases'],axis=1)
    display_df = display_df.rename(columns = {'customer_id':'customers'})
    fig_age_pay = px.bar(
        display_df,
        x="age_range",
        y="customers",
        color = 'payment_method'
    )
    ap_col.plotly_chart(fig_age_pay,use_container_width=True)
    
    # Age x Frequency of Purchases
    display_df =  insight_df.groupby(['age_range','frequency_of_purchases']).agg("count").reset_index()
    display_df = display_df.drop(['payment_method'],axis=1)
    display_df = display_df.rename(columns = {'customer_id':'customers'})
    fig_age_freq = px.bar(
        display_df,
        x="age_range",
        y="customers",
        color = 'frequency_of_purchases'
    )
    af_col.plotly_chart(fig_age_freq,use_container_width=True)

    # Frequency of Purchases x Payment Method
    display_df =  insight_df.groupby(['frequency_of_purchases','payment_method']).agg("count").reset_index()
    display_df = display_df.drop(['age_range'],axis=1)
    display_df = display_df.rename(columns = {'customer_id':'customers'})
    fig_freq_pay = px.bar(
        display_df,
        x="frequency_of_purchases",
        y="customers",
        color = 'payment_method'
    )
    fp_col.plotly_chart(fig_freq_pay,use_container_width=True)