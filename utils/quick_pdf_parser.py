#!/usr/bin/env python3
"""
Quick PDF Parser for Testing Mexican Etsy PDF
Testing whether totals can be extracted from Spanish/Mexican PDFs
"""

import sys
import re
try:
    import pdfplumber
except ImportError:
    print("❌ pdfplumber not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

def parse_pdf(pdf_path):
    """Extract text and look for total values"""
    print(f"🔍 Parsing PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    print("\n📋 FULL TEXT EXTRACTED:")
    print("=" * 50)
    print(full_text)
    print("=" * 50)
    
    # Look for total patterns
    print("\n🎯 SEARCHING FOR TOTALS:")
    
    # Pattern for various total formats
    total_patterns = [
        r'Item Total[:\s]*([0-9,]+\.?[0-9]*)\s*([A-Z]{3})',
        r'Shipping Total[:\s]*([0-9,]+\.?[0-9]*)\s*([A-Z]{3})', 
        r'Total[:\s]*([0-9,]+\.?[0-9]*)\s*([A-Z]{3})',
        r'([0-9,]+\.?[0-9]*)\s*MXN',
        r'(\$[0-9,]+\.?[0-9]*)',
    ]
    
    for pattern in total_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            print(f"✅ Pattern '{pattern}' found: {matches}")
        else:
            print(f"❌ Pattern '{pattern}' not found")
    
    return full_text

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 quick_pdf_parser.py <pdf_file>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    parse_pdf(pdf_file)