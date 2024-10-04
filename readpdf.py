import PyPDF2

def pdf_to_text(pdf_path):
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        
        # Iterate through each page
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    
    return text

# Example usage
pdf_path = './data/data (1).pdf'
text = pdf_to_text(pdf_path)
print(text)