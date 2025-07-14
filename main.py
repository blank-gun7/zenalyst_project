import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


@st.cache_data
def load_and_process_data(file_path, analysis_type):
    """Load and process the revenue data for quarterly analysis"""
    
    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    
    # Drop unnecessary columns upfront
    columns_to_drop = [
        "Entity\nUpto Mar 2024", 
        "Entity April 2024", 
        "Entity grouped",
        "S. no."
    ]
    
    # Drop columns if they exist
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
    
    # Debug: Show remaining columns
    # st.write("**Remaining columns after cleanup:**", len(df.columns))
    # st.write("**All column names:**", df.columns.tolist())
    # st.write("**Column data types:**", df.dtypes.head(20))
    
    # Find the appropriate grouping column based on analysis type
    if analysis_type == "Geography":
        grouping_col = 'Country'
        if grouping_col not in df.columns:
            # st.error(f"Geography column '{grouping_col}' not found!")
            return None, None, None
    else:  # Industry
        grouping_col = 'Industry'
        if grouping_col not in df.columns:
            # st.error(f"Industry column '{grouping_col}' not found!")
            return None, None, None
    
    # IMPROVED: Multiple methods to detect datetime columns for 2024
    monthly_cols = []
    
    # Method 1: Check for pandas Timestamp objects
    for col in df.columns:
        if isinstance(col, pd.Timestamp) and col.year == 2024:
            monthly_cols.append(col)
    
    # Method 2: If no Timestamp objects found, try parsing string columns
    if not monthly_cols:
        for col in df.columns:
            if isinstance(col, str):
                # Check if it looks like a date string
                if '2024' in str(col) and ('-' in str(col) or '/' in str(col)):
                    try:
                        parsed_date = pd.to_datetime(col, errors='coerce')
                        if pd.notna(parsed_date) and parsed_date.year == 2024:
                            monthly_cols.append(col)
                    except:
                        continue
    
    # Method 3: If still no columns found, look for datetime-like strings
    if not monthly_cols:
        for col in df.columns:
            col_str = str(col)
            # Look for datetime pattern like "2024-01-01 00:00:00"
            if '2024-' in col_str and '00:00:00' in col_str:
                monthly_cols.append(col)
    
    # Method 4: Last resort - look for any column containing "2024"
    if not monthly_cols:
        for col in df.columns:
            if '2024' in str(col):
                monthly_cols.append(col)
    
    # Sort monthly columns chronologically
    if monthly_cols:
        try:
            # Try to sort by converting to datetime
            monthly_cols = sorted(monthly_cols, key=lambda x: pd.to_datetime(str(x)))
        except:
            # If that fails, sort as strings
            monthly_cols = sorted(monthly_cols)
    
    # st.write(f"**Found {len(monthly_cols)} monthly columns**")
    # if monthly_cols:
    #     st.write("**Monthly columns found:**", [str(col) for col in monthly_cols[:6]])
    
    if len(monthly_cols) == 0:
        # st.error("No monthly revenue columns found for 2024!")
        # st.write("**Debug info - all columns:**")
        # for i, col in enumerate(df.columns):
        #     st.write(f"{i}: {col} (type: {type(col)})")
        return None, None, None
    
    # Prepare clean dataframe
    mrr_df = df[[grouping_col] + monthly_cols].copy()
    
    # Convert monthly columns to numeric, handling any data type issues
    for col in monthly_cols:
        mrr_df[col] = pd.to_numeric(mrr_df[col], errors='coerce').fillna(0)
    
    # Remove rows where grouping column is null or empty
    mrr_df = mrr_df.dropna(subset=[grouping_col])
    mrr_df = mrr_df[mrr_df[grouping_col].astype(str).str.strip() != '']
    
    # Group by the selected column and sum monthly MRR
    mrr_grouped = mrr_df.groupby(grouping_col).sum()
    
    # Use first 12 months or available months
    available_months = min(12, len(monthly_cols))
    monthly_cols = monthly_cols[:available_months]
    
    # Create quarterly aggregation
    quarters_mapping = {
        'Q1 2024': monthly_cols[:3],                    # Jan, Feb, Mar
        'Q2 2024': monthly_cols[3:6] if len(monthly_cols) >= 6 else [],    # Apr, May, Jun
        'Q3 2024': monthly_cols[6:9] if len(monthly_cols) >= 9 else [],    # Jul, Aug, Sep
        'Q4 2024': monthly_cols[9:12] if len(monthly_cols) >= 12 else []   # Oct, Nov, Dec
    }
    
    # Calculate quarterly MRR
    quarterly_mrr = pd.DataFrame(index=mrr_grouped.index)
    for quarter, months in quarters_mapping.items():
        if months:  # Only process if months exist
            quarterly_mrr[quarter] = mrr_grouped[months].sum(axis=1)
        else:
            quarterly_mrr[quarter] = 0
    
    # Debug: Show quarterly totals
    # quarterly_totals = quarterly_mrr.sum()
    # st.write("**Quarterly Totals Debug:**")
    # for quarter, total in quarterly_totals.items():
    #     st.write(f"- {quarter}: ${total:,.2f}")
    
    # Calculate quarterly percentages
    quarterly_percentages = pd.DataFrame(index=quarterly_mrr.index)
    for quarter in quarterly_mrr.columns:
        total = quarterly_mrr[quarter].sum()
        if total > 0:
            quarterly_percentages[quarter] = (quarterly_mrr[quarter] / total) * 100
        else:
            quarterly_percentages[quarter] = 0
    
    # Round to 2 decimal places
    quarterly_mrr = quarterly_mrr.round(2)
    quarterly_percentages = quarterly_percentages.round(2)
    
    return quarterly_mrr, quarterly_percentages, mrr_grouped


def create_mrr_chart(quarterly_mrr, analysis_type):
    """Create a bar chart for quarterly MRR by selected dimension"""
    
    # Choose color scheme based on analysis type
    color_scheme = px.colors.qualitative.Set3 if analysis_type == "Geography" else px.colors.qualitative.Set2
    
    fig = px.bar(
        quarterly_mrr.T,
        x=quarterly_mrr.T.index,
        y=quarterly_mrr.columns,
        title=f"Quarterly MRR by {analysis_type}",
        labels={'value': 'MRR (in millions)', 'index': 'Quarter'},
        color_discrete_sequence=color_scheme
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Quarter",
        yaxis_title="MRR (USD)",
        legend_title=analysis_type,
        font=dict(size=12)
    )
    
    return fig


def create_percentage_pie_chart(quarterly_percentages, quarter, analysis_type):
    """Create a pie chart for MRR percentage distribution for a single quarter"""
    
    # Get data for the selected quarter
    quarter_data = quarterly_percentages[quarter]
    
    # Filter out zero values for cleaner pie chart
    quarter_data = quarter_data[quarter_data > 0]
    
    # Choose color scheme based on analysis type
    color_scheme = px.colors.qualitative.Set3 if analysis_type == "Geography" else px.colors.qualitative.Set2
    
    fig = px.pie(
        values=quarter_data.values,
        names=quarter_data.index,
        title=f"MRR Percentage Distribution by {analysis_type} - {quarter}",
        color_discrete_sequence=color_scheme
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_size=12
    )
    
    fig.update_layout(
        height=500,
        legend_title=analysis_type,
        font=dict(size=12),
        showlegend=True
    )
    
    return fig


def create_trend_chart(quarterly_mrr, analysis_type):
    """Create a line chart showing MRR trends by selected dimension"""
    
    fig = go.Figure()
    
    for dimension in quarterly_mrr.index:
        fig.add_trace(go.Scatter(
            x=quarterly_mrr.columns,
            y=quarterly_mrr.loc[dimension],
            mode='lines+markers',
            name=dimension,
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title=f"MRR Trend Analysis by {analysis_type}",
        xaxis_title="Quarter",
        yaxis_title="MRR (USD)",
        height=500,
        font=dict(size=12)
    )
    
    return fig

def calculate_monthly_data_simple(monthly_mrr):
    """Calculate monthly MRR totals and MOM growth rates - simplified version"""
    
    # Get monthly totals across all dimensions
    monthly_totals = monthly_mrr.sum()
    
    # Calculate MOM growth rates
    mom_growth = monthly_totals.pct_change() * 100
    
    # Create a simple monthly dataframe
    monthly_df = pd.DataFrame({
        'Month': [pd.to_datetime(str(col)).strftime('%b %Y') if pd.to_datetime(str(col), errors='coerce') is not pd.NaT else str(col)[:10] for col in monthly_totals.index],
        'Total_MRR': monthly_totals.values,
        'MOM_Growth_Pct': mom_growth.values
    })
    
    return monthly_df


def create_simple_mom_chart(monthly_df):
    """Create a simple combination chart for monthly MRR and MOM growth"""
    
    from plotly.subplots import make_subplots
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add MRR bars
    fig.add_trace(
        go.Bar(
            x=monthly_df['Month'],
            y=monthly_df['Total_MRR'],
            name="Monthly MRR",
            marker_color='lightblue'
        ),
        secondary_y=False,
    )
    
    # Add MOM growth line
    fig.add_trace(
        go.Scatter(
            x=monthly_df['Month'],
            y=monthly_df['MOM_Growth_Pct'],
            mode='lines+markers',
            name="MOM Growth %",
            line=dict(color='red', width=3),
            marker=dict(size=8)
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title="Monthly Revenue and MOM Growth",
        height=500
    )
    
    fig.update_yaxes(title_text="MRR (USD)", secondary_y=False)
    fig.update_yaxes(title_text="MOM Growth (%)", secondary_y=True)
    
    return fig

def analyze_individual_customers_q1(df, top_n_list=[5, 10, 15]):
    """Analyze individual customers by Q1 2024 revenue"""
    
    # Find customer/client column - look for common customer identifier columns
    customer_column = None
    possible_customer_cols = ['Customer', 'Client', 'Customer Name', 'Client Name', 
                             'Company', 'Company Name', 'Entity', 'Account', 
                             'Customer_Name', 'Client_Name']
    
    for col in possible_customer_cols:
        if col in df.columns:
            customer_column = col
            break
    
    if customer_column is None:
        # If no standard customer column found, use the first non-numeric column
        for col in df.columns:
            if df[col].dtype == 'object' and col not in ['Country', 'Industry', 'Geography']:
                customer_column = col
                break
    
    if customer_column is None:
        raise ValueError("No customer identifier column found in the dataset")
    
    # Get monthly columns for 2024
    monthly_cols = []
    for col in df.columns:
        if isinstance(col, pd.Timestamp) and col.year == 2024:
            monthly_cols.append(col)
        elif isinstance(col, str) and '2024' in str(col):
            try:
                parsed_date = pd.to_datetime(col, errors='coerce')
                if pd.notna(parsed_date) and parsed_date.year == 2024:
                    monthly_cols.append(col)
            except:
                continue
    
    if not monthly_cols:
        # Last resort - look for any column containing "2024"
        for col in df.columns:
            if '2024' in str(col):
                monthly_cols.append(col)
    
    # Sort monthly columns chronologically
    if monthly_cols:
        try:
            monthly_cols = sorted(monthly_cols, key=lambda x: pd.to_datetime(str(x)))
        except:
            monthly_cols = sorted(monthly_cols)
    
    # Get Q1 columns (first 3 months)
    q1_cols = monthly_cols[:3]
    
    if len(q1_cols) == 0:
        raise ValueError("No Q1 monthly columns found")
    
    # Create customer revenue dataframe
    customer_df = df[[customer_column] + q1_cols].copy()
    
    # Convert monthly columns to numeric
    for col in q1_cols:
        customer_df[col] = pd.to_numeric(customer_df[col], errors='coerce').fillna(0)
    
    # Remove rows with null or empty customer names
    customer_df = customer_df.dropna(subset=[customer_column])
    customer_df = customer_df[customer_df[customer_column].astype(str).str.strip() != '']
    
    # Group by customer (in case there are duplicate customer entries)
    customer_grouped = customer_df.groupby(customer_column).sum()
    
    # Calculate Q1 total revenue for each customer
    customer_grouped['Q1_Total'] = customer_grouped[q1_cols].sum(axis=1)
    
    # Sort customers by Q1 revenue in descending order
    customer_q1_sorted = customer_grouped['Q1_Total'].sort_values(ascending=False)
    
    # Create analysis for different top N values
    top_customers_analysis = {}
    
    for n in top_n_list:
        top_n_customers = customer_q1_sorted.head(n)
        
        # Calculate percentage of total revenue
        total_q1_revenue = customer_q1_sorted.sum()
        top_n_percentage = (top_n_customers.sum() / total_q1_revenue) * 100 if total_q1_revenue > 0 else 0
        
        top_customers_analysis[n] = {
            'customers': top_n_customers,
            'total_revenue': top_n_customers.sum(),
            'percentage_of_total': top_n_percentage,
            'count': len(top_n_customers),
            'customer_details': customer_grouped.loc[top_n_customers.index]
        }
    
    return top_customers_analysis, customer_q1_sorted, customer_column


def create_individual_customers_chart(top_customers_data, top_n):
    """Create a horizontal bar chart for top N individual customers"""
    
    customers = top_customers_data[top_n]['customers']
    
    fig = px.bar(
        x=customers.values,
        y=customers.index,
        orientation='h',
        title=f"Top {top_n} Individual Customers by Q1 2024 Revenue",
        labels={'x': 'Q1 Revenue (USD)', 'y': 'Customer Name'},
        color=customers.values,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        height=max(400, len(customers) * 35),  # Dynamic height based on number of customers
        yaxis={'categoryorder': 'total ascending'},  # Sort by revenue
        showlegend=False,
        font=dict(size=10),
        margin=dict(l=200)  # More left margin for customer names
    )
    
    # Format hover text
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Q1 Revenue: $%{x:,.2f}<extra></extra>'
    )
    
    return fig


def create_customer_monthly_breakdown_chart(customer_details, top_n, q1_cols):
    """Create a stacked bar chart showing monthly breakdown for top customers"""
    
    # Get top N customers monthly data
    top_customers_monthly = customer_details.head(top_n)[q1_cols]
    
    fig = px.bar(
        top_customers_monthly.T,
        x=top_customers_monthly.T.index,
        y=top_customers_monthly.columns,
        title=f"Monthly Q1 Breakdown - Top {top_n} Customers",
        labels={'value': 'Monthly Revenue (USD)', 'index': 'Month'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Month",
        yaxis_title="Revenue (USD)",
        legend_title="Customer",
        font=dict(size=12)
    )
    
    return fig


def create_customer_concentration_chart(top_customers_analysis):
    """Create a chart showing revenue concentration across different top N groups"""
    
    top_n_values = list(top_customers_analysis.keys())
    percentages = [top_customers_analysis[n]['percentage_of_total'] for n in top_n_values]
    
    fig = px.bar(
        x=[f"Top {n}" for n in top_n_values],
        y=percentages,
        title="Revenue Concentration Analysis",
        labels={'x': 'Customer Groups', 'y': 'Percentage of Total Q1 Revenue'},
        color=percentages,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        font=dict(size=12)
    )
    
    fig.update_traces(
        texttemplate='%{y:.1f}%',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Revenue Share: %{y:.2f}%<extra></extra>'
    )
    
    return fig
