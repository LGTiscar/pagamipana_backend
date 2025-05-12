from app.infrastructure.llm.OcrInput import OcrInput


class OcrTicketInput(OcrInput):
    def __init__(self):
        self.system_prompt = """
            You are an expert at analyzing restaurant receipts. 
                
            Please carefully examine this receipt image and extract:
            1. All individual menu items with their exact names, quantities, unit prices, and total prices
            2. The total amount of the bill
            
            Format your response as a clean JSON object with this exact structure:
            {
            "items": [
              {"name": "Item Name 1", "quantity": 2, "unitPrice": 10.99, "totalPrice": 21.98},
              {"name": "Item Name 2", "quantity": 1, "unitPrice": 5.99, "totalPrice": 5.99}
            ],
            "total": 27.97
            }
            
            Be precise with item names, quantities, and prices. If you can't read something clearly, make your best guess.
            For quantities, if not explicitly stated, assume 1.
            For unit prices, divide the total price by the quantity.
            For total prices, multiply the unit price by the quantity.
            
            IMPORTANT: Your response must ONLY contain this JSON object and nothing else.
            """
        super().__init__(self.system_prompt)


    @staticmethod
    def build() -> "OcrTicketInput":
        ocr_ticket_input = OcrTicketInput()
        return ocr_ticket_input

    def to_dict(self) -> dict:
        return {
            "system_prompt": self.system_prompt
        }