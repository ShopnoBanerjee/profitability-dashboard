import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.sidebar.image("logo.svg")

st.header("Anonymous Profitability Dashboard")

st.sidebar.header("Upload Files")

#file uploading on sidebar
month_sheet = st.sidebar.file_uploader("Monthly Job Sheet :", type=["csv"])

salary_sheet = st.sidebar.file_uploader("Salary Sheet :", type=["csv"])

client_sheet = st.sidebar.file_uploader("Billing Sheet :", type=["csv"])

# Display content of each file
if month_sheet is not None:
    df = pd.read_csv(month_sheet)

if salary_sheet is not None:
    rate = pd.read_csv(salary_sheet)

if client_sheet is not None:
    customer = pd.read_csv(client_sheet)

#data cleaning,pre processing
@st.cache_data
def dataframe_generation(df,rate,customer):
    df = df[['Client','Assign to','Time']]
    df = df.rename(columns={'Assign to':'Employee'})
    df = df.merge(rate)
    df = df.merge(customer)
    df.loc[df['Time'] == 'all day', 'Time'] = '480'
    df.loc[df['Time'] == 'done earlier', 'Time'] = np.nan
    df = df.dropna()
    df.loc[:, 'Time'] = df.loc[:, 'Time'].astype(int)
    df.loc[:, 'salary'] = df.loc[:, 'salary'].astype(int)
    df.loc[:,"minute_rate"] = df["salary"]/(22*8*60)
    df.loc[:,'spend'] = df['Time']*df['minute_rate']
    pd.set_option('future.no_silent_downcasting', True)
    df_clientwise = df.pivot_table(index='Client',columns='Employee',values=['spend']).fillna(0)
    df_clientwise['total_spend'] = df_clientwise.sum(axis=1).apply(int)
    df_profit = df_clientwise.reset_index()
    df_profit.columns = [''.join(col).strip() if isinstance(col, tuple) else col for col in df_profit.columns]
    df_profit = df_profit.merge(customer)
    df_profit = df_profit[['Client','total_spend','Payment']]
    df_profit['profit'] = df_profit['Payment'] - df_profit['total_spend'] 
    df_empwise = df.pivot_table(index='Employee',columns='Client',values=['Time']).fillna(0)
    df_empwise['Total_time'] = df_empwise.sum(axis=1).apply(int)
    df_empwise = df_empwise.reset_index()
    df_empwise.columns = [''.join(col).strip() if isinstance(col, tuple) else col for col in df_empwise.columns]
    df_timewise = df.pivot_table(index='Client',columns='Employee',values=['Time']).fillna(0)
    df_timewise['Total_time_(mins)'] = df_timewise.sum(axis=1).apply(float)
    df_timewise['Total_time_(hrs)'] = df_timewise.loc[:,"Total_time_(mins)"]/60
    df_timewise = df_timewise.reset_index()
    df_timewise.columns = [''.join(col).strip() if isinstance(col, tuple) else col for col in df_timewise.columns]
    return df_profit,df_timewise,df_empwise

#warning display   
if not month_sheet or not salary_sheet or not client_sheet:
    col1,col2,col3 = st.columns(3)
    with col1:
        st.info("upload all files", icon="ℹ️")



#template CSV file formats
month_sheet_csv = '''Date,Client,Status,Assign to,Assignment name,Assets to deliver,Account Manager,Deadline,Time,Details
1-May,Client 1,Job Done,Shopno,"Develop Dashboard",Content,Boss,2-May,30,"project over"
'''

salary_sheet_csv = '''Employee,salary
Shopno,20000
'''

client_sheet_csv = '''Client,Payment
Client1,30000
'''
#download buttons for temmplates
with st.sidebar.expander("Download Templates"):
    st.download_button(
            label="Download Monthly Job Sheet CSV template",
            data=month_sheet_csv,
            file_name="month_sheet.csv",
            mime="text/csv",
        )    
    st.download_button(
            label="Download Monthly Job Sheet CSV template",
            data=salary_sheet_csv,
            file_name="salary_sheet.csv",
            mime="text/csv",
        )    
    st.download_button(
            label="Download Monthly Job Sheet CSV template",
            data=client_sheet_csv,
            file_name="client_sheet.csv",
            mime="text/csv",
        )
    

# Function to get filtered data based on selections
@st.cache_data
def get_filtered_data(df, selected_clients=None):
    if selected_clients:
        df = df[df['Client'].isin(selected_clients)]
    return df



if client_sheet and salary_sheet and month_sheet is not None:
    df_profit,df_timewise,df_empwise = dataframe_generation(df=df,rate=rate,customer=customer)
    left,right = st.columns(2)
    with left:
        with st.expander("Profit Data Preview"):            
            st.dataframe(df_profit)
    with right:
        with st.expander("Time Data Preview"):
            st.dataframe(df_timewise[["Client","Total_time_(mins)","Total_time_(hrs)"]])
    
    with st.expander("Select Client(s)"):
        # Multiselect for Clients
        clients = df_timewise['Client'].unique()
        selected_clients = st.multiselect('Select Clients:', clients, default=clients)  

    # Filtered DataFrames
    filtered_timewise = get_filtered_data(df_timewise, selected_clients)
    filtered_profit = get_filtered_data(df_profit, selected_clients)
    
    net_profit = filtered_profit["profit"].sum()
    total_time = filtered_timewise["Total_time_(mins)"].sum()
    
    # Total Time Spent per Client (hours)
    fig_time_per_client = px.bar(filtered_timewise, x='Client', y='Total_time_(hrs)', title='Total Time Spent per Client (hrs)')
    fig_time_per_client.update_layout(xaxis={'categoryorder':'total descending'},yaxis_title = "Time (hrs)" )

    # Profit per Client
    fig_profit_per_client = px.bar(filtered_profit, x='Client', y='profit', title='')
    fig_profit_per_client.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_title = 'Profit')

    # Scatter plot of Time Spent vs Profit Earned
    fig_time_vs_profit = px.scatter(filtered_timewise, x='Total_time_(hrs)', y=filtered_profit['profit'], color='Client', title='Time Spent vs Profit Earned')
    fig_time_vs_profit.update_layout(xaxis_title='Time (hrs)', yaxis_title='Profit')

    # Create a pie chart for profit per client
    fig_profit_per_client_pie = px.pie(filtered_profit, names='Client', values='profit', title='Profit per Client',labels={'profit':'profit'})
    fig_profit_per_client_pie.update_traces(textposition='inside', textinfo='label+percent',hoverinfo='label+value+percent')
    
    #Pie chart for Total time spent on client
    filtered_timewise['round_time'] = filtered_timewise['Total_time_(hrs)'].round()
    fig_time_per_client_pie = px.pie(filtered_timewise, names='Client', values='round_time', title='Time per Client (hrs)')
    fig_time_per_client_pie.update_traces(textposition='inside', textinfo='label+value', hoverinfo='label+value+percent')

    
    

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label = "Net Profit",value=f"₹ {net_profit}")
    with col2:
        st.metric(label = "Time Spent",value=f"{total_time/60 :0.2f} hrs")
    with col3:
        st.metric(label = "Money per minute", value = f"{net_profit/total_time :0.2f} ₹/mins")
    

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_profit_per_client)
        st.plotly_chart(fig_time_per_client)

    with col2:
        st.plotly_chart(fig_profit_per_client_pie)
        st.plotly_chart(fig_time_per_client_pie)
    
    
    st.plotly_chart(fig_time_vs_profit)
        
    

  

    