"""
LangChain Integration for CIBIL OCR Pipeline
--------------------------------------------
Integrates the CIBIL parser with LangChain document loaders and processors
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .pipeline import parse_cibil_report


class CIBILDocumentLoader:
    """
    LangChain-compatible document loader for CIBIL credit reports
    Supports PDF and text formats
    """

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.raw_text = None
        self.documents = []

    def load(self):
        """Load and parse the CIBIL document"""
        # Load based on file type
        if self.file_path.suffix.lower() == ".pdf":
            self._load_pdf()
        elif self.file_path.suffix.lower() == ".txt":
            self._load_text()
        else:
            raise ValueError(f"Unsupported file type: {self.file_path.suffix}")

        return self.documents

    def _load_pdf(self):
        """Load PDF using PyPDF"""
        try:
            loader = PyPDFLoader(str(self.file_path))
            docs = loader.load()
            self.raw_text = "\n\n".join([doc.page_content for doc in docs])

            # Create a single document with all content
            self.documents = [
                Document(
                    page_content=self.raw_text,
                    metadata={"source": str(self.file_path), "type": "cibil_report", "format": "pdf"},
                )
            ]
        except Exception as e:
            print(f"PyPDFLoader failed, trying UnstructuredPDFLoader: {e}")
            try:
                loader = UnstructuredPDFLoader(str(self.file_path))
                docs = loader.load()
                self.raw_text = "\n\n".join([doc.page_content for doc in docs])

                self.documents = [
                    Document(
                        page_content=self.raw_text,
                        metadata={"source": str(self.file_path), "type": "cibil_report", "format": "pdf"},
                    )
                ]
            except Exception as e2:
                raise Exception(f"Failed to load PDF with both loaders: {e2}")

    def _load_text(self):
        """Load text file"""
        loader = TextLoader(str(self.file_path), encoding="utf-8")
        docs = loader.load()
        self.raw_text = "\n\n".join([doc.page_content for doc in docs])

        self.documents = [
            Document(
                page_content=self.raw_text,
                metadata={"source": str(self.file_path), "type": "cibil_report", "format": "text"},
            )
        ]

    def get_raw_text(self) -> Optional[str]:
        """Get the raw text content"""
        if not self.raw_text:
            self.load()
        return self.raw_text


class CIBILDocumentProcessor:
    """
    Process CIBIL documents using LangChain and custom parser
    """

    def __init__(self, loader: CIBILDocumentLoader):
        self.loader = loader
        self.parsed_data = None

    def process(self) -> Dict:
        """Process the document and extract structured data"""
        # Get raw text
        raw_text = self.loader.get_raw_text()

        # Parse using custom parser
        self.parsed_data = parse_cibil_report(raw_text)

        return self.parsed_data

    def get_json(self, indent: int = 2) -> str:
        """Get parsed data as JSON string"""
        if not self.parsed_data:
            self.process()
        return json.dumps(self.parsed_data, indent=indent, ensure_ascii=False)

    def save_json(self, output_path: Union[str, Path]):
        """Save parsed data to JSON file"""
        if not self.parsed_data:
            self.process()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.parsed_data, f, indent=2, ensure_ascii=False)

    def get_summary(self) -> Dict:
        """Get a summary of the credit report"""
        if not self.parsed_data:
            self.process()

        metadata = self.parsed_data.get("report_metadata", {}) if self.parsed_data else {}
        personal = self.parsed_data.get("personal_details", {}) if self.parsed_data else {}

        return {
            "name": personal.get("name"),
            "cibil_score": metadata.get("cibil_score"),
            "report_date": metadata.get("report_date"),
            "total_loan_accounts": len(self.parsed_data.get("loan_accounts", []) if self.parsed_data else []),
            "total_credit_cards": len(self.parsed_data.get("credit_cards", []) if self.parsed_data else []),
            "active_accounts": self._count_active_accounts(),
            "total_outstanding": self._calculate_total_outstanding(),
        }

    def _count_active_accounts(self) -> int:
        """Count total active accounts"""
        count = 0
        for loan in self.parsed_data.get("loan_accounts", []) if self.parsed_data else []:
            if loan.get("status", "").lower() == "active":
                count += 1
        for card in self.parsed_data.get("credit_cards", []) if self.parsed_data else []:
            if card.get("status", "").lower() == "active":
                count += 1
        return count

    def _calculate_total_outstanding(self) -> float:
        """Calculate total outstanding amount"""
        total = 0
        for loan in self.parsed_data.get("loan_accounts", []) if self.parsed_data else []:
            outstanding = loan.get("current_outstanding")
            if outstanding:
                total += outstanding
        for card in self.parsed_data.get("credit_cards", []) if self.parsed_data else []:
            outstanding = card.get("current_outstanding")
            if outstanding:
                total += outstanding
        return total


class CIBILChunker:
    """
    Split CIBIL report into meaningful chunks for further processing
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\nAccount:", "\n\nBack to Top", "\n\n", "\n", " "],
        )

    def chunk_document(self, document: Document) -> List[Document]:
        """Split document into chunks"""
        return self.splitter.split_documents([document])

    def chunk_by_section(self, text: str) -> Dict[str, str]:
        """Split CIBIL report by logical sections"""
        sections = {}

        # Personal Details
        personal_section = self._extract_section(text, "Profile Details", "Back to Top")
        if personal_section:
            sections["personal_details"] = personal_section

        # Credit Factors
        credit_factors_section = self._extract_section(text, "Credit Factors", "Account Summary")
        if credit_factors_section:
            sections["credit_factors"] = credit_factors_section

        # Active Accounts
        active_accounts_section = self._extract_section(text, "Active Accounts", "Closed Accounts")
        if active_accounts_section:
            sections["active_accounts"] = active_accounts_section

        # Closed Accounts
        closed_accounts_section = self._extract_section(text, "Closed Accounts", "Payment History")
        if closed_accounts_section:
            sections["closed_accounts"] = closed_accounts_section

        # Credit Enquiries
        enquiries_section = self._extract_section(text, "Credit Enquiries", "Employment Details")
        if enquiries_section:
            sections["credit_enquiries"] = enquiries_section

        return sections

    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> Optional[str]:
        """Extract text between two markers"""
        import re

        pattern = f"{re.escape(start_marker)}(.*?){re.escape(end_marker)}"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None


class CIBILReportAnalyzer:
    """
    Analyze CIBIL report data for insights
    """

    def __init__(self, parsed_data: Dict):
        self.data = parsed_data

    def get_risk_indicators(self) -> Dict:
        """Identify risk indicators in the report"""
        indicators = {"high_risk": [], "medium_risk": [], "low_risk": []}

        # Check credit score
        score = self.data["report_metadata"].get("cibil_score")
        if score:
            if score < 650:
                indicators["high_risk"].append(f"Low credit score: {score}")
            elif score < 750:
                indicators["medium_risk"].append(f"Average credit score: {score}")
            else:
                indicators["low_risk"].append(f"Good credit score: {score}")

        # Check for delayed payments
        for loan in self.data.get("loan_accounts", []):
            delayed_days = loan.get("miscellaneous", {}).get("payment_delayed_days", 0)
            if delayed_days and delayed_days > 90:
                indicators["high_risk"].append(f"{loan.get('lender_name')} - Payment delayed by {delayed_days} days")
            elif delayed_days and delayed_days > 30:
                indicators["medium_risk"].append(f"{loan.get('lender_name')} - Payment delayed by {delayed_days} days")

        # Check credit utilization for cards
        for card in self.data.get("credit_cards", []):
            limit = card.get("credit_limit")
            outstanding = card.get("current_outstanding")
            if limit and outstanding:
                utilization = (outstanding / limit) * 100
                if utilization > 80:
                    indicators["high_risk"].append(f"{card.get('issuer_name')} - High utilization: {utilization:.1f}%")
                elif utilization > 50:
                    indicators["medium_risk"].append(
                        f"{card.get('issuer_name')} - Moderate utilization: {utilization:.1f}%"
                    )

        # Check number of recent enquiries
        enquiries = self.data.get("credit_factors", {}).get("credit_enquiries", {}).get("count")
        if enquiries:
            if enquiries > 10:
                indicators["high_risk"].append(f"High number of enquiries: {enquiries}")
            elif enquiries > 5:
                indicators["medium_risk"].append(f"Moderate enquiries: {enquiries}")

        return indicators

    def get_account_summary(self) -> Dict:
        """Get summary of all accounts"""
        return {
            "total_loans": len(self.data.get("loan_accounts", [])),
            "total_credit_cards": len(self.data.get("credit_cards", [])),
            "active_loans": sum(
                1 for loan in self.data.get("loan_accounts", []) if loan.get("status", "").lower() == "active"
            ),
            "active_cards": sum(
                1 for card in self.data.get("credit_cards", []) if card.get("status", "").lower() == "active"
            ),
            "total_loan_outstanding": sum(
                loan.get("current_outstanding", 0) for loan in self.data.get("loan_accounts", [])
            ),
            "total_card_outstanding": sum(
                card.get("current_outstanding", 0) for card in self.data.get("credit_cards", [])
            ),
        }


# Example usage pipeline
def process_cibil_report_pipeline(file_path: str, output_dir: str = ".") -> Dict:
    """
    Complete pipeline to process CIBIL report

    Args:
        file_path: Path to CIBIL report file (PDF or TXT)
        output_dir: Directory to save output files

    Returns:
        Dictionary with parsed data and analysis
    """
    # Step 1: Load document
    print(f"Loading document: {file_path}")
    loader = CIBILDocumentLoader(file_path)
    loader.load()

    # Step 2: Process document
    print("Processing document...")
    processor = CIBILDocumentProcessor(loader)
    parsed_data = processor.process()

    # Step 3: Save JSON
    output_json = Path(output_dir) / "cibil_report_parsed.json"
    print(f"Saving parsed data to: {output_json}")
    processor.save_json(output_json)

    # Step 4: Get summary
    print("Generating summary...")
    summary = processor.get_summary()

    # Step 5: Analyze for risk
    print("Analyzing risk indicators...")
    analyzer = CIBILReportAnalyzer(parsed_data)
    risk_indicators = analyzer.get_risk_indicators()
    account_summary = analyzer.get_account_summary()

    # Step 6: Chunk by sections
    print("Chunking document by sections...")
    chunker = CIBILChunker()
    sections = chunker.chunk_by_section(loader.get_raw_text())

    return {
        "parsed_data": parsed_data,
        "summary": summary,
        "risk_indicators": risk_indicators,
        "account_summary": account_summary,
        "sections": list(sections.keys()),
    }


# if __name__ == "__main__":
#     # Example usage
#     result = process_cibil_report_pipeline(
#         file_path="/Users/shubhamprajapati/Desktop/sahiloan/sahiloan-customer-chatbot/",
#         output_dir="./output",
#     )

#     print("\n=== Summary ===")
#     print(json.dumps(result["summary"], indent=2))

#     print("\n=== Risk Indicators ===")
#     print(json.dumps(result["risk_indicators"], indent=2))

#     print("\n=== Account Summary ===")
#     print(json.dumps(result["account_summary"], indent=2))
