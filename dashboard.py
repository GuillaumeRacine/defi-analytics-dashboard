#!/usr/bin/env python3
"""
Streamlit dashboard for visualizing DeFillama dataset.
Run with: streamlit run dashboard.py
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List


@st.cache_resource
def get_connection():
    """Get database connection (cached)"""
    return duckdb.connect("data/duckdb/defillama.db")


@st.cache_data
def load_tokens():
    """Load token list"""
    conn = get_connection()
    tokens = conn.execute("""
        SELECT contract_id, symbol, name, chain
        FROM tokens
        ORDER BY symbol
    """).fetchall()
    return tokens


@st.cache_data
def load_price_data(contract_id: str, days: int = 30):
    """Load price data for a token"""
    conn = get_connection()
    
    cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    prices = conn.execute("""
        SELECT timestamp, price, confidence
        FROM price_history
        WHERE contract_id = ?
          AND timestamp >= ?
        ORDER BY timestamp
    """, (contract_id, cutoff_time)).fetchall()
    
    if not prices:
        return pd.DataFrame()
    
    df = pd.DataFrame(prices, columns=['timestamp', 'price', 'confidence'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='s')
    return df


@st.cache_data
def load_all_prices():
    """Load all price data"""
    conn = get_connection()
    
    data = conn.execute("""
        SELECT 
            t.symbol,
            ph.timestamp,
            ph.price,
            ph.confidence
        FROM price_history ph
        JOIN tokens t ON ph.contract_id = t.contract_id
        ORDER BY ph.timestamp
    """).fetchall()
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data, columns=['symbol', 'timestamp', 'price', 'confidence'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='s')
    return df


def create_price_chart(df: pd.DataFrame, symbol: str):
    """Create interactive price chart"""
    if df.empty:
        st.warning(f"No data available for {symbol}")
        return
    
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['price'],
        mode='lines+markers',
        name=f'{symbol} Price',
        line=dict(width=2),
        marker=dict(size=4),
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Date: %{x}<br>' +
                      'Price: $%{y:.4f}<br>' +
                      '<extra></extra>'
    ))
    
    # Calculate returns for title
    if len(df) > 1:
        first_price = df.iloc[0]['price']
        last_price = df.iloc[-1]['price']
        total_return = (last_price - first_price) / first_price
        
        fig.update_layout(
            title=f'{symbol} Price History (Return: {total_return:+.2%})',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            hovermode='x unified'
        )
    else:
        fig.update_layout(
            title=f'{symbol} Price History',
            xaxis_title='Date',
            yaxis_title='Price (USD)'
        )
    
    return fig


def create_comparison_chart(df: pd.DataFrame):
    """Create multi-token comparison chart (normalized)"""
    if df.empty:
        st.warning("No data available for comparison")
        return
    
    # Pivot data for easier plotting
    pivot_df = df.pivot(index='date', columns='symbol', values='price')
    
    # Normalize prices (set first day = 100)
    normalized_df = (pivot_df / pivot_df.iloc[0] * 100).fillna(method='forward')
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, symbol in enumerate(normalized_df.columns):
        if not normalized_df[symbol].isna().all():
            fig.add_trace(go.Scatter(
                x=normalized_df.index,
                y=normalized_df[symbol],
                mode='lines',
                name=symbol,
                line=dict(width=2, color=colors[i % len(colors)])
            ))
    
    fig.update_layout(
        title='Token Performance Comparison (Normalized to 100)',
        xaxis_title='Date',
        yaxis_title='Normalized Price (Base = 100)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def show_database_stats():
    """Show database statistics"""
    conn = get_connection()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total records
    total_prices = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
    with col1:
        st.metric("Total Price Records", f"{total_prices:,}")
    
    # Unique tokens
    unique_tokens = conn.execute("SELECT COUNT(DISTINCT contract_id) FROM price_history").fetchone()[0]
    with col2:
        st.metric("Tokens Tracked", unique_tokens)
    
    # Date range
    date_range = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_history").fetchone()
    if date_range[0]:
        days = (date_range[1] - date_range[0]) / 86400  # Convert seconds to days
        with col3:
            st.metric("Days of History", f"{days:.0f}")
        
        with col4:
            last_update = datetime.fromtimestamp(date_range[1]).strftime('%Y-%m-%d')
            st.metric("Last Update", last_update)


def main():
    """Main dashboard"""
    st.set_page_config(
        page_title="DeFillama Dataset Explorer",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 DeFillama Backtesting Dataset Explorer")
    st.markdown("Interactive visualization of your collected DeFi data")
    
    # Sidebar for navigation
    st.sidebar.title("🧭 Navigation")
    
    # Database status
    show_database_stats()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Charts", "📊 Data Tables", "🔍 SQL Query", "📋 Database Info"])
    
    with tab1:
        st.header("Token Price Visualization")
        
        # Load tokens for selection
        tokens = load_tokens()
        if not tokens:
            st.error("No tokens found in database. Run the data collector first!")
            return
        
        token_options = {f"{token[1]} ({token[2]})": token[0] for token in tokens}
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_token_display = st.selectbox("Select Token", list(token_options.keys()))
            selected_token_id = token_options[selected_token_display]
        
        with col2:
            days = st.slider("Days of History", 7, 90, 30)
        
        # Individual token chart
        df = load_price_data(selected_token_id, days)
        if not df.empty:
            symbol = selected_token_display.split()[0]
            fig = create_price_chart(df, symbol)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${df.iloc[-1]['price']:.4f}")
            with col2:
                if len(df) > 1:
                    change = (df.iloc[-1]['price'] - df.iloc[0]['price']) / df.iloc[0]['price']
                    st.metric("Total Return", f"{change:+.2%}")
            with col3:
                daily_returns = df['price'].pct_change().dropna()
                volatility = daily_returns.std() if len(daily_returns) > 1 else 0
                st.metric("Volatility", f"{volatility:.4f}")
            with col4:
                avg_confidence = df['confidence'].mean()
                st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        # Comparison chart
        st.header("Multi-Token Comparison")
        df_all = load_all_prices()
        if not df_all.empty:
            # Filter by days
            cutoff_date = datetime.now() - timedelta(days=days)
            df_filtered = df_all[df_all['date'] >= cutoff_date]
            
            if not df_filtered.empty:
                fig_comp = create_comparison_chart(df_filtered)
                st.plotly_chart(fig_comp, use_container_width=True)
    
    with tab2:
        st.header("Data Tables")
        
        # Tokens table
        st.subheader("🪙 Tokens")
        if tokens:
            tokens_df = pd.DataFrame(tokens, columns=['Contract ID', 'Symbol', 'Name', 'Chain'])
            st.dataframe(tokens_df, use_container_width=True)
        
        # Recent prices
        st.subheader("💰 Recent Prices")
        conn = get_connection()
        recent_prices = conn.execute("""
            SELECT 
                t.symbol,
                ph.timestamp,
                ph.price,
                ph.confidence,
                ph.source
            FROM price_history ph
            JOIN tokens t ON ph.contract_id = t.contract_id
            ORDER BY ph.timestamp DESC
            LIMIT 50
        """).fetchall()
        
        if recent_prices:
            prices_df = pd.DataFrame(recent_prices, 
                                   columns=['Symbol', 'Timestamp', 'Price', 'Confidence', 'Source'])
            prices_df['Date'] = pd.to_datetime(prices_df['Timestamp'], unit='s')
            prices_df = prices_df[['Symbol', 'Date', 'Price', 'Confidence', 'Source']]
            st.dataframe(prices_df, use_container_width=True)
    
    with tab3:
        st.header("🔍 Custom SQL Queries")
        
        # Predefined useful queries
        st.subheader("📝 Quick Queries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Database Summary"):
                query = """
                    SELECT 
                        'Tokens' as Entity,
                        COUNT(*) as Count
                    FROM tokens
                    UNION ALL
                    SELECT 
                        'Price Records' as Entity,
                        COUNT(*) as Count
                    FROM price_history
                """
                st.code(query)
                result = get_connection().execute(query).fetchall()
                st.dataframe(pd.DataFrame(result, columns=['Entity', 'Count']))
        
        with col2:
            if st.button("📈 Price Ranges"):
                query = """
                    SELECT 
                        t.symbol,
                        MIN(ph.price) as Min_Price,
                        MAX(ph.price) as Max_Price,
                        AVG(ph.price) as Avg_Price
                    FROM tokens t
                    JOIN price_history ph ON t.contract_id = ph.contract_id
                    GROUP BY t.symbol
                    ORDER BY t.symbol
                """
                st.code(query)
                result = get_connection().execute(query).fetchall()
                if result:
                    df = pd.DataFrame(result, columns=['Symbol', 'Min Price', 'Max Price', 'Avg Price'])
                    df['Min Price'] = df['Min Price'].apply(lambda x: f"${x:.4f}")
                    df['Max Price'] = df['Max Price'].apply(lambda x: f"${x:.4f}")
                    df['Avg Price'] = df['Avg Price'].apply(lambda x: f"${x:.4f}")
                    st.dataframe(df, use_container_width=True)
        
        # Custom query box
        st.subheader("✍️ Custom Query")
        
        default_query = """SELECT 
    t.symbol,
    COUNT(ph.price) as records,
    MIN(ph.timestamp) as first_timestamp,
    MAX(ph.timestamp) as last_timestamp
FROM tokens t
LEFT JOIN price_history ph ON t.contract_id = ph.contract_id
GROUP BY t.symbol
ORDER BY t.symbol"""
        
        query = st.text_area("Enter SQL Query:", value=default_query, height=150)
        
        if st.button("🚀 Run Query"):
            try:
                result = get_connection().execute(query).fetchall()
                if result:
                    # Try to get column names
                    desc = get_connection().execute(query).description
                    columns = [col[0] for col in desc] if desc else [f"Col_{i}" for i in range(len(result[0]))]
                    
                    df = pd.DataFrame(result, columns=columns)
                    
                    # Format timestamp columns
                    for col in df.columns:
                        if 'timestamp' in col.lower() and df[col].dtype in ['int64', 'float64']:
                            df[f"{col}_formatted"] = pd.to_datetime(df[col], unit='s').dt.strftime('%Y-%m-%d %H:%M')
                    
                    st.dataframe(df, use_container_width=True)
                    
                    # Option to download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Query executed successfully but returned no results.")
                    
            except Exception as e:
                st.error(f"Query Error: {e}")
    
    with tab4:
        st.header("📋 Database Information")
        
        # Table overview
        st.subheader("📊 Tables Overview")
        conn = get_connection()
        
        tables = conn.execute("SHOW TABLES").fetchall()
        
        table_info = []
        for table in tables:
            table_name = table[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            # Get sample of data types
            try:
                desc = conn.execute(f"DESCRIBE {table_name}").fetchall()
                columns = len(desc)
            except:
                columns = "N/A"
            
            table_info.append([table_name, count, columns])
        
        table_df = pd.DataFrame(table_info, columns=['Table Name', 'Row Count', 'Columns'])
        st.dataframe(table_df, use_container_width=True)
        
        # Schema information
        st.subheader("🔧 Schema Details")
        
        selected_table = st.selectbox("Select table to view schema:", [t[0] for t in tables])
        
        if selected_table:
            try:
                schema = conn.execute(f"DESCRIBE {selected_table}").fetchall()
                schema_df = pd.DataFrame(schema, columns=['Column', 'Type', 'Null', 'Key', 'Default', 'Extra'])
                st.dataframe(schema_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading schema: {e}")
        
        # Contract ID examples
        st.subheader("🔗 Contract ID Examples")
        st.markdown("""
        **Format**: `{chain}:{contract_address}`
        
        **Examples**:
        - USDC: `ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`
        - WETH: `ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2`
        - Uniswap V3 Pool: `ethereum:0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8`
        
        This format enables seamless integration with:
        - DeFillama API
        - The Graph Protocol  
        - Etherscan/Block explorers
        - Direct RPC calls
        - Any blockchain data source
        """)


def main():
    """Main dashboard function"""
    
    # Check if database exists
    try:
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
    except Exception as e:
        st.error("❌ Database not found!")
        st.markdown("""
        Please run the following commands first:
        ```bash
        python3 init_database.py
        python3 collect_history_fixed.py
        ```
        """)
        return
    
    # Sidebar info
    st.sidebar.markdown("### 📈 Dataset Info")
    
    try:
        # Quick stats for sidebar
        conn = get_connection()
        stats = {
            "Price Records": conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0],
            "Tokens": conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0],
            "LP Pools": conn.execute("SELECT COUNT(*) FROM lp_pools").fetchone()[0],
        }
        
        for key, value in stats.items():
            st.sidebar.metric(key, f"{value:,}")
        
        # Last update
        last_update = conn.execute("SELECT MAX(timestamp) FROM price_history").fetchone()[0]
        if last_update:
            last_date = datetime.fromtimestamp(last_update).strftime('%Y-%m-%d')
            st.sidebar.metric("Last Update", last_date)
    
    except Exception as e:
        st.sidebar.error(f"Error loading stats: {e}")
    
    # Instructions
    st.sidebar.markdown("### 🛠️ Quick Commands")
    st.sidebar.markdown("""
    **View Data in Terminal:**
    ```bash
    python3 query_data.py
    ```
    
    **Add More Tokens:**
    Edit `collect_history_fixed.py`
    
    **Custom Queries:**
    Use the SQL Query tab above
    """)


if __name__ == "__main__":
    main()