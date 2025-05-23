import streamlit as st
import pyodbc

def main():
    st.title("Database Connection App")
    st.subheader("SQL Server Connection Demo")

    # Database configuration
    SERVER = "P3NWPLSK12SQL-v06.shr.prod.phx3.secureserver.net"
    DATABASE = "SKNFSPROD"
    USERNAME = "SKNFSPROD"
    PASSWORD = "Password2011@"

    # Connection function
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
            st.error(f"Connection failed: {str(e)}")
            return None

    # Test connection button
    if st.button("Test Database Connection"):
        with st.spinner("Connecting to database..."):
            conn = get_connection()
            if conn:
                st.success("Successfully connected to database!")
                conn.close()
            else:
                st.error("Connection failed")

    # Simple query interface
    st.markdown("---")
    st.subheader("Run a Query")

    query = st.text_area("Enter your SQL query:", "SELECT TOP 5 * FROM INFORMATION_SCHEMA.TABLES")

    if st.button("Execute Query"):
        if not query:
            st.warning("Please enter a query")
        else:
            with st.spinner("Executing query..."):
                conn = get_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(query)
                        
                        # Get column names
                        columns = [column[0] for column in cursor.description]
                        
                        # Get data
                        data = cursor.fetchall()
                        
                        # Display results
                        if data:
                            st.write(f"Found {len(data)} rows")
                            st.table(data)
                        else:
                            st.info("Query executed successfully but returned no results")
                            
                    except Exception as e:
                        st.error(f"Query failed: {str(e)}")
                    finally:
                        conn.close()
                else:
                    st.error("Cannot execute query - no database connection")

if __name__ == "__main__":
    main()
