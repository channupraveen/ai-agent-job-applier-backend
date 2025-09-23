# Fixed regex patterns for name and phone extraction

import re

def extract_name_fixed(text):
    """Extract name from resume text - Fixed version"""
    # Remove invisible Unicode characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    # Look for name at the beginning followed by contact info
    name_patterns = [
        r'^([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)(?=\s+Phone:|\s+Email:|\s+Location:)',
        r'^([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)(?=\s)',
        r'^([A-Z][A-Z\s]+)(?=\s+Phone:|\s+Email:)'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Validate it's actually a name
            if re.match(r'^[A-Za-z\s]+$', name) and 2 <= len(name.split()) <= 4:
                return name
    return ""

def extract_phone_fixed(text):
    """Extract phone number - Fixed version"""
    # Remove invisible Unicode characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    # Enhanced phone patterns
    phone_patterns = [
        r'Phone:\s*([\+]?[\d\s\-\(\)\.]{7,15})',  # Phone: 8106775767
        r'Phone\s*[:\-]\s*([\+]?[\d\s\-\(\)\.]{7,15})',  # Phone - 8106775767
        r'(?:Mobile|Cell|Tel):\s*([\+]?[\d\s\-\(\)\.]{7,15})',  # Mobile: numbers
        r'(\d{10})',  # Direct 10 digit numbers
        r'([\+]?\d{1,3}[\s\-]?\(?\d{3}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4})'  # International formats
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                phone = re.sub(r'[^\d\+\(\)\-\s]', '', match)
                if len(re.sub(r'[^\d]', '', phone)) >= 7:  # At least 7 digits
                    return phone.strip()
    return ""

# Test with your actual text
test_text = "CHANNU PRAVEEN KUMAR Phone: 8106775767​ Email: channupraveen66@gmail.com​ Location: Hyderabad, Telangana Professional Summary Full Stack Developer"

print("Testing fixed extraction:")
print(f"Name: '{extract_name_fixed(test_text)}'")
print(f"Phone: '{extract_phone_fixed(test_text)}'")
