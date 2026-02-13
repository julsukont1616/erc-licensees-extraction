#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to analyze electricity production fuel types from Thai license data.
Extracts BOTH main and supplementary fuel types and technology details.
FIXED: Properly splits ALL comma-separated fuel types.
"""

import csv
import re
from collections import Counter

def parse_fuel_type(fuel_string):
    """
    Parse fuel type string and extract main fuel type and technology detail.

    Args:
        fuel_string: String like "พลังแสงอาทิตย์ (Solar){Tech Detail}"

    Returns:
        tuple: (main_fuel, tech_detail)
    """
    if not fuel_string or fuel_string.strip() == '':
        return None, None

    fuel_string = fuel_string.strip()

    # Extract technology detail in curly braces {}
    tech_detail = None
    curly_match = re.search(r'\{([^}]+)\}', fuel_string)
    if curly_match:
        tech_detail = curly_match.group(1)
        # Remove the curly braces part from main fuel string
        main_fuel = re.sub(r'\{[^}]+\}', '', fuel_string).strip()
    else:
        main_fuel = fuel_string

    return main_fuel, tech_detail

def split_fuels_smart(fuel_string):
    """
    Smart split that handles commas outside of curly braces.
    Returns list of individual fuel strings.
    Examples:
      "Solar, Biomass" -> ["Solar", "Biomass"]
      "Solar{tech}, Biomass" -> ["Solar{tech}", "Biomass"]
      "Solar, Biomass{tech}" -> ["Solar", "Biomass{tech}"]
    """
    if not fuel_string or ',' not in fuel_string:
        return [fuel_string] if fuel_string else []

    # Strategy: Find closing brace if it exists, then look for commas after it
    result = []
    parts = []

    # First, let's try a regex-based approach to split on commas NOT inside braces
    import re

    # Split by comma, but only if not inside curly braces
    # Pattern: comma that's not inside {...}
    depth = 0
    current_part = []

    for char in fuel_string:
        if char == '{':
            depth += 1
            current_part.append(char)
        elif char == '}':
            depth -= 1
            current_part.append(char)
        elif char == ',' and depth == 0:
            # This is a separator comma
            parts.append(''.join(current_part).strip())
            current_part = []
        else:
            current_part.append(char)

    # Don't forget the last part
    if current_part:
        parts.append(''.join(current_part).strip())

    return [p for p in parts if p]

def main():
    csv_file = 'RadGridExport.csv'

    # Storage for analysis
    main_fuel_types = []
    supplementary_fuel_types = []
    all_tech_details = []

    # For enhanced CSV
    rows_with_parsed_data = []

    # Read CSV and extract fuel types
    print("Reading CSV file...")
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)

        main_fuel_col = 6
        supp_fuel_col = 7

        for row_num, row in enumerate(reader, start=2):
            if len(row) > supp_fuel_col:
                main_fuel_string = row[main_fuel_col]
                supp_fuel_string = row[supp_fuel_col]

                # Parse main fuel
                parsed_main_fuels = []
                parsed_main_techs = []

                if main_fuel_string:
                    fuel_parts = split_fuels_smart(main_fuel_string)
                    for fuel_part in fuel_parts:
                        main_fuel, tech_detail = parse_fuel_type(fuel_part)
                        if main_fuel:
                            main_fuel_types.append(main_fuel)
                            parsed_main_fuels.append(main_fuel)
                            if tech_detail:
                                all_tech_details.append(tech_detail)
                                parsed_main_techs.append(tech_detail)

                # Parse supplementary fuel
                parsed_supp_fuels = []
                parsed_supp_techs = []

                if supp_fuel_string:
                    fuel_parts = split_fuels_smart(supp_fuel_string)
                    for fuel_part in fuel_parts:
                        supp_fuel, tech_detail = parse_fuel_type(fuel_part)
                        if supp_fuel:
                            supplementary_fuel_types.append(supp_fuel)
                            parsed_supp_fuels.append(supp_fuel)
                            if tech_detail:
                                all_tech_details.append(tech_detail)
                                parsed_supp_techs.append(tech_detail)

                # Store parsed data
                rows_with_parsed_data.append({
                    'row': row,
                    'main_fuels': parsed_main_fuels,
                    'main_techs': parsed_main_techs,
                    'supp_fuels': parsed_supp_fuels,
                    'supp_techs': parsed_supp_techs
                })

    # Count occurrences
    main_fuel_counter = Counter(main_fuel_types)
    supp_fuel_counter = Counter(supplementary_fuel_types)
    tech_counter = Counter(all_tech_details)

    # Print results
    print("\n" + "="*80)
    print("MAIN FUEL TYPES (ชนิดเชื้อเพลิงหลัก)")
    print("="*80)
    print(f"\nTotal unique main fuel types: {len(main_fuel_counter)}")
    print(f"Total main fuel entries: {len(main_fuel_types)}")
    print("\nMain fuel types sorted by frequency:\n")

    for fuel_type, count in main_fuel_counter.most_common():
        print(f"{count:5d}  {fuel_type}")

    print("\n" + "="*80)
    print("SUPPLEMENTARY FUEL TYPES (ชนิดเชื้อเพลิงเสริม)")
    print("="*80)
    print(f"\nTotal unique supplementary fuel types: {len(supp_fuel_counter)}")
    print(f"Total supplementary fuel entries: {len(supplementary_fuel_types)}")
    print("\nSupplementary fuel types sorted by frequency:\n")

    for fuel_type, count in supp_fuel_counter.most_common():
        print(f"{count:5d}  {fuel_type}")

    print("\n" + "="*80)
    print("TECHNOLOGY DETAILS (from curly braces - both main and supplementary)")
    print("="*80)
    print(f"\nTotal unique technology details: {len(tech_counter)}")
    print(f"Total entries with tech details: {len(all_tech_details)}")
    print("\nTechnology details sorted by frequency:\n")

    for tech, count in tech_counter.most_common():
        print(f"{count:5d}  {tech}")

    # Save to output files
    print("\n" + "="*80)
    print("Saving results to files...")
    print("="*80)

    with open('main_fuel_types.txt', 'w', encoding='utf-8') as f:
        f.write("MAIN FUEL TYPES (ชนิดเชื้อเพลิงหลัก)\n")
        f.write("="*80 + "\n\n")
        for fuel_type, count in main_fuel_counter.most_common():
            f.write(f"{count:5d}  {fuel_type}\n")
    print("[OK] Saved: main_fuel_types.txt")

    with open('supplementary_fuel_types.txt', 'w', encoding='utf-8') as f:
        f.write("SUPPLEMENTARY FUEL TYPES (ชนิดเชื้อเพลิงเสริม)\n")
        f.write("="*80 + "\n\n")
        for fuel_type, count in supp_fuel_counter.most_common():
            f.write(f"{count:5d}  {fuel_type}\n")
    print("[OK] Saved: supplementary_fuel_types.txt")

    with open('technology_details.txt', 'w', encoding='utf-8') as f:
        f.write("TECHNOLOGY DETAILS (from both main and supplementary)\n")
        f.write("="*80 + "\n\n")
        for tech, count in tech_counter.most_common():
            f.write(f"{count:5d}  {tech}\n")
    print("[OK] Saved: technology_details.txt")

    # Create enhanced CSV
    print("\nCreating enhanced CSV with split columns...")
    with open(csv_file, 'r', encoding='utf-8-sig') as f_in:
        with open('RadGridExport_complete.csv', 'w', encoding='utf-8-sig', newline='') as f_out:
            reader = csv.reader(f_in)
            writer = csv.writer(f_out)

            header = next(reader)
            enhanced_header = (
                header[:7] +
                ['เชื้อเพลิงหลัก (Main Fuel Only)', 'เทคโนโลยีหลัก (Main Tech Detail)'] +
                [header[7]] +
                ['เชื้อเพลิงเสริม (Supp Fuel Only)', 'เทคโนโลยีเสริม (Supp Tech Detail)'] +
                header[8:]
            )
            writer.writerow(enhanced_header)

            for parsed_data in rows_with_parsed_data:
                row = parsed_data['row']
                main_fuels = ', '.join(parsed_data['main_fuels']) if parsed_data['main_fuels'] else ''
                main_techs = ', '.join(parsed_data['main_techs']) if parsed_data['main_techs'] else ''
                supp_fuels = ', '.join(parsed_data['supp_fuels']) if parsed_data['supp_fuels'] else ''
                supp_techs = ', '.join(parsed_data['supp_techs']) if parsed_data['supp_techs'] else ''

                enhanced_row = (
                    row[:7] +
                    [main_fuels, main_techs] +
                    [row[7]] +
                    [supp_fuels, supp_techs] +
                    row[8:]
                )
                writer.writerow(enhanced_row)

    print("[OK] Saved: RadGridExport_complete.csv")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"\nTotal licenses analyzed: {len(rows_with_parsed_data)}")
    print(f"Licenses with supplementary fuel: {sum(1 for d in rows_with_parsed_data if d['supp_fuels'])}")
    print(f"Percentage with supplementary fuel: {sum(1 for d in rows_with_parsed_data if d['supp_fuels']) / len(rows_with_parsed_data) * 100:.1f}%")

    # Count how many licenses have multiple main fuels
    multi_main = sum(1 for d in rows_with_parsed_data if len(d['main_fuels']) > 1)
    print(f"Licenses with multiple main fuels: {multi_main}")
    print(f"Percentage with multiple main fuels: {multi_main / len(rows_with_parsed_data) * 100:.1f}%")

    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)

if __name__ == '__main__':
    main()
