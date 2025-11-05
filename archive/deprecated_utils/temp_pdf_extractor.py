import PyPDF2
import sys
import codecs

try:
    with open('C:/Users/VictorMaciel/Downloads/acebotlostconvo.pdf', 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            page_text = page.extract_text()
            # Handle encoding issues by replacing problematic characters
            page_text = page_text.encode('utf-8', errors='replace').decode('utf-8')
            text += page_text + '\n'

        # Write to a file to avoid encoding issues with print
        with codecs.open('extracted_conversation.txt', 'w', encoding='utf-8') as out_file:
            out_file.write(text)

        print("Text extracted and saved to extracted_conversation.txt")
        print("\nFirst 1000 characters:")
        print(text[:1000])

except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
