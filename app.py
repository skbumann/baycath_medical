import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection

# Page Config
st.set_page_config(page_title="BayCath Medical Catheter Calculator", layout="wide")
left_co, cent_co, last_co = st.columns([1, 2, 1])

with cent_co:

	st.title("BayCath Medical Catheter Calculator")

	st.image("model_cath_annot.jpg", caption="This is a model catheter")

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

	var_a = 0.001

	# Wall thickness: inches as default
	od_in = od_val if od_unit=="inches (in)" else od_val * 0.3937007 # convert to in if in cm
	id_in = id_val if id_unit=="inches (in)" else id_val * 0.3937007 # convert to in if in cm
	if od_in < id_in:
		raise ValueError("The outer diameter must be larger than the inner diameter.")
	wall_thickness = (od_in - id_in) / 2.0

	# French size of catheter
	cath_french_size = 30.0 * (od_val if od_unit=="centimeters (cm)" else od_val * 2.54)

	# Mandrel OD (inches)
	mandrel_od = (id_val if id_unit=="inches (in)" else id_val * 0.3937007) + var_a
	mandrel_suggestion = ((coil_wire != "N/A") and (id_in < 0.08)) or (id_in < 0.03)

	# SPC Mandrel (if using based on suggestion)
	spc_mandrel_od = id_in + 0.0005

	# PTFE Beading (if using based on suggestion)
	ptfe_beading = id_in + 0.002

	# Mandrel length (inches)
	oal_in = oal_val if oal_unit=="inches (in)" else oal_val * 0.3937007 # convert to in if in cm
	mandrel_length = oal_in + 6.0

	# PTFE linear ID (inches)
	ptfe_liner_id = mandrel_od + 0.003
	ptfe_liner_wall = 0.001 if id_in < 0.1 else 0.0015 if (id_in > 0.1 and id_in < 0.2) else 0.2
	ptfe_liner_length = mandrel_length + 6.0

	braid_thickness = 0.1 # inches
	coil_thickness = 0.1  # inches

	# Extrusion ID
	extrusion_id = mandrel_od + 2.0 * ptfe_liner_wall + 4.0 * braid_thickness + 2.0 * coil_thickness + 0.006

	# Extrusion wall
	melted_extrusion_id = mandrel_od + 2.0 * ptfe_liner_wall
	melted_extrusion_od = od_in + var_a

	# Cross-sectional area

	total_extrusion_length = oal_in + 2.0

	# FEP parts
	fep_expanded_id = id_in + 2.0 * ptfe_liner_wall + 0.006
	fep_wall = 0.01 if od_in < 0.3 else 0.012
	fep_recovered_max = od_in - 0.04
	fep_ration_min = fep_expanded_id / fep_recovered_max
	fep_ration_min_too_high = fep_ration_min > 2.0
	fep_ration_min_too_high = 4.0

	# Summary

	df_spec = pd.DataFrame({
		"Inner Diameter (ID)": [f"{id_val} {id_unit}"],
		"Outer Diameter (OD)": [f"{od_val} {od_unit}"],
		"Catheter Wall Thickness": [f"{wall_thickness} inches"],
		"Catheter French Size": [f"{cath_french_size} Fr"],
		"Mandrel OD": [f"{mandrel_od} inches"], 
		"Mandrel Length": [f"{mandrel_length} inches"],

	})


	st.write("### Summary of Specifications")

	st.table(df_spec.T)
	with st.container(border=True):
		st.write(f"Inner Diameter (ID): {id_val} {id_unit}")
		st.write(f"Outer Diameter (OD): {od_val} {od_unit}")
		st.write(f"Catheter Wall Thickness: {wall_thickness} inches")
		st.write(f"Catheter French Size: {cath_french_size} Fr")
		st.write(f"Mandrel OD: {mandrel_od} inches")
		if mandrel_suggestion:
			st.write("SPC or PTFE Beading Suggested.")
		if fep_ration_min_too_high:
			st.write("FEP ration min is too high (>2.0 in). Proceed with caution.")
		
		


	# 1. Setup connection
	conn = st.connection("gsheets", type=GSheetsConnection)


	# 2. Create the form
	with st.form("user_form"):
		name = st.text_input("Name")
		size = st.number_input("French Size", value=12)
		submitted = st.form_submit_button("Send to Owner")

		if submitted:
			# Read existing data
			existing_data = conn.read(worksheet="Sheet1", usecols=[0, 1], ttl=0)
			existing_data = existing_data.dropna(how="all")  # Drop empty rows

			# Create new row as a DataFrame
			new_row = pd.DataFrame([{"Name": name, "French Size": size}])

			# Append new row to existing data
			updated_data = pd.concat([existing_data, new_row], ignore_index=True)

			# Write back to the sheet
			conn.update(worksheet="Sheet1", data=updated_data)

			st.success("Data sent!")
