from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
import markdown2 as markdown

def read_markdown_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def markdown_to_pdf(markdown_text, pdf_path):
    # Convert Markdown to HTML
    html_text = markdown.markdown(markdown_text)
    
    # Create a PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add HTML content to the PDF
    story.append(Paragraph(html_text, styles['Normal']))
    
    # Build the PDF
    doc.build(story)

# Example usage
markdown_file_path = 'example.md'
pdf_file_path = 'output.pdf'

markdown_text = read_markdown_file(markdown_file_path)
markdown_to_pdf(markdown_text, pdf_file_path)

print(f"PDF created at: {pdf_file_path}")