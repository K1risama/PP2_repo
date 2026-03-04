import re
import json
from typing import List, Dict, Any

class ReceiptParser:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.lines = raw_text.split('\n')
    
    def extract_all_items(self) -> List[Dict[str, Any]]:
        """Extract all items with their numbers, names, quantities and prices"""
        items = []
        current_item = None
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i].strip()
            
            # Check for item number (start of new item)
            item_num_match = re.match(r'^(\d+)\.$', line)
            if item_num_match:
                # Save previous item if exists
                if current_item:
                    items.append(current_item)
                
                item_number = int(item_num_match.group(1))
                
                # Next line contains the product name
                if i + 1 < len(self.lines):
                    product_name = self.lines[i + 1].strip()
                    
                    # Initialize new item
                    current_item = {
                        'number': item_number,
                        'name': product_name,
                        'quantity': 0.0,
                        'unit_price': 0.0,
                        'total_price': 0.0
                    }
                    
                    # Look for quantity and price (usually 2 lines after product name)
                    if i + 2 < len(self.lines):
                        qty_line = self.lines[i + 2].strip()
                        # Match pattern like "2,000 x 154,00" or "1,000 x 51,00"
                        qty_match = re.search(r'(\d+,\d{3})\s*x\s*(\d+(?:\s\d+)*,\d{2})', qty_line)
                        if qty_match:
                            quantity_str = qty_match.group(1).replace(',', '.')
                            unit_price_str = qty_match.group(2).replace(' ', '').replace(',', '.')
                            current_item['quantity'] = float(quantity_str)
                            current_item['unit_price'] = float(unit_price_str)
                    
                    # Look for total price (usually 3 lines after product name)
                    if i + 3 < len(self.lines):
                        total_line = self.lines[i + 3].strip()
                        # Match pattern like "308,00" or "51,00"
                        total_match = re.search(r'^(\d+(?:\s\d+)*,\d{2})$', total_line)
                        if total_match:
                            total_price_str = total_match.group(1).replace(' ', '').replace(',', '.')
                            current_item['total_price'] = float(total_price_str)
                    
                    # Skip ahead to avoid reprocessing the same lines
                    i += 3
            i += 1
        
        # Add the last item
        if current_item:
            items.append(current_item)
        
        return items
    
    def extract_total_amount(self) -> float:
        """Extract the total amount from the receipt"""
        for line in self.lines:
            if 'ИТОГО:' in line:
                match = re.search(r'ИТОГО:\s*(\d+(?:\s\d+)*,\d{2})', line)
                if match:
                    total_str = match.group(1).replace(' ', '').replace(',', '.')
                    return float(total_str)
        return 0.0
    
    def extract_payment_info(self) -> Dict[str, Any]:
        """Extract payment method and card payment amount"""
        payment_info = {
            'method': 'Unknown',
            'card_amount': 0.0
        }
        
        for i, line in enumerate(self.lines):
            if 'Банковская карта:' in line:
                payment_info['method'] = 'Card'
                # Look for amount on the same line or next line
                amount_match = re.search(r'(\d+(?:\s\d+)*,\d{2})', line)
                if amount_match:
                    amount_str = amount_match.group(1).replace(' ', '').replace(',', '.')
                    payment_info['card_amount'] = float(amount_str)
                elif i + 1 < len(self.lines):
                    next_line = self.lines[i + 1].strip()
                    amount_match = re.search(r'^(\d+(?:\s\d+)*,\d{2})$', next_line)
                    if amount_match:
                        amount_str = amount_match.group(1).replace(' ', '').replace(',', '.')
                        payment_info['card_amount'] = float(amount_str)
        
        return payment_info
    
    def extract_datetime(self) -> Dict[str, str]:
        """Extract date and time information"""
        for line in self.lines:
            if 'Время:' in line:
                match = re.search(r'Время:\s*(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})', line)
                if match:
                    return {
                        'date': match.group(1),
                        'time': match.group(2)
                    }
        return {'date': '', 'time': ''}
    
    def extract_store_info(self) -> Dict[str, str]:
        """Extract store/branch information"""
        store_info = {}
        
        for line in self.lines:
            if 'Филиал' in line:
                store_info['branch'] = line.strip()
            elif 'БИН' in line:
                store_info['bin'] = line.replace('БИН', '').strip()
            elif 'г.' in line and 'Казахстан' in line:
                store_info['address'] = line.strip()
        
        return store_info
    
    def extract_receipt_numbers(self) -> Dict[str, str]:
        """Extract various receipt numbers"""
        receipt_info = {}
        
        for line in self.lines:
            if 'Чек №' in line and 'Порядковый' not in line:
                receipt_info['receipt_number'] = line.replace('Чек №', '').strip()
            elif 'Порядковый номер чека' in line:
                match = re.search(r'№(\d+)', line)
                if match:
                    receipt_info['order_number'] = match.group(1)
            elif 'Фискальный признак:' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    receipt_info['fiscal_sign'] = match.group(1)
        
        return receipt_info
    
    def parse(self) -> Dict[str, Any]:
        """Parse all information and return structured data"""
        
        # Extract all information
        items = self.extract_all_items()
        total_amount = self.extract_total_amount()
        payment_info = self.extract_payment_info()
        datetime_info = self.extract_datetime()
        store_info = self.extract_store_info()
        receipt_numbers = self.extract_receipt_numbers()
        
        # Calculate totals
        items_total = sum(item['total_price'] for item in items)
        
        # Print debug information
        print(f"Debug: Found {len(items)} items")
        print(f"Debug: Items total = {items_total}")
        print(f"Debug: Receipt total = {total_amount}")
        
        return {
            'store': store_info,
            'receipt': receipt_numbers,
            'datetime': datetime_info,
            'payment': payment_info,
            'items': items,
            'totals': {
                'items_sum': items_total,
                'total_amount': total_amount,
                'item_count': len(items)
            }
        }
    
    def to_formatted_text(self) -> str:
        """Convert parsed data to readable formatted text"""
        data = self.parse()
        
        output = []
        output.append("=" * 100)
        output.append("RECEIPT DETAILS".center(100))
        output.append("=" * 100)
        
        # Store info
        if data['store']:
            output.append("\nSTORE INFORMATION:")
            for key, value in data['store'].items():
                output.append(f"  {key.capitalize()}: {value}")
        
        # Receipt info
        if data['receipt']:
            output.append("\nRECEIPT NUMBERS:")
            for key, value in data['receipt'].items():
                output.append(f"  {key.replace('_', ' ').capitalize()}: {value}")
        
        # Date and time
        if data['datetime']['date']:
            output.append(f"\nDATE: {data['datetime']['date']}")
            output.append(f"TIME: {data['datetime']['time']}")
        
        # Items table header
        output.append("\n" + "=" * 100)
        output.append("ITEMS PURCHASED:")
        output.append("-" * 100)
        output.append(f"{'No.':<4} {'Product Name':<55} {'Quantity':<12} {'Unit Price':<12} {'Item Total':<12}")
        output.append("-" * 100)
        
        # Items
        for item in data['items']:
            # Truncate long names
            name = item['name'][:55] if len(item['name']) > 55 else item['name']
            output.append(f"{item['number']:<4} {name:<55} {item['quantity']:<12.3f} {item['unit_price']:<12.2f} {item['total_price']:<12.2f}")
        
        # Totals
        output.append("-" * 100)
        output.append(f"{'':<71} {'SUBTOTAL:':<12} {data['totals']['items_sum']:.2f}")
        output.append(f"{'':<71} {'TOTAL:':<12} {data['totals']['total_amount']:.2f}")
        
        # Payment info
        if data['payment']['method'] != 'Unknown':
            output.append(f"\nPAYMENT METHOD: {data['payment']['method']}")
            if data['payment']['card_amount'] > 0:
                output.append(f"  Card amount: {data['payment']['card_amount']:.2f}")
        
        # Final summary
        output.append("\n" + "=" * 100)
        output.append("FINAL RECEIPT SUMMARY".center(100))
        output.append("-" * 100)
        output.append(f"Total Items: {data['totals']['item_count']}")
        output.append(f"Subtotal (Sum of all items): {data['totals']['items_sum']:.2f}")
        output.append(f"Final Total (from receipt): {data['totals']['total_amount']:.2f}")
        
        # Verification
        if abs(data['totals']['items_sum'] - data['totals']['total_amount']) < 0.01:
            output.append("\n✓ VERIFICATION: Items sum matches receipt total")
        else:
            output.append(f"\n⚠ VERIFICATION: Items sum ({data['totals']['items_sum']:.2f}) differs from receipt total ({data['totals']['total_amount']:.2f})")
        
        output.append("=" * 100)
        
        return '\n'.join(output)
    
    def to_json(self) -> str:
        """Convert parsed data to JSON string"""
        data = self.parse()
        return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    """Main function to run the receipt parser"""
    try:
        # Read the raw.txt file
        with open('raw.txt', 'r', encoding='utf-8') as file:
            raw_text = file.read()
        
        # Print raw text preview
        print("Raw text preview (first 500 chars):")
        print(raw_text[:500])
        print("\n" + "=" * 50 + "\n")
        
        # Parse the receipt
        parser = ReceiptParser(raw_text)
        
        # Output formatted text to console
        print(parser.to_formatted_text())
        
        # Save JSON output
        with open('receipt_output.json', 'w', encoding='utf-8') as json_file:
            json_file.write(parser.to_json())
        print("\nJSON output saved to receipt_output.json")
        
        # Save formatted text
        with open('receipt_output.txt', 'w', encoding='utf-8') as text_file:
            text_file.write(parser.to_formatted_text())
        print("Text output saved to receipt_output.txt")
        
    except FileNotFoundError:
        print("Error: raw.txt file not found in the current directory")
    except Exception as e:
        print(f"Error parsing receipt: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()