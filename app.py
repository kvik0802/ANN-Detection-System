import streamlit as st
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model

st.set_page_config(page_title="AML Transaction Detector", page_icon="💰", layout="centered")

# ---------------------------------------------------------------
# Background image + styling
# ---------------------------------------------------------------
BACKGROUND_IMAGE_URL = "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?auto=format&fit=crop&w=1950&q=80"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image:
            linear-gradient(rgba(10, 12, 20, 0.80), rgba(10, 12, 20, 0.80)),
            url("{BACKGROUND_IMAGE_URL}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}

    [data-testid="stForm"] {{
        background-color: rgba(20, 22, 32, 0.75);
        padding: 1.5rem 1.5rem 1rem 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    [data-testid="stAlert"] {{
        border-radius: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Load artifacts (cached so they're loaded only once per session)
# ---------------------------------------------------------------
@st.cache_resource
def load_artifacts():
    preprocessor = joblib.load("preprocessor")
    model = load_model("AML.keras")
    return preprocessor, model

preprocessor, model = load_artifacts()

PAYMENT_CURRENCIES = [
    "UK pounds", "Euro", "Turkish lira", "Swiss franc", "Dirham",
    "Pakistani rupee", "Naira", "US dollar", "Yen", "Moroccan dirham",
    "Mexican Peso", "Albanian lek", "Indian rupee",
]

RECEIVED_CURRENCIES = PAYMENT_CURRENCIES  # same currency list in the dataset

BANK_LOCATIONS = [
    "UK", "Turkey", "Switzerland", "Pakistan", "UAE", "Nigeria", "Spain",
    "Germany", "USA", "Italy", "France", "Japan", "Morocco", "Austria",
    "Mexico", "Albania", "India", "Netherlands",
]

PAYMENT_TYPES = [
    "Cash Withdrawal", "ACH", "Cash Deposit", "Cheque",
    "Debit card", "Cross-border", "Credit card",
]

# ---------------------------------------------------------------
# UI
# ---------------------------------------------------------------
st.title("💰 Intelligent AML Detection System")
st.markdown(
    "Enter the transaction details below to check whether it looks "
    "**legitimate** or **suspicious (potential money laundering)**."
)

with st.form("transaction_form"):
    st.subheader("Transaction details")

    amount = st.number_input("Amount", min_value=0.0, value=1000.0, step=100.0)

    col1, col2 = st.columns(2)
    with col1:
        payment_currency = st.selectbox("Payment currency", PAYMENT_CURRENCIES)
        sender_bank_location = st.selectbox("Sender bank location", BANK_LOCATIONS)
    with col2:
        received_currency = st.selectbox("Received currency", RECEIVED_CURRENCIES)
        receiver_bank_location = st.selectbox("Receiver bank location", BANK_LOCATIONS)

    payment_type = st.selectbox("Payment type", PAYMENT_TYPES)

    submitted = st.form_submit_button("Check transaction")

# Fixed decision threshold (standard 0.5 cutoff for a sigmoid output)
THRESHOLD = 0.5

if submitted:
    input_df = pd.DataFrame([{
        "Amount": amount,
        "Payment_currency": payment_currency,
        "Received_currency": received_currency,
        "Sender_bank_location": sender_bank_location,
        "Receiver_bank_location": receiver_bank_location,
        "Payment_type": payment_type,
    }])

    try:
        X_transformed = preprocessor.transform(input_df)
        if hasattr(X_transformed, "toarray"):
            X_transformed = X_transformed.toarray()

        probability = float(model.predict(X_transformed, verbose=0)[0][0])
        is_suspicious = probability >= THRESHOLD

        st.subheader("Result")
        st.metric("Suspicious probability", f"{probability:.2%}")

        if is_suspicious:
            st.error("🚨 This transaction is flagged as **SUSPICIOUS**.")
        else:
            st.success("✅ This transaction looks **LEGITIMATE**.")

        st.progress(min(max(probability, 0.0), 1.0))

        with st.expander("Transaction summary"):
            st.dataframe(input_df, use_container_width=True)

    except Exception as e:
        st.error(f"Something went wrong while scoring the transaction: {e}")

st.divider()