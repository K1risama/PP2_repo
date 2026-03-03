import re
import json
from typing import List, Dict, Any

class ReceiptParser:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.lines = raw_text.split('\n')
    
    def extract_prices(self) -> List[float]:
        """Extract all prices from the receipt"""
        # Pattern for prices: numbers with optional spaces and commas, followed by ,00
        # Handles formats like 154,00, 1 200,00, 7 330,00
        price_pattern = r'(\d+(?:\s\d+)*,\d{2})'
        prices = []
        
        for line in self.lines:
            matches = re.findall(price_pattern, line)
            for match in matches:
                # Remove spaces and convert comma to dot for float conversion
                clean_price = match.replace(' ', '').replace(',', '.')
                try:
                    price = float(clean_price)
                    prices.append(price)
                except ValueError:
                    continue
        
        return prices
    
    def extract_product_names(self) -> List[str]:
        """Extract all product names from numbered items"""
        product_names = []
        # Pattern for product lines: number followed by dot and product name
        # Stops before quantity (which has pattern like 1,000 x)
        product_pattern = r'^\d+\.\s*(.+?)(?=\s+\d+,\d{3}\s+x|$)'
        
        for line in self.lines:
            match = re.match(product_pattern, line.strip())
            if match:
                product_name = match.group(1).strip()
                # Skip if it's just a number or empty
                if product_name and not product_name.isdigit():
                    product_names.append(product_name)
        
        return product_names
    
    def calculate_total(self) -> float:
        """Extract the total amount from the receipt"""
        # Pattern for total amount line
        total_pattern = r'ИТОГО:\s*(\d+(?:\s\d+)*,\d{2})'
        
        for line in self.lines:
            match = re.search(total_pattern, line)
            if match:
                total_str = match.group(1).replace(' ', '').replace(',', '.')
                return float(total_str)
        
        return 0.0
    
    def extract_datetime(self) -> Dict[str, str]:
        """Extract date and time information"""
        datetime_pattern = r'Время:\s*(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})'
        
        for line in self.lines:
            match = re.search(datetime_pattern, line)
            if match:
                return {
                    'date': match.group(1),
                    'time': match.group(2)
                }
        
        return {'date': '', 'time': ''}
    
    def extract_payment_method(self) -> str:
        """Extract payment method"""
        payment_patterns = [
            (r'Банковская карта', 'Card'),
            (r'Наличные', 'Cash'),
            (r'Банковская карта:', 'Card')  # From the receipt format
        ]
        
        for line in self.lines:
            for pattern, method in payment_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return method
        
        return 'Unknown'
    
    def extract_items_with_prices(self) -> List[Dict[str, Any]]:
        """Extract items with their quantities, unit prices, and total prices"""
        items = []
        current_item = {}
        
        for i, line in enumerate(self.lines):
            # Check for item number (start of new item)
            item_num_match = re.match(r'^(\d+)\.\s*(.+)$', line.strip())
            if item_num_match:
                if current_item:
                    items.append(current_item)
                
                current_item = {
                    'number': int(item_num_match.group(1)),
                    'name': item_num_match.group(2).strip(),
                    'quantity': 0.0,
                    'unit_price': 0.0,
                    'total_price': 0.0
                }
            
            # Extract quantity and unit price (format: 2,000 x 154,00)
            quantity_match = re.search(r'(\d+,\d{3})\s*x\s*(\d+(?:\s\d+)*,\d{2})', line)
            if quantity_match and current_item:
                quantity_str = quantity_match.group(1).replace(',', '.')
                unit_price_str = quantity_match.group(2).replace(' ', '').replace(',', '.')
                current_item['quantity'] = float(quantity_str)
                current_item['unit_price'] = float(unit_price_str)
            
            # Extract total price (format: 308,00)
            total_price_match = re.search(r'^(\d+(?:\s\d+)*,\d{2})$', line.strip())
            if total_price_match and current_item and current_item['total_price'] == 0.0:
                total_price_str = total_price_match.group(1).replace(' ', '').replace(',', '.')
                current_item['total_price'] = float(total_price_str)
        
        # Add the last item
        if current_item:
            items.append(current_item)
        
        return items
    
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
            elif 'Фискальный признак' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    receipt_info['fiscal_sign'] = match.group(1)
        return receipt_info
    
    def parse(self) -> Dict[str, Any]:
        """Parse all information and return structured data"""
        
        # Extract all information
        items = self.extract_items_with_prices()
        product_names = self.extract_product_names()
        prices = self.extract_prices()
        total = self.calculate_total()
        datetime_info = self.extract_datetime()
        payment_method = self.extract_payment_method()
        store_info = self.extract_store_info()
        receipt_numbers = self.extract_receipt_numbers()
        
        # Calculate summary statistics
        subtotal = sum(item['total_price'] for item in items)
        item_count = len(items)
        
        return {
            'store': store_info,
            'receipt': receipt_numbers,
            'datetime': datetime_info,
            'payment': {
                'method': payment_method,
                'total': total
            },
            'items': items,
            'summary': {
                'item_count': item_count,
                'product_names': product_names[:10],  # First 10 products
                'total_unique_products': len(product_names),
                'subtotal': subtotal,
                'total': total
            },
            'debug': {
                'prices_found': len(prices),
                'product_names_found': len(product_names)
            }
        }
    
    def to_json(self) -> str:
        """Convert parsed data to JSON string"""
        data = self.parse()
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def to_formatted_text(self) -> str:
        """Convert parsed data to readable formatted text"""
        data = self.parse()
        
        output = []
        output.append("=" * 60)
        output.append("RECEIPT PARSER OUTPUT".center(60))
        output.append("=" * 60)
        
        # Store info
        if data['store']:
            output.append("\n STORE INFORMATION:")
            for key, value in data['store'].items():
                output.append(f"   {key.capitalize()}: {value}")
        
        # Receipt info
        if data['receipt']:
            output.append("\n RECEIPT INFORMATION:")
            for key, value in data['receipt'].items():
                output.append(f"   {key.replace('_', ' ').capitalize()}: {value}")
        
        # Date and time
        output.append(f"\n DATE: {data['datetime']['date']}")
        output.append(f" TIME: {data['datetime']['time']}")
        
        # Payment
        output.append(f"\n PAYMENT METHOD: {data['payment']['method']}")
        output.append(f" TOTAL AMOUNT: {data['payment']['total']:.2f}")
        
        # Items
        output.append(f"\n PURCHASED ITEMS ({data['summary']['item_count']}):")
        output.append("-" * 60)
        for item in data['items']:
            output.append(f"{item['number']}. {item['name']}")
            output.append(f"   {item['quantity']:.3f} x {item['unit_price']:.2f} = {item['total_price']:.2f}")
        
        # Summary
        output.append("-" * 60)
        output.append(f"\n SUMMARY:")
        output.append(f"   Subtotal: {data['summary']['subtotal']:.2f}")
        output.append(f"   Total: {data['summary']['total']:.2f}")
        output.append(f"   Unique products: {data['summary']['total_unique_products']}")
        
        # Product list
        output.append(f"\n PRODUCT LIST (first 10):")
        for i, name in enumerate(data['summary']['product_names'], 1):
            output.append(f"   {i}. {name}")
        
        output.append("\n" + "=" * 60)
        
        return '\n'.join(output)


def main():
    """Main function to run the receipt parser"""
    try:
        # Read the raw.txt file
        with open('raw.txt', 'r', encoding='utf-8') as file:
            raw_text = file.read()
        
        # Parse the receipt
        parser = ReceiptParser(raw_text)
        
        # Output in formatted text
        print(parser.to_formatted_text())
        
        # Save JSON output
        with open('receipt_output.json', 'w', encoding='utf-8') as json_file:
            json_file.write(parser.to_json())
        
        print("\n JSON output saved to receipt_output.json")
        
        # Also save as text file
        with open('receipt_output.txt', 'w', encoding='utf-8') as text_file:
            text_file.write(parser.to_formatted_text())
        
        print("✅ Text output saved to receipt_output.txt")
        
    except FileNotFoundError:
        print("Error: raw.txt file not found in the current directory")
    except Exception as e:
        print(f"Error parsing receipt: {e}")


if __name__ == "__main__":
    main()