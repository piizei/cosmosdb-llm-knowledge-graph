from pypdf import PdfReader

def parse_pdf(file):
    offset = 0
    page_map = []
  
    reader = PdfReader(file)
    pages = reader.pages
    for page_num, p in enumerate(pages):
        page_text = p.extract_text()
        page_map.append((page_num, offset, page_text))
        offset += len(page_text)
    return page_map


