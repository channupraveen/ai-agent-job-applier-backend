    def _extract_name(self, lines: List[str]) -> str:
        """Extract name from the first few lines"""
        # Combine all text to handle single-line extraction
        full_text = ' '.join(lines)
        
        # Remove invisible Unicode characters
        full_text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', full_text)
        
        # Look for name patterns at the beginning
        name_patterns = [
            r'^([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)(?=\s+Phone:|\s+Email:|\s+Location:)',
            r'^([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)(?=\s)',
            r'^([A-Z][A-Z\s]+)(?=\s+Phone:|\s+Email:)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, full_text)
            if match:
                name = match.group(1).strip()
                # Validate it's actually a name
                if re.match(r'^[A-Za-z\s]+$', name) and 2 <= len(name.split()) <= 4:
                    return name
        
        # Fallback: look in individual lines  
        clean_lines = [line.strip() for line in lines[:5] if line.strip()]
        for line in clean_lines:
            # Remove invisible characters
            line = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', line)
            if (line and 
                not self.email_pattern.search(line) and 
                not self.phone_pattern.search(line) and
                not any(word.lower() in line.lower() for word in ['phone', 'email', 'location', 'address', 'summary']) and
                len(line.split()) >= 2 and len(line.split()) <= 5 and
                len(line) > 5 and len(line) < 50 and
                re.match(r'^[A-Za-z\s]+$', line)):
                return line
        return ""
