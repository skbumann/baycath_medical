import streamlit as st
import pandas as pd
import numpy as np
import re
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(page_title="Engineering Workbench", layout="wide")

st.title("Michael's Catheter Calculator")
st.markdown("---")

# Sidebar Navigation
page = st.sidebar.radio("Select a Module", ["Linear Regression (Math)", "NLP & Regex Tool"])

# --- MODULE 1: LINEAR REGRESSION ---
if page == "Linear Regression (Math)":
    st.header("📉 Linear Regression & Noise Simulator")
    st.write("Demonstrating Ordinary Least Squares (OLS) and weight estimation.")

    # User Inputs
    col1, col2 = st.columns(2)
    with col1:
        n_points = st.slider("Number of Data Points", 10, 500, 100)
        noise = st.slider("Noise Level", 0.0, 50.0, 10.0)
    with col2:
        true_slope = st.number_input("True Slope", value=2.5)
        true_intercept = st.number_input("True Intercept", value=10.0)

    # Generate Data
    X = np.linspace(0, 100, n_points).reshape(-1, 1)
    y = true_slope * X + true_intercept + np.random.normal(0, noise, (n_points, 1))

    # Fit Model
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # Plotting
    fig, ax = plt.subplots()
    ax.scatter(X, y, alpha=0.5, label="Data")
    ax.plot(X, y_pred, color='red', label=f"OLS Fit (m={model.coef_[0][0]:.2f})")
    ax.legend()
    st.pyplot(fig)

    st.success(f"Estimated Slope: {model.coef_[0][0]:.4f} | Intercept: {model.intercept_[0]:.4f}")

# --- MODULE 2: NLP & REGEX ---
elif page == "NLP & Regex Tool":
    st.header("🔤 NLP Data Cleaning & Pattern Matching")
    st.write("Demonstrating text preprocessing and regex extraction.")

    text_input = st.text_area("Input Text", "Contact us at support@company.com or sales@ai-tech.io. Order #12345.")
    regex_pattern = st.text_input("Regex Pattern (e.g., for emails)", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    if st.button("Extract Patterns"):
        matches = re.findall(regex_pattern, text_input)
        if matches:
            st.write("**Found Matches:**")
            st.json(matches)
        else:
            st.warning("No matches found.")

    st.markdown("---")
    st.subheader("Basic Tokenization")
    tokens = text_input.lower().split()
    st.write(f"**Token Count:** {len(tokens)}")
    st.write(tokens)
