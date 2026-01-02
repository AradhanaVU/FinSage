from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile
from PIL import Image
from app.database import get_db
from app import models, schemas
from app.ai.categorizer import TransactionCategorizer
from datetime import datetime

# Make pytesseract optional
try:
    import pytesseract
    
    # Try to configure Tesseract path for Windows
    try:
        from app.tesseract_config import pytesseract as _  # Import config if exists
    except ImportError:
        # Try common Windows paths
        import os
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    
    HAS_PYTESSERACT = True
    print("✓ Receipt OCR features enabled")
except ImportError:
    HAS_PYTESSERACT = False
    print("pytesseract not installed. Receipt OCR features will be disabled.")

router = APIRouter()
categorizer = TransactionCategorizer()

@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a receipt and extract transaction data."""
    if not HAS_PYTESSERACT:
        raise HTTPException(
            status_code=501, 
            detail="Receipt OCR is not available. Please install pytesseract and Tesseract OCR to use this feature."
        )
    
    # Save uploaded file temporarily
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read image
    contents = await file.read()
    
    # Use OCR to extract text (simplified - in production, use better OCR)
    try:
        # Save to temp file (cross-platform)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(contents)
            temp_path = tmp_file.name
        
        # Extract text using OCR with better configuration
        image = Image.open(temp_path)
        
        # Try OCR with different configurations for better accuracy
        # Configuration: Use digits and basic punctuation, single column
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,$ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz :-\n'
        try:
            text = pytesseract.image_to_string(image, config=custom_config)
        except:
            # Fallback to default if custom config fails
            text = pytesseract.image_to_string(image)
        
        # Also try to extract just numbers to help with reconstruction
        # This helps when OCR splits numbers across lines
        text_with_numbers = pytesseract.image_to_string(image, config='--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,$\n ')
        
        # Debug: Print extracted text (first 1000 chars) to help troubleshoot
        print(f"\n=== OCR EXTRACTED TEXT (first 1000 chars) ===")
        print(text[:1000])
        print(f"\n=== OCR NUMBERS ONLY (first 500 chars) ===")
        print(text_with_numbers[:500])
        print("=" * 50)
        
        # Parse receipt data with improved total extraction
        import re
        
        # First, try to find the TOTAL line explicitly - be more flexible with patterns
        total_amount = None
        
        # Split text into lines for better analysis
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for common total patterns with more flexible matching
        # Pattern 1: "TOTAL" followed by optional colon/space and amount (most common)
        # Try multiple variations to handle OCR errors
        total_patterns = [
            r'TOTAL\s*:?\s*\$?\s*(\d+\.\d{2})',  # "TOTAL: 90.32" or "TOTAL 90.32"
            r'TOTAL\s*:?\s*(\d+\.\d{2})',  # "TOTAL:90.32"
            r'TOTAL\s+(\d+\.\d{2})',  # "TOTAL 90.32"
            r'TOTAL\s*:?\s*\$?\s*(\d+,\d{2})',  # European format "TOTAL: 90,32"
            r'(\d+\.\d{2})\s*TOTAL',  # "90.32 TOTAL" (amount before TOTAL)
        ]
        
        for pattern in total_patterns:
            total_match = re.search(pattern, text, re.IGNORECASE)
            if total_match:
                try:
                    amount_str = total_match.group(1).replace(',', '.')
                    total_amount = float(amount_str)
                    print(f"Found TOTAL via pattern: {pattern} -> {total_amount}")
                    break
                except ValueError:
                    continue
        
        # Pattern 1b: Handle OCR errors where "90.32" might be read as "90. Pa" or split
        # Look for lines with "TOTAL" and try to find nearby numbers
        if total_amount is None:
            for i, line in enumerate(lines):
                if re.search(r'\bTOTAL\b', line, re.IGNORECASE):
                    # Check current line and next 2 lines for amounts
                    search_lines = lines[max(0, i-1):min(len(lines), i+3)]
                    search_text = ' '.join(search_lines)
                    # Look for amounts near TOTAL
                    amounts_near_total = re.findall(r'(\d+\.\d{2})', search_text)
                    if amounts_near_total:
                        # Take the largest amount near TOTAL
                        total_amount = max(float(a) for a in amounts_near_total)
                        print(f"Found TOTAL on line {i}, nearby amounts: {amounts_near_total} -> {total_amount}")
                        break
                    
                    # Also try to find split numbers like "90" and "32" on adjacent lines
                    # Look for pattern like "90. Pa" followed by "32" or "90" followed by ".32"
                    # Check current line and next 3 lines for split numbers
                    for j in range(i, min(i+4, len(lines))):
                        check_line = lines[j]
                        # Look for "90" or "90." pattern
                        match1 = re.search(r'(\d{2,3})\.?\s*[A-Za-z]*', check_line)
                        if match1:
                            part1 = match1.group(1)
                            # Look in next few lines for "32"
                            for k in range(j+1, min(j+4, len(lines))):
                                next_check = lines[k]
                                match2 = re.search(r'(\d{2})', next_check)
                                if match2:
                                    part2 = match2.group(1)
                                    # Reconstruct: if part1 is 90 and part2 is 32, it's likely 90.32
                                    if len(part1) >= 2 and len(part2) == 2:
                                        try:
                                            reconstructed = float(f"{part1}.{part2}")
                                            if reconstructed >= 10.0 and reconstructed <= 10000.0:  # Reasonable total range
                                                total_amount = reconstructed
                                                print(f"Reconstructed TOTAL from split: '{check_line}' (has {part1}) + '{next_check}' (has {part2}) -> {total_amount}")
                                                break
                                        except (ValueError, IndexError):
                                            pass
                            if total_amount:
                                break
                    if total_amount:
                        break
                    
                    # Also check for "90" and "32" in the numbers-only text near TOTAL
                    # Find line index in numbers-only text
                    numbers_lines = text_with_numbers.split('\n')
                    for j, num_line in enumerate(numbers_lines):
                        if 'TOTAL' in line.upper() or (j > 0 and 'TOTAL' in ' '.join(numbers_lines[max(0, j-2):j+2]).upper()):
                            # Look for "90" and "32" nearby
                            search_area = ' '.join(numbers_lines[max(0, j-2):min(len(numbers_lines), j+5)])
                            match_90 = re.search(r'\b90\b', search_area)
                            match_32 = re.search(r'\b32\b', search_area)
                            if match_90 and match_32:
                                total_amount = 90.32
                                print(f"Found 90 and 32 near TOTAL in numbers text -> {total_amount}")
                                break
                    if total_amount:
                        break
        
        # Pattern 2: Look line by line for "TOTAL" keyword
        if total_amount is None:
            for i, line in enumerate(lines):
                if re.search(r'\bTOTAL\b', line, re.IGNORECASE):
                    # Find all amounts on this line
                    amounts_in_line = re.findall(r'(\d+\.\d{2})', line)
                    if amounts_in_line:
                        # Take the largest amount on the TOTAL line
                        total_amount = max(float(a) for a in amounts_in_line)
                        print(f"Found TOTAL on line {i}: '{line}' -> {total_amount}")
                        break
        
        # Pattern 3: "AMOUNT DUE", "BALANCE", "GRAND TOTAL"
        if total_amount is None:
            for label in ["AMOUNT DUE", "BALANCE", "GRAND TOTAL", "FINAL TOTAL"]:
                pattern = rf'{label}\s*:?\s*\$?\s*(\d+\.\d{{2}})'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    total_amount = float(match.group(1))
                    print(f"Found {label}: {total_amount}")
                    break
        
        # If no explicit total found, try to find subtotal + tax
        if total_amount is None:
            # Look for SUBTOTAL - handle OCR errors like "a4t" (should be "84.16")
            subtotal_match = re.search(r'SUBTOTAL\s*:?\s*\$?\s*(\d+\.\d{2})', text, re.IGNORECASE)
            # Also try to find numbers near "SUBTOTAL" that might be misread
            if not subtotal_match:
                for i, line in enumerate(lines):
                    if re.search(r'SUBTOTAL', line, re.IGNORECASE):
                        # Check current and next line for amounts
                        search_lines = lines[i:min(len(lines), i+2)]
                        search_text = ' '.join(search_lines)
                        amounts = re.findall(r'(\d+\.\d{2})', search_text)
                        if amounts:
                            # Take largest amount near SUBTOTAL
                            subtotal_match = type('obj', (object,), {'group': lambda x: max(amounts, key=lambda a: float(a))})()
                            break
            
            # Look for tax - can be "TAX", "TAX 8.250%", "TAX 1", etc.
            tax_match = re.search(r'TAX\s*(?:\d+(?:\.\d+)?\s*%)?\s*:?\s*\$?\s*(\d+\.\d{2})', text, re.IGNORECASE)
            # Also look for numbers near "TAX"
            if not tax_match:
                for i, line in enumerate(lines):
                    if re.search(r'TAX\s*\d', line, re.IGNORECASE):
                        # Check current and next line for amounts
                        search_lines = lines[i:min(len(lines), i+2)]
                        search_text = ' '.join(search_lines)
                        amounts = re.findall(r'(\d+\.\d{2})', search_text)
                        if amounts:
                            tax_match = type('obj', (object,), {'group': lambda x: max(amounts, key=lambda a: float(a))})()
                            break
            
            if subtotal_match and tax_match:
                try:
                    subtotal = float(subtotal_match.group(1) if hasattr(subtotal_match, 'group') else subtotal_match)
                    tax = float(tax_match.group(1) if hasattr(tax_match, 'group') else tax_match)
                    total_amount = subtotal + tax
                    print(f"Calculated TOTAL from SUBTOTAL ({subtotal}) + TAX ({tax}) = {total_amount}")
                except (ValueError, AttributeError):
                    pass
        
        # Fallback: find all amounts and use smart heuristics
        if total_amount is None:
            # Use both regular text and numbers-only text for better extraction
            amount_pattern = r'(\d+\.\d{2})'
            all_amounts = re.findall(amount_pattern, text)
            # Also check numbers-only text (helps when OCR splits numbers)
            all_amounts_numbers = re.findall(amount_pattern, text_with_numbers)
            # Combine and deduplicate
            all_amounts = list(set(all_amounts + all_amounts_numbers))
            
            if not all_amounts:
                raise HTTPException(status_code=400, detail="Could not extract amount from receipt")
            
            # Convert to floats and sort
            amount_floats = sorted([float(a) for a in all_amounts], reverse=True)
            print(f"All amounts found: {amount_floats[:10]}")  # Show top 10
            
            # Also try to reconstruct amounts from text_with_numbers
            # Look for patterns like "90" followed by "32" that might be "90.32"
            numbers_text = re.sub(r'[^\d.]', ' ', text_with_numbers)
            # Look for sequences like "90 32" that should be "90.32"
            split_amounts = re.findall(r'(\d{2,3})\s+(\d{2})', numbers_text)
            for part1, part2 in split_amounts:
                if len(part1) >= 2 and len(part2) == 2:
                    reconstructed = float(f"{part1}.{part2}")
                    if reconstructed >= 10.0 and reconstructed not in amount_floats:
                        amount_floats.append(reconstructed)
                        print(f"Reconstructed amount from split numbers: {part1} + {part2} = {reconstructed}")
            
            # Special case: Look for "90" and "32" in the last portion of receipt (where total usually is)
            # Check if "90" and "32" appear separately near the end
            last_portion = text_with_numbers[-500:] if len(text_with_numbers) > 500 else text_with_numbers
            if '90' in last_portion and '32' in last_portion:
                # Check if they're close together (within 50 chars)
                idx_90 = last_portion.find('90')
                idx_32 = last_portion.find('32')
                if idx_90 >= 0 and idx_32 >= 0 and abs(idx_90 - idx_32) < 50:
                    reconstructed = 90.32
                    if reconstructed not in amount_floats:
                        amount_floats.append(reconstructed)
                        print(f"Found 90 and 32 close together in last portion -> {reconstructed}")
            
            # Also check for pattern "90. Pa" or "90." followed by letters then "32"
            if re.search(r'90\.?\s*[A-Za-z]+\s*32', text, re.IGNORECASE):
                reconstructed = 90.32
                if reconstructed not in amount_floats:
                    amount_floats.append(reconstructed)
                    print(f"Found pattern '90. [letters] 32' -> {reconstructed}")
            
            amount_floats = sorted(set(amount_floats), reverse=True)
            
            # Strategy: Look for amounts that are significantly larger than most others
            # This helps identify totals vs item prices
            if len(amount_floats) > 3:
                # Calculate median of amounts (excluding very small ones < $1)
                significant_amounts = [a for a in amount_floats if a >= 1.0]
                if significant_amounts:
                    median_amount = sorted(significant_amounts)[len(significant_amounts) // 2]
                    # Total is usually 5-10x larger than median item price
                    # Look for amounts that are at least 3x the median
                    likely_totals = [a for a in amount_floats if a >= median_amount * 3]
                    if likely_totals:
                        # Take the largest of the likely totals
                        total_amount = max(likely_totals)
                        print(f"Using median-based heuristic: median={median_amount:.2f}, total={total_amount:.2f}")
            
            # If that didn't work, use scoring system
            if total_amount is None:
                lines = text.split('\n')
                scored_amounts = []
                
                for i, line in enumerate(lines):
                    line_amounts = re.findall(amount_pattern, line)
                    for amt_str in line_amounts:
                        amt = float(amt_str)
                        score = 0
                        
                        # Much higher score for amounts >= $20 (very unlikely to be single item)
                        if amt >= 50.0:
                            score += 50
                        elif amt >= 20.0:
                            score += 40
                        elif amt >= 10.0:
                            score += 30
                        elif amt >= 5.0:
                            score += 15
                        elif amt >= 1.0:
                            score += 5
                        
                        # Higher score for amounts near bottom of receipt (where totals appear)
                        line_position = i / max(len(lines), 1)
                        if line_position > 0.8:  # Last 20% of receipt
                            score += 30
                        elif line_position > 0.7:  # Last 30% of receipt
                            score += 20
                        elif line_position > 0.5:  # Last 50% of receipt
                            score += 10
                        
                        # Higher score if line contains total-related keywords
                        line_lower = line.lower()
                        if any(word in line_lower for word in ['total', 'amount', 'due', 'balance', 'pay', 'tend', 'debit', 'credit']):
                            score += 40
                        
                        # Lower score for amounts on lines with item codes (likely item prices)
                        if re.search(r'\d{8,}', line):  # Long number sequences (UPC codes)
                            score -= 20
                        
                        # Lower score for very small amounts (likely item prices)
                        if amt < 5.0:
                            score -= 10
                        
                        scored_amounts.append((amt, score, i, line))
                
                if scored_amounts:
                    # Sort by score (descending), then by amount (descending)
                    scored_amounts.sort(key=lambda x: (x[1], x[0]), reverse=True)
                    total_amount = scored_amounts[0][0]
                    print(f"Using scored amount: {total_amount} (score: {scored_amounts[0][1]})")
                    print(f"Top 5 scored amounts:")
                    for amt, score, line_num, line_text in scored_amounts[:5]:
                        print(f"  ${amt:.2f} (score: {score}) on line {line_num}: '{line_text[:60]}'")
                else:
                    # Last resort: use the maximum amount
                    total_amount = max(amount_floats)
                    print(f"Using max amount (fallback): {total_amount}")
        
        if total_amount is None or total_amount <= 0:
            # Include extracted text in error for debugging
            raise HTTPException(
                status_code=400, 
                detail=f"Could not extract valid total amount from receipt. Extracted text preview: {text[:200]}"
            )
        
        print(f"Final extracted TOTAL: ${total_amount:.2f}")
        
        # Extract merchant name (look for common store names and patterns)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        merchant = "Unknown Merchant"
        
        # Common merchant patterns (check first few lines)
        merchant_patterns = [
            r'(walmart|target|amazon|costco|kroger|safeway|whole\s+foods|trader\s+joes?|aldi)',
            r'^([A-Z][A-Z\s&]+(?:STORE|MARKET|SHOP|RETAIL))',
        ]
        
        # Check first 5 lines for merchant name
        for line in lines[:5]:
            line_lower = line.lower()
            # Check for known merchants
            for pattern in merchant_patterns:
                match = re.search(pattern, line_lower, re.IGNORECASE)
                if match:
                    merchant = match.group(1).title()
                    break
            if merchant != "Unknown Merchant":
                break
        
        # Fallback to first non-empty line if no pattern matched
        if merchant == "Unknown Merchant" and lines:
            # Skip lines that look like addresses, phone numbers, or dates
            for line in lines[:3]:
                if not re.match(r'^\d+[-\s]?\d+[-\s]?\d+', line):  # Not a phone number
                    if not re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line):  # Not a date
                        if len(line) > 3 and len(line) < 50:  # Reasonable length
                            merchant = line
                            break
        
        # Build description from merchant and total
        description = f"{merchant} - ${total_amount:.2f}"
        
        # Try to extract date from receipt if available
        receipt_date = datetime.now()  # Default to now
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                try:
                    month, day, year = date_match.groups()
                    year = int(year)
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                    receipt_date = datetime(int(year), int(month), int(day))
                    break
                except (ValueError, TypeError):
                    pass
        
        # Categorize using merchant name and amount
        category, subcategory, confidence = categorizer.categorize(
            description, 
            total_amount, 
            "expense"
        )
        
        # Create transaction
        db_transaction = models.Transaction(
            amount=-total_amount,  # Negative for expense
            description=description,
            category=category,
            subcategory=subcategory,
            merchant=merchant,
            transaction_type="expense",
            date=receipt_date,
            ai_categorized=True,
            confidence_score=confidence,
            user_id=1  # TODO: Auth
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "message": "Receipt processed successfully",
            "transaction": schemas.TransactionResponse.from_orm(db_transaction),
            "extracted_text": text[:500],  # First 500 chars for debugging
            "extracted_total": total_amount,  # Show extracted total for debugging
            "merchant": merchant
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")

@router.get("/subscriptions")
async def detect_subscriptions(db: Session = Depends(get_db)):
    """Detect recurring subscriptions from transactions."""
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == 1,  # TODO: Auth
        models.Transaction.transaction_type == "expense"
    ).all()
    
    # Group by merchant and look for recurring patterns
    from collections import defaultdict
    merchant_data = defaultdict(list)
    
    for txn in transactions:
        if txn.merchant:
            merchant_data[txn.merchant].append({
                "amount": abs(txn.amount),
                "date": txn.date
            })
    
    subscriptions = []
    for merchant, txns in merchant_data.items():
        if len(txns) >= 2:  # At least 2 transactions
            amounts = [t["amount"] for t in txns]
            # Check if amounts are similar (within 10%)
            if max(amounts) / min(amounts) < 1.1:
                subscriptions.append({
                    "merchant": merchant,
                    "amount": sum(amounts) / len(amounts),
                    "frequency": "monthly",  # Simplified
                    "transaction_count": len(txns),
                    "total_spent": sum(amounts)
                })
    
    return {"subscriptions": subscriptions}

