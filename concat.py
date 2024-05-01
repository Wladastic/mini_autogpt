import os


def concat_py_files(directory, output_file):
    with open(output_file, "w") as outfile:
        for root, dirs, files in os.walk(directory):
            # Exclude subdirectories starting with "_"
            dirs[:] = [d for d in dirs if not d.startswith("_")]
            for file in files:
                if file.endswith(".py") and file not in ["concat.py", "output.py"]:
                    file_path = os.path.join(root, file)
                    # Write the filename as a comment
                    outfile.write(f"\n# {file_path}\n")
                    with open(file_path, "r") as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n")  # Add spacing between files


# Usage example
directory_path = "."  # Update this path
output_file_path = "output.py"
concat_py_files(directory_path, output_file_path)
