import streamlit as st
import pandas as pd
import numpy as np
from main import (
    load_and_process_data,
    create_mrr_chart,
    create_percentage_pie_chart,
    create_trend_chart,
    calculate_monthly_data_simple,
    create_simple_mom_chart,
    analyze_individual_customers_q1,
    create_individual_customers_chart,
    create_customer_monthly_breakdown_chart,
    create_customer_concentration_chart,
    # Revenue Bridge functions
    calculate_revenue_bridge,
    create_revenue_bridge_chart,
    create_customer_segment_chart,
    create_nrr_grr_gauge_chart
)

# Set page configuration
st.set_page_config(
    page_title="Unified MRR Analysis Dashboard",
    page_icon="📊",
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
    .quarter-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e86de;
        margin: 1rem 0;
    }
    .analysis-selector {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .bridge-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Main header
    st.markdown('<h1 class="main-header">Unified Quarterly MRR Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Analysis Type Selector
    st.markdown('<div class="analysis-selector">', unsafe_allow_html=True)
    st.subheader("Choose Your Analysis Type")
    analysis_type = st.radio(
        "Select the analysis type you want to perform:",
        options=["Geography", "Industry", "Revenue Bridge"],
        index=0,
        horizontal=True,
        help="Choose between Geographic/Industry MRR analysis or Revenue Bridge analysis"
    )
    
    # Display selected analysis info
    if analysis_type == "Geography":
        st.info("**Geographic Analysis Selected** - Analyzing MRR distribution across different countries/regions")
    elif analysis_type == "Industry":
        st.info("**Industry Analysis Selected** - Analyzing MRR distribution across different industry sectors")
    else: 
        st.info("**Revenue Bridge Analysis Selected** - Analyzing revenue movement from Q1 to Q2 with churn, expansion, and acquisition insights")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar for file upload
    st.sidebar.header("Data Input")
    uploaded_file = st.sidebar.file_uploader("Upload Revenue Excel File", type=['xlsx', 'xls'])
    
    # Sidebar info about selected analysis
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current Analysis")
    st.sidebar.write(f"**Type:** {analysis_type}")
    if analysis_type == "Geography":
        st.sidebar.write("**Required Column:** 'Country'")
    elif analysis_type == "Industry":
        st.sidebar.write("**Required Column:** 'Industry'")
    else:  # Revenue Bridge
        st.sidebar.write("**Required Data:** Q1 & Q2 2024 monthly data")
        st.sidebar.markdown("**Components:**")
        st.sidebar.write("• Expansion")
        st.sidebar.write("• Contraction") 
        st.sidebar.write("• Churn")
        st.sidebar.write("• New Customers")
        st.sidebar.markdown("**Key Metrics:**")
        st.sidebar.write("• **NRR** - Net Revenue Retention")
        st.sidebar.write("• **GRR** - Gross Revenue Retention")
    
    if uploaded_file is not None:
        try:
            if analysis_type == "Revenue Bridge":
                # REVENUE BRIDGE ANALYSIS FLOW
                
                # Load and process data for Revenue Bridge
                df_original = pd.read_excel(uploaded_file, sheet_name='Sheet1')
                
                # Drop unnecessary columns
                columns_to_drop = [
                    "Entity\nUpto Mar 2024", 
                    "Entity April 2024", 
                    "Entity grouped",
                    "S. no."
                ]
                df_original = df_original.drop(columns=[col for col in columns_to_drop if col in df_original.columns], errors='ignore')
                
                # Find customer column
                customer_column = None
                possible_customer_cols = ['Customer', 'Client', 'Customer Name', 'Client Name', 
                                         'Company', 'Company Name', 'Entity', 'Account']
                
                for col in possible_customer_cols:
                    if col in df_original.columns:
                        customer_column = col
                        break
                
                if customer_column is None:
                    for col in df_original.columns:
                        if df_original[col].dtype == 'object' and col not in ['Country', 'Industry']:
                            customer_column = col
                            break
                
                # Get monthly columns
                monthly_cols_bridge = []
                for col in df_original.columns:
                    if isinstance(col, pd.Timestamp) and col.year == 2024:
                        monthly_cols_bridge.append(col)
                    elif isinstance(col, str) and '2024' in str(col):
                        try:
                            parsed_date = pd.to_datetime(col, errors='coerce')
                            if pd.notna(parsed_date) and parsed_date.year == 2024:
                                monthly_cols_bridge.append(col)
                        except:
                            continue
                
                if not monthly_cols_bridge:
                    for col in df_original.columns:
                        if '2024' in str(col):
                            monthly_cols_bridge.append(col)
                
                try:
                    monthly_cols_bridge = sorted(monthly_cols_bridge, key=lambda x: pd.to_datetime(str(x)))
                except:
                    monthly_cols_bridge = sorted(monthly_cols_bridge)
                
                if len(monthly_cols_bridge) >= 6 and customer_column:
                    # Calculate revenue bridge
                    bridge_data, customer_analysis, bridge_metrics = calculate_revenue_bridge(df_original, customer_column, monthly_cols_bridge)
                    
                    # REVENUE BRIDGE DASHBOARD
                    
                    # Key Bridge Metrics
                    st.header("Revenue Bridge Key Metrics")
                    
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
                    
                    # Q1 to Q2 Overview
                    st.header("Q1 to Q2 Revenue Overview")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "Q1 2024 Opening Revenue", 
                            f"${bridge_data['Opening_Revenue_Q1']:,.0f}",
                            help="Total revenue from all customers in Q1 2024"
                        )
                    
                    with col2:
                        st.metric(
                            "Q2 2024 Closing Revenue", 
                            f"${bridge_data['Closing_Revenue_Q2']:,.0f}",
                            delta=f"${bridge_data['Net_Change']:+,.0f}",
                            delta_color="normal" if bridge_data['Net_Change'] >= 0 else "inverse"
                        )
                    
                    # NRR and GRR Gauges
                    st.subheader("NRR & GRR Performance Gauges")
                    gauge_chart = create_nrr_grr_gauge_chart(bridge_data['NRR'], bridge_data['GRR'])
                    st.plotly_chart(gauge_chart, use_container_width=True)
                    
                    # Revenue Bridge Chart
                    st.subheader("Revenue Bridge Waterfall Analysis")
                    bridge_chart = create_revenue_bridge_chart(bridge_data)
                    st.plotly_chart(bridge_chart, use_container_width=True)
                    
                    # Customer Segmentation and Analysis
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Customer Movement Segmentation")
                        segment_chart = create_customer_segment_chart(customer_analysis)
                        st.plotly_chart(segment_chart, use_container_width=True)
                    
                    with col2:
                        st.subheader("Bridge Components Summary")
                        
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
                        
                        bridge_summary['Amount_Formatted'] = bridge_summary['Amount'].apply(lambda x: f"${x:,.0f}")
                        bridge_summary['% of Q1'] = (bridge_summary['Amount'] / bridge_data['Opening_Revenue_Q1'] * 100).apply(lambda x: f"{x:.1f}%")
                        
                        st.dataframe(
                            bridge_summary[['Component', 'Amount_Formatted', '% of Q1', 'Customer Count']].rename(columns={'Amount_Formatted': 'Amount'}),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # Detailed Customer Analysis
                    st.subheader("Detailed Customer Movement Analysis")
                    
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
                    
                    # Show top 20 customers by default, all if filtered
                    display_count = 20 if segment_filter == 'All Segments' else len(filtered_analysis)
                    filtered_analysis = filtered_analysis.head(display_count)
                    
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
                    st.subheader("Key Revenue Bridge Insights")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Top Risk Areas:**")
                        if bridge_data['Churn'] < 0:
                            st.write(f"• **Churn Impact**: ${abs(bridge_data['Churn']):,.0f} lost from {bridge_metrics['churned_customers_count']} customers")
                        if bridge_data['Contraction'] < 0:
                            st.write(f"• **Contraction Impact**: ${abs(bridge_data['Contraction']):,.0f} from {bridge_metrics['contraction_customers_count']} customers")
                        
                        if len(bridge_metrics['top_contraction_customers']) > 0:
                            st.write("**Highest Contracting Customers:**")
                            for customer, change in bridge_metrics['top_contraction_customers'].head(3).items():
                                st.write(f"• {customer}: ${change:,.0f}")
                    
                    with col2:
                        st.write("**Growth Drivers:**")
                        if bridge_data['New_Customers'] > 0:
                            st.write(f"• **New Customers**: ${bridge_data['New_Customers']:,.0f} from {bridge_metrics['new_customers_count']} customers")
                        if bridge_data['Expansion'] > 0:
                            st.write(f"• **Expansion**: ${bridge_data['Expansion']:,.0f} from {bridge_metrics['expansion_customers_count']} customers")
                        
                        if len(bridge_metrics['top_expansion_customers']) > 0:
                            st.write("**Top Expanding Customers:**")
                            for customer, change in bridge_metrics['top_expansion_customers'].head(3).items():
                                st.write(f"• {customer}: +${change:,.0f}")
                
                else:
                    # Show error message for insufficient data
                    st.error("Insufficient Data for Revenue Bridge Analysis")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if len(monthly_cols_bridge) < 6:
                            st.warning(f"**Missing Monthly Data:** Found {len(monthly_cols_bridge)} months, need at least 6 (Q1 + Q2)")
                    
                    with col2:
                        if not customer_column:
                            st.warning("**Missing Customer Column:** No customer identifier found")
                    
                    st.info("**Requirements for Revenue Bridge Analysis:**")
                    st.write("• At least 6 monthly revenue columns (Q1: Jan-Mar, Q2: Apr-Jun)")
                    st.write("• Customer identifier column (Customer, Client, Company Name, etc.)")
                    st.write("• Individual customer-level data (not aggregated)")
            
            else:
                # EXISTING QUARTERLY MRR ANALYSIS FLOW (Geography/Industry)
                
                # Process the data
                quarterly_mrr, quarterly_percentages, monthly_mrr = load_and_process_data(uploaded_file, analysis_type)
                
                if quarterly_mrr is not None and quarterly_percentages is not None:
                    # Overview metrics
                    st.header("Executive Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_q1 = quarterly_mrr['Q1 2024'].sum()
                    total_q2 = quarterly_mrr['Q2 2024'].sum()
                    total_q3 = quarterly_mrr['Q3 2024'].sum()
                    total_q4 = quarterly_mrr['Q4 2024'].sum()
                    
                    with col1:
                        st.metric("Q1 2024 Total MRR", f"${total_q1:,.2f}", 
                                 delta=None, delta_color="normal")
                    
                    with col2:
                        delta_q2 = ((total_q2 - total_q1) / total_q1 * 100) if total_q1 != 0 else 0
                        st.metric("Q2 2024 Total MRR", f"${total_q2:,.2f}", 
                                 delta=f"{delta_q2:+.2f}%", delta_color="normal")
                    
                    with col3:
                        delta_q3 = ((total_q3 - total_q2) / total_q2 * 100) if total_q2 != 0 else 0
                        st.metric("Q3 2024 Total MRR", f"${total_q3:,.2f}", 
                                 delta=f"{delta_q3:+.2f}%", delta_color="normal")
                    
                    with col4:
                        delta_q4 = ((total_q4 - total_q3) / total_q3 * 100) if total_q3 != 0 else 0
                        st.metric("Q4 2024 Total MRR", f"${total_q4:,.2f}", 
                                 delta=f"{delta_q4:+.2f}%", delta_color="normal")
                    
                    # Detailed Analysis
                    st.header(f"{analysis_type} Breakdown")
                    
                    # Create tabs for different views
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "MRR Values", 
                        "Percentage Distribution", 
                        "Trend Analysis", 
                        "MOM Analysis", 
                        "Top Customers",
                        "Revenue Bridge"
                    ])
                    
                    with tab1:
                        st.subheader(f"Quarterly MRR by {analysis_type} (USD)")
                        
                        # Display the MRR chart
                        mrr_chart = create_mrr_chart(quarterly_mrr, analysis_type)
                        st.plotly_chart(mrr_chart, use_container_width=True)
                        
                        # Display the data table
                        st.subheader("Detailed MRR Table")
                        st.dataframe(
                            quarterly_mrr.style.format("${:,.2f}"),
                            use_container_width=True
                        )
                    
                    with tab2:
                        st.subheader(f"Quarterly Percentage Distribution by {analysis_type}")
                        
                        # Quarter selection dropdown
                        quarter_to_view = st.selectbox(
                            "Select Quarter to View",
                            options=quarterly_percentages.columns.tolist(),
                            index=0
                        )
                        
                        # Display the pie chart for selected quarter
                        pie_chart = create_percentage_pie_chart(quarterly_percentages, quarter_to_view, analysis_type)
                        st.plotly_chart(pie_chart, use_container_width=True)
                        
                        # Display the percentage table
                        st.subheader("Detailed Percentage Table")
                        st.dataframe(
                            quarterly_percentages.style.format("{:.2f}%"),
                            use_container_width=True
                        )
                    
                    with tab3:
                        st.subheader("MRR Trend Analysis")
                        
                        # Display the trend chart
                        trend_chart = create_trend_chart(quarterly_mrr, analysis_type)
                        st.plotly_chart(trend_chart, use_container_width=True)
                        
                        # Growth analysis
                        st.subheader("Quarter-over-Quarter Growth Analysis")
                        growth_df = quarterly_mrr.pct_change(axis=1) * 100
                        growth_df = growth_df.iloc[:, 1:]  # Remove Q1 as it has no previous quarter
                        growth_df = growth_df.round(2)
                        
                        st.dataframe(
                            growth_df.style.format("{:+.2f}%"),
                            use_container_width=True
                        )

                    with tab4:
                        st.subheader("Month-over-Month Revenue Analysis")
                        
                        # Calculate monthly data
                        monthly_df = calculate_monthly_data_simple(monthly_mrr)
                        
                        # Display the chart
                        mom_chart = create_simple_mom_chart(monthly_df)
                        st.plotly_chart(mom_chart, use_container_width=True)
                        
                        # Display the table
                        st.subheader("Monthly Revenue Summary")
                        
                        # Format the dataframe for display
                        display_df = monthly_df.copy()
                        display_df['Total_MRR'] = display_df['Total_MRR'].apply(lambda x: f"${x:,.2f}")
                        display_df['MOM_Growth_Pct'] = display_df['MOM_Growth_Pct'].apply(
                            lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
                        )
                        
                        # Rename columns for better display
                        display_df = display_df.rename(columns={
                            'Total_MRR': 'Total MRR',
                            'MOM_Growth_Pct': 'MOM Growth %'
                        })
                        
                        st.dataframe(
                            display_df[['Month', 'Total MRR', 'MOM Growth %']],
                            use_container_width=True,
                            hide_index=True
                        )

                    with tab5:
                        st.subheader("Individual Customer Analysis - Q1 2024")
                        
                        try:
                            # Load original dataframe for individual customer analysis
                            df_original = pd.read_excel(uploaded_file, sheet_name='Sheet1')
                            
                            # Drop unnecessary columns
                            columns_to_drop = [
                                "Entity\nUpto Mar 2024", 
                                "Entity April 2024", 
                                "Entity grouped",
                                "S. no."
                            ]
                            df_original = df_original.drop(columns=[col for col in columns_to_drop if col in df_original.columns], errors='ignore')
                            
                            # Analyze individual customers
                            top_customers_analysis, all_customers_sorted, customer_column = analyze_individual_customers_q1(df_original)
                            
                            st.success(f"Found customer data in column: **{customer_column}**")
                            st.info(f"Analyzing **{len(all_customers_sorted)}** individual customers")
                            
                            # Overview metrics
                            st.subheader("Customer Concentration Overview")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                top5_pct = top_customers_analysis[5]['percentage_of_total']
                                top5_revenue = top_customers_analysis[5]['total_revenue']
                                st.metric(
                                    "Top 5 Customers", 
                                    f"{top5_pct:.1f}%",
                                    delta=f"${top5_revenue:,.0f}",
                                    help="Percentage and total Q1 revenue from top 5 customers"
                                )
                            
                            with col2:
                                top10_pct = top_customers_analysis[10]['percentage_of_total']
                                top10_revenue = top_customers_analysis[10]['total_revenue']
                                st.metric(
                                    "Top 10 Customers", 
                                    f"{top10_pct:.1f}%",
                                    delta=f"${top10_revenue:,.0f}",
                                    help="Percentage and total Q1 revenue from top 10 customers"
                                )
                            
                            with col3:
                                top15_pct = top_customers_analysis[15]['percentage_of_total']
                                top15_revenue = top_customers_analysis[15]['total_revenue']
                                st.metric(
                                    "Top 15 Customers", 
                                    f"{top15_pct:.1f}%",
                                    delta=f"${top15_revenue:,.0f}",
                                    help="Percentage and total Q1 revenue from top 15 customers"
                                )
                            
                            # Revenue concentration chart
                            st.subheader("Revenue Concentration Analysis")
                            concentration_chart = create_customer_concentration_chart(top_customers_analysis)
                            st.plotly_chart(concentration_chart, use_container_width=True)
                            
                            # Interactive selection for detailed analysis
                            st.subheader("Individual Customer Detailed Analysis")
                            
                            # Dropdown to select top N customers to analyze
                            selected_top_n = st.selectbox(
                                "Select number of top customers to analyze:",
                                options=[5, 10, 15],
                                index=0,
                                help="Choose how many top individual customers you want to see in detail"
                            )
                            
                            # Display chart for selected top N individual customers
                            st.subheader(f"Top {selected_top_n} Individual Customers - Q1 2024 Revenue")
                            top_customers_chart = create_individual_customers_chart(top_customers_analysis, selected_top_n)
                            st.plotly_chart(top_customers_chart, use_container_width=True)
                            
                            # Display detailed table for individual customers
                            st.subheader(f"Top {selected_top_n} Individual Customers - Detailed Table")
                            
                            selected_customers = top_customers_analysis[selected_top_n]['customers']
                            customer_details = top_customers_analysis[selected_top_n]['customer_details']
                            
                            # Create detailed dataframe with monthly breakdown
                            detailed_df = pd.DataFrame({
                                'Rank': range(1, len(selected_customers) + 1),
                                'Customer_Name': selected_customers.index,
                                'Q1_Total_Revenue': selected_customers.values,
                                'Percentage_of_Total': (selected_customers.values / all_customers_sorted.sum()) * 100
                            })
                            
                            # Add monthly columns if available
                            monthly_cols = [col for col in customer_details.columns if col != 'Q1_Total']
                            if len(monthly_cols) >= 3:
                                q1_monthly_cols = monthly_cols[:3]
                                for i, month_col in enumerate(q1_monthly_cols, 1):
                                    detailed_df[f'Month_{i}'] = [customer_details.loc[customer, month_col] for customer in selected_customers.index]
                            
                            # Format for display
                            display_detailed_df = detailed_df.copy()
                            display_detailed_df['Q1_Total_Revenue'] = display_detailed_df['Q1_Total_Revenue'].apply(lambda x: f"${x:,.2f}")
                            display_detailed_df['Percentage_of_Total'] = display_detailed_df['Percentage_of_Total'].apply(lambda x: f"{x:.2f}%")
                            
                            # Format monthly columns if they exist
                            month_columns = [col for col in display_detailed_df.columns if col.startswith('Month_')]
                            for col in month_columns:
                                display_detailed_df[col] = display_detailed_df[col].apply(lambda x: f"${x:,.2f}")
                            
                            # Rename columns for better display
                            column_renames = {
                                'Customer_Name': 'Customer Name',
                                'Q1_Total_Revenue': 'Q1 Total Revenue',
                                'Percentage_of_Total': '% of Total Q1'
                            }
                            
                            # Add month names if available
                            if len(month_columns) >= 3:
                                column_renames.update({
                                    'Month_1': 'Jan 2024',
                                    'Month_2': 'Feb 2024', 
                                    'Month_3': 'Mar 2024'
                                })
                            
                            display_detailed_df = display_detailed_df.rename(columns=column_renames)
                            
                            st.dataframe(
                                display_detailed_df,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Individual customer insights
                            st.subheader("Key Customer Insights")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Top Individual Performers:**")
                                top_3_customers = selected_customers.head(3)
                                for i, (customer, revenue) in enumerate(top_3_customers.items(), 1):
                                    percentage = (revenue / all_customers_sorted.sum()) * 100
                                    st.write(f"{i}. **{customer}**: ${revenue:,.2f} ({percentage:.2f}%)")
                            
                            with col2:
                                st.write("**Customer Distribution Stats:**")
                                st.write(f"• **Total Individual Customers**: {len(all_customers_sorted)}")
                                st.write(f"• **Average Q1 Revenue**: ${all_customers_sorted.mean():,.2f}")
                                st.write(f"• **Median Q1 Revenue**: ${all_customers_sorted.median():,.2f}")
                                st.write(f"• **Top Customer Revenue**: ${all_customers_sorted.iloc[0]:,.2f}")
                                
                                # Revenue distribution
                                customers_above_avg = (all_customers_sorted > all_customers_sorted.mean()).sum()
                                st.write(f"• **Customers Above Average**: {customers_above_avg} ({customers_above_avg/len(all_customers_sorted)*100:.1f}%)")
                            
                        except Exception as e:
                            st.error(f"Error analyzing individual customers: {str(e)}")
                            st.info("Please ensure your data has a customer identifier column (Customer, Client, Company Name, etc.)")

                    with tab6:
                        st.subheader("Revenue Bridge Analysis (Q1 to Q2)")
                        
                        st.markdown('<div class="bridge-warning">', unsafe_allow_html=True)
                        st.info("**Quick Access**: For detailed Revenue Bridge analysis, select 'Revenue Bridge' from the analysis type selector at the top of the page.")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        try:
                            # Load original dataframe for revenue bridge analysis
                            df_original = pd.read_excel(uploaded_file, sheet_name='Sheet1')
                            
                            # Drop unnecessary columns
                            columns_to_drop = [
                                "Entity\nUpto Mar 2024", 
                                "Entity April 2024", 
                                "Entity grouped",
                                "S. no."
                            ]
                            df_original = df_original.drop(columns=[col for col in columns_to_drop if col in df_original.columns], errors='ignore')
                            
                            # Find customer column
                            customer_column = None
                            possible_customer_cols = ['Customer', 'Client', 'Customer Name', 'Client Name', 
                                                     'Company', 'Company Name', 'Entity', 'Account']
                            
                            for col in possible_customer_cols:
                                if col in df_original.columns:
                                    customer_column = col
                                    break
                            
                            if customer_column is None:
                                for col in df_original.columns:
                                    if df_original[col].dtype == 'object' and col not in ['Country', 'Industry']:
                                        customer_column = col
                                        break
                            
                            # Get monthly columns
                            monthly_cols_bridge = []
                            for col in df_original.columns:
                                if isinstance(col, pd.Timestamp) and col.year == 2024:
                                    monthly_cols_bridge.append(col)
                                elif isinstance(col, str) and '2024' in str(col):
                                    try:
                                        parsed_date = pd.to_datetime(col, errors='coerce')
                                        if pd.notna(parsed_date) and parsed_date.year == 2024:
                                            monthly_cols_bridge.append(col)
                                    except:
                                        continue
                            
                            if not monthly_cols_bridge:
                                for col in df_original.columns:
                                    if '2024' in str(col):
                                        monthly_cols_bridge.append(col)
                            
                            try:
                                monthly_cols_bridge = sorted(monthly_cols_bridge, key=lambda x: pd.to_datetime(str(x)))
                            except:
                                monthly_cols_bridge = sorted(monthly_cols_bridge)
                            
                            if len(monthly_cols_bridge) >= 6 and customer_column:
                                # Calculate revenue bridge
                                bridge_data, customer_analysis, bridge_metrics = calculate_revenue_bridge(df_original, customer_column, monthly_cols_bridge)
                                
                                # Simplified Bridge Metrics
                                st.subheader("Key Bridge Metrics")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    nrr_value = bridge_data['NRR']
                                    st.metric(
                                        "Net Revenue Retention", 
                                        f"{nrr_value:.1%}",
                                        delta=f"{(nrr_value - 1.0):.1%}",
                                        delta_color="normal" if nrr_value >= 1.0 else "inverse"
                                    )
                                
                                with col2:
                                    grr_value = bridge_data['GRR']
                                    st.metric(
                                        "Gross Revenue Retention", 
                                        f"{grr_value:.1%}",
                                        delta=f"{(grr_value - 1.0):.1%}",
                                        delta_color="normal" if grr_value >= 0.9 else "inverse"
                                    )
                                
                                with col3:
                                    net_change = bridge_data['Net_Change']
                                    st.metric(
                                        "Net Revenue Change", 
                                        f"${net_change:,.0f}",
                                        delta=f"{(net_change / bridge_data['Opening_Revenue_Q1']):.1%}",
                                        delta_color="normal" if net_change >= 0 else "inverse"
                                    )
                                
                                # Quick Bridge Chart
                                st.subheader("Revenue Bridge Overview")
                                bridge_chart = create_revenue_bridge_chart(bridge_data)
                                st.plotly_chart(bridge_chart, use_container_width=True)
                                
                                # Quick Bridge Summary
                                st.subheader("Bridge Components")
                                
                                bridge_summary = pd.DataFrame({
                                    'Component': ['Q1 Opening', 'Churn', 'Expansion', 'Contraction', 'New Customers', 'Q2 Closing'],
                                    'Amount': [
                                        f"${bridge_data['Opening_Revenue_Q1']:,.0f}",
                                        f"${bridge_data['Churn']:,.0f}",
                                        f"${bridge_data['Expansion']:,.0f}",
                                        f"${bridge_data['Contraction']:,.0f}",
                                        f"${bridge_data['New_Customers']:,.0f}",
                                        f"${bridge_data['Closing_Revenue_Q2']:,.0f}"
                                    ],
                                    'Impact': [
                                        "Baseline",
                                        f"Lost {bridge_metrics['churned_customers_count']} customers",
                                        f"Growth from {bridge_metrics['expansion_customers_count']} customers",
                                        f"Decline from {bridge_metrics['contraction_customers_count']} customers",
                                        f"Added {bridge_metrics['new_customers_count']} customers",
                                        f"Net change: ${bridge_data['Net_Change']:+,.0f}"
                                    ]
                                })
                                
                                st.dataframe(bridge_summary, use_container_width=True, hide_index=True)
                                
                            else:
                                if len(monthly_cols_bridge) < 6:
                                    st.warning(f"Need at least 6 months of data for Revenue Bridge analysis. Found {len(monthly_cols_bridge)} months.")
                                if not customer_column:
                                    st.warning("Need customer identifier column for Revenue Bridge analysis.")
                                
                                st.info("For complete Revenue Bridge analysis, select 'Revenue Bridge' from the main analysis selector above.")
                                
                        except Exception as e:
                            st.error(f"Error in Revenue Bridge preview: {str(e)}")
                            st.info("For detailed Revenue Bridge analysis, please select 'Revenue Bridge' from the analysis type selector at the top.")
                    
                    # Key insights
                    st.header("Key Insights")
                    
                    # Top performer by quarter
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"Top {analysis_type} by Quarter")
                        top_performer_by_quarter = quarterly_mrr.idxmax()
                        for quarter, performer in top_performer_by_quarter.items():
                            value = quarterly_mrr.loc[performer, quarter]
                            percentage = quarterly_percentages.loc[performer, quarter]
                            st.write(f"**{quarter}**: {performer} - ${value:,.2f} ({percentage:.2f}%)")
                    
                    with col2:
                        st.subheader("Overall Performance")
                        total_by_dimension = quarterly_mrr.sum(axis=1).sort_values(ascending=False)
                        st.write(f"**Total MRR by {analysis_type} (2024):**")
                        for dimension, value in total_by_dimension.items():
                            percentage = (value / total_by_dimension.sum()) * 100
                            st.write(f"• {dimension}: ${value:,.2f} ({percentage:.2f}%)")
                            
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            if analysis_type == "Revenue Bridge":
                st.info("Please ensure your data has sufficient Q1 and Q2 data with customer identifiers.")
            else:
                st.info(f"Please ensure the file has the correct format with {analysis_type} and monthly columns.")
    
    else:
        st.info("Please upload your revenue Excel file using the sidebar to begin analysis.")
        
        # Show sample data format
        st.subheader("Expected Data Format")
        st.write("Your Excel file should contain:")
        if analysis_type == "Geography":
            st.write("• A **'Country'** column for geographic analysis")
            st.write("• Monthly revenue columns for 2024 (datetime format)")
        elif analysis_type == "Industry":
            st.write("• An **'Industry'** column for industry analysis")
            st.write("• Monthly revenue columns for 2024 (datetime format)")
        else:  # Revenue Bridge
            st.write("• A customer identifier column (Customer, Client, Company Name, etc.)")
            st.write("• At least 6 monthly revenue columns for 2024 (Q1 + Q2)")
            st.write("• Individual customer-level data (not aggregated)")
        
        st.write("• Each row representing a different entity/customer")
        
        # Analysis-specific tips
        if analysis_type != "Revenue Bridge":
            st.info("**Tip:** You can switch between Geography, Industry, and Revenue Bridge analysis using the radio buttons at the top!")
        else:
            st.info("**Tip:** Revenue Bridge analysis shows customer movement, churn, expansion, and acquisition insights between Q1 and Q2!")


if __name__ == "__main__":
    main()
