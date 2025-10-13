# modules/export.py
import pandas as pd
from io import BytesIO

class ExportService:
    def __init__(self):
        """Initialize the export service."""
        pass
    
    def generate_csv(self, answers):
        """Convert answers to CSV format."""
        df = pd.DataFrame(answers, columns=['Question', 'Answer'])
        return df.to_csv(index=False).encode('utf-8')
        
    def generate_excel(self, answers):
        """Convert answers to Excel format with error handling."""
        try:
            df = pd.DataFrame(answers, columns=['Question', 'Answer'])
            output = BytesIO()
            
            # Try to use xlsxwriter if available
            try:
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Responses')
            except (ImportError, ModuleNotFoundError):
                # Fall back to openpyxl if xlsxwriter isn't available
                try:
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Responses')
                except (ImportError, ModuleNotFoundError):
                    # If neither Excel writer is available, raise a more helpful error
                    raise ImportError("Excel export libraries (xlsxwriter or openpyxl) not available")
                    
            return output.getvalue()
        except Exception as e:
            print(f"Could not generate Excel file: {e}")
            # Return CSV as fallback
            return self.generate_csv(answers)