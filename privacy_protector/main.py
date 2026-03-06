import sys
import os
from .data_generator import generate_fake_data
from .regex_extractor import extract_info_with_regex

def process_text(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        input_text = file.read()

    print(f"Original text:\n{input_text}\n")
    print("Replacing sensitive information with fake data...")
    
    regex_matches = extract_info_with_regex(input_text)
    replacements = []
    processed_text = input_text

    for data_type, matches in regex_matches.items():
        for match in matches:
            if isinstance(match, tuple):
                match = ''.join(match)  # Flatten the tuple if regex captures groups
            fake_data = generate_fake_data(data_type, match)
            processed_text = processed_text.replace(match, fake_data, 1)
            replacements.append((match, fake_data))
            print(f"Replaced {data_type}: {match} -> {fake_data}")

    print(f"\nProcessed text:\n{processed_text}\n")
    
    if replacements:
        print("\nReplacements made:")
        for original, fake in replacements:
            print(f"  {original} -> {fake}")
    else:
        print("\nNo replacements were made.")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(processed_text)

    print(f"Processed text has been written to {output_file}")

    return processed_text

def get_file_name(prompt, default):
    file_name = input(f"{prompt} (default: {default}): ").strip()
    return file_name if file_name else default

def main():
    print("Welcome to Privacy Protector!")
    
    # Use default names or prompt for input
    input_file = get_file_name("Enter input file name", "input.txt")
    output_file = get_file_name("Enter output file name", "output.txt")

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    process_text(input_file, output_file)

if __name__ == "__main__":
    main()