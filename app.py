
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="LULU Hypermarket - Sales Dashboard (UAE)", layout="wide")

@st.cache_data
def load_data():
    tx = pd.read_csv("data/transactions.csv", parse_dates=["date"])
    customers = pd.read_csv("data/customers.csv", parse_dates=["join_date"])
    ad = pd.read_csv("data/ad_budget.csv")
    return tx, customers, ad

tx, customers, ad_budget = load_data()

st.title("LULU Hypermarket — UAE Sales & Loyalty Dashboard")
st.markdown("Interactive dashboard showing sales by demographics, categories, and loyalty program impact.")

# Filters
with st.sidebar:
    st.header("Filters")
    min_date = tx['date'].min()
    max_date = tx['date'].max()
    date_range = st.date_input("Date range", value=(min_date, max_date))
    if len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start, end = min_date, max_date
    age_min, age_max = int(tx.age.min()), int(tx.age.max())
    age_sel = st.slider("Age range", age_min, age_max, (25,45))
    gender_sel = st.multiselect("Gender", options=tx.gender.unique().tolist(), default=tx.gender.unique().tolist())
    locations = st.multiselect("Locations", options=tx.location.unique().tolist(), default=tx.location.unique().tolist())
    categories = st.multiselect("Categories", options=tx.category.unique().tolist(), default=tx.category.unique().tolist())
    loyalty = st.selectbox("Loyalty membership", options=["All","Members only","Non-members only"])

# Apply filters
d = tx.copy()
d = d[(d['date']>=pd.to_datetime(start)) & (d['date']<=pd.to_datetime(end))]
d = d[(d['age']>=age_sel[0]) & (d['age']<=age_sel[1])]
d = d[d['gender'].isin(gender_sel)]
d = d[d['location'].isin(locations)]
d = d[d['category'].isin(categories)]
if loyalty == "Members only":
    d = d[d['has_loyalty_card'] == True]
elif loyalty == "Non-members only":
    d = d[d['has_loyalty_card'] == False]

# Key metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales (AED)", f"{d.total_amount_aed.sum():,.2f}")
col2.metric("Transactions", f"{d.transaction_id.nunique()}")
col3.metric("Average Basket (AED)", f"{d.total_amount_aed.mean():,.2f}")
col4.metric("Loyalty Sales %", f"{100 * d[d.has_loyalty_card==True].total_amount_aed.sum() / (d.total_amount_aed.sum()+1e-9):.1f}%\")


# Sales by Category
st.subheader("Sales by Category")
cat_chart = d.groupby("category", as_index=False).total_amount_aed.sum().sort_values("total_amount_aed", ascending=False)
bar = alt.Chart(cat_chart).mark_bar().encode(
    x=alt.X("category:N", sort="-y"),
    y=alt.Y("total_amount_aed:Q", title="Sales (AED)"),
    tooltip=["category", "total_amount_aed"]
).properties(width=700, height=350)
st.altair_chart(bar, use_container_width=True)

# Demographics: Age groups
st.subheader("Sales by Age Group and Gender")
d['age_group'] = pd.cut(d.age, bins=[15,24,34,44,54,64,100], labels=["16-24","25-34","35-44","45-54","55-64","65+"])
age_gender = d.groupby(['age_group','gender'], as_index=False).total_amount_aed.sum()
chart = alt.Chart(age_gender).mark_bar().encode(
    x=alt.X('age_group:N', title='Age Group'),
    y=alt.Y('total_amount_aed:Q', title='Sales (AED)'),
    color='gender:N',
    column='gender:N',
    tooltip=['age_group','gender','total_amount_aed']
).properties(width=200)
st.altair_chart(chart, use_container_width=True)

# Loyalty impact
st.subheader("Loyalty Program Impact")
loyal_summary = d.groupby("has_loyalty_card", as_index=False).agg(
    sales=('total_amount_aed','sum'),
    transactions=('transaction_id','nunique'),
    avg_basket=('total_amount_aed','mean')
)
loyal_summary['label'] = loyal_summary['has_loyalty_card'].map({True:"Members", False:"Non-members"})
st.dataframe(loyal_summary[['label','sales','transactions','avg_basket']])

# Points earned vs redeemed (sample)
st.subheader("Points Earned vs Redeemed (sample)")
points = d.groupby('card_tier', as_index=False).agg(points_earned=('points_earned','sum'), points_redeemed=('points_redeemed','sum'))
st.altair_chart(alt.Chart(points).transform_fold(['points_earned','points_redeemed'], as_=['type','value']).mark_bar().encode(
    x='card_tier:N',
    y='value:Q',
    color='type:N',
    tooltip=['card_tier','value']
).properties(width=700))

# Offer effect: compare average transaction when offer applied
st.subheader("Offer Effect on Average Transaction")
offer_stats = d.groupby('offer_applied', as_index=False).total_amount_aed.agg(['count','mean'])
offer_stats = offer_stats.reset_index().rename(columns={'mean':'avg_amount','count':'num_tx'})
st.write(offer_stats)

# Ad spend overview
st.subheader("Advertising Spend (monthly sample)")
st.write(ad_budget.head(12))
ad_chart = alt.Chart(ad_budget).mark_line(point=True).encode(
    x='month:T',
    y='ad_spend_uae_aed:Q',
    color='category:N',
    tooltip=['month','category','ad_spend_uae_aed']
).properties(width=900, height=300)
# ensure month is datetime
ad_budget['month'] = pd.to_datetime(ad_budget['month'] + "-01")
st.altair_chart(ad_chart, use_container_width=True)

st.markdown("---\n**Notes:** This is a synthetic dataset created for prototyping. Use the filters on the left to explore different slices. ")
