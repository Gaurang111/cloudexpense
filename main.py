import streamlit as st
from Upload_Receipt import main1
from Calculate import main2
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Upload Receipts", "Calculate"])

    if page == "Upload Receipts":
        main1()
    elif page == "Calculate":
        main2()

if __name__ == "__main__":
    main()