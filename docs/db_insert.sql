

INSERT INTO users (
  id, first_name, last_name, email, phone_number,
  created_at, modified_at
)
VALUES
(
  '11111111-1111-1111-1111-111111111111',
  'Rahul',
  'Sharma',
  'rahul.sharma@gmail.com',
  '9876543210',
  '2024-01-10 10:30:00',
  '2024-01-10 10:30:00'
),
(
  '22222222-2222-2222-2222-222222222222',
  'Priya',
  'Mehta',
  'priya.mehta@gmail.com',
  '9876543211',
  '2024-02-05 14:15:00',
  '2024-02-05 14:15:00'
),
(
  '33333333-3333-3333-3333-333333333333',
  'Amit',
  'Verma',
  'amit.verma@gmail.com',
  '9876543212',
  '2024-03-01 09:45:00',
  '2024-03-01 09:45:00'
);



INSERT INTO loans (
  id, user_id, loan_id, loan_type, lender_name,
  loan_amount, remaining_amount, interest_rate,
  tenure_months, emi_amount, status,
  open_date, due_date,
  created_at, modified_at
)
VALUES
(
  'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
  '11111111-1111-1111-1111-111111111111',
  'HL-1001',
  'Home Loan',
  'SBI',
  7500000.00,
  6200000.00,
  8.50,
  240,
  65000.00,
  'active',
  '2021-04-15',
  '2041-04-15',
  '2024-01-10 11:00:00',
  '2024-01-10 11:00:00'
),
(
  'aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaa2',
  '22222222-2222-2222-2222-222222222222',
  'HL-1002',
  'Home Loan',
  'HDFC',
  6000000.00,
  4800000.00,
  8.65,
  240,
  52000.00,
  'active',
  '2020-06-10',
  '2040-06-10',
  '2024-02-05 14:30:00',
  '2024-02-05 14:30:00'
),
(
  'aaaaaaa3-aaaa-aaaa-aaaa-aaaaaaaaaaa3',
  '33333333-3333-3333-3333-333333333333',
  'HL-1003',
  'Home Loan',
  'ICICI',
  9000000.00,
  8700000.00,
  8.75,
  300,
  78000.00,
  'active',
  '2023-01-05',
  '2048-01-05',
  '2024-03-01 10:00:00',
  '2024-03-01 10:00:00'
),
(
  'aaaaaaa4-aaaa-aaaa-aaaa-aaaaaaaaaaa4',
  '11111111-1111-1111-1111-111111111111',
  'HL-1004',
  'Home Loan',
  'LIC Housing Finance',
  4500000.00,
  0.00,
  8.20,
  180,
  38000.00,
  'closed',
  '2008-03-01',
  '2023-03-01',
  '2024-01-10 11:10:00',
  '2024-01-10 11:10:00'
);




INSERT INTO loans (
  id,
  user_id,
  loan_id,
  loan_type,
  lender_name,
  loan_amount,
  remaining_amount,
  interest_rate,
  tenure_months,
  emi_amount,
  status,
  open_date,
  due_date,
  created_at,
  modified_at
)
VALUES
(
  'bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbb1',
  '22222222-2222-2222-2222-222222222222',
  'LAP-2001',
  'Loan Against Property',
  'Axis Bank',
  5000000.00,
  3500000.00,
  9.75,
  180,
  52000.00,
  'active',
  '2022-08-12',
  '2037-08-12',
  '2024-02-05 15:00:00',
  '2024-02-05 15:00:00'
);



INSERT INTO loans (
  id,
  user_id,
  loan_id,
  loan_type,
  lender_name,
  loan_amount,
  remaining_amount,
  interest_rate,
  tenure_months,
  emi_amount,
  status,
  open_date,
  due_date,
  created_at,
  modified_at
)
VALUES
(
  'ccccccc1-cccc-cccc-cccc-ccccccccccc1',
  '22222222-2222-2222-2222-222222222222',
  'PL-3001',
  'Personal Loan',
  'Kotak Mahindra',
  800000.00,
  420000.00,
  13.50,
  48,
  21500.00,
  'active',
  '2023-02-10',
  '2027-02-10',
  '2024-02-05 15:10:00',
  '2024-02-05 15:10:00'
),
(
  'ccccccc2-cccc-cccc-cccc-ccccccccccc2',
  '33333333-3333-3333-3333-333333333333',
  'PL-3002',
  'Personal Loan',
  'ICICI',
  500000.00,
  0.00,
  12.90,
  36,
  16800.00,
  'closed',
  '2020-01-15',
  '2023-01-15',
  '2024-03-01 10:45:00',
  '2024-03-01 10:45:00'
);



INSERT INTO loans (
  id,
  user_id,
  loan_id,
  loan_type,
  lender_name,
  loan_amount,
  remaining_amount,
  interest_rate,
  tenure_months,
  emi_amount,
  status,
  open_date,
  due_date,
  created_at,
  modified_at
)
VALUES
(
  'ddddddd1-dddd-dddd-dddd-ddddddddddd1',
  '11111111-1111-1111-1111-111111111111',
  'GL-4001',
  'Gold Loan',
  'Muthoot Finance',
  350000.00,
  180000.00,
  10.90,
  24,
  16500.00,
  'active',
  '2024-05-01',
  '2026-05-01',
  '2024-05-01 12:00:00',
  '2024-05-01 12:00:00'
);

