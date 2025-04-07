import os
from typing import List, Dict
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFProcessor:
    def __init__(self, data_dir: str = "data"):
        """Initialize the PDF processor with the directory containing PDF files."""
        self.data_dir = data_dir
        
    def get_pdf_files(self) -> List[str]:
        """Get list of PDF files in the data directory."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"Created directory {self.data_dir}")
            return []
        
        pdf_files = [
            os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir)
            if f.lower().endswith(".pdf")
        ]
        return pdf_files
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def split_text_into_chunks(self, text: str, 
                               chunk_size: int = 1000, 
                               chunk_overlap: int = 200) -> List[str]:
        """Split text into smaller chunks for processing."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def process_pdf_documents(self) -> Dict[str, List[str]]:
        """Process all PDF documents in the data directory."""
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            print("No PDF files found in the data directory.")
            return {}
        
        document_chunks = {}
        for pdf_file in pdf_files:
            filename = os.path.basename(pdf_file)
            print(f"Processing {filename}...")
            text = self.extract_text_from_pdf(pdf_file)
            if text:
                chunks = self.split_text_into_chunks(text)
                document_chunks[filename] = chunks
                print(f"Extracted {len(chunks)} chunks from {filename}")
            else:
                print(f"No text extracted from {filename}")
        
        return document_chunks
