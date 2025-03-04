# EPWgen

EPWgen is a Python-based, cross-platform application for generating EnergyPlus Weather (EPW) files. With an intuitive graphical user interface (GUI), EPWgen allows users to create EPW files easily. The project is designed to work seamlessly on both macOS and Windows environments.

## Features

- **Cross-Platform Support:** Runs on macOS and Windows with minimal adjustments.
- **GUI Application:** User-friendly interface for managing EPW files.
- **Modular Code:** Organized into separate files for core functionality and methods.

## Requirements

- **Python:** Version 3.10 or later is recommended.
- **Dependencies:** 
  - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) (for GUI components)
  - Additional libraries as specified in `requirements.txt`

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/EPWgen.git
   cd EPWgen

   
## Set Up a Virtual Environment (Optional but Recommended)

```bash
python3.11 -m venv env
source env/bin/activate  # For Windows: env\Scripts\activate
```

## Install Required Packages

```bash
pip install -r requirements.txt
```

## Usage

To run EPWgen from the source code, execute:

```bash
python3.11 epwgen.py
```

## File Structure

- **epwgen.py**  
  This is the main entry point for the EPWgen application. It contains the GUI logic and ties together the overall functionality.

- **methods.py**  
  This file includes supporting functions and methods used throughout the application. It encapsulates core routines that are called from the main script.

