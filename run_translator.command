#!/bin/bash
# Move to the folder where this script is located
cd "$(dirname "$0")"

# This line ensures the script can see your secret API key
source ~/.zshrc

echo "------------------------------------------------"
echo "   GEMINI EPUB TRANSLATOR - PORTSMOUTH v2026   "
echo "------------------------------------------------"
echo ""

# Check if a file was dropped onto the icon
if [ "$1" != "" ]; then
    FILE_PATH="$1"
else
    # Prompt the user to drag the file into this window
    echo "Please DRAG and DROP your EPUB file here and press ENTER:"
    read FILE_PATH
fi

# Clean up the path (removes quotes and escape slashes from Mac drag-and-drop)
CLEAN_PATH=$(echo "$FILE_PATH" | sed "s/\\\\//g" | sed "s/'//g" | sed 's/"//g')

# Run the Python script
python3 translate_epub.py "$CLEAN_PATH"

echo ""
echo "Translation complete. Press ENTER to close this window."
read
