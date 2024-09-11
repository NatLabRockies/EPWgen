import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont
import folium
import os
from epwgen_methods import run_individual_location
from PyQt5.QtCore import QUrl, QDateTime
from datetime import datetime

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EPWgen")

        # Create layout and buttons
        layout = QVBoxLayout()

        # Add the logo using QLabel
        logo_text = """
        \t\t       _____           ___ _           _     _ ___
        _ ___  _________           ___ _           _              
              | ''''''' |               _________     _   _        
        ___ _ | ''''''' |   ___ _      | ''''''' |   _________    
              | ''''''' |              | ''''''' |  |'''''''''|   
         __ _ | '' _____ ______        __''''''' | _|'''''''''| - __
              | ' | ____|  _ \ \      / /_ _  ___ _ __   '''''| 
              | ' |  _| | |_) \ \ /\ / / _` |/ _ \ '_ \  '''''| 
        --  - | ' | |___|  __/ \ V  V / (_| |  __/ | | | '''''| 
              | ' |_____|_|     \_/\_/ \__, |\___|_| |_| '''''| 
         ___ _| '           _________  |___/             '''''|     
              | ''''''' |  | ''''''' | | ''''''' |  | ''''''''| 
              | ''''''' |  | ''''''' | | ''''''' |  | ''''''''| __ 
        ___ _ | ''''''' |  | ''''''' | | ''''''' |  | ''''''''|  
              | ''''''' |  | ''''''' | | ''''''' |  | ''''''''|   
        '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\n\n\n\n
        """

        # Add the logo using QLabel with monospaced font
     #    logo_text = """
     #       _____           ___ _           _     _ _________  
     # _ ___  _________           ___ _           _              
     #      | ''''''' |               _________     _   _        
     # ___ _ | ''''''' |   ___ _      | ''''''' |   _________    
     #      | ''''''' |              | ''''''' |  |'''''''''|   
     #  __ _ | '' _____ ______        __''''''' | _|'''''''''| - __
     #      | ' | ____|  _ \\ \\      / /_ _  ___ _ __   '''''| 
     #      | ' |  _| | |_) \\ \\ /\\ / / _` |/ _ \\ '_ \\  '''''| 
     # --  - | ' | |___|  __/ \\ V  V / (_| |  __/ | | | '''''| 
     #      | ' |_____|_|     \\_/\\_/ \\__, |\\___|_| |_| '''''| 
     #  ___ _| '           _________  |___/             '''''|     
     #      | ''''''' |  | ''''''' | | ''''''' |  | ''''''''| 
     #      | ''''''' |  | ''''''' | | ''''''' |  | ''''''''| __ 
     # ___ _ | ''''''' |  | ''''''' | | ''''''' |  | ''''''''|  
     #      | ''''''' |  | ''''''' | | ''''''' |  | ''''''''|   
     # '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\n\n\n\n
     #    """
        logo_label = QLabel(logo_text)
        logo_label.setFont(QFont("Courier", 10))  # Set monospaced font
        layout.addWidget(logo_label)


        # Create buttons
        self.button_individual = QPushButton("Retrieve weather data for an individual location")
        self.button_csv = QPushButton("Retrieve data from CSV file list")

        # Connect buttons to their respective actions
        self.button_individual.clicked.connect(self.open_individual_dialog)
        self.button_csv.clicked.connect(self.run_csv_list)

        # Add buttons to the layout
        layout.addWidget(self.button_individual)
        layout.addWidget(self.button_csv)

        self.setLayout(layout)

    def open_individual_dialog(self):
        # Create dialog for input
        dialog = IndividualLocationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            lat, lon, save_name, year, save_folder, file_type = dialog.get_values()

            # Get the current year
            current_year = datetime.now().year

            # Validate the year input
            if year > (current_year - 1):
                # Show error message if year is greater than current year - 1
                error_msg = QMessageBox()
                error_msg.setIcon(QMessageBox.Warning)
                error_msg.setWindowTitle("Invalid Year")
                error_msg.setText(f"The input year {year} is invalid. It must be less than or equal to {current_year - 1}.")
                error_msg.setStandardButtons(QMessageBox.Ok)
                error_msg.exec_()
                return  # Exit the function without continuing if the year is invalid

            # Call the function to retrieve weather data
            retrieve_status, distance, wmo, hdd, cdd, latitude_station, longitude_station, _ = run_individual_location(lat, lon, year, file_type, save_folder, save_name)

            if retrieve_status:
                answer = 'Yes'
            else:
                answer = 'No'

            # Check if distance is a valid number and convert to miles, otherwise set to 'N/A'
            if distance is not None and isinstance(distance, (int, float)):
                distance_miles = round(distance * 0.000621371, 1)  # Convert to miles and round to 1 decimal
            else:
                distance_miles = '0'

            # Display the result in a simple message
            result_dialog = QDialog(self)
            result_dialog.setWindowTitle("Weather Data Result")
            result_layout = QVBoxLayout()
            result_layout.addWidget(QLabel(f"Did we manage to retrieve data for the selected location for {year}?: {answer}\n"
                                           f"Weather station distance from originally requested location: {distance_miles} Miles\n"
                                           f"WMO: {wmo}\n"
                                           f"Heating Degree Days: {hdd}\n"
                                           f"Cooling Degree Days: {cdd}"))

            # Add Folium map view with both markers
            folium_map = self.create_folium_map(lat, lon, latitude_station, longitude_station)
            result_layout.addWidget(folium_map)

            result_dialog.setLayout(result_layout)
            result_dialog.exec_()

    def run_csv_list(self):
        save_folder = ''
        file_type = 'AMY'
        year = 2022
        csv_list_name = 'resources/zip_code_list.csv'

        # Load the zip codes CSV file
        zipcodes = pd.read_csv(csv_list_name, dtype={f'Do we have data for {year}?': str, f'weather_station_wmo_{year}': str})

        # Initialize a counter for iterations
        counter = 0

        for index, row in zipcodes.iterrows():
            print(index)
            zip_code = str(row['zip0']).zfill(5)
            lat = row['lat']
            lon = row['lng']
            save_name = None

            # Retrieve data for the current location
            retrieve_status, distance, wmo, hdd, cdd, latitude_station, longitude_station, _ = run_individual_location(lat, lon, year, file_type, save_folder, save_name)

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

    def create_folium_map(self, lat, lon, latitude_station, longitude_station):
        # Create a folium map
        folium_map = folium.Map(zoom_start=14)

        # Add a marker (pin) at the requested location with a popup label "Requested location"
        folium.Marker([lat, lon], popup="Requested location", tooltip="Requested location").add_to(folium_map)

        # Add a second marker (pin) at the weather station location with a red icon and popup label
        folium.Marker([latitude_station, longitude_station], popup="Weather station location", 
                      tooltip="Weather station location", icon=folium.Icon(color='red')).add_to(folium_map)

        # Fit the map to show both markers (requested location and weather station location)
        folium_map.fit_bounds([[lat, lon], [latitude_station, longitude_station]])

        # Save the map to an HTML file
        map_path = 'map.html'
        folium_map.save(map_path)

        # Create a QWebEngineView and load the local HTML map
        map_view = QWebEngineView()
        map_view.setUrl(QUrl.fromLocalFile(os.path.abspath(map_path)))

        return map_view


class IndividualLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Input Location Details")
        self.form_layout = QFormLayout()
 
        # Default values
        self.lat_input = QLineEdit("39.740198")
        self.lon_input = QLineEdit("-105.169336")
        self.save_name_input = QLineEdit("NREL")
        self.year_input = QLineEdit("2022")
        self.save_folder_input = QLineEdit("")
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
