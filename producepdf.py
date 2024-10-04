import markdown2
from xhtml2pdf import pisa

def read_markdown_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def convert_markdown_to_html(markdown_text):
    return markdown2.markdown(markdown_text)

def convert_html_to_pdf(source_html, output_filename):

    # Open a file to write the PDF to
    with open(output_filename, "w+b") as result_file:
        # Convert HTML to PDF
        pisa_status = pisa.CreatePDF(source_html, dest=result_file)
    
    return pisa_status.err

def file_to_html(markdown_file_path):

    # Read the Markdown file
    markdown_text = read_markdown_file(markdown_file_path)
    
    # Convert Markdown to HTML
    html_text = convert_markdown_to_html(markdown_text)

    return html_text

def markdown_to_pdf(markdown_file_path, pdf_file_path):

    # Convert Markdown to HTML
    html_text = file_to_html(markdown_file_path)

    styling = """
    @page {size: letter landscape;margin: 2cm;}
    """

    html_text = f"<html><head><style>{styling}</style></head><body>{html_text}</body></html>"

    # Convert HTML to PDF
    result = convert_html_to_pdf(html_text, pdf_file_path)
    
    if result == 0:
        print(f"PDF created successfully at: {pdf_file_path}")
    else:
        print("Error in PDF creation")


# Example usage
markdown_file_path = 'example.md'
pdf_file_path = 'output.pdf'

markdown_to_pdf(markdown_file_path, pdf_file_path)