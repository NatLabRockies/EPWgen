import sys
import os
import tempfile
import folium
import pandas as pd

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# IMPORTANT: set Qt attribute before creating QApplication or importing QtWebEngineWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QLineEdit,
    QDialog, QDialogButtonBox, QFileDialog, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QPixmap

from epwgen.methods import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EPWgen")

        # Create layout
        layout = QVBoxLayout()

        # Load and display the logo
        self.logo_label = QLabel()
        # Load and resize the logo
        logo_path = os.path.join(SCRIPT_DIR, "resources", "Logo.png")
        pixmap = QPixmap(logo_path)  
        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio)  # Adjust size as needed
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)  # Center align the logo
        layout.addWidget(self.logo_label)  # Add logo to layout

        # Create buttons
        self.button_individual = QPushButton("Retrieve weather data for an individual location")
        self.button_multi_year = QPushButton("Retrieve data for a single location over multiple years")
        self.button_csv = QPushButton("Retrieve data from CSV file list")
        self.button_metered = QPushButton("Download metered variables (NOAA data only)")

        # Connect buttons to their respective actions
        self.button_individual.clicked.connect(self.open_individual_dialog)
        self.button_multi_year.clicked.connect(self.open_multi_year_dialog)
        self.button_csv.clicked.connect(self.run_csv_list)
        self.button_metered.clicked.connect(self.open_metered_dialog)

        # Add buttons to layout
        layout.addWidget(self.button_individual)
        layout.addWidget(self.button_multi_year)
        layout.addWidget(self.button_csv)
        layout.addWidget(self.button_metered)

        # Add an 'About' link at the bottom (clickable label)
        about_label = QLabel('<a href="#">About</a>')
        about_label.setOpenExternalLinks(False)
        about_label.setAlignment(Qt.AlignCenter)
        about_label.linkActivated.connect(self.open_about_dialog)
        layout.addWidget(about_label)

        self.setLayout(layout)

    def open_individual_dialog(self):
        # Create dialog for input
        dialog = IndividualLocationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            lat, lon, save_name, year, save_folder, file_type = dialog.get_values()

            # Create outputs folder in the script directory
            outputs_folder = os.path.join(SCRIPT_DIR, "outputs")
            os.makedirs(outputs_folder, exist_ok=True)
            
            # Update save_folder to be inside outputs
            if save_folder == '.':
                save_folder = outputs_folder
            else:
                save_folder = os.path.join(outputs_folder, save_folder)
            os.makedirs(save_folder, exist_ok=True)

            # 1. Call your function to retrieve weather data
            (
                retrieve_status,
                wmo,
                hdd,
                cdd,
                latitude_station,
                longitude_station,
                retrieve_info_closest_other_locations,
                flags
            ) = run_individual_location(lat, lon, year, file_type, save_folder, save_name)

            # Run Quality Check and EnergyPlus simulation
            filename = f"{save_name.replace(' ', '_').replace('.', '_')}_{year}.epw"

            # If user picked "." as save folder (same folder), just use filename
            if save_folder == '.':
                epw_path = filename
            else:
                epw_path = os.path.join(save_folder, filename)

            # Check if file really exists
            if not os.path.isfile(epw_path):
                raise FileNotFoundError(f"❌ EPW file not found: {epw_path}")

            quality_checks = check_epw_quality(epw_path)


            quality_checks = check_epw_quality(epw_path)
            # status_EP = run_energyplus_simulations(epw_path)
            # print(status_EP)

            # 2. Suppose retrieve_distance_station_location returns [distance_mi, lat_station, lon_station].
            [distance_mi, lat_station, lon_station] = retrieve_distance_station_location(wmo, lat, lon)

            # 3. Show a single dialog with text info + map including quality_checks and EnergyPlus status
            self.show_result_and_map(
                retrieve_status, distance_mi, wmo, hdd, cdd,
                lat, lon, lat_station, lon_station, quality_checks, flags
                # status_EP
            )

    def open_multi_year_dialog(self):
        # Create dialog for multi-year input
        dialog = MultiYearLocationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            lat, lon, save_name, start_year, end_year, save_folder, file_type = dialog.get_values()

            # Create outputs folder in the script directory
            outputs_folder = os.path.join(SCRIPT_DIR, "outputs")
            os.makedirs(outputs_folder, exist_ok=True)
            
            # Update save_folder to be inside outputs
            if save_folder == '.':
                save_folder = outputs_folder
            else:
                save_folder = os.path.join(outputs_folder, save_folder)
            os.makedirs(save_folder, exist_ok=True)

            # Loop through each year in the range
            for year in range(start_year, end_year + 1):
                print(f"Processing year {year}...")
                
                # Call your function to retrieve weather data
                (
                    retrieve_status,
                    wmo,
                    hdd,
                    cdd,
                    latitude_station,
                    longitude_station,
                    retrieve_info_closest_other_locations,
                    flags
                ) = run_individual_location(lat, lon, year, file_type, save_folder, save_name)

                # Run Quality Check for each year
                filename = f"{save_name.replace(' ', '_').replace('.', '_')}_{year}.epw"

                # If user picked "." as save folder (same folder), just use filename
                if save_folder == '.':
                    epw_path = filename
                else:
                    epw_path = os.path.join(save_folder, filename)

                # Check if file really exists
                if not os.path.isfile(epw_path):
                    print(f"❌ EPW file not found for year {year}: {epw_path}")
                    continue

                quality_checks = check_epw_quality(epw_path)
                
                # Report NOAA data gaps
                if flags:
                    var_names = {6: 'Temp', 7: 'Dewpt', 8: 'RH', 9: 'Pres', 
                                20: 'Wdir', 21: 'Wspd', 30: 'Snow', 33: 'Prcp'}
                    gap_report = []
                    for col_num, name in var_names.items():
                        if col_num in flags:
                            info = flags[col_num]
                            total = info.get('original_holes', 0)
                            if total > 0:
                                interp = info.get('interpolated', 0)
                                merra2 = info.get('filled_merra2', 0)
                                gap_report.append(f"{name}:{total}(i:{interp},m:{merra2})")
                    
                    if gap_report:
                        print(f"  NOAA gaps: {', '.join(gap_report)}")
                
                print(f"✓ Completed year {year}: {retrieve_status}")

            print(f"All years from {start_year} to {end_year} have been processed.")
            # Show summary dialog with branding
            branding = (
                "EPWgen\n"
                "EPWgen was created by Carlo Bianchi.\n"
                "Developed at NREL; tool registered under software record SWR-26-017.\n"
                "Do not distribute. Confidential.\n"
            )
            QMessageBox.information(
                self,
                "Multi-Year Complete",
                f"All years from {start_year} to {end_year} have been processed.\n\n{branding}"
            )

    def open_metered_dialog(self):
        # Create dialog for metered variables input
        dialog = MeteredVariablesDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            lat, lon, location_name, start_year, end_year = dialog.get_values()

            # Create outputs folder in the script directory
            outputs_folder = os.path.join(SCRIPT_DIR, "outputs")
            os.makedirs(outputs_folder, exist_ok=True)

            # List to store all dataframes for combining
            all_data = []
            station_info = {}

            # Loop through each year in the range (or single year if start==end)
            for year in range(start_year, end_year + 1):
                print(f"Downloading metered variables for {location_name}, year {year}...")
                
                # Call get_data_noaa to retrieve NOAA data
                (data, timezone, elevation, wmo, station_name, state, country, 
                 latitude_station, longitude_station, epw_exists, incomplete_timeseries) = get_data_noaa(lat, lon, year, outputs_folder)
                
                if epw_exists:
                    print(f"⚠️ EPW already exists for year {year}, skipping...")
                    continue
                
                if incomplete_timeseries:
                    print(f"❌ Incomplete timeseries for year {year}, cannot proceed")
                    QMessageBox.warning(
                        self,
                        "Incomplete Data",
                        f"Could not find complete NOAA data for {location_name} in {year}.\n"
                        f"Data has too many gaps or is insufficient."
                    )
                    continue
                
                if isinstance(data, pd.DataFrame) and not data.empty:
                    # Store the dataframe for later combining
                    all_data.append(data)
                    
                    # Store station info (from the first successful download)
                    if not station_info:
                        station_info = {
                            'station_name': station_name,
                            'wmo': wmo,
                            'latitude': latitude_station,
                            'longitude': longitude_station,
                            'elevation': elevation,
                            'timezone': timezone
                        }
                    
                    print(f"✓ Retrieved data for year {year}")
                    print(f"  Station: {station_name} (WMO: {wmo})")
                    print(f"  Location: {latitude_station}, {longitude_station}")
                    print(f"  Elevation: {elevation}m, Timezone: {timezone}")
                else:
                    print(f"❌ No data retrieved for year {year}")
            
            # Combine all dataframes and save as a single CSV
            if all_data:
                # Concatenate all dataframes
                combined_data = pd.concat(all_data, axis=0)
                
                # Sort by datetime index
                combined_data = combined_data.sort_index()
                
                # Create filename based on year range
                if start_year == end_year:
                    csv_filename = f"{location_name.replace(' ', '_').replace('.', '_')}_{start_year}_metered.csv"
                else:
                    csv_filename = f"{location_name.replace(' ', '_').replace('.', '_')}_{start_year}-{end_year}_metered.csv"
                
                csv_path = os.path.join(outputs_folder, csv_filename)
                
                # Save combined data to CSV with datetime index
                combined_data.to_csv(csv_path, index=True)
                
                print(f"\n✓ Combined data saved to: {csv_path}")
                print(f"  Total records: {len(combined_data)}")
                print(f"  Date range: {combined_data.index.min()} to {combined_data.index.max()}")
                
                # Show completion message
                if start_year == end_year:
                    message = f"Metered variables downloaded for {location_name} ({start_year})"
                else:
                    message = f"Metered variables downloaded for {location_name}\nYears: {start_year} to {end_year}\n\nAll years combined into single file"
                
                # Prepend branding header to CSV file
                branding_header = (
                    "# EPWgen\n"
                    "# EPWgen was created by Carlo Bianchi.\n"
                    "# Developed at NREL; tool registered under software record SWR-26-017.\n"
                    "# Do not distribute. Confidential.\n"
                )
                try:
                    # Read the CSV as text, then write branding + original
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        original = f.read()
                    with open(csv_path, 'w', encoding='utf-8') as f:
                        f.write(branding_header + original)
                except Exception:
                    # If writing header fails, continue but log
                    print("Warning: could not write branding header to CSV")

                QMessageBox.information(
                    self,
                    "Download Complete",
                    f"{message}\n\nFile saved to:\n{csv_path}\n\n"
                    f"Total records: {len(combined_data)}\n"
                    f"Station: {station_info.get('station_name', 'N/A')} (WMO: {station_info.get('wmo', 'N/A')})\n\n"
                    f"EPWgen\nEPWgen was created by Carlo Bianchi.\nDeveloped at NREL; tool registered under software record SWR-26-017.\nDo not distribute. Confidential."
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Data",
                    f"No data could be retrieved for {location_name}\n"
                    f"Years: {start_year} to {end_year}"
                )

    def open_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    # def show_result_and_map(self, status, distance_mi, wmo, hdd, cdd, lat, lon, lat_station, lon_station, quality_checks, status_EP):
    def show_result_and_map(self, status, distance_mi, wmo, hdd, cdd, lat, lon, lat_station, lon_station, quality_checks, flags):
        """
        Create a dialog that displays textual info at the top (split into two columns)
        and a map at the bottom.
        Left column: general info (distance, WMO, HDD, CDD, EnergyPlus status).
        Right column: organized quality checks.
        The map shows two pins: requested location and the weather station.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Weather Data & Map")

        # Main layout for the dialog
        main_layout = QVBoxLayout(dialog)

        # Create a horizontal layout for the top info
        info_layout = QHBoxLayout()

        # Left column: General information including EnergyPlus status, with bold formatting for the label.
        # Add NOAA data gaps info
        gaps_info = "<b>NOAA Data Gaps:</b><br>"
        if flags:
            # Map column numbers to readable names
            var_names = {6: 'Temperature', 7: 'Dew Point', 8: 'Rel. Humidity', 
                        9: 'Pressure', 20: 'Wind Dir', 21: 'Wind Speed', 
                        30: 'Snow', 33: 'Precipitation'}
            
            has_gaps = False
            for col_num, name in var_names.items():
                if col_num in flags:
                    info = flags[col_num]
                    total = info.get('original_holes', 0)
                    if total > 0:
                        has_gaps = True
                        interp = info.get('interpolated', 0)
                        merra2 = info.get('filled_merra2', 0)
                        gaps_info += f"{name}: {total} hrs (Interp: {interp}, MERRA2: {merra2})<br>"
            
            if not has_gaps:
                gaps_info += "No gaps - complete NOAA data<br>"
        else:
            gaps_info += "No data<br>"
        
        general_info_text = (
            f"Distance: {distance_mi.round(2)} mi<br>"
            f"WMO: {wmo}<br>"
            f"HDD: {hdd}<br>"
            f"CDD: {cdd}<br><br>"
            f"{gaps_info}"
            # f"<b>EnergyPlus Status:</b><br>{status_EP}"
        )
        general_info_label = QLabel()
        general_info_label.setTextFormat(Qt.RichText)
        general_info_label.setText(general_info_text)
        info_layout.addWidget(general_info_label)

        # Right column: Organized quality checks with bold header.
        quality_checks_str = "<br>".join(f"{key}: {value}" for key, value in quality_checks.items())
        quality_checks_text = f"<b>Quality Checks:</b><br>{quality_checks_str}"
        quality_checks_label = QLabel()
        quality_checks_label.setTextFormat(Qt.RichText)
        quality_checks_label.setText(quality_checks_text)
        info_layout.addWidget(quality_checks_label)

        # Add the horizontal layout to the main layout
        main_layout.addLayout(info_layout)

        # Create a Folium map centered between the two points with a moderate zoom.
        center_lat = (lat + lat_station) / 2
        center_lon = (lon + lon_station) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

        # Add a marker for the requested location
        folium.Marker(
            [lat, lon],
            tooltip="Requested Location",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

        # Add a marker for the weather station
        folium.Marker(
            [lat_station, lon_station],
            tooltip="Weather Station",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

        # Save the map to a temporary HTML file
        tmp_file = os.path.join(tempfile.gettempdir(), "epwgen_map.html")
        m.save(tmp_file)

        # Create a QWebEngineView to display the map
        web_view = QWebEngineView()
        web_view.setUrl(QUrl.fromLocalFile(tmp_file))
        main_layout.addWidget(web_view)

        # Branding block to display at the bottom of the final window
        branding_html = (
            "<hr>"
            "<b>EPWgen</b><br>"
            "EPWgen was created by Carlo Bianchi.<br>"
            "Developed at NREL; tool registered under software record SWR-26-017.<br>"
            "<b>Do not distribute. Confidential.</b><br>"
        )
        branding_label = QLabel()
        branding_label.setTextFormat(Qt.RichText)
        branding_label.setText(branding_html)
        branding_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(branding_label)

        dialog.setLayout(main_layout)
        dialog.resize(800, 600)  # Make the window large enough to see the map
        dialog.exec_()

    def run_csv_list(self):
        # Show CSV format help dialog
        help_dialog = CSVFormatHelpDialog(self)
        if help_dialog.exec_() != QDialog.Accepted:
            return  # User cancelled
        
        # Open file dialog to select CSV file
        csv_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            SCRIPT_DIR,  # Start in the project directory
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not csv_file_path:
            return  # User cancelled file selection
        
        # Extract the CSV file name without path and extension
        csv_base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
        
        # Create outputs folder in the script directory and subfolder for this CSV
        outputs_folder = os.path.join(SCRIPT_DIR, "outputs")
        save_folder = os.path.join(outputs_folder, csv_base_name)
        os.makedirs(save_folder, exist_ok=True)
        
        # Path for the updated CSV file (save in the same folder as the EPWs)
        updated_csv_path = os.path.join(save_folder, os.path.basename(csv_file_path))
        
        file_type = 'AMY'  # Default file type

        # Check if an updated CSV already exists in the output folder
        # If so, load from that to resume progress. Otherwise, load the original CSV.
        if os.path.isfile(updated_csv_path):
            try:
                zipcodes = pd.read_csv(updated_csv_path)
                QMessageBox.information(
                    self,
                    "Resuming Progress",
                    f"Found existing progress file in:\n{save_folder}\n\n"
                    f"Resuming from previous session.\n"
                    f"Already processed locations will be skipped."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read existing progress file:\n{str(e)}")
                return
        else:
            # Load the original CSV file
            try:
                zipcodes = pd.read_csv(csv_file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read CSV file:\n{str(e)}")
                return
        
        # Remove old columns with year suffixes to clean up the CSV
        old_columns_patterns = [
            r'Do we have data for \d+\?',
            r'distance_location_station_miles_\d+',
            r'weather_station_wmo_\d+',
            r'hdd_base65F_\d+',
            r'cdd_base65F_\d+',
            r'Retrieve_Status_\d+',
            r'Distance_Miles_\d+',
            r'Weather_Station_WMO_\d+',
            r'Weather_Station_Latitude_\d+',
            r'Weather_Station_Longitude_\d+',
            r'HDD_base65F_\d+',
            r'CDD_base65F_\d+',
            r'QC_.*_\d+',
            r'Temp_Data_Holes_\d+',
            r'Dewpoint_Data_Holes_\d+',
            r'RH_Data_Holes_\d+',
            r'Temp_Holes_\d+',
            r'Dewpoint_Holes_\d+',
            r'RH_Holes_\d+',
            r'Status_\d+'
        ]
        
        import re
        cols_to_drop = []
        for pattern in old_columns_patterns:
            cols_to_drop.extend([col for col in zipcodes.columns if re.match(pattern, col)])
        
        if cols_to_drop:
            zipcodes = zipcodes.drop(columns=cols_to_drop)
            print(f"Removed {len(cols_to_drop)} old columns with year suffixes")
        
        # Verify required columns exist
        required_columns = ['Latitude', 'Longitude', 'Location Name', 'Year']
        missing_columns = [col for col in required_columns if col not in zipcodes.columns]
        if missing_columns:
            QMessageBox.critical(
                self, 
                "Error", 
                f"CSV file is missing required columns: {', '.join(missing_columns)}\n\n"
                f"Required columns: Latitude, Longitude, Location Name, Year"
            )
            return

        # Initialize shared columns if they don't exist
        if 'Station_WMO' not in zipcodes.columns:
            zipcodes['Station_WMO'] = ''
        if 'Station_Latitude' not in zipcodes.columns:
            zipcodes['Station_Latitude'] = ''
        if 'Station_Longitude' not in zipcodes.columns:
            zipcodes['Station_Longitude'] = ''
        if 'Distance_Miles' not in zipcodes.columns:
            zipcodes['Distance_Miles'] = ''
        if 'Status' not in zipcodes.columns:
            zipcodes['Status'] = ''
        if 'HDD_base65F' not in zipcodes.columns:
            zipcodes['HDD_base65F'] = ''
        if 'CDD_base65F' not in zipcodes.columns:
            zipcodes['CDD_base65F'] = ''

        # Initialize a counter for iterations
        counter = 0

        for index, row in zipcodes.iterrows():
            print(index)
            location_name = str(row['Location Name'])
            lat = row['Latitude']
            lon = row['Longitude']
            year = int(row['Year'])
            save_name = location_name

            # Check if EPW file already exists
            epw_filename = f"{save_name.replace(' ', '_').replace('.', '_')}_{year}.epw"
            epw_path = os.path.join(save_folder, epw_filename)
            
            # Check both: EPW file exists AND Status column is not empty/False
            status_value = row.get('Status', '')
            epw_exists = os.path.isfile(epw_path)
            has_valid_status = status_value and str(status_value).strip() and str(status_value).strip().lower() not in ['false', 'nan', '']
            
            if epw_exists and has_valid_status:
                print(f"Skipping {location_name} ({year}) - Already processed (EPW exists and Status is True)")
                counter += 1
                continue
            elif epw_exists and not has_valid_status:
                print(f"Reprocessing {location_name} ({year}) - EPW exists but Status is False/empty")
            elif not epw_exists and has_valid_status:
                print(f"Processing {location_name} ({year}) - Status is True but EPW file missing")
            else:
                print(f"Processing {location_name} ({year}) - New location")

            # Retrieve data for the current location
            (
                retrieve_status,
                wmo,
                hdd,
                cdd,
                latitude_station,
                longitude_station,
                retrieve_info_closest_other_locations,
                flags
            ) = run_individual_location(lat, lon, year, file_type, save_folder, save_name)
            
            # Get distance and station info if we have station coordinates
            if latitude_station and longitude_station:
                distance_mi, _, _ = retrieve_distance_station_location(wmo, lat, lon)
            else:
                distance_mi = ''
            
            # Run quality checks if EPW file was created
            
            quality_checks = {}
            if os.path.isfile(epw_path):
                quality_checks = check_epw_quality(epw_path)

            # Update the DataFrame with all results
            # Basic info (no year suffix needed - year is in its own column)
            zipcodes.at[index, 'Status'] = retrieve_status
            zipcodes.at[index, 'HDD_base65F'] = hdd
            zipcodes.at[index, 'CDD_base65F'] = cdd
            
            # Station info (shared across years, only set once)
            if pd.isna(zipcodes.at[index, 'Station_WMO']) or zipcodes.at[index, 'Station_WMO'] == '':
                zipcodes.at[index, 'Station_WMO'] = wmo
                zipcodes.at[index, 'Station_Latitude'] = latitude_station
                zipcodes.at[index, 'Station_Longitude'] = longitude_station
                zipcodes.at[index, 'Distance_Miles'] = distance_mi
            
            # Add quality check results (no year suffix)
            for check_name, check_result in quality_checks.items():
                column_name = f"QC_{check_name.replace(' ', '_')}"
                if column_name not in zipcodes.columns:
                    zipcodes[column_name] = ''
                zipcodes.at[index, column_name] = check_result
            
            # Add flags for data holes - now tracking all variables with detail
            gap_columns = {
                6: 'Temp', 7: 'Dewpoint', 8: 'RH', 9: 'Pressure',
                20: 'WindDir', 21: 'WindSpeed', 30: 'Snow', 33: 'Precipitation'
            }
            
            for col_num, var_name in gap_columns.items():
                # Initialize columns if they don't exist
                if f'{var_name}_Total_Holes' not in zipcodes.columns:
                    zipcodes[f'{var_name}_Total_Holes'] = ''
                if f'{var_name}_Interpolated' not in zipcodes.columns:
                    zipcodes[f'{var_name}_Interpolated'] = ''
                if f'{var_name}_MERRA2_Fill' not in zipcodes.columns:
                    zipcodes[f'{var_name}_MERRA2_Fill'] = ''
                
                # Fill values if available in flags
                if col_num in flags and isinstance(flags[col_num], dict):
                    zipcodes.at[index, f'{var_name}_Total_Holes'] = flags[col_num].get('original_holes', 0)
                    zipcodes.at[index, f'{var_name}_Interpolated'] = flags[col_num].get('interpolated', 0)
                    zipcodes.at[index, f'{var_name}_MERRA2_Fill'] = flags[col_num].get('filled_merra2', 0)

            # Save CSV after each successful download to preserve progress
            zipcodes.to_csv(updated_csv_path, index=False)

            counter += 1

        # Final save (in case last iteration was skipped)
        zipcodes.to_csv(updated_csv_path, index=False)
        
        QMessageBox.information(
            self,
            "Complete",
            f"Successfully processed {counter} locations.\n\n"
            f"EPW files saved to: {save_folder}\n"
            f"Updated CSV saved to: {updated_csv_path}\n\n"
            f"Added columns include:\n"
            f"- Retrieve Status, Distance, WMO Station\n"
            f"- Weather Station Lat/Lon\n"
            f"- HDD/CDD values\n"
            f"- Quality Check results\n"
            f"- Data holes flags"
        )


class IndividualLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Input Location Details")
        self.form_layout = QFormLayout()

        # Default values
        self.lat_input = QLineEdit("40")
        self.lon_input = QLineEdit("-76")
        self.save_name_input = QLineEdit("TEST")
        self.year_input = QLineEdit("2022")
        self.save_folder_input = QLineEdit(".")
        self.file_type_input = QLineEdit("AMY")

        # Add widgets to form layout
        self.form_layout.addRow("Latitude:", self.lat_input)
        self.form_layout.addRow("Longitude:", self.lon_input)
        self.form_layout.addRow("Save Name:", self.save_name_input)
        self.form_layout.addRow("Year:", self.year_input)
        self.form_layout.addRow("Save Folder:", self.save_folder_input)
        self.form_layout.addRow("File Type:", self.file_type_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Set layout
        layout = QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_values(self):
        return (
            float(self.lat_input.text()),
            float(self.lon_input.text()),
            self.save_name_input.text(),
            int(self.year_input.text()),
            self.save_folder_input.text(),
            self.file_type_input.text()
        )

class MultiYearLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Input Location Details for Multiple Years")
        self.form_layout = QFormLayout()

        # Default values
        self.lat_input = QLineEdit("40")
        self.lon_input = QLineEdit("-76")
        self.save_name_input = QLineEdit("TEST")
        self.start_year_input = QLineEdit("2020")
        self.end_year_input = QLineEdit("2022")
        self.save_folder_input = QLineEdit(".")
        self.file_type_input = QLineEdit("AMY")

        # Add widgets to form layout
        self.form_layout.addRow("Latitude:", self.lat_input)
        self.form_layout.addRow("Longitude:", self.lon_input)
        self.form_layout.addRow("Save Name:", self.save_name_input)
        self.form_layout.addRow("Start Year:", self.start_year_input)
        self.form_layout.addRow("End Year:", self.end_year_input)
        self.form_layout.addRow("Save Folder:", self.save_folder_input)
        self.form_layout.addRow("File Type:", self.file_type_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Set layout
        layout = QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_values(self):
        return (
            float(self.lat_input.text()),
            float(self.lon_input.text()),
            self.save_name_input.text(),
            int(self.start_year_input.text()),
            int(self.end_year_input.text()),
            self.save_folder_input.text(),
            self.file_type_input.text()
        )

class MeteredVariablesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Download Metered Variables (NOAA Data Only)")
        self.form_layout = QFormLayout()

        # Default values
        self.lat_input = QLineEdit("40.7128")
        self.lon_input = QLineEdit("-74.0060")
        self.location_name_input = QLineEdit("New_York")
        self.start_year_input = QLineEdit("2022")
        self.end_year_input = QLineEdit("2022")

        # Add widgets to form layout
        self.form_layout.addRow("Latitude:", self.lat_input)
        self.form_layout.addRow("Longitude:", self.lon_input)
        self.form_layout.addRow("Location Name:", self.location_name_input)
        self.form_layout.addRow("Start Year:", self.start_year_input)
        self.form_layout.addRow("End Year:", self.end_year_input)

        # Add help text
        help_label = QLabel(
            "<i>Note: If start and end year are the same, data for one year will be downloaded.<br>"
            "Data will be saved as CSV without EPW processing.</i>"
        )
        help_label.setWordWrap(True)
        self.form_layout.addRow("", help_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Set layout
        layout = QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_values(self):
        return (
            float(self.lat_input.text()),
            float(self.lon_input.text()),
            self.location_name_input.text(),
            int(self.start_year_input.text()),
            int(self.end_year_input.text())
        )

class CSVFormatHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("CSV File Format Requirements")
        layout = QVBoxLayout()

        # Create a text edit widget with the format explanation
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>CSV File Format Requirements</h3>
        <p>Your CSV file must contain the following columns:</p>
        <ul>
            <li><b>Latitude</b> - Latitude (decimal degrees)</li>
            <li><b>Longitude</b> - Longitude (decimal degrees)</li>
            <li><b>Location Name</b> - Name for the location (used in filename)</li>
            <li><b>Year</b> - Year for weather data retrieval</li>
        </ul>
        
        <h4>Example CSV Format:</h4>
        <pre>
Latitude,Longitude,Location Name,Year
40.7128,-74.0060,New York,2022
34.0901,-118.4065,Beverly Hills,2022
41.8781,-87.6298,Chicago,2021
        </pre>
        
        <h4>Additional Information:</h4>
        <ul>
            <li>EPW files will be named: <b>LocationName_Year.epw</b></li>
            <li>The CSV file can contain additional columns - they will be preserved</li>
            <li>Results will be added as new columns with year suffix (e.g., weather_station_wmo_2022)</li>
            <li>The updated CSV will be saved back to the original file location</li>
            <li>EPW files will be saved in: <b>outputs/[csv_filename]/</b></li>
        </ul>
        
        <p><i>Note: Processing may take several minutes depending on the number of locations.</i></p>
        """)
        help_text.setMinimumHeight(400)
        layout.addWidget(help_text)

        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.resize(600, 500)

def main():
    """Entry point for the EPWgen application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About EPWgen")
        layout = QVBoxLayout()

        about_text = (
            "<h3>EPWgen</h3>"
            "<p>EPWgen was created by Carlo Bianchi.</p>"
            "<p>Developed at the National Lab of the Rockies (NLR); tool registered under software record SWR-26-017.</p>"
            "<p><b>Do not distribute. Confidential.</b></p>"
            "<hr>"
            "<h4>License</h4>"
            "<p>This software is released under the MIT License.</p>"
            "<pre>Copyright (c) 2025 Carlo Bianchi\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
            "SOFTWARE.</pre>"
        )

        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setHtml(about_text)
        text_widget.setMinimumSize(600, 400)
        layout.addWidget(text_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        button_box.button(QDialogButtonBox.Close).clicked.connect(self.close)
        layout.addWidget(button_box)

        self.setLayout(layout)


if __name__ == "__main__":
    main()
