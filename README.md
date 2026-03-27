# Qatar Gratuity — ERPNext 15
**Qatar Labour Law No. 14 of 2004, Article 54 — End of Service Gratuity**

---

## 📐 Gratuity Formula

```
Gratuity = (Basic Salary ÷ 30) × 21 days × Years of Service
```

| Parameter | Value |
|-----------|-------|
| Basis | Basic Salary ONLY (no allowances) |
| Days per year | 21 days (Qatar Labour Law minimum) |
| Working days/month | 30 |
| Labour Law eligibility | 1 year |
| **Company Policy eligibility** | **5 years** ← your setting |
| Partial year | Pro-rata calculated |
| Unpaid leave | Excluded from service period |

---

## 🚀 Installation

### Step 1 — Copy app to your bench
```bash
cd /home/frappe/frappe-bench/apps
cp -r /path/to/qatar_gratuity .
```

### Step 2 — Install app
```bash
cd /home/frappe/frappe-bench
bench --site your-site.local install-app qatar_gratuity
bench --site your-site.local migrate
bench build
bench restart
```

### Docker / CloudCluster install (recommended)
If your ERPNext is running in Docker (CloudCluster), run bench commands **inside** the backend container:

```bash
# from your docker host
docker compose exec backend bash

# inside container
cd /home/frappe/frappe-bench
bench get-app /workspace/qatar_gratuity
bench --site your-site.local install-app qatar_gratuity
bench --site your-site.local migrate
```

If you maintain custom images, rebuild and restart after adding the app:

```bash
docker compose build
docker compose up -d
```

---

## ⚙️ ERPNext Setup (Do this ONCE)

### 1. Create Salary Component — "Basic"
```
HR → Salary Component → New
  Component Name : Basic
  Type           : Earning
  Is Tax Applicable: As needed
```

### 2. Create Salary Structure — "Qatar Standard"
```
HR → Salary Structure → New
  Name      : Qatar Standard
  Company   : Your Company
  Currency  : QAR

  Earnings table:
    Component: Basic | Amount: [set per employee]
    Component: Housing Allowance | Amount: [set per employee]
    Component: Transport Allowance | Amount: [set per employee]

  NOTE: Only "Basic" is used for gratuity — others are excluded automatically.
```

### 3. Assign Salary Structure to Employee
```
HR → Salary Structure Assignment → New
  Employee          : [Select Employee]
  Salary Structure  : Qatar Standard
  From Date         : [Joining Date]
  Base              : [Monthly Basic Salary in QAR]
```

### 4. Create Accounts in Chart of Accounts
```
Accounting → Chart of Accounts

Under "Expenses":
  New Account: "Gratuity Expense"
  Type: Expense

Under "Current Liabilities":
  New Account: "Gratuity Payable"
  Type: Payable
```

---

## 📋 How to Use

### Method 1 — Quick Calculator (Employee Form)
```
HR → Employee → Open Employee Record
→ Actions button → "Calculate Qatar Gratuity"
→ Enter Termination Date
→ Choose Policy (5yr company / 1yr law)
→ Click Calculate
→ Popup shows full breakdown
→ Option to create Gratuity Voucher
```

### Method 2 — Gratuity Voucher (Full Document)
```
HR → Qatar Gratuity Voucher → New
→ Select Employee
→ Set Termination Date
→ Save → Calculates automatically
→ Submit → Creates Journal Entry
```

### Method 3 — API / Python Console
```python
from qatar_gratuity.utils.gratuity_calculator import calculate_qatar_gratuity

result = calculate_qatar_gratuity(
    employee           = "HR-EMP-00001",
    to_date            = "2025-03-31",
    use_company_policy = True,   # False = Labour Law 1yr
)
print(result)
```

---

## 🔢 Calculation Example

| Field | Value |
|-------|-------|
| Employee | Ahmed Al-Mansouri |
| Joining Date | 01-Jan-2018 |
| Termination Date | 31-Mar-2025 |
| Service | 7 years, 2 months, 30 days |
| Basic Salary | QAR 5,000/month |
| Daily Basic | 5000 ÷ 30 = QAR 166.67 |
| Per Year Gratuity | 166.67 × 21 = QAR 3,500 |
| **Total Gratuity** | **3,500 × 7.25 = QAR 25,375** |

---

## 📁 File Structure

```
qatar_gratuity/
├── qatar_gratuity/
│   ├── hooks.py                          ← App hooks
│   ├── utils/
│   │   ├── gratuity_calculator.py        ← Core calculation logic ⭐
│   │   └── gratuity_accrual.py           ← Monthly accrual scheduler
│   ├── doctype/
│   │   └── qatar_gratuity_voucher/
│   │       ├── qatar_gratuity_voucher.py   ← DocType controller
│   │       └── qatar_gratuity_voucher.json ← DocType definition
│   └── public/js/
│       └── employee_gratuity.js           ← Employee form button
└── README.md
```

---

## ⚠️ Important Notes

1. **Eligibility**: Employee WILL NOT get gratuity if service < 5 years (company policy)
2. **Article 61**: If employee is dismissed for misconduct — set status to "Cancelled" in voucher
3. **Unpaid Leave**: System automatically deducts approved LWP (Leave Without Pay) days
4. **Salary Source**: System reads from last active Salary Structure Assignment
5. **Accounts**: Create "Gratuity Expense" and "Gratuity Payable" accounts before submitting vouchers

---

## 🆘 Troubleshooting

| Error | Solution |
|-------|----------|
| Doctype create manually karna hai? | **Nahi**. `Qatar Gratuity Voucher` DocType app install/migrate par auto-sync hota hai from JSON. Run `bench --site your-site.local migrate` and then search `Qatar Gratuity Voucher` in Awesome Bar. |
| "No Salary Structure Assignment found" | Assign Salary Structure to employee first |
| "Basic Salary component not found" | Name your earnings component exactly "Basic" |
| "Gratuity accounts not found" | Create accounts as described in Step 4 above |
| Employee shows 0 years service | Check Date of Joining is set on Employee |
| `ModuleNotFoundError: No module named 'qatar_gratuity'` | App code is not available inside backend container. Run `bench get-app` **inside** the container, then `bench --site ... install-app qatar_gratuity`. |
| `App qatar_gratuity is not in installed_apps` after restart | Run `bench --site your-site.local install-app qatar_gratuity` and `bench --site your-site.local migrate`, then restart containers. |
| `ImportError` / failed app install due to old caches | Run `bench clear-cache && bench clear-website-cache`, then retry install. |
| App installed but module not visible in Desk | Run `bench --site your-site.local migrate && bench --site your-site.local clear-cache`, then `bench --site your-site.local execute qatar_gratuity.setup.install.ensure_workspace` and hard refresh browser (`Ctrl+Shift+R`). |
