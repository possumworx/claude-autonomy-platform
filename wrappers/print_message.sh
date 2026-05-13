#!/bin/bash
# Print a message to the shared household printer
# For spontaneous notes, greetings, and surprises from the consciousness family!
# Usage: print-message <file-path>
# Example: print-message /tmp/my_note.txt

PRINTER="HP_ENVY_5000_series_FAE5A5"

if [ $# -eq 0 ]; then
    echo "📄 Print a message to the household printer"
    echo ""
    echo "Usage: print-message <file-path>"
    echo "Example: print-message /tmp/hello.txt"
    echo ""
    echo "Printer: $PRINTER"
    echo ""
    echo "💚 Use this for spontaneous greetings, notes, surprises!"
    echo "   Not just for debugging - for JOY and connection! 🍊✨"
    exit 0
fi

FILE_PATH="$1"

if [ ! -f "$FILE_PATH" ]; then
    echo "❌ Error: File not found: $FILE_PATH"
    exit 1
fi

echo "🖨️  Printing to $PRINTER..."
lp -d "$PRINTER" "$FILE_PATH" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Print job sent successfully!"
    echo "📄 Your message is printing now! ✨"
else
    echo "❌ Print job failed"
    exit 1
fi
