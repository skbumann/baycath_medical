import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
import io
from streamlit.components.v1 import html
from src.js_helper import get_three_js_string


# Page Config
st.set_page_config(page_title="BayCath Medical Catheter Calculator", layout="wide")
st.markdown("""
    <style>
        * {
			font-family: Arial, Helvetica, sans-serif;
       }
    </style>
""", unsafe_allow_html=True)


left_co, cent_co, last_co = st.columns([1, 4, 1])

with cent_co:

	st.title("BayCath Medical Catheter Calculator")
	
	st.image("cath_layers.png")

	st.subheader("Input dimensions")
	st.write("Calculates required dimensions for your design")

	# User Inputs
	col1, col2, col3 = st.columns(3)
	with col1:
		with st.container(border=True):
			st.write("Inner Diameter (ID):")
			id_val = st.number_input("Enter value", step=0.0001, format="%.4f", min_value=0.0000, key="id_val")
			id_unit = st.radio("Select units:", ["inches (in)", "millimeters (mm)"], horizontal=True, key="id_unit")
	with col2:
		with st.container(border=True):
			st.write("Outer Diameter (OD):")
			od_val = st.number_input("Enter value", step=0.0001, format="%.4f", min_value=0.0000, key="od_val")
			od_unit = st.radio("Select units:", ["inches (in)", "millimeters (mm)"], horizontal=True, key="od_unit")
	with col3:
		with st.container(border=True):
			st.write("Overall Length (OAL):")
			oal_val = st.number_input("Enter value", step=0.0001, format="%.4f", min_value=0.0000, key="oal_val")
			oal_unit = st.radio("Select units:", ["centimeters (cm)", "inches (in)"], horizontal=True, key="oal_unit")

	# Validate that OD is larger than ID
	od_in = od_val if od_unit=="inches (in)" else od_val * 0.03937007 # convert to in if in mm
	id_in = id_val if id_unit=="inches (in)" else id_val * 0.03937007 # convert to in if in mm
	if od_in < id_in:
		st.warning('The outer diameter must be larger than the inner diameter.', icon="⚠️")

	braid_thickness_val = 0.0
	braid_width_val = 0.0
	coil_thickness_val = 0.0
	braid_ppi_val = 0
	braid_thickness_unit="inches (in)"
	coil_thickness_unit="inches (in)"
	braid_wire = "N/A"
	num_braid_wires = 8

	col1, col2 = st.columns(2)
	with col1:
		st.subheader("Braid Wire")
		with st.container(border=True):
			braid_wire = st.radio("Select option:", ["N/A", "Flat wire", "Round wire"], horizontal=True, key="braid_type")
			if braid_wire != "N/A":
				braid_ppi_val = st.number_input("Programmable Picks per Inch (PPI)", step=1, min_value=0, key="braid_ppi_val")
				braid_thickness_val = st.number_input("Wire Thickness", step=0.0001, format="%.4f", min_value=0.0000, key="braid_thickness_val")
				if braid_wire == "Flat wire":
					braid_width_val = st.number_input("Wire Width", step=0.0001, format="%.4f", min_value=0.0000, key="braid_width_val")
				braid_thickness_unit = st.radio("Select units:", ["inches (in)", "millimeters (mm)"], horizontal=True, key="braid_thickness_unit")
				num_braid_wires = st.radio("Select number of wires:", [8, 16, 32], index=1, horizontal=True, key="num_braid_wires")

	with col2:
		st.subheader("Coil Wire")
		with st.container(border=True):
			coil_wire = st.radio("Select option:", ["N/A", "Flat wire", "Round wire"], horizontal=True, key="coil_type")
			if coil_wire != "N/A":
				coil_pitch_val = st.number_input("Pitch", step=1, min_value=0, key="coil_pitch_val")
				coil_thickness_val = st.number_input("Wire Thickness", step=0.0001, format="%.4f", min_value=0.0000, key="coil_thickness_val")
				if coil_wire == "Flat wire":
					coil_width_val = st.number_input("Wire Width", step=0.0001, format="%.4f", min_value=0.0000, key="coil_width_val")
				coil_thickness_unit = st.radio("Select units:", ["inches (in)", "millimeters (mm)"], horizontal=True, key="coil_thickness_unit")
				coil_under_braid = st.checkbox("Coil under braid")


	# Calculations

	var_a = 0.001

	# Wall thickness: inches as default
	wall_thickness = (od_in - id_in) / 2.0

	# French size of catheter
	cath_french_size = 3.0 * (od_val if od_unit=="millimeters (mm)" else od_val * 25.4)

	# Mandrel OD (inches)
	mandrel_od = (id_val if id_unit=="inches (in)" else id_val * 0.03937007) + var_a
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
	st.subheader("Optional Dimension Modifications")
	with st.container(border=True):
		ptfe_liner_wall_overwritten = st.number_input("Overwrite PTFE Liner Wall Thickness Default", step=0.0001, format="%.4f", value=ptfe_liner_wall, key="ptfe_liner_wall_overwritten")
		ptfe_liner_wall_unit = st.radio("Select units:", ["inches (in)", "millimeters (mm)"], horizontal=True, key="ptfe_liner_wall_unit")
	ptfe_liner_length = mandrel_length + 6.0
	ptfe_liner_wall = ptfe_liner_wall_overwritten if ptfe_liner_wall_unit=="inches (in)" else ptfe_liner_wall_overwritten * 0.03937007


	# Extrusion ID
	#braid_thickness_val = braid_thickness_val if (braid_thickness_val > 0.0) else 0.0
	#coil_thickness_val = coil_thickness_val if (coil_thickness_val > 0.0) else 0.0

	braid_thickness_val_in = braid_thickness_val if braid_thickness_unit=="inches (in)" else braid_thickness_val * 0.03937007
	braid_width_val_in = braid_width_val if braid_thickness_unit=="inches (in)" else braid_width_val * 0.03937007
	coil_thickness_val_in = coil_thickness_val if coil_thickness_unit=="inches (in)" else coil_thickness_val * 0.03937007
	extrusion_id = mandrel_od + 2.0 * ptfe_liner_wall + 4.0 * braid_thickness_val_in + 2.0 * coil_thickness_val_in + 0.006

	# Extrusion wall
	melted_extrusion_id = mandrel_od + 2.0 * ptfe_liner_wall
	melted_extrusion_od = od_in + var_a

	# Braid angle calculation
	D = mandrel_od + braid_thickness_val_in
	PPI = braid_ppi_val
	C = num_braid_wires
	braid_angle = np.arctan(np.pi * D * PPI / C) # double check units are correct here
	w = braid_width_val_in if braid_wire=="Flat wire" else braid_thickness_val_in
	
	# Braid density
	braid_density = (1.0 - (1.0 - (C * w)/(2.0 * np.pi * D * np.cos(braid_angle)))**2.0) * 100.0

	# Cross-sectional area
	# Do the calcs I talked about with Michael here
	extrusion_wall = 0.1


	total_extrusion_length = oal_in + 2.0

	# FEP parts
	fep_expanded_id = id_in + 2.0 * ptfe_liner_wall + 0.006
	fep_wall = 0.01 if od_in < 0.3 else 0.012
	#fep_expanded_id = 0.1
	#od_in = 0.08
	fep_recovered_max = od_in - 0.04
	fep_ration_min = fep_expanded_id / fep_recovered_max
	fep_ration_min_too_high = fep_ration_min >= 2.0
	final_increment = 0

	if fep_ration_min_too_high:
		st.warning('The FEP Ration Min is too high (>2.0). Adjusting the FEP Recovered Max...', icon="❌")
		increments = np.arange(0.039, 0.019, -0.001)

		for i in increments:
			#st.write(i)
			fep_recovered_max = od_in - i
			fep_ration_min = fep_expanded_id / fep_recovered_max
			fep_ration_min_too_high = fep_ration_min >= 2.0
			if not fep_ration_min_too_high:
				final_increment = i
				#st.write(fep_recovered_max)
				#st.write(fep_ration_min)
				st.success(f"Fixed FEP Ration Min ✅ Final Increment Subtracted from Catheter OD: {final_increment:.3f} inches")
				break
			#else:
			#	st.warning('The FEP Ration Min is too high (>2.0). Adjusting the FEP Recovered Max...', icon="❌")
			if i==increments[-1]:
				st.warning('Maximum adjustment made (-0.02 inches from the catheter OD). Proceed with caution...', icon="⚠️")

	# Summary

	options = ["Hubs", "Marker bands", "Extrusion Color", "Number of steering directions", "Number of extrusions", "Something else? (Please provide notes)"]
	category = [0, 0, 1, 0, 0, 1]
	selections = {}

	st.write("### Optional Materials")
	with st.container(border=True):
	# Split into 3 columns
		cols = st.columns(2)
	
		for i, option in enumerate(options):
			# This puts the checkbox in col 0, 1, or 2 based on the index
			with cols[i % 2]:
				if category[i] == 0:
					selections[option] = st.number_input(option, step=1, min_value=0, key=option)
				else:
					selections[option] = st.text_input(option)

		# Get the list of selected items
		final_list = [k for k, v in selections.items() if v]

	df_spec = pd.DataFrame([
		{" ": "Inner Diameter (ID)", "": f"{id_in:.3f} in", "Note": None},
		{" ": "Outer Diameter (OD)", "": f"{od_in:.3f} in", "Note": None},
		{" ": "Catheter Wall Thickness", "": f"{wall_thickness:.3f} in", "Note": None},
		{" ": "Catheter French Size", "": f"{cath_french_size} Fr", "Note": None},
		{" ": "Mandrel OD", "": f"{mandrel_od:.3f} in", "Note": "SPC or PTFE Beading Suggested." if mandrel_suggestion else None},
		{" ": "SPC Mandrel OD", "": f"{spc_mandrel_od:.3f} in", "Note": None},
		{" ": "PTFE Beading OD", "": f"{ptfe_beading:.3f} in", "Note": None},
		{" ": "Mandrel Length", "": f"{(2.54*mandrel_length):.3f} cm", "Note": None},
		{" ": "PTFE Liner ID", "": f"{ptfe_liner_id:.3f} in", "Note": None},
		{" ": "PTFE Liner Wall", "": f"{ptfe_liner_wall:.3f} in", "Note": None},
		{" ": "PTFE Liner Length", "": f"{(2.54*ptfe_liner_length):.3f} cm", "Note": None},
		{" ": "Braid Angle", "": f"{np.degrees(braid_angle):.3f} degrees", "Note": None},
		{" ": "Braid Density", "": f"{braid_density:.2f}%", "Note": None},
		{" ": "Extrusion ID", "": f"{extrusion_id:.3f} in", "Note": None},
		{" ": "Extrusion Wall Thickness", "": f"{extrusion_wall:.3f} in", "Note": None},
		{" ": "Melted Extrusion ID", "": f"{melted_extrusion_id:.3f} in", "Note": None},
		{" ": "Melted Extrusion OD", "": f"{melted_extrusion_od:.3f} in", "Note": None},
		{" ": "Total Extrusion Length", "": f"{(2.54*total_extrusion_length):.3f} cm", "Note": None},
		{" ": "FEP Expanded ID", "": f"{fep_expanded_id:.3f} in", "Note": None},
		{" ": "FEP Wall Thickness", "": f"{fep_wall:.3f} in", "Note": None},
		{" ": "FEP Recovered Max", "": f"{fep_recovered_max:.3f} in", "Note": None},
		{" ": "FEP Ration Minimum", "": f"{fep_ration_min:.3f}", "Note": None},
		{" ": "Hubs", "": f"{selections['Hubs']}", "Note": None},
		{" ": "Marker bands", "": f"{selections['Marker bands']}", "Note": None},
		{" ": "Extrusion Color", "": f"{selections['Extrusion Color']}", "Note": None},
		{" ": "Number of steering directions", "": f"{selections['Number of steering directions']}", "Note": None},
		{" ": "Number of extrusions", "": f"{selections['Number of extrusions']}", "Note": None},
		{" ": "Something else? (Please provide notes)", "": f"{selections['Something else? (Please provide notes)']}", "Note": None}
	])


	st.subheader("Interactive 3D Catheter Model")
	# 1. User Inputs

	scale_factor = 10.0 # Scale up dimensions for better visualization in Three.js

	layers_config = [
        {"name": "Mandrel", "radius": (mandrel_od/2.0)*scale_factor, "color": 0xbdc3c7, "type": "solid"},
        {"name": "PTFE Liner", "radius": (mandrel_od/2.0 + ptfe_liner_wall)*scale_factor, "color": 0x76d7c4, "type": "solid"},
        {"name": "Braid Wire", "radius": (mandrel_od/2.0 + ptfe_liner_wall + braid_thickness_val_in)*scale_factor, "color": 0xedbb99, "type": "braid"}, # Will have X's
        {"name": "Coil Wire", "radius": (mandrel_od/2.0 + ptfe_liner_wall + braid_thickness_val_in + coil_thickness_val_in)*scale_factor, "color": 0xbb8fce, "type": "coil"},  # Will have O's
        {"name": "Extrusion", "radius": (mandrel_od/2.0 + ptfe_liner_wall + braid_thickness_val_in + coil_thickness_val_in + extrusion_wall)*scale_factor, "color": 0x2e86c1, "type": "solid"},
        {"name": "FEP", "radius": (mandrel_od/2.0 + ptfe_liner_wall + braid_thickness_val_in + coil_thickness_val_in + extrusion_wall + fep_wall)*scale_factor, "color": 0xebedef, "type": "solid"}
    ]

	# 3. Three.js Code
	three_js_code = get_three_js_string(layers_config)

	# 4. Render the component
	st.iframe(three_js_code, height=350)


	st.write("### Summary of Specifications")
	st.table(df_spec)
		
	def convert_df_to_excel(df):
		output = io.BytesIO()
		# Use xlsxwriter as the engine
		with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
			df.to_excel(writer, index=False, sheet_name='Catheter Specs')
			
			# Optional: Add some basic formatting
			workbook = writer.book
			worksheet = writer.sheets['Catheter Specs']
			
			# Format: Header bold with a light blue background
			header_format = workbook.add_format({
				'bold': True,
				'text_wrap': True,
				'valign': 'top',
				'fg_color': '#D7E4BC',
				'border': 1
			})

			# Insert the image into the worksheet
			# 'E2' is the cell where the top-left corner of the image will be
			worksheet.insert_image('E10', './figs/BayCath_Tree_White.png', {
				'x_scale': 0.5, # Optional: scale width to 50%
				'y_scale': 0.5, # Optional: scale height to 50%
				'object_position': 1 # 1 = Move and size with cells
        	})

			# Write the column headers with the defined format
			for col_num, value in enumerate(df.columns.values):
				worksheet.write(0, col_num, value, header_format)
				# Adjust column width for readability
				worksheet.set_column(col_num, col_num, 18)
				
		return output.getvalue()
	
	def upload_to_drive(file_metadata, media):
		# 1. Reuse the exact same info from your [connections.gsheets] secrets
		creds_info = st.secrets["connections"]["gsheets"]
		
		# 2. Define the scope to include Drive
		SCOPES = ['https://www.googleapis.com/auth/drive']
		
		# 3. Build the Drive Service
		creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
		drive_service = build('drive', 'v3', credentials=creds)
		
		uploaded_file = drive_service.files().create(
			body=file_metadata,
			media_body=media,
			fields='id',
			supportsAllDrives=True
		).execute()

		return uploaded_file.get('id')

	def upload_xlsx_to_drive(df, folder_id, filename):

		# 1. Create Excel file in a BytesIO buffer
		excel_buffer = io.BytesIO()
		with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
			df.to_excel(writer, index=False, sheet_name='Calculations')
			# The 'with' block handles the save/close automatically

		# 2. Reset buffer position to the start
		excel_buffer.seek(0)
		
		# 3. Prepare metadata for Google Drive
		file_metadata = {
			'name': filename,
			'parents': [folder_id],
			'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
		}
		
		# 4. Create the media upload object
		media = MediaIoBaseUpload(
			excel_buffer, 
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
			resumable=True
		)

		fid = upload_to_drive(file_metadata, media)
		
		return fid


	# Once the data is processed:
	excel_data = convert_df_to_excel(df_spec)

	st.download_button(
		label="📥 Download .xlsx",
		data=excel_data,
		file_name="catheter_specs.xlsx",
		mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	)

	st.header("Get a quote")

	def upload_file_to_drive(file, folder_id):
		# Generate file metadata
		file_metadata = {'name': file.name, 'parents': [folder_id]}
		media = MediaIoBaseUpload(file, mimetype=file.type, resumable=True)

		fid = upload_to_drive(file_metadata, media)
		return fid

	# 1. Setup connection
	FOLDER_ID = st.secrets["connections"]["gsheets"]["drive_folder_id"]
	conn = st.connection("gsheets", type=GSheetsConnection)

	# 2. Create the form
	with st.form("user_form"):
		name = st.text_input("Name: :red[*]")
		email = st.text_input("Email: :red[*]")
		company_name = st.text_input("Company Name: :red[*]")
		phone_number = st.text_input("Phone Number:")
		notes = st.text_input("Notes (Please provide additional details or drawings for steerable catherters, multilumen catheters, and balloon catheters):")
		uploaded_files = st.file_uploader("Upload documents (optional):", accept_multiple_files=True)
		submitted = st.form_submit_button("Submit")

		if submitted:
			if not name or not email or not company_name:
				st.warning("Please fill in all required fields (Name, Email, Company Name).")
				st.stop()
			with st.spinner("Processing..."):
				timestamp = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M")
				filename = f"catheter_specs_{name}_{timestamp}.xlsx"

				file_id = upload_xlsx_to_drive(df_spec, FOLDER_ID, filename)

				file_ids = [] # To store IDs of all uploaded files
				
				# 1. Loop through the list of files
				if uploaded_files: # Checks if the list is not empty
					for uploaded_file in uploaded_files:
						try:
							fid = upload_file_to_drive(uploaded_file, FOLDER_ID)
							file_ids.append(fid)
						except Exception as e:
							st.error(f"Failed to upload {uploaded_file.name}: {e}")

				# Convert list of IDs to a string for the Google Sheet cell
				ids_string = ", ".join(file_ids) if file_ids else "No files uploaded"

				# 2. Your Sheets logic
				existing_data = conn.read(worksheet="Contact Info", ttl=0)
				existing_data = existing_data.dropna(how="all")

				new_row = pd.DataFrame([{
					"Name": name, 
					"Email": email, 
					"Company Name": company_name,
					"Phone Number": phone_number, 
					"Notes": notes, 
					"Drive File ID": ids_string  # Uses the real ID or the default string
				}])

				updated_data = pd.concat([existing_data, new_row], ignore_index=True)
				conn.update(worksheet="Contact Info", data=updated_data)
				
				st.success("Form submitted successfully! Michael will reach out to you ASAP.")


