#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Apple Health XML to CSV
==============================
:File: convert.py
:Description: Convert Apple Health "export.xml" file into a csv
:Version: 0.0.2
:Created: 2019-10-04
:Updated: 2023-10-29
:Authors: Jason Meno (jam)
:Dependencies: An export.xml file from Apple Health
:License: BSD-2-Clause
"""

# %% Imports
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint
import xml.etree.ElementTree as ET
import sys
from matplotlib.ticker import MaxNLocator


# %% Function Definitions

def preprocess_to_temp_file(file_path):
    """
    The export.xml file is where all your data is, but Apple Health Export has
    two main problems that make it difficult to parse: 
        1. The DTD markup syntax is exported incorrectly by Apple Health for some data types.
        2. The invisible character \x0b (sometimes rendered as U+000b) likes to destroy trees. Think of the trees!

    Knowing this, we can save the trees and pre-processes the XML data to avoid destruction and ParseErrors.
    """

    print("Pre-processing and writing to temporary file...", end="")
    sys.stdout.flush()

    temp_file_path = "temp_preprocessed_export.xml"
    with open(file_path, 'r') as infile, open(temp_file_path, 'w') as outfile:
        skip_dtd = False
        for line in infile:
            if '<!DOCTYPE' in line:
                skip_dtd = True
            if not skip_dtd:
                line = strip_invisible_character(line)
                outfile.write(line)
            if ']>' in line:
                skip_dtd = False

    print("done!")
    return temp_file_path

def strip_invisible_character(line):
    return line.replace("\x0b", "")


def xml_to_csv(file_path):
    """Loops through the element tree, retrieving all objects, and then
    combining them together into a dataframe
    """

    print("Converting XML File to CSV...", end="")
    sys.stdout.flush()

    attribute_list = []

    for event, elem in ET.iterparse(file_path, events=('end',)):
        if event == 'end':
            child_attrib = elem.attrib
            for metadata_entry in list(elem):
                metadata_values = list(metadata_entry.attrib.values())
                if len(metadata_values) == 2:
                    metadata_dict = {metadata_values[0]: metadata_values[1]}
                    child_attrib.update(metadata_dict)
            attribute_list.append(child_attrib)

            # Clear the element from memory to avoid excessive memory consumption
            elem.clear()

    health_df = pd.DataFrame(attribute_list)

    # Every health data type and some columns have a long identifer
    # Removing these for readability
    health_df.type = health_df.type.str.replace('HKQuantityTypeIdentifier', "")
    health_df.type = health_df.type.str.replace('HKCategoryTypeIdentifier', "")
    health_df.columns = \
        health_df.columns.str.replace("HKCharacteristicTypeIdentifier", "")

    # Reorder some of the columns for easier visual data review
    original_cols = list(health_df)
    shifted_cols = ['type',
                    'sourceName',
                    'value',
                    'unit',
                    'startDate',
                    'endDate',
                    'creationDate']

    # Add loop specific column ordering if metadata entries exist
    if 'com.loopkit.InsulinKit.MetadataKeyProgrammedTempBasalRate' in original_cols:
        shifted_cols.append(
            'com.loopkit.InsulinKit.MetadataKeyProgrammedTempBasalRate')

    if 'com.loopkit.InsulinKit.MetadataKeyScheduledBasalRate' in original_cols:
        shifted_cols.append(
            'com.loopkit.InsulinKit.MetadataKeyScheduledBasalRate')

    if 'com.loudnate.CarbKit.HKMetadataKey.AbsorptionTimeMinutes' in original_cols:
        shifted_cols.append(
            'com.loudnate.CarbKit.HKMetadataKey.AbsorptionTimeMinutes')

    remaining_cols = list(set(original_cols) - set(shifted_cols))
    reordered_cols = shifted_cols + remaining_cols
    health_df = health_df.reindex(labels=reordered_cols, axis='columns')

    # Sort by newest data first
    health_df.sort_values(by='startDate', ascending=False, inplace=True)

    print("done!")

    return health_df

def plot_data(df, column1, column2):
    x = df[column1]  # Column for x-axis
    y = df[column2]  # Column for y-axis

    # Step 3: Create a plot (for example, a scatter plot)
    plt.figure(figsize=(10,6))  # Optional: Define the size of the figure
    plt.plot(x, y, color='blue', label='Data points')  # Create a scatter plot
    # plt.ylim(60, 80)  # Set the range for y-axis values (adjust as needed)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True, prune='both', steps=[1])) # Optional: Set y-axis to integer values

    # Step 4: Add labels and a title
    plt.xlabel('Column 1')  # x-axis label
    plt.ylabel('Column 2')  # y-axis label
    plt.title('Scatter Plot of Column 1 vs Column 2')  # Title of the plot
    plt.legend()  # Display legend

    # Step 5: Show the plot
    plt.show()


def main():
    file_path = "C:/Apple Health/export/apple_health_export/export.xml" # Path to export.xml
    temp_file_path = preprocess_to_temp_file(file_path) # Preprocess file
    health_df = xml_to_csv(temp_file_path) # Convert to data frame

    print(health_df.columns)
    health_df = health_df[health_df['type'] == 'BodyMass'] # Filter by type
    columns_to_select = ['type', 'creationDate', 'value'] # List columns select to output
    body_mass = health_df[columns_to_select] # Select columns from data frame
    body_mass['creationDate'] = body_mass['creationDate'].str[:10] # Extract date only from datetime
    body_mass.sort_values(by='creationDate', ascending=True, inplace=True) # Sort by date
    body_mass = body_mass.drop_duplicates(subset='creationDate', keep='first') # Drop duplicates for dates
    pprint(body_mass)
    plot_data(body_mass, 'creationDate', 'value') # Plot data
    body_mass.to_excel('output_file.xlsx', index=False, engine='openpyxl') # Save to excel

    return


# %%
if __name__ == '__main__':
    main()