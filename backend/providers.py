import random
from typing import List, Dict, Any

class CameraProvider:
    def capture_views(self, barcode: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Captures 5 views of the product packaging.
        Returns:
            List of dicts containing view_name, image_path, quality_status
        """
        raise NotImplementedError

class SimulatedCameraProvider(CameraProvider):
    def capture_views(self, barcode: str, session_id: str, force_perfect: bool = False) -> List[Dict[str, Any]]:
        views = ["FRONT", "BACK", "LEFT", "RIGHT", "TOP"]
        results = []
        
        # Determine if we should simulate a quality failure to show the E2E operator check
        # Let's say Product D (repeat offender barcode 8901000000003 or random) has a glare issue on RIGHT camera
        fail_view = None
        if not force_perfect:
            if barcode == "8901000000003":  # Bharti Moisturizer
                fail_view = "RIGHT" # Glare
            elif barcode == "8901000000007": # Deccan Pilsner
                fail_view = "LEFT" # Blur
                
        for view in views:
            q_status = "GOOD"
            if view == fail_view:
                q_status = "GLARE" if view == "RIGHT" else "BLUR"
                
            results.append({
                "camera_view": view,
                "image_path": f"/static/images/demo/{barcode}_{view.lower()}.jpg",
                "quality_status": q_status
            })
        return results

class OCRProvider:
    def extract_text(self, barcode: str, camera_view: str) -> List[Dict[str, Any]]:
        """
        Runs OCR on a specific image view.
        Returns list of bounding box OCR results.
        """
        raise NotImplementedError

class DemoOCRProvider(OCRProvider):
    def __init__(self):
        # Seeded products OCR lookup data
        self.ocr_database = {
            "8901000000001": { # Apex Digestive Biscuits 500g
                "FRONT": [
                    {"field": "brand", "text": "APEX DIGESTIVE", "confidence": 98.2, "box": "50,120,400,60"},
                    {"field": "net_qty", "text": "NET QTY: 500g", "confidence": 97.4, "box": "200,450,150,30"}
                ],
                "BACK": [
                    {"field": "mrp", "text": "MRP Rs. 150.00 (Incl. of all taxes)", "confidence": 98.5, "box": "40,80,320,40"},
                    {"field": "packed_date", "text": "Pkd: 05/2026", "confidence": 96.1, "box": "40,140,180,30"},
                    {"field": "manufacturer_name", "text": "Mfg by: Apex Foods Ltd, Gurugram, Haryana", "confidence": 94.7, "box": "40,200,450,50"},
                    {"field": "consumer_care_phone", "text": "Consumer care cell: 1800-000-0000, feedback@apexfoods.com", "confidence": 95.2, "box": "40,280,480,40"}
                ],
                "LEFT": [
                    {"field": "nutrition", "text": "Energy 480 kcal, Protein 6g, Fat 18g", "confidence": 90.0, "box": "20,50,300,150"}
                ],
                "RIGHT": [
                    {"field": "ingredients", "text": "Wheat Flour, Sugar, Vegetable Oil, Fiber", "confidence": 92.5, "box": "15,80,350,120"}
                ],
                "TOP": [
                    {"field": "brand_logo", "text": "APEX", "confidence": 99.0, "box": "100,50,200,100"}
                ]
            },
            "8901000000003": { # Bharti Moisturizing Cream 200ml
                "FRONT": [
                    {"field": "brand", "text": "BHARTI MOISTURIZER", "confidence": 99.1, "box": "40,150,350,50"},
                    {"field": "net_qty", "text": "Net Vol: 200 ml", "confidence": 98.3, "box": "150,420,180,35"}
                ],
                "BACK": [
                    {"field": "mrp", "text": "Max. Retail Price: ₹249.00", "confidence": 97.9, "box": "30,90,280,38"},
                    {"field": "packed_date", "text": "Packed: 05/2026", "confidence": 95.8, "box": "30,150,190,32"},
                    {"field": "manufacturer_name", "text": "Mfd by Bharti Cosmetics Ltd, Okhla, New Delhi", "confidence": 93.6, "box": "30,210,420,45"},
                    # SIMULATE VIOLATION: Missing Consumer Care details on back (Not detected)
                    {"field": "consumer_care_phone", "text": "For feedback write to info@bharticosmetics.com", "confidence": 92.0, "box": "30,290,390,30"}
                ],
                "LEFT": [
                    {"field": "usage", "text": "Apply daily to face and neck.", "confidence": 96.0, "box": "10,60,250,80"}
                ],
                "RIGHT": [
                    {"field": "ingredients", "text": "Aqua, Glycerin, Stearic Acid, Fragrance", "confidence": 91.0, "box": "10,80,300,110"}
                ],
                "TOP": [
                    {"field": "logo", "text": "BHARTI", "confidence": 98.5, "box": "80,30,150,60"}
                ]
            },
            "8901000000007": { # Deccan Premium Pilsner Beer 650ml
                "FRONT": [
                    {"field": "brand", "text": "DECCAN PREMIUM PILSNER", "confidence": 97.8, "box": "30,110,380,55"},
                    {"field": "net_qty", "text": "Net Qty: 650 ml", "confidence": 98.1, "box": "120,400,160,30"}
                ],
                "BACK": [
                    {"field": "mrp", "text": "MRP ₹180/- (incl all taxes)", "confidence": 98.4, "box": "35,80,260,35"},
                    {"field": "packed_date", "text": "Packed Date: 05/2026", "confidence": 96.5, "box": "35,130,200,30"},
                    {"field": "manufacturer_name", "text": "Brewed & Bottled by: Deccan Breweries, Pune", "confidence": 95.0, "box": "35,180,410,48"},
                    # SIMULATE VIOLATION: Missing Consumer Care
                    {"field": "consumer_care_phone", "text": "Not Detected", "confidence": 10.0, "box": "0,0,0,0"}
                ],
                "LEFT": [
                    {"field": "warnings", "text": "CONSUMPTION OF ALCOHOL IS INJURIOUS TO HEALTH", "confidence": 99.0, "box": "10,40,280,80"}
                ],
                "RIGHT": [
                    {"field": "details", "text": "Alcohol content: v/v 5%", "confidence": 95.0, "box": "10,70,250,50"}
                ],
                "TOP": [
                    {"field": "logo", "text": "DECCAN", "confidence": 97.0, "box": "80,40,160,50"}
                ]
            }
        }

    def extract_text(self, barcode: str, camera_view: str) -> List[Dict[str, Any]]:
        # Fallback for dynamic/other barcodes
        if barcode not in self.ocr_database:
            return self.generate_generic_ocr(barcode, camera_view)
        
        return self.ocr_database[barcode].get(camera_view, [])

    def generate_generic_ocr(self, barcode: str, camera_view: str) -> List[Dict[str, Any]]:
        # Generate clean standard OCR facts dynamically if it's not a pre-seeded target
        if camera_view == "FRONT":
            return [
                {"field": "brand", "text": f"GENERIC BRAND {barcode[-4:]}", "confidence": 95.0, "box": "40,100,350,50"},
                {"field": "net_qty", "text": "NET QUANTITY: 250 g", "confidence": 96.0, "box": "150,400,180,30"}
            ]
        elif camera_view == "BACK":
            return [
                {"field": "mrp", "text": "MRP Rs. 199.00 (Incl. of all taxes)", "confidence": 97.0, "box": "30,80,300,40"},
                {"field": "packed_date", "text": "Packed: 06/2026", "confidence": 95.0, "box": "30,140,200,30"},
                {"field": "manufacturer_name", "text": "Mfg By: Pioneer Foods India, Pune, Maharashtra", "confidence": 94.0, "box": "30,200,400,50"},
                {"field": "consumer_care_phone", "text": "Helpline: 1800-222-3333, help@pioneerfoods.in", "confidence": 93.0, "box": "30,270,450,40"},
                {"field": "country_of_origin", "text": "Country of Origin: India", "confidence": 96.0, "box": "30,340,250,30"}
            ]
        return []

class ProductIdentificationProvider:
    def identify_product(self, barcode: str) -> Dict[str, Any]:
        raise NotImplementedError

class DemoProductIdentificationProvider(ProductIdentificationProvider):
    def identify_product(self, barcode: str) -> Dict[str, Any]:
        # Scans the database metadata lookup
        return {
            "barcode": barcode,
            "identified": True,
            "source": "INTERNAL_REGISTRY_FINGERPRINT"
        }
