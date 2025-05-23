import streamlit as st
import pyodbc
import pandas as pd

def main():
    st.title("Database Query Tool")
    st.markdown("Connect to SQL Server and execute queries")

    # Database configuration (you can move these to secrets later)
    SERVER = "P3NWPLSK12SQL-v06.shr.prod.phx3.secureserver.net"
    DATABASE = "SKNFSPROD"
    USERNAME = "SKNFSPROD"
    PASSWORD = "Password2011@"

    # Connection function with error handling
    @st.cache_resource(show_spinner="Connecting to database...")
    def get_connection():
        try:
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={SERVER};"
                f"DATABASE={DATABASE};"
                f"UID={USERNAME};"
                f"PWD={PASSWORD};"
            )
            return conn
        except Exception as e:
            st.error(f"🚨 Connection failed: {str(e)}")
            st.stop()
            return None

    # Initialize connection
    conn = get_connection()

    # Query execution function
    def execute_query(query):
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                
                # For SELECT queries
                if cursor.description:  
                    columns = [column[0] for column in cursor.description]
                    data = cursor.fetchall()
                    return pd.DataFrame.from_records(data, columns=columns)
                # For INSERT/UPDATE/DELETE
                else:  
                    conn.commit()
                    return f"Query executed successfully. {cursor.rowcount} rows affected."
                    
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Query failed: {str(e)}")
            return None

    # UI Components
    st.sidebar.header("Query Options")
    sample_queries = {
        "Show Tables": "SELECT TOP 10 * FROM INFORMATION_SCHEMA.TABLES",
        "Count Records": "SELECT COUNT(*) AS total_records FROM {table_name}",
        "Table Structure": "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'"
    }
    
    selected_query = st.sidebar.selectbox("Sample Queries", list(sample_queries.keys()))
    
    # Main query interface
    query = st.text_area(
        "Enter your SQL query:",
        height=150,
        value=sample_queries[selected_query] if selected_query else ""
    )

    # Execute button with custom styling
    execute_btn = st.button(
        "🚀 Execute Query",
        type="primary",
        help="Click to run your SQL query"
    )

    # Results section
    if execute_btn and query:
        st.markdown("---")
        st.subheader("Results")
        
        with st.spinner("Executing query..."):
            result = execute_query(query)
            
            if isinstance(result, pd.DataFrame):
                st.success(f"✅ Returned {len(result)} rows")
                
                # Display as expandable dataframe
                with st.expander("View Data", expanded=True):
                    st.dataframe(result)
                    
                # Download options
                csv = result.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name='query_results.csv',
                    mime='text/csv'
                )
            elif result:
                st.success(result)

    # Connection info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(f"""
    **Connection Info**  
    Server: `{SERVER}`  
    Database: `{DATABASE}`  
    Status: {'✅ Connected' if conn else '❌ Disconnected'}
    """)

if __name__ == "__main__":
    main()
