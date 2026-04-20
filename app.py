import streamlit as st
import pandas as pd
import numpy as np
import re

# Page Config
st.set_page_config(page_title="Engineering Workbench", layout="wide")

st.title("BayCath Medical Catheter Calculator")
#st.markdown("---")

st.image("model_cath_annot.jpg", caption="This is a model catheter")


import streamlit as st

st.header("Header")
st.write("Calculates required dimensions for your design")

# User Inputs
col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.write("Inner Diameter (ID):")
        id_val = st.number_input("Enter value", min_value=0.0, key="id_val")
        id_unit = st.radio("Select units:", ["millimeters (mm)", "inches (in)"], horizontal=True, key="id_unit")
with col2:
    with st.container(border=True):
        st.write("Outer Diameter (OD):")
        od_val = st.number_input("Enter value", min_value=0.0, key="od_val")
        od_unit = st.radio("Select units:", ["millimeters (mm)", "inches (in)"], horizontal=True, key="od_unit")
with col3:
    with st.container(border=True):
        st.write("Overall Length (OAL):")
        oal_val = st.number_input("Enter value", min_value=0.0, key="oal_val")
        oal_unit = st.radio("Select units:", ["centimeters (cm)", "inches (in)"], horizontal=True, key="oal_unit")

st.subheader("Braid Wire")
col1, col2, col3 = st.columns(3)
with col1:
	with st.container(border=True):
		braid_wire = st.radio("Select option:", ["N/A", "Flat wire", "Round wire"], horizontal=True, key="braid_type")

st.subheader("Coil Wire")
col1, col2, col3 = st.columns(3)
with col1:
	with st.container(border=True):
		coil_wire = st.radio("Select option:", ["N/A", "Coil under braid", "Flat wire", "Round wire"], horizontal=True, key="coil_type")

# Calculations
# Wall thickness: inches as default
od_in = od_val if od_unit=="inches (in)" else od_val * 0.3937007 # convert to in if in cm
id_in = id_val if id_unit=="inches (in)" else id_val * 0.3937007 # convert to in if in cm
if od_in < id_in:
	raise ValueError("The outer diameter must be larger than the inner diameter.")
wall_thickness = (od_in - id_in) / 2.0

# French size of catheter
cath_french_size = 30.0 * (od_val if od_unit=="centimeters (cm)" else od_val * 2.54)

# Mandrel OD (inches)
mandrel_od = (id_val if id_unit=="inches (in)" else id_val * 0.3937007) + 0.001
mandrel_suggest = (coil_wire != "N/A") and (id_in < 0.08)


df_spec = pd.DataFrame({
    "Inner Diameter (ID)": [f"{id_val} {id_unit}"],
	"Outer Diameter (OD)": [f"{od_val} {od_unit}"],
	"Catheter Wall Thickness": [f"{wall_thickness} inches"],
	"Catheter French Size": [f"{cath_french_size} Fr"],
	"Mandrel OD": [f"{mandrel_od} inches"]

})


st.write("### Summary of Specifications")
col1, col2, col3 = st.columns(3)
with col1:
	st.table(df_spec.T)
with st.container(border=True):
	st.write(f"Inner Diameter (ID): {id_val} {id_unit}")
	st.write(f"Outer Diameter (OD): {od_val} {od_unit}")
	st.write(f"Catheter Wall Thickness: {wall_thickness} inches")
	st.write(f"Catheter French Size: {cath_french_size} Fr")
	st.write(f"Mandrel OD: {mandrel_od} inches")
	if mandrel_suggest:
		st.write("SPC or PTFE Beading Suggested.")
    
    