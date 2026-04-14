# haddock Platform — CX Actuation Manual

> **Version**: 3.0 | **Last Updated**: April 2026 | **Audience**: Customer Experience Team
> **Classification**: Internal — Level 1 Support Guidelines

---

## 1. Introduction: Customer Persona & CX Tone

### 1.1 The Audience
Our customers are restaurant owners, executive chefs, managers, and accountants. They operate in an industry with razor-thin margins, extreme time scarcity, and high stress. They usually do their administrative work late at night or during chaotic shifts. If a metric looks wrong, they panic because they fear they are losing money. 

### 1.2 Our CX Tone
- **Direct & Concise**: They do not have time to read essays. Use bullet points and clear, numbered steps.
- **Empathetic & Reassuring**: Acknowledge the chaos of a restaurant kitchen. If they are stressed about a price spike or an OCR error, reassure them that the data is secure and the problem is easily fixable.
- **Technically Precise**: We are their trusted financial advisors. When explaining profit margins or POS syncing, our terminology must be exact (e.g., distinguishing between gross margin and net profit, or delivery notes vs. invoices).

---

## 2. Document Uploads & AI OCR

### 2.1 How the OCR Works
Restaurant staff take photos or upload PDFs of their supplier documents (delivery notes / *albaranes* and invoices / *facturas*). haddock’s AI automatically reads and extracts every single line item, quantity, unit, tax, and price. This eliminates manual data entry in Excel.

### 2.2 Troubleshooting Uploads & "Failed" Documents
**"My invoice is stuck in 'Processing' or was marked as 'Review Needed'."**
- **Root Cause**: The AI couldn't confidently read the document. This usually happens due to poor lighting, crumpled paper, or blurry photos.
- **CX Action**: 
  1. Go to the customer's **Document Inbox** in the admin panel.
  2. If the document is illegible even to a human, reply to the customer: *"Our system couldn't read the latest upload from [Supplier Name]. Could you please re-upload a clearer photo? Best practices: flatten the paper, avoid shadows cast by your phone, and ensure all corners are visible."*
  3. If it's a multi-page PDF that failed because it contained multiple different invoices merged into one document, advise the customer to use the **"Split PDF"** tool available in the Upload module.

### 2.3 Deleting or Editing Line Items
**"The AI extracted 'Coca-Cola 33cl' but the price is wrong."**
- **CX Action**: Instruct the user to click on the invoice in the **Documents** tab, click **Edit Items**, manually correct the unit price or quantity, and hit **Save**. Reassure them that manual corrections actively train the AI for their specific account, so it won't happen next time.

---

## 3. Price Fluctuation Alerts

### 3.1 Understanding the Feature
haddock tracks historical purchase data for every ingredient. If a supplier raises the price of tomatoes from €2.00/kg to €2.50/kg, haddock flags this variation and alerts the restaurateur.

### 3.2 Common Queries
**"Where do I see my price variations for the week?"**
- **CX Action**: Guide the user to the **Dashboard → Price Variations**. Explain that they can filter by supplier or by specific product category (e.g., "Meat", "Produce").

**"Why didn't I get alerted when my salmon price increased?"**
- **CX Action**: Check if the supplier changed the spelling or the exact barcode description of the product (e.g., from "Fresh Salmon 1kg" to "Premium Norwegian Salmon"). If so, the system treats it as a new product. Instruct the user to **merge the products** in the **Products** tab so the historical data connects, triggering the alert properly.

---

## 4. Dynamic Recipe Costing ("Escandallos")

### 4.1 How it Works
A recipe (*escandallo*) is the mathematical formula of a dish's cost. haddock connects these recipes directly to the live AI OCR invoice data. If the cost of cheese goes up today on an invoice, the profit margin of the cheeseburger automatically drops in the dashboard, warning the chef in real-time.

### 4.2 Handling Escandallo Issues
**"My profit margin for the Truffle Burger shows as 0% (or an error)!"**
- **Root Cause**: An ingredient in the recipe is unlinked, or the conversion metrics are missing (e.g., buying in Liters but using in Grams without a conversion factor).
- **CX Action**: 
  1. Ask the customer to open the recipe in **Menu → Escandallos**.
  2. Look for the red warning icon next to an ingredient.
  3. Instruct them to update the conversion metric (e.g., 1 Unit of Truffle Oil = 500ml). Provide a warm reassurance like: *"Once you set this conversion rate, the margin will instantly recalculate and live-sync with all future invoices!"*

---

## 5. Account & User Management

### 5.1 Inviting Staff Members
**"How do I give my head chef access without letting him see my total revenue?"**
- **CX Action**: Instruct the owner to go to **Settings → Team Members**. Click **Invite User** and select the **"Chef" or "Operations" role**. Emphasize that these roles can upload invoices and create recipes, but do NOT have access to the Financial Dashboard or total sales data.

### 5.2 Password Resets & Billing
**"I forgot my password / The login is failing."**
- **CX Action**: Send the standard password reset link. Remind them to check their promotions/spam folder.
**"I need to update my credit card for the haddock subscription."**
- **CX Action**: Direct them to **Settings → Billing**. Here they can update their payment method and download past haddock subscription invoices.

---

## 6. Integrations (POS & Accounting)

### 6.1 Understanding 360º Integrations
haddock connects to POS (Point of Sale) systems (Square, Revo, Last.app) to pull daily sales data, and accounting software (Holded) to sync expenses and generate general ledgers.

### 6.2 Setup & Sync Issues
**"How do I connect Last.app to haddock?"**
- **CX Action**: 
  1. Generate the API Key in their Last.app back office.
  2. In haddock, navigate to **Settings → Integrations → POS Systems → Last.app**.
  3. Paste the API Key and click **Connect**.
  4. Let the customer know that the initial sync can take up to 24 hours to pull historical sales data.

**"My daily sales aren't showing up from Revo."**
- **CX Action**: 
  1. First, verify the integration status under **Settings → Integrations**. If the token expired, ask them to click **Reconnect**.
  2. Explain that daily syncs happen automatically at 04:00 AM local time after the restaurant's Z-read (cierre de caja). Manual syncing can be forced by clicking the **Refresh Data** button on the Financial Dashboard.

---

## 7. Reports & Data Exports

**"My accountant needs all my invoices for Q1 in Excel."**
- **CX Action**: 
  1. Navigate to **Reports → Document Export**.
  2. Select the date range (e.g., Jan 1 to Mar 31).
  3. Choose the format: **CSV/Excel** for spreadsheet data, or **ZIP** to download the physical PDF/image files.
  4. Mention that the link will be emailed to them within 5 minutes so they don't have to wait on the page.
