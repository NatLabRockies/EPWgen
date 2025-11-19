#!/bin/bash
# EPWgen Cleanup Script
# Removes backup files, old scripts, test outputs, and cached files
# DO NOT RUN without reviewing what will be deleted!

echo "EPWgen Cleanup Script"
echo "====================="
echo ""
echo "This script will delete the following files and folders:"
echo ""

# List what will be deleted
echo "Backup/Old Files:"
echo "  - epwgenBACKUP.ipynb"
echo "  - epwgenBACKUP.py"
echo "  - epwgen_DOENLOAD_INCOMPLETE_YEAR.ipynb"
echo "  - epwgen_GUI.ipynb"
echo "  - epwgen.py (root level - old script)"
echo "  - methods.py (root level - old script)"
echo "  - epwgen/methods.py.backup"
echo ""

echo "Cache/Temporary Files:"
echo "  - __pycache__/ (all locations)"
echo "  - .DS_Store (all locations)"
echo "  - ~\$epwgen.pptx"
echo ""

echo "Presentation/Documentation:"
echo "  - epwgen.pptx"
echo ""

echo "Redundant Installation/Config Files:"
echo "  - prereq.txt (duplicate of requirements.txt with old versions)"
echo "  - INSTALL.md (duplicate instructions in README.md)"
echo "  - MANIFEST.in (only needed for PyPI publishing)"
echo ""

echo "Unused Data Files:"
echo "  - Fairbanks_2025.csv"
echo "  - TES_ratestructures.csv"
echo "  - TES_ratestructures_updated.csv"
echo "  - TEST_LIST.csv (test output file)"
echo "  - FIPS_2007.csv, FIPS_2008.csv, FIPS_2009.csv, FIPS_2010.csv, FIPS_2011.csv"
echo "    (duplicates - fips_complete.csv contains all data)"
echo "  - resources/ (root folder - duplicates epwgen/resources/)"
echo "  - resources/test_MOSMIX/ (test data folder)"
echo "  - design conditions/ (if you don't use it - has design_conditions.ipynb)"
echo ""

echo "Test EPW Files (root level):"
echo "  - Anaktuvuk_2024.epw"
echo "  - Juneau_2024.epw"
echo "  - Nome_2024.epw"
echo "  - Point_Lay_2024.epw"
echo "  - SanBernardino_2023.epw"
echo "  - TEST_2007.epw"
echo "  - TEST_2022.epw"
echo ""

echo "Test Directories:"
echo "  - test/"
echo "  - test_2025/"
echo "  - test_epws_dir/"
echo "  - epws_wmo_2022/"
echo "  - epws_wmo_2023/"
echo "  - epws_wmo_2024/"
echo ""

echo "Output Directory (old runs):"
echo "  - outputs/ (excluding debug/outputs/)"
echo ""

read -p "Do you want to proceed with deletion? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Remove backup files
echo "Removing backup files..."
rm -f epwgenBACKUP.ipynb
rm -f epwgenBACKUP.py
rm -f epwgen_DOENLOAD_INCOMPLETE_YEAR.ipynb
rm -f epwgen_GUI.ipynb
rm -f epwgen.py
rm -f methods.py
rm -f epwgen/methods.py.backup

# Remove cache and temporary files (in all locations)
echo "Removing cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name ".DS_Store" -exec rm -f {} + 2>/dev/null
rm -f ~\$epwgen.pptx

# Remove presentation files
echo "Removing presentation files..."
rm -f epwgen.pptx

# Remove redundant installation/config files
echo "Removing redundant installation/config files..."
rm -f prereq.txt
rm -f INSTALL.md
rm -f MANIFEST.in

# Remove unused data files
echo "Removing unused data files..."
rm -f Fairbanks_2025.csv
rm -f TES_ratestructures.csv
rm -f TES_ratestructures_updated.csv
rm -f TEST_LIST.csv

# Remove duplicate FIPS files (keep fips_complete.csv only)
echo "Removing duplicate FIPS files..."
rm -f FIPS_2007.csv
rm -f FIPS_2008.csv
rm -f FIPS_2009.csv
rm -f FIPS_2010.csv
rm -f FIPS_2011.csv

# Remove duplicate resources folder (keep epwgen/resources/)
echo "Removing duplicate resources folder..."
if [ -d "resources" ] && [ -d "epwgen/resources" ]; then
    rm -rf resources/
fi

# Remove design conditions folder (uncomment if you don't need it)
# echo "Removing design conditions folder..."
# rm -rf "design conditions/"

# Remove test EPW files in root
echo "Removing test EPW files..."
rm -f Anaktuvuk_2024.epw
rm -f Juneau_2024.epw
rm -f Nome_2024.epw
rm -f Point_Lay_2024.epw
rm -f SanBernardino_2023.epw
rm -f TEST_2007.epw
rm -f TEST_2022.epw

# Remove test directories
echo "Removing test directories..."
rm -rf test/
rm -rf test_2025/
rm -rf test_epws_dir/
rm -rf epws_wmo_2022/
rm -rf epws_wmo_2023/
rm -rf epws_wmo_2024/

# Remove outputs directory (but not debug/outputs)
echo "Removing outputs directory..."
if [ -d "outputs" ] && [ ! -L "outputs" ]; then
    # Check if it's not the same as debug/outputs
    if [ "$(realpath outputs 2>/dev/null)" != "$(realpath debug/outputs 2>/dev/null)" ]; then
        rm -rf outputs/
    else
        echo "  Skipped: outputs/ is the same as debug/outputs/"
    fi
fi

echo ""
echo "Cleanup completed!"
echo ""
echo "Remaining structure:"
ls -la | grep -E '^d|^-' | grep -v '^total'
