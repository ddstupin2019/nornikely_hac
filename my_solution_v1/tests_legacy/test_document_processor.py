import pytest
from unittest.mock import patch, mock_open
from my_solution_v1.rag.document_processor import (
    parse_pdf, parse_docx, parse_excel, parse_csv, process_document
)

def test_parse_pdf_success():
    with patch("my_solution_v1.rag.document_processor.PyPDF2.PdfReader") as mock_reader, \
         patch("builtins.open", mock_open()):
        
        mock_page = mock_reader.return_value.pages[0]
        mock_page.extract_text.return_value = "PDF TEXT"
        mock_reader.return_value.pages = [mock_page]
        
        text = parse_pdf("dummy.pdf")
        assert "PDF TEXT" in text

def test_parse_docx_success():
    with patch("my_solution_v1.rag.document_processor.DocxDocument") as mock_doc_class:
        mock_doc = mock_doc_class.return_value
        mock_para = type('Para', (), {'text': 'DOCX TEXT'})
        mock_doc.paragraphs = [mock_para]
        
        text = parse_docx("dummy.docx")
        assert "DOCX TEXT" in text

def test_parse_excel_success():
    with patch("my_solution_v1.rag.document_processor.load_workbook") as mock_load:
        mock_wb = mock_load.return_value
        mock_wb.sheetnames = ["Sheet1"]
        mock_sheet = mock_wb["Sheet1"]
        mock_sheet.iter_rows.return_value = [("EXCEL", "TEXT")]
        
        text = parse_excel("dummy.xlsx")
        assert "EXCEL | TEXT" in text

def test_parse_csv_success():
    csv_content = "col1,col2\nval1,val2"
    with patch("builtins.open", mock_open(read_data=csv_content)):
        text = parse_csv("dummy.csv")
        assert "col1 | col2" in text
        assert "val1 | val2" in text

def test_process_document():
    with patch("my_solution_v1.rag.document_processor.parse_pdf", return_value="PDF TEXT"):
        res = process_document("test.pdf")
        assert res["filename"] == "test.pdf"
        assert res["content"] == "PDF TEXT"
