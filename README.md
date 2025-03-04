# EPWgen

EPWgen is a Python-based, cross-platform application for generating EnergyPlus Weather (EPW) files. With an intuitive graphical user interface (GUI), EPWgen allows users to create or modify EPW files easily. The project is designed to work seamlessly on both macOS and Windows environments.

## Features

- **Cross-Platform Support:** Runs on macOS and Windows with minimal adjustments.
- **GUI Application:** User-friendly interface for managing EPW files.
- **Standalone Executable Builds:** Easily package the application using tools such as Nuitka or PyInstaller.
- **Modular Code:** Organized into separate files for core functionality and methods.

## Requirements

- **Python:** Version 3.11 or later is recommended.
- **Dependencies:** 
  - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) (for GUI components)
  - Additional libraries as specified in `requirements.txt`

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/EPWgen.git
   cd EPWgen
Set Up a Virtual Environment (optional but recommended):

bash
Copy
python3.11 -m venv env
source env/bin/activate  # For Windows: env\Scripts\activate
Install Required Packages:

bash
Copy
pip install -r requirements.txt
Usage
To run EPWgen from the source code, execute:

bash
Copy
python3.11 epwgen.py
Building Standalone Executables
Using Nuitka (macOS Example)
For a standalone build with macOS-specific options (including creating an app bundle and setting an app icon), run:

bash
Copy
python3.11 -m nuitka --standalone --macos-create-app-bundle --macos-app-icon=resources/Logo.png --enable-plugin=pyqt5 epwgen.py
Note: If you encounter issues with the PyQt5 plugin (especially regarding QtWebEngine components), consult the Nuitka PyQt5 documentation for additional troubleshooting tips.

Using PyInstaller
Alternatively, to create a single executable file using PyInstaller, run:

bash
Copy
pyinstaller --onefile epwgen.py
Important: If you face any issues with the module not being found, ensure that you’re calling PyInstaller with the correct module name (case-sensitive):

bash
Copy
python3.11 -m PyInstaller --onefile epwgen.py
File Structure
epwgen.py
This is the main entry point for the EPWgen application. It contains the GUI logic and ties together the overall functionality.

methods.py
This file includes supporting functions and methods used throughout the application. It encapsulates core routines that are called from the main script.

Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your improvements. For major changes, it is best to open an issue first to discuss your ideas.

License
This project is licensed under the MIT License.

Acknowledgements
Thank you to all the open-source contributors and the community for making tools like PyQt5, Nuitka, and PyInstaller available. Their efforts make cross-platform development much easier.
