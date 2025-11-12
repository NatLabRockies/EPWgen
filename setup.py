from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="epwgen",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for generating EnergyPlus Weather (EPW) files from meteorological data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/EPWgen",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "folium>=0.14.0",
        "pandas>=1.3.0",  # Relaxed to accommodate isd package requirement
        "PyQt5>=5.15.0",
        "PyQtWebEngine>=5.15.0",
        "meteostat>=1.6.0",
        "timezonefinder>=6.0.0",
        "pytz>=2023.0",
        "requests>=2.28.0",
        "openstudio>=3.5.0",
        "numpy>=1.24.0,<2.0",  # numpy 2.x incompatible with pandas 1.5.3
        "isd>=0.3.0",
        "paramiko",
        "scp",
    ],
    entry_points={
        "console_scripts": [
            "epwgen=epwgen.main:main",
        ],
    },
    package_data={
        "epwgen": ["resources/*"],
    },
    include_package_data=True,
)
