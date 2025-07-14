import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Revenue Bridge Analysis",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .bridge-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e86de;
        margin: 1rem 0;
    }
    .nrr-positive {
        color: #28a745;
        font-weight: bold;
    }
    .nrr-negative {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_process_data(file_path):
    """Load and process the revenue data for bridge analysis"""
    
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
    st.write("**Remaining columns after cleanup:**", len(df.columns))
    st.write("**All column names:**", df.columns.tolist())
    st.write("**Column data types:**", df.dtypes.head(20))
    
    # Find customer column
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
        st.error("No customer identifier column found!")
        return None, None, None
    
    st.success(f"✅ Found customer data in column: **{customer_column}**")
    
    # Multiple methods to detect datetime columns for 2024
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
    
    st.write(f"**Found {len(monthly_cols)} monthly columns**")
    if monthly_cols:
        st.write("**Monthly columns found:**", [str(col) for col in monthly_cols[:6]])
    
    if len(monthly_cols) < 6:
        st.error("Need at least 6 months of data for Q1 vs Q2 bridge analysis!")
        return None, None, None
    
    return df, customer_column, monthly_cols


def calculate_revenue_bridge(df, customer_column, monthly_cols):
    """Calculate revenue bridge components between Q1 and Q2"""
    
    # Get Q1 and Q2 columns
    q1_cols = monthly_cols[:3]   # First 3 months
    q2_cols = monthly_cols[3:6]  # Next 3 months
    
    # Create customer revenue dataframes
    customer_df = df[[customer_column] + q1_cols + q2_cols].copy()
    
    # Convert to numeric
    for col in q1_cols + q2_cols:
        customer_df[col] = pd.to_numeric(customer_df[col], errors='coerce').fillna(0)
    
    # Remove rows with null customer names
    customer_df = customer_df.dropna(subset=[customer_column])
    customer_df = customer_df[customer_df[customer_column].astype(str).str.strip() != '']
    
    # Group by customer and sum quarterly revenue
    customer_grouped = customer_df.groupby(customer_column).sum()
    
    # Calculate Q1 and Q2 totals per customer
    customer_grouped['Q1_Total'] = customer_grouped[q1_cols].sum(axis=1)
    customer_grouped['Q2_Total'] = customer_grouped[q2_cols].sum(axis=1)
    
    # Calculate overall Q1 and Q2 revenue
    opening_revenue = customer_grouped['Q1_Total'].sum()
    #opening_revenue =  11984265
    closing_revenue = customer_grouped['Q2_Total'].sum()
    #closing_revenue =  13511929
    
    # Calculate bridge components
    q1_revenue = customer_grouped['Q1_Total']
    q2_revenue = customer_grouped['Q2_Total']
    
    # Churn: Customers with revenue in Q1 but zero in Q2
    churned_customers = q1_revenue[(q1_revenue > 0) & (q2_revenue == 0)]
    churn = -churned_customers.sum()  # Negative value (lost revenue)
    
    # New customers: Customers with zero revenue in Q1 but revenue in Q2
    new_customers_data = q2_revenue[(q1_revenue == 0) & (q2_revenue > 0)]
    new_customers = new_customers_data.sum()
    
    # Expansion: Existing customers with increased revenue
    expansion_data = q2_revenue - q1_revenue
    expansion = expansion_data[(expansion_data > 0) & (q1_revenue > 0)].sum()
    
    # Contraction: Existing customers with decreased revenue (but not churned)
    contraction = expansion_data[(expansion_data < 0) & (q2_revenue > 0)].sum()
    
    # Calculate NRR and GRR - CORRECTED FORMULAS
    nrr = (opening_revenue + churn + expansion + contraction) / opening_revenue if opening_revenue != 0 else 0
    grr = (opening_revenue + churn + contraction) / opening_revenue if opening_revenue != 0 else 0
    
    # Prepare detailed customer breakdown - ENSURE THIS IS PROPERLY DEFINED
    customer_analysis = pd.DataFrame({
        'Customer': customer_grouped.index,
        'Q1_Revenue': customer_grouped['Q1_Total'],
        'Q2_Revenue': customer_grouped['Q2_Total'],
        'Change': customer_grouped['Q2_Total'] - customer_grouped['Q1_Total'],
        'Change_Pct': ((customer_grouped['Q2_Total'] - customer_grouped['Q1_Total']) / customer_grouped['Q1_Total'] * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    })
    
    # Add customer segments
    def categorize_customer(row):
        if row['Q1_Revenue'] > 0 and row['Q2_Revenue'] == 0:
            return 'Churned'
        elif row['Q1_Revenue'] == 0 and row['Q2_Revenue'] > 0:
            return 'New Customer'
        elif row['Change'] > 0 and row['Q1_Revenue'] > 0:
            return 'Expansion'
        elif row['Change'] < 0 and row['Q2_Revenue'] > 0:
            return 'Contraction'
        else:
            return 'Stable'
    
    customer_analysis['Segment'] = customer_analysis.apply(categorize_customer, axis=1)
    
    # Bridge data
    bridge_data = {
        'Opening_Revenue_Q1': opening_revenue,
        'Churn': churn,
        'Expansion': expansion,
        'Contraction': contraction,
        'New_Customers': new_customers,
        'Closing_Revenue_Q2': closing_revenue,
        'Net_Change': closing_revenue - opening_revenue,
        'NRR': nrr,
        'GRR': grr
    }
    
    # Detailed metrics
    bridge_metrics = {
        'churned_customers_count': len(churned_customers),
        'new_customers_count': len(new_customers_data),
        'expansion_customers_count': len(expansion_data[(expansion_data > 0) & (q1_revenue > 0)]),
        'contraction_customers_count': len(expansion_data[(expansion_data < 0) & (q2_revenue > 0)]),
        'churned_customers_list': churned_customers,
        'new_customers_list': new_customers_data,
        'top_expansion_customers': expansion_data[(expansion_data > 0) & (q1_revenue > 0)].nlargest(5),
        'top_contraction_customers': expansion_data[(expansion_data < 0) & (q2_revenue > 0)].nsmallest(5)
    }
    
    # ENSURE ALL THREE VARIABLES ARE RETURNED
    return bridge_data, customer_analysis, bridge_metrics


def create_revenue_bridge_chart(bridge_data):
    """Create a waterfall-style revenue bridge chart"""
    
    categories = ['Q1 Revenue', 'Churn', 'Expansion', 'Contraction', 'New Customers', 'Q2 Revenue']
    values = [
        bridge_data['Opening_Revenue_Q1'],
        bridge_data['Churn'],
        bridge_data['Expansion'], 
        bridge_data['Contraction'],
        bridge_data['New_Customers'],
        bridge_data['Closing_Revenue_Q2']
    ]
    
    # Create colors - green for positive, red for negative, blue for totals
    colors = ['lightblue', 'red', 'green', 'orange', 'purple', 'lightblue']
    
    fig = go.Figure()
    
    # Add bars for each component
    for i, (cat, val, color) in enumerate(zip(categories, values, colors)):
        fig.add_trace(go.Bar(
            x=[cat],
            y=[val],
            name=cat,
            marker_color=color,
            text=f'${val:,.0f}',
            textposition='outside' if val >= 0 else 'inside',
            showlegend=False
        ))
    
    fig.update_layout(
        title='Revenue Bridge: Q1 to Q2 2024',
        xaxis_title='Components',
        yaxis_title='Revenue (USD)',
        height=500,
        font=dict(size=12),
        yaxis=dict(tickformat='$,.0f')
    )
    
    return fig


def create_customer_segment_chart(customer_analysis):
    """Create a pie chart showing customer segmentation"""
    
    segment_counts = customer_analysis['Segment'].value_counts()
    
    fig = px.pie(
        values=segment_counts.values,
        names=segment_counts.index,
        title='Customer Segmentation: Q1 to Q2 Movement',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12
    )
    
    fig.update_layout(
        height=400,
        font=dict(size=12)
    )
    
    return fig


def create_nrr_grr_gauge_chart(nrr, grr):
    """Create gauge charts for NRR and GRR"""
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=("Net Revenue Retention (NRR)", "Gross Revenue Retention (GRR)")
    )
    
    # NRR Gauge
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = nrr * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "NRR %"},
        delta = {'reference': 100},
        gauge = {
            'axis': {'range': [None, 150]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 90], 'color': "lightgray"},
                {'range': [90, 100], 'color': "orange"},
                {'range': [100, 150], 'color': "lightgreen"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 100}}
    ), row=1, col=1)
    
    # GRR Gauge
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = grr * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "GRR %"},
        delta = {'reference': 100},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 80], 'color': "lightgray"},
                {'range': [80, 90], 'color': "orange"},
                {'range': [90, 100], 'color': "lightgreen"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}
    ), row=1, col=2)
    
    fig.update_layout(height=300, font={'size': 12})
    
    return fig


def main():
    # Main header
    st.markdown('<h1 class="main-header">🌉 Revenue Bridge Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666;">
            Analyze revenue movement from Q1 to Q2 2024 with customer churn, expansion, contraction, and acquisition insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for file upload
    st.sidebar.header("📁 Data Input")
    uploaded_file = st.sidebar.file_uploader("Upload Revenue Excel File", type=['xlsx', 'xls'])
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Analysis Overview")
    st.sidebar.write("**Revenue Bridge Components:**")
    st.sidebar.write("• 📈 **Expansion** - Existing customers growing")
    st.sidebar.write("• 📉 **Contraction** - Existing customers declining")
    st.sidebar.write("• ❌ **Churn** - Customers lost completely")
    st.sidebar.write("• ✨ **New Customers** - Fresh acquisitions")
    
    st.sidebar.markdown("**Key Metrics:**")
    st.sidebar.write("• **NRR** - Net Revenue Retention")
    st.sidebar.write("• **GRR** - Gross Revenue Retention")
    
    if uploaded_file is not None:
        try:
            # Process the data
            df, customer_column, monthly_cols = load_and_process_data(uploaded_file)
            
            if df is not None:
                # Calculate revenue bridge
                bridge_data, customer_analysis, bridge_metrics = calculate_revenue_bridge(df, customer_column, monthly_cols)
                
                # Key Metrics Row
                st.header("📊 Key Revenue Bridge Metrics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    nrr_value = bridge_data['NRR']
                    nrr_color = "normal" if nrr_value >= 1.0 else "inverse"
                    st.metric(
                        "Net Revenue Retention (NRR)", 
                        f"{nrr_value:.1%}",
                        delta=f"{(nrr_value - 1.0):.1%}",
                        delta_color=nrr_color,
                        help="(Opening Revenue + Churn + Expansion + Contraction) / Opening Revenue"
                    )
                
                with col2:
                    grr_value = bridge_data['GRR']
                    grr_color = "normal" if grr_value >= 0.9 else "inverse"
                    st.metric(
                        "Gross Revenue Retention (GRR)", 
                        f"{grr_value:.1%}",
                        delta=f"{(grr_value - 1.0):.1%}",
                        delta_color=grr_color,
                        help="(Opening Revenue + Churn + Contraction) / Opening Revenue"
                    )
                
                with col3:
                    net_change = bridge_data['Net_Change']
                    change_color = "normal" if net_change >= 0 else "inverse"
                    st.metric(
                        "Net Revenue Change", 
                        f"${net_change:,.0f}",
                        delta=f"{(net_change / bridge_data['Opening_Revenue_Q1']):.1%}",
                        delta_color=change_color
                    )
                
                with col4:
                    churn_rate = abs(bridge_data['Churn']) / bridge_data['Opening_Revenue_Q1']
                    st.metric(
                        "Churn Rate", 
                        f"{churn_rate:.1%}",
                        delta=f"{bridge_metrics['churned_customers_count']} customers",
                        delta_color="inverse"
                    )
                
                # NRR and GRR Gauges
                st.subheader("🎯 NRR & GRR Performance Gauges")
                gauge_chart = create_nrr_grr_gauge_chart(bridge_data['NRR'], bridge_data['GRR'])
                st.plotly_chart(gauge_chart, use_container_width=True)
                
                # Revenue Bridge Chart
                st.subheader("📈 Revenue Bridge Waterfall Analysis")
                bridge_chart = create_revenue_bridge_chart(bridge_data)
                st.plotly_chart(bridge_chart, use_container_width=True)
                
                # Two column layout for charts and data
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("👥 Customer Movement Segmentation")
                    segment_chart = create_customer_segment_chart(customer_analysis)
                    st.plotly_chart(segment_chart, use_container_width=True)
                
                with col2:
                    st.subheader("📋 Bridge Components Summary")
                    
                    # Create summary table
                    bridge_summary = pd.DataFrame({
                        'Component': ['Opening Revenue (Q1)', 'Churn', 'Expansion', 'Contraction', 'New Customers', 'Closing Revenue (Q2)'],
                        'Amount': [
                            bridge_data['Opening_Revenue_Q1'],
                            bridge_data['Churn'],
                            bridge_data['Expansion'],
                            bridge_data['Contraction'],
                            bridge_data['New_Customers'],
                            bridge_data['Closing_Revenue_Q2']
                        ],
                        'Customer Count': [
                            len(customer_analysis[customer_analysis['Q1_Revenue'] > 0]),
                            bridge_metrics['churned_customers_count'],
                            bridge_metrics['expansion_customers_count'],
                            bridge_metrics['contraction_customers_count'],
                            bridge_metrics['new_customers_count'],
                            len(customer_analysis[customer_analysis['Q2_Revenue'] > 0])
                        ]
                    })
                    
                    # Format for display
                    bridge_summary['Amount_Formatted'] = bridge_summary['Amount'].apply(lambda x: f"${x:,.0f}")
                    bridge_summary['% of Q1'] = (bridge_summary['Amount'] / bridge_data['Opening_Revenue_Q1'] * 100).apply(lambda x: f"{x:.1f}%")
                    
                    display_summary = bridge_summary[['Component', 'Amount_Formatted', '% of Q1', 'Customer Count']].copy()
                    display_summary = display_summary.rename(columns={'Amount_Formatted': 'Amount'})
                    
                    st.dataframe(display_summary, use_container_width=True, hide_index=True)
                
                # Detailed Customer Analysis
                st.subheader("🔍 Detailed Customer Movement Analysis")
                
                # Filter options
                segment_filter = st.selectbox(
                    "Filter by Customer Segment:",
                    options=['All Segments'] + list(customer_analysis['Segment'].unique()),
                    index=0
                )
                
                # Filter data
                if segment_filter != 'All Segments':
                    filtered_analysis = customer_analysis[customer_analysis['Segment'] == segment_filter]
                else:
                    filtered_analysis = customer_analysis
                
                # Format customer analysis for display
                display_customer_analysis = filtered_analysis.copy()
                display_customer_analysis['Q1_Revenue'] = display_customer_analysis['Q1_Revenue'].apply(lambda x: f"${x:,.2f}")
                display_customer_analysis['Q2_Revenue'] = display_customer_analysis['Q2_Revenue'].apply(lambda x: f"${x:,.2f}")
                display_customer_analysis['Change'] = display_customer_analysis['Change'].apply(lambda x: f"${x:,.2f}")
                display_customer_analysis['Change_Pct'] = display_customer_analysis['Change_Pct'].apply(
                    lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
                )
                
                # Rename columns for display
                display_customer_analysis = display_customer_analysis.rename(columns={
                    'Q1_Revenue': 'Q1 Revenue',
                    'Q2_Revenue': 'Q2 Revenue',
                    'Change_Pct': 'Change %'
                })
                
                st.dataframe(
                    display_customer_analysis[['Customer', 'Q1 Revenue', 'Q2 Revenue', 'Change', 'Change %', 'Segment']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Key Insights
                st.subheader("💡 Key Revenue Bridge Insights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🔥 Top Risk Areas:**")
                    if bridge_data['Churn'] < 0:
                        st.write(f"• **Churn Impact**: ${abs(bridge_data['Churn']):,.0f} lost from {bridge_metrics['churned_customers_count']} customers")
                    if bridge_data['Contraction'] < 0:
                        st.write(f"• **Contraction Impact**: ${abs(bridge_data['Contraction']):,.0f} from {bridge_metrics['contraction_customers_count']} customers")
                    
                    if len(bridge_metrics['top_contraction_customers']) > 0:
                        st.write("**📉 Highest Contracting Customers:**")
                        for customer, change in bridge_metrics['top_contraction_customers'].head(3).items():
                            st.write(f"• {customer}: ${change:,.0f}")
                
                with col2:
                    st.write("**🚀 Growth Drivers:**")
                    if bridge_data['New_Customers'] > 0:
                        st.write(f"• **New Customers**: ${bridge_data['New_Customers']:,.0f} from {bridge_metrics['new_customers_count']} customers")
                    if bridge_data['Expansion'] > 0:
                        st.write(f"• **Expansion**: ${bridge_data['Expansion']:,.0f} from {bridge_metrics['expansion_customers_count']} customers")
                    
                    if len(bridge_metrics['top_expansion_customers']) > 0:
                        st.write("**📈 Top Expanding Customers:**")
                        for customer, change in bridge_metrics['top_expansion_customers'].head(3).items():
                            st.write(f"• {customer}: +${change:,.0f}")
                    
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            st.info("Please ensure your data has sufficient Q1 and Q2 data with customer identifiers.")
    
    else:
        st.info("👆 Please upload your revenue Excel file using the sidebar to begin analysis.")
        
        # Show sample data format
        st.subheader("📝 Expected Data Format")
        st.write("Your Excel file should contain:")
        st.write("• A customer identifier column (Customer, Client, Company Name, etc.)")
        st.write("• At least 6 monthly revenue columns for 2024 (Q1 + Q2)")
        st.write("• Each row representing a different customer/entity")
        
        # Show example NRR/GRR calculations
        st.subheader("📊 Metric Calculations")
        st.write("**NRR (Net Revenue Retention):**")
        st.code("NRR = (Opening Revenue + Churn + Expansion + Contraction) / Opening Revenue")
        st.write("**GRR (Gross Revenue Retention):**")
        st.code("GRR = (Opening Revenue + Churn + Contraction) / Opening Revenue")


if __name__ == "__main__":
    main()
