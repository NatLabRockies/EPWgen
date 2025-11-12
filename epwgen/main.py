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

        # Connect buttons to their respective actions
        self.button_individual.clicked.connect(self.open_individual_dialog)
        self.button_multi_year.clicked.connect(self.open_multi_year_dialog)
        self.button_csv.clicked.connect(self.run_csv_list)

        # Add buttons to layout
        layout.addWidget(self.button_individual)
        layout.addWidget(self.button_multi_year)
        layout.addWidget(self.button_csv)

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
                lat, lon, lat_station, lon_station, quality_checks, 
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
                print(f"✓ Completed year {year}: {retrieve_status}")

            print(f"All years from {start_year} to {end_year} have been processed.")

    # def show_result_and_map(self, status, distance_mi, wmo, hdd, cdd, lat, lon, lat_station, lon_station, quality_checks, status_EP):
    def show_result_and_map(self, status, distance_mi, wmo, hdd, cdd, lat, lon, lat_station, lon_station, quality_checks):
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
        general_info_text = (
            f"Distance: {distance_mi.round(2)} mi<br>"
            f"WMO: {wmo}<br>"
            f"HDD: {hdd}<br>"
            f"CDD: {cdd}<br><br>"
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

        # Load the zip codes CSV file
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
            
            if os.path.isfile(epw_path):
                print(f"Skipping {location_name} ({year}) - EPW file already exists")
                counter += 1
                continue

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
            
            # Add flags for data holes (no year suffix)
            if 'Temp_Holes' not in zipcodes.columns:
                zipcodes['Temp_Holes'] = ''
            if 'Dewpoint_Holes' not in zipcodes.columns:
                zipcodes['Dewpoint_Holes'] = ''
            if 'RH_Holes' not in zipcodes.columns:
                zipcodes['RH_Holes'] = ''
                
            zipcodes.at[index, 'Temp_Holes'] = flags.get(6, '')
            zipcodes.at[index, 'Dewpoint_Holes'] = flags.get(7, '')
            zipcodes.at[index, 'RH_Holes'] = flags.get(8, '')

            counter += 1
            if counter % 10 == 0:
                zipcodes.to_csv(updated_csv_path, index=False)

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

if __name__ == "__main__":
    main()
