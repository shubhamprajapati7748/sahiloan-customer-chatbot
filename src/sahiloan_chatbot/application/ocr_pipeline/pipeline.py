"""
CIBIL Credit Report OCR Pipeline
---------------------------------
A comprehensive rule-based extraction pipeline for parsing CIBIL credit reports
without using LLMs. Uses pattern matching, regex, and structured text processing.
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AccountStatus(Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    PAYMENT_DELAYED = "Payment Delayed"


@dataclass
class ReportMetadata:
    source: str = "Paisabazaar"
    provider: str = "CIBIL"
    report_date: Optional[str] = None
    enquiry_control_number: Optional[str] = None
    cibil_score: Optional[int] = None


@dataclass
class PersonalDetails:
    name: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    pan_number: Optional[str] = None
    mobile_numbers: List[str] = None
    addresses: Dict[str, Optional[str]] = None

    def __post_init__(self):
        if self.mobile_numbers is None:
            self.mobile_numbers = []
        if self.addresses is None:
            self.addresses = {"permanent_address": None, "residence_address": None}


@dataclass
class CreditFactors:
    on_time_payment: Dict[str, Any] = None
    credit_card_utilization: Dict[str, Any] = None
    length_of_credit_history: Dict[str, Any] = None
    credit_enquiries: Dict[str, Any] = None
    credit_mix: Dict[str, Any] = None

    def __post_init__(self):
        if self.on_time_payment is None:
            self.on_time_payment = {"percentage": None, "good_threshold": 90}
        if self.credit_card_utilization is None:
            self.credit_card_utilization = {"percentage": None, "good_threshold": 70}
        if self.length_of_credit_history is None:
            self.length_of_credit_history = {"years": None, "months": None}
        if self.credit_enquiries is None:
            self.credit_enquiries = {"count": None, "good_threshold": 5}
        if self.credit_mix is None:
            self.credit_mix = {"secured_accounts": None, "unsecured_accounts": None}


@dataclass
class LoanAccount:
    lender_name: Optional[str] = None
    loan_type: Optional[str] = None
    status: Optional[str] = None
    account_number_masked: Optional[str] = None
    date_opened: Optional[str] = None
    repayment_tenure: Dict[str, int] = None
    sanction_amount: Optional[float] = None
    current_outstanding: Optional[float] = None
    emi_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    miscellaneous: Dict[str, Any] = None

    def __post_init__(self):
        if self.repayment_tenure is None:
            self.repayment_tenure = {"years": None, "months": None}  # pyright: ignore[reportAttributeAccessIssue]
        if self.miscellaneous is None:
            self.miscellaneous = {
                "ownership": None,
                "payment_frequency": None,
                "credit_limit": None,
                "cash_limit": None,
                "collateral": {"type": None, "value": None},
                "last_payment_date": None,
                "last_updated_date": None,
                "date_closed": None,
                "overdue_amount": None,
                "payment_delayed_days": None,
            }


@dataclass
class CreditCard:
    issuer_name: Optional[str] = None
    card_type: str = "Credit Card"
    status: Optional[str] = None
    account_number_masked: Optional[str] = None
    credit_limit: Optional[float] = None
    cash_limit: Optional[float] = None
    high_credit: Optional[float] = None
    current_outstanding: Optional[float] = None
    emi_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    repayment_tenure: Optional[Dict[str, int]] = None
    miscellaneous: Dict[str, Any] = None

    def __post_init__(self):
        if self.miscellaneous is None:
            self.miscellaneous = {
                "ownership": None,
                "payment_frequency": None,
                "last_payment_amount": None,
                "last_payment_date": None,
                "last_updated_date": None,
                "date_closed": None,
                "collateral": {"type": None, "value": None},
                "overdue_amount": None,
                "payment_delayed_days": None,
            }


class CIBILReportParser:
    """Main parser class for CIBIL credit reports"""

    def __init__(self, text: str):
        self.text = text
        self.lines = text.split("\n")
        self.metadata = ReportMetadata()
        self.personal_details = PersonalDetails()
        self.credit_factors = CreditFactors()
        self.loan_accounts = []
        self.credit_cards = []

    def parse(self) -> Dict:
        """Main parsing method that orchestrates all extraction"""
        self._extract_metadata()
        self._extract_personal_details()
        self._extract_credit_factors()
        self._extract_accounts()
        return self._to_dict()

    def _extract_metadata(self):
        """Extract report metadata like ECN, date, and score"""
        # Extract ECN
        ecn_pattern = r"Enquiry Control Number \(ECN\):?\s*(\d+)"
        ecn_match = re.search(ecn_pattern, self.text)
        if ecn_match:
            self.metadata.enquiry_control_number = ecn_match.group(1)

        # Extract Report Date
        date_pattern = r"Report Date:?\s*(\d{1,2}\s+\w+\s+\d{4})"
        date_match = re.search(date_pattern, self.text)
        if date_match:
            date_str = date_match.group(1)
            self.metadata.report_date = self._parse_date(date_str)

        # Extract CIBIL Score
        score_pattern = r"(?:CIBIL Score|Credit Score)[\s:]*(\d{3})"
        score_match = re.search(score_pattern, self.text)
        if score_match:
            self.metadata.cibil_score = int(score_match.group(1))
        else:
            # Try to find score in the beginning of document
            first_500_chars = self.text[:500]
            standalone_score = re.search(r"\b([6-8]\d{2})\b", first_500_chars)
            if standalone_score:
                self.metadata.cibil_score = int(standalone_score.group(1))

    def _extract_personal_details(self):
        """Extract personal information"""
        # Extract Name
        name_pattern = r"^([A-Z\s]{2,50})\s*$"
        for line in self.lines[:50]:  # Check first 50 lines
            line = line.strip()
            if line and len(line.split()) <= 6:
                match = re.match(name_pattern, line)
                if match and not any(
                    keyword in line.lower()
                    for keyword in ["report", "date", "enquiry", "credit", "profile", "gender", "dob"]
                ):
                    potential_name = match.group(1).strip()
                    if len(potential_name) > 5:  # Reasonable name length
                        self.personal_details.name = potential_name
                        break

        # Extract Gender
        gender_pattern = r"Gender[\s:]*(\w+)"
        gender_match = re.search(gender_pattern, self.text, re.IGNORECASE)
        if gender_match:
            self.personal_details.gender = gender_match.group(1).upper()

        # Extract DOB
        dob_pattern = r"(?:DOB|Date of Birth)[\s:]*(\d{1,2}\s+\w+\s+\d{4})"
        dob_match = re.search(dob_pattern, self.text, re.IGNORECASE)
        if dob_match:
            self.personal_details.date_of_birth = self._parse_date(dob_match.group(1))

        # Extract Email
        email_pattern = r"Email[\s:]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        email_match = re.search(email_pattern, self.text, re.IGNORECASE)
        if email_match:
            self.personal_details.email = email_match.group(1)

        # Extract PAN
        pan_pattern = r"PAN[\s\w]*:?\s*([A-Z]{5}\d{4}[A-Z])"
        pan_match = re.search(pan_pattern, self.text, re.IGNORECASE)
        if pan_match:
            self.personal_details.pan_number = pan_match.group(1)

        # Extract Mobile Numbers
        mobile_pattern = r"(?:Mobile Phone|Phone Number|Not Classified)[\s:]*(\d{10})"
        mobile_matches = re.finditer(mobile_pattern, self.text)
        for match in mobile_matches:
            phone = match.group(1)
            if phone not in self.personal_details.mobile_numbers:
                self.personal_details.mobile_numbers.append(phone)

        # Extract Addresses
        self._extract_addresses()

    def _extract_addresses(self):
        """Extract permanent and residence addresses"""
        # Find address section
        address_section = re.search(
            r"Address Details.*?(?=Back to Top|Credit Factors|$)", self.text, re.DOTALL | re.IGNORECASE
        )

        if address_section:
            address_text = address_section.group(0)

            # Extract Permanent Address
            perm_pattern = r"Permanent Address\s+[A-Z\s]+\s+\d{2}\s+\w+\s+\d{4}\s*(.+?)(?=Permanent Address|Residence Address|Back to Top|$)"
            perm_match = re.search(perm_pattern, address_text, re.DOTALL)
            if perm_match:
                addr = self._clean_address(perm_match.group(1))
                self.personal_details.addresses["permanent_address"] = addr

            # Extract Residence Address
            res_pattern = r"Residence Address\s+[A-Z\s]+\s+\d{2}\s+\w+\s+\d{4}\s*(.+?)(?=Permanent Address|Residence Address|Back to Top|$)"
            res_match = re.search(res_pattern, address_text, re.DOTALL)
            if res_match:
                addr = self._clean_address(res_match.group(1))
                self.personal_details.addresses["residence_address"] = addr

    def _extract_credit_factors(self):
        """Extract credit score factors"""
        # On-time Payment Percentage
        payment_pattern = r"On-Time Payments?:\s*(\d+)%"
        payment_match = re.search(payment_pattern, self.text, re.IGNORECASE)
        if payment_match:
            self.credit_factors.on_time_payment["percentage"] = int(payment_match.group(1))

        # Credit History Length
        history_pattern = r"Age of Oldest Account:\s*(\d+)\s*years?\s*(\d+)\s*months?"
        history_match = re.search(history_pattern, self.text, re.IGNORECASE)
        if history_match:
            self.credit_factors.length_of_credit_history["years"] = int(history_match.group(1))
            self.credit_factors.length_of_credit_history["months"] = int(history_match.group(2))

        # Total Enquiries
        enquiry_pattern = r"Total Enquiries:\s*(\d+)"
        enquiry_match = re.search(enquiry_pattern, self.text, re.IGNORECASE)
        if enquiry_match:
            self.credit_factors.credit_enquiries["count"] = int(enquiry_match.group(1))

        # Credit Mix
        secured_pattern = r"Secured Accounts?:\s*(\d+)"
        secured_match = re.search(secured_pattern, self.text, re.IGNORECASE)
        if secured_match:
            self.credit_factors.credit_mix["secured_accounts"] = int(secured_match.group(1))

        unsecured_pattern = r"Unsecured Accounts?:\s*(\d+)"
        unsecured_match = re.search(unsecured_pattern, self.text, re.IGNORECASE)
        if unsecured_match:
            self.credit_factors.credit_mix["unsecured_accounts"] = int(unsecured_match.group(1))

    def _extract_accounts(self):
        """Extract all loan accounts and credit cards"""
        # Find all account blocks
        account_blocks = self._find_account_blocks()

        for block in account_blocks:
            account_data = self._parse_account_block(block)
            if account_data:
                # Determine if it's a credit card or loan
                product_type = account_data.get("product_type", "").lower()
                if "credit card" in product_type:
                    self.credit_cards.append(self._create_credit_card(account_data))
                else:
                    self.loan_accounts.append(self._create_loan_account(account_data))

    def _find_account_blocks(self) -> List[str]:
        """Find individual account information blocks"""
        blocks = []

        # Pattern to identify account headers
        # account_header_pattern = r"(?:^|\n)([A-Z\s&]+(?:BANK|BK|FIN|FINANCIAL|CARD))\s*\n"

        # Split text into potential account sections
        sections = re.split(r"Account:\s*\d+/\d+", self.text)

        for section in sections[1:]:  # Skip first split (before any accounts)
            if len(section.strip()) > 100:  # Minimum length for valid account
                blocks.append(section)

        return blocks

    def _parse_account_block(self, block: str) -> Dict:
        """Parse a single account block and extract all fields"""
        account = {}

        # Extract Financial Institution
        fi_pattern = r"^([A-Z\s&]+(?:BANK|BK|FIN|FINANCIAL|CARD|MUTHOOT|IDFC|HOME|IKF|LNTFIN|SOUTH|HLF|HDB|BAJAJ|CHOLA|RBL|SBI|TCFSL|DMIFINANCE|SUNDARAM))"
        fi_match = re.search(fi_pattern, block, re.MULTILINE)
        if fi_match:
            account["lender_name"] = fi_match.group(1).strip()

        # Extract Product Type
        product_pattern = r"Product Type\s*-\s*(.+?)(?:\s+Status:|\n)"
        product_match = re.search(product_pattern, block)
        if product_match:
            account["product_type"] = product_match.group(1).strip()

        # Extract Status
        status_pattern = r"Status:\s*(\w+(?:\s+\w+)?)"
        status_match = re.search(status_pattern, block)
        if status_match:
            account["status"] = status_match.group(1).strip()

        # Extract Account Number
        acc_num_pattern = r"Account Number\s+([X\d]+)"
        acc_num_match = re.search(acc_num_pattern, block)
        if acc_num_match:
            account["account_number"] = acc_num_match.group(1).strip()

        # Extract Ownership
        ownership_pattern = r"Ownership\s+(\w+)"
        ownership_match = re.search(ownership_pattern, block)
        if ownership_match:
            account["ownership"] = ownership_match.group(1).strip()

        # Extract Credit Limit
        credit_limit_pattern = r"Credit Limit\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        credit_limit_match = re.search(credit_limit_pattern, block)
        if credit_limit_match:
            account["credit_limit"] = self._parse_amount(credit_limit_match.group(1))

        # Extract Cash Limit
        cash_limit_pattern = r"Cash Limit\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        cash_limit_match = re.search(cash_limit_pattern, block)
        if cash_limit_match:
            account["cash_limit"] = self._parse_amount(cash_limit_match.group(1))

        # Extract Payment Frequency
        freq_pattern = r"Payment Frequency\s+(\w+)"
        freq_match = re.search(freq_pattern, block)
        if freq_match:
            account["payment_frequency"] = freq_match.group(1).strip()

        # Extract Last Payment
        last_payment_pattern = r"Last Payment\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        last_payment_match = re.search(last_payment_pattern, block)
        if last_payment_match:
            account["last_payment"] = self._parse_amount(last_payment_match.group(1))

        # Extract Collateral Value
        collateral_value_pattern = r"Value of Collateral\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        collateral_value_match = re.search(collateral_value_pattern, block)
        if collateral_value_match:
            account["collateral_value"] = self._parse_amount(collateral_value_match.group(1))

        # Extract Collateral Type
        collateral_type_pattern = r"Type of Collateral\s+(\w+)"
        collateral_type_match = re.search(collateral_type_pattern, block)
        if collateral_type_match:
            account["collateral_type"] = collateral_type_match.group(1).strip()

        # Extract Last Payment Date
        last_payment_date_pattern = r"Last Payment Date\s+(\d{1,2}\s+\w+\s+\d{4})"
        last_payment_date_match = re.search(last_payment_date_pattern, block)
        if last_payment_date_match:
            account["last_payment_date"] = self._parse_date(last_payment_date_match.group(1))

        # Extract Last Updated Date
        last_updated_pattern = r"Last Updated Date\s+(\d{1,2}\s+\w+\s+\d{4})"
        last_updated_match = re.search(last_updated_pattern, block)
        if last_updated_match:
            account["last_updated_date"] = self._parse_date(last_updated_match.group(1))

        # Extract Date Opened
        date_opened_pattern = r"Date Opened\s+(\d{1,2}\s+\w+\s+\d{4})"
        date_opened_match = re.search(date_opened_pattern, block)
        if date_opened_match:
            account["date_opened"] = self._parse_date(date_opened_match.group(1))

        # Extract Date Closed
        date_closed_pattern = r"Date Closed\s+(\d{1,2}\s+\w+\s+\d{4})"
        date_closed_match = re.search(date_closed_pattern, block)
        if date_closed_match:
            account["date_closed"] = self._parse_date(date_closed_match.group(1))

        # Extract Sanction Amount
        sanction_pattern = r"Sanction Amount\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        sanction_match = re.search(sanction_pattern, block)
        if sanction_match:
            account["sanction_amount"] = self._parse_amount(sanction_match.group(1))

        # Extract Current Outstanding
        outstanding_pattern = r"Current Outstanding\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        outstanding_match = re.search(outstanding_pattern, block)
        if outstanding_match:
            account["current_outstanding"] = self._parse_amount(outstanding_match.group(1))

        # Extract Overdue Amount
        overdue_pattern = r"Overdue Amount\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        overdue_match = re.search(overdue_pattern, block)
        if overdue_match:
            account["overdue_amount"] = self._parse_amount(overdue_match.group(1))

        # Extract Rate of Interest
        interest_pattern = r"Rate of Interest\s+(\d+(?:\.\d+)?)%?"
        interest_match = re.search(interest_pattern, block)
        if interest_match:
            account["interest_rate"] = float(interest_match.group(1))

        # Extract Repayment Tenure
        tenure_pattern = r"Repayment Tenure\s+(\d+)Y(?:\s*(\d+)M)?"
        tenure_match = re.search(tenure_pattern, block)
        if tenure_match:
            years = int(tenure_match.group(1))
            months = int(tenure_match.group(2)) if tenure_match.group(2) else 0
            account["repayment_tenure"] = {"years": years, "months": months}

        # Extract EMI Amount
        emi_pattern = r"EMI Amount\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        emi_match = re.search(emi_pattern, block)
        if emi_match:
            account["emi_amount"] = self._parse_amount(emi_match.group(1))

        # Extract Payment Delayed Days
        delayed_pattern = r"Payment Delayed by:\s*(\d+)\s*days?"
        delayed_match = re.search(delayed_pattern, block)
        if delayed_match:
            account["payment_delayed_days"] = int(delayed_match.group(1))

        # Extract High Credit (for credit cards)
        high_credit_pattern = r"High Credit\s+(?:₹\s*)?(\d+(?:,\d+)*)"
        high_credit_match = re.search(high_credit_pattern, block)
        if high_credit_match:
            account["high_credit"] = self._parse_amount(high_credit_match.group(1))

        return account

    def _create_loan_account(self, data: Dict) -> LoanAccount:
        """Create a LoanAccount object from extracted data"""
        loan = LoanAccount()

        loan.lender_name = data.get("lender_name")
        loan.loan_type = data.get("product_type")
        loan.status = data.get("status")
        loan.account_number_masked = data.get("account_number")
        loan.date_opened = data.get("date_opened")
        loan.sanction_amount = data.get("sanction_amount")
        loan.current_outstanding = data.get("current_outstanding")
        loan.emi_amount = data.get("emi_amount")
        loan.interest_rate = data.get("interest_rate")

        if data.get("repayment_tenure"):
            loan.repayment_tenure = data["repayment_tenure"]

        # Fill miscellaneous
        loan.miscellaneous["ownership"] = data.get("ownership")
        loan.miscellaneous["payment_frequency"] = data.get("payment_frequency")
        loan.miscellaneous["credit_limit"] = data.get("credit_limit")
        loan.miscellaneous["cash_limit"] = data.get("cash_limit")
        loan.miscellaneous["collateral"]["type"] = data.get("collateral_type")
        loan.miscellaneous["collateral"]["value"] = data.get("collateral_value")
        loan.miscellaneous["last_payment_date"] = data.get("last_payment_date")
        loan.miscellaneous["last_updated_date"] = data.get("last_updated_date")
        loan.miscellaneous["date_closed"] = data.get("date_closed")
        loan.miscellaneous["overdue_amount"] = data.get("overdue_amount")
        loan.miscellaneous["payment_delayed_days"] = data.get("payment_delayed_days")

        return loan

    def _create_credit_card(self, data: Dict) -> CreditCard:
        """Create a CreditCard object from extracted data"""
        card = CreditCard()

        card.issuer_name = data.get("lender_name")
        card.status = data.get("status")
        card.account_number_masked = data.get("account_number")
        card.credit_limit = data.get("credit_limit")
        card.cash_limit = data.get("cash_limit")
        card.high_credit = data.get("high_credit")
        card.current_outstanding = data.get("current_outstanding")
        card.emi_amount = data.get("emi_amount")
        card.interest_rate = data.get("interest_rate")

        if data.get("repayment_tenure"):
            card.repayment_tenure = data["repayment_tenure"]

        # Fill miscellaneous
        card.miscellaneous["ownership"] = data.get("ownership")
        card.miscellaneous["payment_frequency"] = data.get("payment_frequency")
        card.miscellaneous["last_payment_amount"] = data.get("last_payment")
        card.miscellaneous["last_payment_date"] = data.get("last_payment_date")
        card.miscellaneous["last_updated_date"] = data.get("last_updated_date")
        card.miscellaneous["date_closed"] = data.get("date_closed")
        card.miscellaneous["collateral"]["type"] = data.get("collateral_type", "Other")
        card.miscellaneous["collateral"]["value"] = data.get("collateral_value")
        card.miscellaneous["overdue_amount"] = data.get("overdue_amount")
        card.miscellaneous["payment_delayed_days"] = data.get("payment_delayed_days")

        return card

    def _parse_date(self, date_str: str) -> str:
        """Convert date string to YYYY-MM-DD format"""
        try:
            # Handle format like "10 Jan 2026"
            dt = datetime.strptime(date_str.strip(), "%d %b %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                # Try alternative format
                dt = datetime.strptime(date_str.strip(), "%d %B %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return date_str

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Convert currency string to float"""
        # Remove commas and convert to float
        cleaned = amount_str.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _clean_address(self, address: str) -> Optional[str]:
        """Clean and format address string"""
        # Remove extra whitespace and newlines
        address = re.sub(r"\s+", " ", address)
        address = address.strip()
        # Remove trailing comma and whitespace
        address = address.rstrip(", ")
        return address if address else None

    def _to_dict(self) -> Dict:
        """Convert parsed data to dictionary"""
        return {
            "report_metadata": asdict(self.metadata),
            "personal_details": asdict(self.personal_details),
            "credit_factors": asdict(self.credit_factors),
            "loan_accounts": [asdict(loan) for loan in self.loan_accounts],
            "credit_cards": [asdict(card) for card in self.credit_cards],
        }


def parse_cibil_report(text: str) -> Dict:
    """
    Main function to parse CIBIL credit report text

    Args:
        text: Raw text content of the CIBIL report

    Returns:
        Dictionary containing structured credit report data
    """
    parser = CIBILReportParser(text)
    return parser.parse()


def parse_cibil_report_to_json(text: str, output_file: Optional[str] = None) -> str:
    """
    Parse CIBIL report and return/save as JSON

    Args:
        text: Raw text content of the CIBIL report
        output_file: Optional file path to save JSON output

    Returns:
        JSON string of parsed data
    """
    parsed_data = parse_cibil_report(text)
    json_str = json.dumps(parsed_data, indent=2, ensure_ascii=False)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_str)

    return json_str


# Example usage
if __name__ == "__main__":
    # Example: Read from file and parse
    with open("cibil_report.txt", "r", encoding="utf-8") as f:
        report_text = f.read()

    # Parse and get JSON
    json_output = parse_cibil_report_to_json(report_text, "output.json")
    print(json_output)
