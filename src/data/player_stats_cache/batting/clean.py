import csv

input_file = "pitching_qualified.csv"
output_file = "cleaned.csv"

with open(input_file, newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames

    # Keep only the first 'team name' column
    seen = set()
    new_fieldnames = []
    for name in fieldnames:
        if name == "team name":
            if name in seen:
                continue
            seen.add(name)
        new_fieldnames.append(name)

    # Write cleaned file
    with open(output_file, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
        writer.writeheader()
        for row in reader:
            # Remove any duplicate keys before writing
            clean_row = {k: row[k] for k in new_fieldnames if k in row}
            writer.writerow(clean_row)

print(f"✅ Cleaned file written to '{output_file}' (duplicates removed).")
