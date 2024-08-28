from methods import *
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QGridLayout, QMessageBox
)


def run_code():
    try:
        lat = float(lat_input.text())
        lon = float(lon_input.text())
        year = int(year_input.text())
        name = name_input.text()
        output_name = output_name_input.text()
        file_type = file_type_input.text()

        # Run your existing code with these parameters
        data_meteostat_merra2, missing_dates, info_dict = get_noaa_merra2_data(lat, lon, year, file_type)
        if missing_dates:
            QMessageBox.critical(window, "Error", "Too many missing hours in the data.")
        else:
            data_meteostat_merra2.to_csv(output_name, header=False, index=False)
            with open(output_name, 'r') as original_file:
                data_content = original_file.read()
            header_lines = create_header(data_meteostat_merra2, year, info_dict)
            with open(output_name, 'w') as new_file:
                new_file.write("\n".join(header_lines) + "\n" + data_content)
            QMessageBox.information(window, "Success", f"Data saved successfully to {output_name}")
    except Exception as e:
        QMessageBox.critical(window, "Error", f"An error occurred: {str(e)}")

app = QApplication(sys.argv)

# Create the main window
window = QWidget()
window.setWindowTitle("Input Data for NOAA MERRA2")
window.setGeometry(100, 100, 600, 400)

# Create layout
layout = QGridLayout()

# Latitude
layout.addWidget(QLabel("Latitude:"), 0, 0)
lat_input = QLineEdit()
layout.addWidget(lat_input, 0, 1)
lat_input.setText("30.6833")

# Longitude
layout.addWidget(QLabel("Longitude:"), 1, 0)
lon_input = QLineEdit()
layout.addWidget(lon_input, 1, 1)
lon_input.setText("-88.0667")

# Year
layout.addWidget(QLabel("Year:"), 2, 0)
year_input = QLineEdit()
layout.addWidget(year_input, 2, 1)
year_input.setText("2023")

# Name
layout.addWidget(QLabel("Name:"), 3, 0)
name_input = QLineEdit()
layout.addWidget(name_input, 3, 1)
name_input.setText("TEST_2023")

# Output Name
layout.addWidget(QLabel("Output Name:"), 4, 0)
output_name_input = QLineEdit()
layout.addWidget(output_name_input, 4, 1)
output_name_input.setText("TEST_2023.epw")

# File Type
layout.addWidget(QLabel("File Type:"), 5, 0)
file_type_input = QLineEdit()
layout.addWidget(file_type_input, 5, 1)
file_type_input.setText("AMY")

# Run Button
run_button = QPushButton("Run")
run_button.clicked.connect(run_code)
layout.addWidget(run_button, 6, 0, 1, 2)

# Set the layout and show the window
window.setLayout(layout)
window.show()

sys.exit(app.exec_())
