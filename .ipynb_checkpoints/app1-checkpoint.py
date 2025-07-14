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
    create_customer_concentration_chart
)

# Set page configuration
st.set_page_config(
    page_title="Quarterly MRR Analysis Dashboard",
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
</style>
""", unsafe_allow_html=True)


def main():
    # Main header
    st.markdown('<h1 class="main-header">📊 Unified Quarterly MRR Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Analysis Type Selector
    st.markdown('<div class="analysis-selector">', unsafe_allow_html=True)
    st.subheader("🎯 Choose Your Analysis Type")
    analysis_type = st.radio(
        "Select the dimension you want to analyze:",
        options=["Geography", "Industry"],
        index=0,
        horizontal=True,
        help="Choose whether to analyze MRR by Geographic regions or Industry sectors"
    )
    
    # Display selected analysis info
    if analysis_type == "Geography":
        st.info("🌍 **Geographic Analysis Selected** - Analyzing MRR distribution across different countries/regions")
    else:
        st.info("🏭 **Industry Analysis Selected** - Analyzing MRR distribution across different industry sectors")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar for file upload
    st.sidebar.header("📁 Data Input")
    uploaded_file = st.sidebar.file_uploader("Upload Revenue Excel File", type=['xlsx', 'xls'])
    
    # Sidebar info about selected analysis
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Current Analysis")
    st.sidebar.write(f"**Type:** {analysis_type}")
    if analysis_type == "Geography":
        st.sidebar.write("**Required Column:** 'Country'")
        st.sidebar.write("**Icon:** 🌍")
    else:
        st.sidebar.write("**Required Column:** 'Industry'")
        st.sidebar.write("**Icon:** 🏭")
    
    if uploaded_file is not None:
        try:
            # Process the data
            quarterly_mrr, quarterly_percentages, monthly_mrr = load_and_process_data(uploaded_file, analysis_type)
            
            if quarterly_mrr is not None and quarterly_percentages is not None:
                # Overview metrics
                st.header("📈 Executive Summary")
                
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
                icon = "🌍" if analysis_type == "Geography" else "🏭"
                st.header(f"{icon} {analysis_type} Breakdown")
                
                # Create five tabs for different views
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 MRR Values", "🥧 Percentage Distribution", "📉 Trend Analysis", "📈 MOM Analysis", "👥 Top Customers"])
                
                with tab1:
                    st.subheader(f"Quarterly MRR by {analysis_type} (USD)")
                    
                    # Display the MRR chart
                    mrr_chart = create_mrr_chart(quarterly_mrr, analysis_type)
                    st.plotly_chart(mrr_chart, use_container_width=True)
                    
                    # Display the data table
                    st.subheader("📋 Detailed MRR Table")
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
                    st.subheader("📋 Detailed Percentage Table")
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
                    st.subheader("📊 Quarter-over-Quarter Growth Analysis")
                    growth_df = quarterly_mrr.pct_change(axis=1) * 100
                    growth_df = growth_df.iloc[:, 1:]  # Remove Q1 as it has no previous quarter
                    growth_df = growth_df.round(2)
                    
                    st.dataframe(
                        growth_df.style.format("{:+.2f}%"),
                        use_container_width=True
                    )

                with tab4:
                    st.subheader("📈 Month-over-Month Revenue Analysis")
                    
                    # Calculate monthly data
                    monthly_df = calculate_monthly_data_simple(monthly_mrr)
                    
                    # Display the chart
                    mom_chart = create_simple_mom_chart(monthly_df)
                    st.plotly_chart(mom_chart, use_container_width=True)
                    
                    # Display the table
                    st.subheader("📋 Monthly Revenue Summary")
                    
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
                    st.subheader("👥 Individual Customer Analysis - Q1 2024")
                    
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
                        
                        st.success(f"✅ Found customer data in column: **{customer_column}**")
                        st.info(f"📊 Analyzing **{len(all_customers_sorted)}** individual customers")
                        
                        # Overview metrics
                        st.subheader("📊 Customer Concentration Overview")
                        
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
                        st.subheader("📈 Revenue Concentration Analysis")
                        concentration_chart = create_customer_concentration_chart(top_customers_analysis)
                        st.plotly_chart(concentration_chart, use_container_width=True)
                        
                        # Interactive selection for detailed analysis
                        st.subheader("🔍 Individual Customer Detailed Analysis")
                        
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
                        st.subheader(f"📋 Top {selected_top_n} Individual Customers - Detailed Table")
                        
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
                        st.subheader("🎯 Key Customer Insights")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**🏆 Top Individual Performers:**")
                            top_3_customers = selected_customers.head(3)
                            for i, (customer, revenue) in enumerate(top_3_customers.items(), 1):
                                percentage = (revenue / all_customers_sorted.sum()) * 100
                                st.write(f"{i}. **{customer}**: ${revenue:,.2f} ({percentage:.2f}%)")
                        
                        with col2:
                            st.write("**📊 Customer Distribution Stats:**")
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
                        
                        # Show available columns for debugging
                        if 'df_original' in locals():
                            st.write("**Available columns in your dataset:**")
                            st.write(df_original.columns.tolist())

                
                # Key insights
                st.header("🔍 Key Insights")
                
                # Top performer by quarter
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"🏆 Top {analysis_type} by Quarter")
                    top_performer_by_quarter = quarterly_mrr.idxmax()
                    for quarter, performer in top_performer_by_quarter.items():
                        value = quarterly_mrr.loc[performer, quarter]
                        percentage = quarterly_percentages.loc[performer, quarter]
                        st.write(f"**{quarter}**: {performer} - ${value:,.2f} ({percentage:.2f}%)")
                
                with col2:
                    st.subheader("📈 Overall Performance")
                    total_by_dimension = quarterly_mrr.sum(axis=1).sort_values(ascending=False)
                    st.write(f"**Total MRR by {analysis_type} (2024):**")
                    for dimension, value in total_by_dimension.items():
                        percentage = (value / total_by_dimension.sum()) * 100
                        st.write(f"• {dimension}: ${value:,.2f} ({percentage:.2f}%)")
                        
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            st.info(f"Please ensure the file has the correct format with {analysis_type} and monthly columns.")
    
    else:
        st.info("👆 Please upload your revenue Excel file using the sidebar to begin analysis.")
        
        # Show sample data format
        st.subheader("📝 Expected Data Format")
        st.write("Your Excel file should contain:")
        if analysis_type == "Geography":
            st.write("• A **'Country'** column for geographic analysis")
        else:
            st.write("• An **'Industry'** column for industry analysis")
        st.write("• Monthly revenue columns for 2024 (datetime format)")
        st.write("• Each row representing a different entity/customer")
        
        # Quick switch reminder
        st.info("💡 **Tip:** You can switch between Geography and Industry analysis using the radio buttons at the top!")


if __name__ == "__main__":
    main()
