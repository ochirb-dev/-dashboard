import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="ADB15/7 аяны хүрээнд", layout="wide")

# =========================
# Load data (cached)
# =========================
@st.cache_data
def load_data():
    df = pd.read_parquet("data/ardiin_erh_code_grouped_combined.pqt")
    return df

df = load_data()
# =========================
# Data prep
# =========================

feb = (
    df[df['year_month'] == '2026-02']
    .groupby(['CUST_CODE','ta'], as_index=False)['TXN_AMOUNT']
    .sum()
)

bins = [100,200,300,400,500,600,700,800,900,1000,float('inf')]
labels = ['150-199','200-299','300-399','400-499','500-599',
          '600-699','700-799','800-899','900-999','+1000']

df.loc[
    (df['TXN_DATE'] >= '2026-02-01') &
    (df['TXN_DESC'] == 'adb15/7 cupcake орлого нэмсний урамшууллыг олгов') &
    (df['LOYAL_CODE'] == 'None'),
    'LOYAL_CODE'
] = '10K_CHARGE_CUPCAKE_1'


def adb_amount_group(feb, df, loyal_cond, desc_cond):

    cust_codes = df[
        loyal_cond &
        (df['TXN_DATE'] >= pd.to_datetime('2026-02-01')) &
        desc_cond
    ]['CUST_CODE']

    temp = feb[feb['CUST_CODE'].isin(cust_codes)].copy()

    temp['AMOUNT_GROUP'] = pd.cut(
        temp['TXN_AMOUNT'],
        bins=bins,
        labels=labels,
        right=False
    )

    result = temp.groupby(['ta','AMOUNT_GROUP']).size().unstack(fill_value=0)

    return temp, result


# =========================
# Create datasets
# =========================

adb15, adb15_table = adb_amount_group(
    feb,
    df,
    ((df['LOYAL_CODE']=='None') | (df['LOYAL_CODE']=='10K_CHARGE_CUPCAKE_1')),
    df['TXN_DESC'].str.contains("adb", case=False, na=False),
)

adb15_loan, adb15_loan_table = adb_amount_group(
    feb, df,
    (df['LOYAL_CODE']=='None'),
    (df['TXN_DESC']=='adb15/7 зээл авсаны урамшууллыг олгов')
)

adb15_txn, adb15_txn_table = adb_amount_group(
    feb, df,
    (df['LOYAL_CODE']=='None'),
    (df['TXN_DESC']=='adb15/7 гүйлгээний урамшууллыг олгов')
)

adb15_cupcake, adb15_cupcake_table = adb_amount_group(
    feb, df,
    (df['LOYAL_CODE']=='10K_CHARGE_CUPCAKE_1'),
    (df['TXN_DESC']=='adb15/7 cupcake орлого нэмсний урамшууллыг олгов')
)

adb15_ardpay, adb15_ardpay_table = adb_amount_group(
    feb, df,
    (df['LOYAL_CODE']=='None'),
    (df['TXN_DESC']=='adb15/7 ardpay зээл авсаны урамшууллыг олгов')
)

# =========================
# Sidebar filters
# =========================

st.sidebar.title("Filters")

ta_map = {
    1: "Түмэн Ард гишүүн",
    0: "Түмэн Ард биш"
}

ta_list = sorted(adb15['ta'].dropna().unique())

selected_label = st.sidebar.multiselect(
    "Түмэн Ард статус",
    options=[ta_map[i] for i in ta_list],
    default=[ta_map[i] for i in ta_list]
)

selected_ta = [k for k,v in ta_map.items() if v in selected_label]

adb15_filtered = adb15[adb15['ta'].isin(selected_ta)]

# =========================
# Title
# =========================

st.title("ADB15/7 аяны хүрээнд")

# =========================
# KPI
# =========================

col1,col2,col3,col4,col5 = st.columns(5)

col1.metric("Нийт харилцагчид", adb15_filtered['CUST_CODE'].nunique())
col2.metric("Зээлийн аянд оролцсон харилцагчид", adb15_loan['CUST_CODE'].nunique())
col3.metric("Гүйлгээ аянд оролцсон харилцагчид", adb15_txn['CUST_CODE'].nunique())
col4.metric("Cupcake аянд оролцсон харилцагчид", adb15_cupcake['CUST_CODE'].nunique())
col5.metric("Ardpay зээлийн аянд оролцсон харилцагчид", adb15_ardpay['CUST_CODE'].nunique())

st.divider()


# =========================
# TA Distribution
# =========================

st.subheader("Түмэн ардын гишүүдийн оролцсон байдал")

ta_df = (
    adb15_filtered.groupby(['ta','AMOUNT_GROUP'])
    .size()
    .reset_index(name='count')
)

ta_df['ta'] = ta_df['ta'].map({
    1: "Түмэн Ард гишүүн",
    0: "Түмэн Ард биш"
})

fig2 = px.bar(
    ta_df,
    x="AMOUNT_GROUP",
    y="count",
    color="ta",
    barmode="group",
    labels={
        "AMOUNT_GROUP": "Нийт цуглуулсан ардын эрх",
        "count": "Харилцагчдын тоо",
        "ta": "Түмэн ард"
    }
)

st.plotly_chart(fig2, use_container_width=True)
# =========================
# Reward comparison
# =========================

st.subheader("Биелүүлсэн байдал")

reward_df = pd.DataFrame({
    "төрөл":["Зээл","Гүйлгээ","Cupcake","ArdPay"],
    "харилцагчдын тоо":[
        adb15_loan['CUST_CODE'].nunique(),
        adb15_txn['CUST_CODE'].nunique(),
        adb15_cupcake['CUST_CODE'].nunique(),
        adb15_ardpay['CUST_CODE'].nunique()
    ]
})

fig3 = px.pie(
    reward_df,
    names="төрөл",
    values="харилцагчдын тоо",
    hole=0.4
)

fig3.update_traces(textinfo="percent+label")

st.plotly_chart(fig3, use_container_width=True)

# =========================
# Tables
# =========================

st.subheader("Хүснэгт харах")

tab1,tab2,tab3,tab4,tab5 = st.tabs(
    ["Нийт","Зээл","Гүйлгээ","Cupcake","ArdPay"]
)
with tab1:
    with st.expander("Хүснэгт харах", expanded=False):
        st.dataframe(adb15_table, hide_index=False)

with tab2:
    with st.expander("Хүснэгт харах", expanded=False):
        st.dataframe(adb15_loan_table, hide_index=False)

with tab3:
    with st.expander("Хүснэгт харах", expanded=False):
        st.dataframe(adb15_txn_table, hide_index=False)

with tab4:
    with st.expander("Хүснэгт харах", expanded=False):
        st.dataframe(adb15_cupcake_table, hide_index=False)

with tab5:
    with st.expander("Хүснэгт харах", expanded=False):
        st.dataframe(adb15_ardpay_table, hide_index=False)