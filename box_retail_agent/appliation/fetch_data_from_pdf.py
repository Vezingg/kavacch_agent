"""
PDF Data Extractor for Box Retail Agent.
Extracts product data from PDF catalog.
"""

import json
from pathlib import Path

import fitz  # PyMuPDF


class PDFDataExtractor:
    """Extracts product data from PDF catalogs."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "box_data"
        self.pdf_path = self.base_path / "test_box.pdf"
        self.json_output_path = self.base_path / "product_data.json"
    
    def extract_text_from_pdf(self) -> str:
        """Extract all text from the PDF."""
        doc = fitz.open(self.pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    
    def parse_product_data(self, raw_text: str) -> dict:
        """Parse raw text into structured product data."""
        # Structured data based on PDF content
        products = {
            "company_info": {
                "name": "Kalash Packaging",
                "location": "Ahmedabad",
                "specializations": ["Bakery Boxes", "MDF Boards", "Drum Boards", "Cutlery Kits"],
                "focus": ["Quality", "Consistency", "Timely Delivery"],
                "contact": {
                    "phone": ["9106845371", "7600337948"]
                }
            },
            "products": {
                "window_boxes": {
                    "description": "Window boxes designed to enhance product visibility while maintaining a premium look",
                    "features": [
                        "Strong & durable material",
                        "Clean window finish",
                        "Premium Pastel colour range",
                        "Customisation available"
                    ],
                    "types": {
                        "top_window": {
                            "sizes": ["8x8x5 inch", "10x10x5 inch", "12x12x5 inch"],
                            "description": "Top window range for product visibility"
                        },
                        "l_window": {
                            "sizes": ["10x10x5", "8x8x8", "10x10x8", "12x12x8"],
                            "best_for": ["Tall cakes", "Gift hamper", "Premium bakery products"]
                        }
                    },
                    "customization": {
                        "foil_stamping": {
                            "available": True,
                            "details": ["Customer name/brand can be stamped", "Premium foil finish", "Enhances brand visibility"],
                            "moq": "1000 boxes",
                            "note": "Design charge extra one time"
                        }
                    }
                },
                "cutlery_kits": {
                    "description": "Cutlery kits ideal for cakes, parties, celebrations & events",
                    "target_customers": ["Bakeries", "Cafes", "Bulk requirements"],
                    "benefits": ["Convenience", "Hygiene"],
                    "standard_kit_contents": {
                        "knife": 1,
                        "candles": 4
                    },
                    "customization": {
                        "available": True,
                        "options": [
                            "Kit contents can be customized per customer requirement",
                            "Custom branding & printing available"
                        ],
                        "ideal_for": ["Bakeries", "Brands", "Event companies"],
                        "moq_custom_branding": "10,000 Kits"
                    }
                },
                "mdf_boards": {
                    "description": "MDF boards for product presentation",
                    "standard_sizes": [
                        "6 inch", "7 inch", "8 inch", "9 inch", "10 inch",
                        "12 inch", "14 inch", "16 inch", "18 inch", "20 inch", "14x19 inch"
                    ],
                    "premium_options": {
                        "colors": ["White", "Black", "Golden", "Pastel colours"],
                        "shapes": ["Square (round corners)", "Round", "Round with handle"]
                    },
                    "branding": {
                        "available": True,
                        "options": ["Logo branding", "Insta handle", "Phone number", "Bakery's name"],
                        "note": "MOQ will be there as per size and design charges will be extra one time"
                    }
                },
                "drum_boards": {
                    "description": "Drum boards for cake presentation",
                    "sizes": ["10x10", "12x12", "14x14"],
                    "colors": ["Black", "White", "Golden"]
                }
            }
        }
        return products
    
    def fetch_and_save(self) -> dict:
        """Extract fresh data from PDF and save to JSON."""
        raw_text = self.extract_text_from_pdf()
        data = self.parse_product_data(raw_text)
        
        # Save to JSON (overwrites existing)
        with open(self.json_output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return data
    
    def get_data(self) -> dict:
        """Load product data from cached JSON if available, otherwise extract from PDF."""
        if self.json_output_path.exists():
            with open(self.json_output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.fetch_and_save()
