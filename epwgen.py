import sys
import os
import tempfile
import folium
import pandas as pd

# IMPORTANT: set Qt attribute before creating QApplication or importing QtWebEngineWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QLineEdit,
    QDialog, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap

from methods import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EPWgen")

        # Create layout
        layout = QVBoxLayout()

        # Load and display the logo
        self.logo_label = QLabel()
        # Load and resize the logo
        pixmap = QPixmap("resources/Logo.png")  
        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio)  # Adjust size as needed
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)  # Center align the logo
        layout.addWidget(self.logo_label)  # Add logo to layout

        # Create buttons
        self.button_individual = QPushButton("Retrieve weather data for an individual location")
        self.button_csv = QPushButton("Retrieve data from CSV file list")

        # Connect buttons to their respective actions
        self.button_individual.clicked.connect(self.open_individual_dialog)
        self.button_csv.clicked.connect(self.run_csv_list)

        # Add buttons to layout
        layout.addWidget(self.button_individual)
        layout.addWidget(self.button_csv)

        self.setLayout(layout)

    def open_individual_dialog(self):
        # Create dialog for input
        dialog = IndividualLocationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            lat, lon, save_name, year, save_folder, file_type = dialog.get_values()

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
            if save_folder == '.':
                epw_path = f'{save_name}_{year}.epw'
            else:
                epw_path = os.path.join(save_folder, f'{save_name}.epw')

            quality_checks = check_epw_quality(epw_path)
            status_EP = run_energyplus_simulations(epw_path)
            print(status_EP)

            # 2. Suppose retrieve_distance_station_location returns [distance_mi, lat_station, lon_station].
            [distance_mi, lat_station, lon_station] = retrieve_distance_station_location(wmo, lat, lon)

            # 3. Show a single dialog with text info + map including quality_checks and EnergyPlus status
            self.show_result_and_map(
                retrieve_status, distance_mi, wmo, hdd, cdd,
                lat, lon, lat_station, lon_station, quality_checks, status_EP
            )

    def show_result_and_map(self, status, distance_mi, wmo, hdd, cdd, lat, lon, lat_station, lon_station, quality_checks, status_EP):
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
            f"<b>EnergyPlus Status:</b><br>{status_EP}"
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
        save_folder = 'epws_wmo'
        file_type = 'AMY'
        year = 2022
        csv_list_name = 'resources/zip_code_list.csv'

        # Load the zip codes CSV file
        zipcodes = pd.read_csv(
            csv_list_name,
            dtype={f'Do we have data for {year}?': str, f'weather_station_wmo_{year}': str}
        )

        # Initialize a counter for iterations
        counter = 0

        for index, row in zipcodes.iterrows():
            print(index)
            zip_code = str(row['zip0']).zfill(5)
            lat = row['lat']
            lon = row['lng']
            save_name = None

            # Retrieve data for the current location
            retrieve_status, distance, wmo, hdd, cdd, _ = run_individual_location(
                lat, lon, year, file_type, save_folder, save_name
            )

            # Update the DataFrame
            zipcodes.at[index, f"Do we have data for {year}?"] = retrieve_status
            zipcodes.at[index, f"distance_location_station_miles_{year}"] = distance * 0.000621371
            zipcodes.at[index, f"weather_station_wmo_{year}"] = wmo
            zipcodes.at[index, f"hdd_base65F_{year}"] = hdd
            zipcodes.at[index, f"cdd_base65F_{year}"] = cdd

            counter += 1
            if counter % 10 == 0:
                zipcodes.to_csv(csv_list_name, index=False)

        zipcodes.to_csv(csv_list_name, index=False)


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
