def filter_pylint_logs(input_file, output_file, filter_string="(invalid-name)"):
    """
    Filters pylint logs from the input file based on a specific filter string
    and writes the filtered logs to the output file.

    :param input_file: Path to the input file containing pylint logs.
    :param output_file: Path to the output file where filtered logs will be saved.
    :param filter_string: The string to filter lines by (default is "(invalid-name)").
    """
    try:
        with open(input_file, "r") as infile:
            lines = infile.readlines()

        # Filter lines that contain the specified filter string
        filtered_lines = [line for line in lines if filter_string in line]

        with open(output_file, "w") as outfile:
            outfile.writelines(filtered_lines)

        print(f"Filtered logs have been written to {output_file}.")

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage
filter_pylint_logs("pylint_logs.txt", "filtered_logs.txt")
