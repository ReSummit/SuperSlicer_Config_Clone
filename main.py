#!/usr/bin/env python
# Program to copy parameters between duplicate print profiles

import re, sys, os
import colorama

def print_color(text="", color=colorama.Fore.WHITE, background=colorama.Back.RESET):
    print(color + background + text + colorama.Fore.WHITE + colorama.Back.RESET)

def print_error():
    print_color("Invalid input, try again", color=colorama.Fore.RED)

def print_length_error():
    print_color("List of inputs invalid. Please manually handle differences. Exiting program.", color=colorama.Fore.RED)

# Open the file for read
if os.path.exists("SuperSlicer_config_bundle.ini"):
    file = open("./SuperSlicer_config_bundle.ini", "rb")
else:
    print_color("Please have the file 'SuperSlicer_config_bundle.ini' in the same directory as this program.", color=colorama.Fore.RED)
    sys.exit()

# Each profile is separated with regex "\[print:.*\]"
# Find all matches as a list of regex objects
matches = re.findall(b"\[print:.*\]", file.read())
file.seek(0)
miter = re.finditer(b"\[print:.*\]", file.read())
matches_iter = []
for match in miter:
    matches_iter.append(match)

# Ask user which profiles to evaluate
print_color("Which profiles would you like to deduplicate?", colorama.Fore.YELLOW)
# Print all matches prepended with a number
for i in range(len(matches)):
    print(str(i) + ": " + matches[i].decode("utf-8").strip())

# Ask user for list of comma separated numbers
print_color("Enter at least 2 numbers separated by commas.", colorama.Fore.YELLOW)

# Get user input and validate
while True:
    try:
        # Get user input
        user_input = input()
        # Split user input into list
        user_input = user_input.split(",")
        # Convert each element to integer
        user_input = [int(i) for i in user_input]
        # Check if there are at least 2 elements
        if len(user_input) >= 2:
            break
        elif user_input == "exit":
            sys.exit()
        else:
            print_error()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit()
    except ValueError:
        print_error()
print_color("\n--------------------", colorama.Fore.YELLOW)

# Create a list of profiles to evaluate
profiles = [matches_iter[i] for i in user_input]
profiles_names = [matches[i].decode("utf-8").strip() for i in user_input]

# The file has a list of variables and their values
# Ex: "first_layer_speed = 20"
# Convert each profile into a dictionary and store in a list
# Key: variable name
# Value: variable value
profile_list = []
for index,profile in enumerate(profiles):
    # Create a dictionary for the profile
    profile_dict = {}
    
    # Starting at match variable profile, iterate through each line until we reach the next profile
    # Set read marker to match variable profile
    file.seek(profile.start())
    file.readline()

    while True:
        # Read line
        line = file.readline().decode("utf-8").strip()
        
        # At the end of each profile, there is a new line
        # If this is empty, we have reached the end of the profile
        if line == "":
            break

        # Split line into variable name and value
        line = line.split(" = ")

        # Sometimes, the value is empty. Replace with None and strip characters
        if len(line) == 1:
            line.append("")
            line[0] = line[0].strip(" =")

        # Add variable name and value to dictionary
        profile_dict[line[0]] = line[1]

    # Add dictionary to list
    profile_list.append((profiles_names[index], profile_dict))

# The plan is to go through each profile key and value
# We aren't sure if there are the same keys for each profile
# Aggregate all keys into a set
all_profile_keys = set()
for profile in profile_list:
    for key in profile[1].keys():
        all_profile_keys.add(key)

# Iterate through each key in each profile using the set of all keys
# Also keep track of inputs in case user wants to redo changes
user_inputs = []
macro_input = -1

# Ask if user has list of inputs already
print_color("Do you have a list of inputs already? (y/n)", colorama.Fore.YELLOW)
while True:
    try:
        # Get user input
        user_input = input()

        if user_input == "y":
            print("Enter list of inputs separated by commas.")
            print("Enter 'exit' to exit.")
            while True:
                try:
                    # Get user input
                    user_input = input()

                    if user_input == "exit":
                        sys.exit()

                    # Split user input into list
                    user_input = user_input.split(",")
                    
                    temp = []
                    for i in user_input:
                        if re.match("((skip)|(s))", i):
                            temp.append(i)
                        else:
                            temp.append(int(i))

                    # Check if there are at least 2 elements
                    if len(user_input) >= 2:
                        break
                    else:
                        print_error()
                except KeyboardInterrupt:
                    print("Exiting...")
                    sys.exit()
                except ValueError:
                    print_error()
            print_color("\n--------------------", colorama.Fore.YELLOW)
            user_inputs = user_input
            macro_input = len(user_inputs)
            break
        elif user_input == "n":
            break
        else:
            print_error()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit()
print_color("\n--------------------", colorama.Fore.YELLOW)

for key in all_profile_keys:
    # Check each profile to see if the key exists
    # If not, exclude the profile from the comparison
    exclude_list = []
    for profile in profile_list:
        if key not in profile[1].keys() or profile[1][key] == "":
            exclude_list.append(profile)
    
    # Compare remaining profiles for different values
    # If different, ask user which value to keep
    diff_check = False
    for profile in profile_list:
        if profile in exclude_list:
            continue
        else:
            for profile2 in profile_list:
                if profile2 in exclude_list:
                    continue
                else:
                    if profile[1][key] != profile2[1][key]:
                        diff_check = True
                        break
            if diff_check:
                break
    
    # Tell user profiles with different values
    # Each profile is associated with regex array profiles
    if diff_check:
        if macro_input == -1:
            print("Profiles with different values for key: " + key)
            for index, profile in enumerate(profile_list):
                if profile in exclude_list:
                    continue
                else:
                    print_color(str(index) + ": " + colorama.Fore.WHITE + profile[0], colorama.Fore.CYAN)
                    print_color("Value: " + colorama.Fore.LIGHTMAGENTA_EX + profile[1][key], colorama.Fore.WHITE)
                    print("")

            print_color("Which profile would you like to keep?", colorama.Fore.YELLOW)
            print_color("Enter one of the numbers above or 'skip' or 's' to keep these different.", colorama.Fore.YELLOW)

        # Ask user for profile to keep
        # Validate user input
        while True:
            try:
                # Get user input
                if macro_input > 0:
                    user_input = user_inputs.pop()
                    macro_input -= 1
                elif macro_input == 0:
                    # We've run out of macros, exit program
                    macro_input = 1
                    raise ValueError
                else:
                    user_input = input()

                if re.search("((skip)|(s))", user_input):
                    print_color("Skipping...", colorama.Fore.YELLOW)
                    break

                # Convert user input to integer
                user_input = int(user_input)
                # Check if user input is in range
                if user_input in range(len(profile_list)):
                    break
                else:
                    print_error()
            except KeyboardInterrupt:
                print("Exiting...")
                sys.exit()
            except ValueError:
                if macro_input > 0:
                    # Macro failed, abort execution of macro
                    print_length_error()
                    sys.exit()
                else:
                    print_error()
        
        user_inputs.append(str(user_input))

        # If user input is not skip, apply changes to all profiles
        if not re.search("((skip)|(s))", str(user_input)):
            # Apply changes to all profiles
            for profile in profile_list:
                if profile in exclude_list:
                    continue
                else:
                    if profile != profile_list[user_input]:
                        print_color("Applied changes to " + profile[0] + " with value " + profile[1][key], colorama.Fore.GREEN)
                    profile[1][key] = profile_list[user_input][1][key]
        print_color("\n--------------------", colorama.Fore.YELLOW)

# If we still have macros, exit program as we don't know if they are valid
if macro_input > 0:
    print_length_error()
    sys.exit()

print_color("All different values have been resolved.", colorama.Fore.GREEN)
print_color("Would you like to save the changes? (y/n)", colorama.Fore.YELLOW)
while True:
    try:
        # Get user input
        user_input = input()
        if user_input == "y":
            break
        elif user_input == "n":
            print("\nYou may run the program again to apply changes.")
            if len(user_inputs) > 0:
                print_color("Run differences with the following inputs to restore changes:", colorama.Fore.CYAN)
                print_color(",".join(user_inputs), colorama.Fore.YELLOW)
            sys.exit()
        else:
            print_error()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit()
    except ValueError:
        print_error()

# Save changes to all profiles
file.close()
print_color("\nSaving changes...", colorama.Fore.YELLOW)
print_color("Backup of original file is saved as SuperSlicer_config_bundle.ini.bak", colorama.Fore.YELLOW)
if os.path.exists("SuperSlicer_config_bundle.ini"):
    os.rename("SuperSlicer_config_bundle.ini", "SuperSlicer_config_bundle.ini.bak")
with open("SuperSlicer_config_bundle.ini", "w") as f:
    f.write("# SuperSlicer config bundle modified by SuperSlicer_clone tool\n\n")
    for index,profile in enumerate(profile_list):
        f.write(profile[0] + "\n")
        for key in profile[1].keys():
            if profile[1][key] != None:
                f.write(key + " = " + profile[1][key] + "\n")
            else:
                f.write(key + " = " + "\n")
        f.write("\n")
