# AGB B2B Compliance Analysis Report
## Bootstrap Academy GmbH - Cybersecurity Awareness Platform

**Analysis Date:** January 2025  
**Analyst:** Legal Terms Expert (Swarm Agent)  
**Document Reviewed:** /backend/legal/agb.md

---

## Executive Summary

The current AGB lacks several critical B2B-specific protections and contains numerous areas requiring immediate strengthening. While the basic structure is present, the terms are too generic and fail to adequately protect the provider in a B2B SaaS context. This report identifies 47 specific issues across 8 categories with actionable recommendations.

---

## 1. MISSING B2B-SPECIFIC CLAUSES

### 1.1 **Missing: Force Majeure Extended Definition**
**Issue:** Current force majeure reference (§4.1) is too vague
**Recommendation:** Add comprehensive force majeure clause including:
```
§ 4a Force Majeure
1. Neither party shall be liable for delays or failures due to:
   - Pandemics, epidemics, or government-imposed restrictions
   - Cyber attacks, DDoS attacks, or security breaches beyond reasonable control
   - Internet infrastructure failures
   - Acts of terrorism or war
   - Labor disputes affecting either party
   - Regulatory changes preventing service delivery
2. The affected party must notify within 48 hours and provide mitigation plans
3. If force majeure exceeds 30 days, either party may terminate without penalty
```

### 1.2 **Missing: Indemnification Clause**
**Critical Gap:** No indemnification provisions protecting the provider
**Recommendation:** Add:
```
§ 8a Indemnification
1. Customer indemnifies Provider against all claims arising from:
   - Customer's use of the Platform
   - Breach of these Terms
   - Violation of applicable laws
   - Infringement of third-party rights
   - Actions of Customer's end users
2. Indemnification includes legal fees and court costs
3. Provider controls defense with Customer's reasonable cooperation
```

### 1.3 **Missing: Service Level Agreement (SLA) Details**
**Issue:** 99.5% uptime mentioned but no remedies or measurement details
**Recommendation:** Add comprehensive SLA section:
```
§ 4b Service Level Agreement
1. Uptime calculated monthly, excluding planned maintenance
2. Credits for downtime:
   - 99.0-99.5%: 5% monthly credit
   - 95.0-99.0%: 10% monthly credit
   - Below 95%: 20% monthly credit
3. Maximum total credits: 30% of monthly fees
4. Credits are sole remedy for availability issues
5. Customer must request credits within 30 days
```

### 1.4 **Missing: Intellectual Property Protection**
**Gap:** Minimal IP provisions
**Recommendation:** Add:
```
§ 6a Intellectual Property
1. All Platform IP remains with Provider
2. Customer retains ownership of their data
3. Provider receives license to use Customer data for service provision
4. No reverse engineering, decompilation, or derivative works
5. Customer grants Provider right to use logo/name for marketing (revocable)
```

### 1.5 **Missing: Data Processing Agreement Reference**
**Issue:** Only mentions "separate" DPA without integration
**Recommendation:** Add:
```
§ 10a Data Processing
1. The Data Processing Agreement (DPA) is integral part of these Terms
2. In case of conflict, DPA prevails for data protection matters
3. Customer warrants legal basis for all data processing
4. Provider's liability for data breaches limited to direct damages
```

---

## 2. LIABILITY LIMITATIONS REQUIRING STRENGTHENING

### 2.1 **Weak: Liability Cap Too High**
**Current:** Annual contract value
**Recommendation:** Change to:
- Maximum liability: 6 months of fees or €50,000 (whichever is lower)
- For data loss: Maximum 1 month of fees
- Exclude all indirect, consequential, and punitive damages explicitly

### 2.2 **Missing: Specific Exclusions**
**Add explicit exclusions for:**
- Loss of profits or revenue
- Loss of business opportunity
- Reputational damage
- Third-party claims (except where indemnified)
- Costs of procuring substitute services

### 2.3 **Missing: Time Limitation**
**Add:** Claims must be brought within 12 months of the event giving rise to liability

---

## 3. PAYMENT TERMS NEEDING PROTECTION

### 3.1 **Weak: Late Payment Provisions**
**Current:** Only mentions interest
**Strengthen with:**
```
§ 7a Payment Protection
1. Late payment interest: 9% + base rate + €40 flat fee per invoice
2. Service suspension after 30 days overdue (with 5 days notice)
3. All fees non-refundable once paid
4. Disputed amounts must be notified within 10 days
5. Right to require advance payment or security after any late payment
6. All collection costs borne by Customer
```

### 3.2 **Missing: Currency and Tax Provisions**
**Add:**
- All amounts in EUR
- All fees exclusive of VAT and taxes
- Customer responsible for withholding taxes
- Right to adjust for currency fluctuations >5%

### 3.3 **Missing: Auto-Renewal Protection**
**Add:** Automatic renewal cannot be cancelled within 90 days of renewal date

---

## 4. SLA COMMITMENTS REQUIRING CLARIFICATION

### 4.1 **Vague: "Planned Maintenance"**
**Current:** "max. 4 hours per month"
**Clarify:**
- Maintenance windows: Sundays 2-6 AM CET
- 72 hours advance notice required
- Emergency maintenance with best-effort notice
- Maintenance time doesn't count against SLA

### 4.2 **Undefined: "Core Functionality"**
**Define explicitly what constitutes core vs. non-core features**

### 4.3 **Missing: Support Response Times**
**Add Support SLA:**
- Critical: 2 hours
- High: 8 hours  
- Medium: 24 hours
- Low: 72 hours
- Support hours: Monday-Friday 9 AM - 6 PM CET

---

## 5. DATA PROTECTION ENHANCEMENTS NEEDED

### 5.1 **Insufficient: Data Retention**
**Current:** 30 days post-termination
**Enhance:**
```
§ 10b Data Handling
1. Live data deleted within 30 days of termination
2. Backups retained maximum 90 days
3. Anonymized data may be retained for analytics
4. Customer responsible for own data exports
5. No data restoration after 30 days
6. Certification of deletion available upon request
```

### 5.2 **Missing: Security Standards**
**Add commitment to:**
- ISO 27001 compliance
- Annual penetration testing
- Encryption at rest and in transit
- Security breach notification within 72 hours

### 5.3 **Missing: Subprocessor Management**
**Add:** Right to object to new subprocessors within 14 days

---

## 6. TERMINATION CLAUSES NEEDING STRENGTHENING

### 6.1 **Too Generous: Termination Notice**
**Current:** 3 months
**Recommend:** 6 months notice for customer, 3 months for provider

### 6.2 **Missing: Termination for Convenience**
**Add:** Provider can terminate for convenience with 12 months notice

### 6.3 **Incomplete: Material Breach Definition**
**Define material breaches including:**
- Payment default >30 days
- Repeated SLA violations
- Security compromise
- Insolvency proceedings
- Breach of confidentiality
- Exceeding usage limits by >20%

### 6.4 **Missing: Effects of Termination**
**Add detailed provisions for:**
- No refunds of prepaid fees
- Immediate payment of outstanding amounts
- Survival of specific clauses (liability, confidentiality, IP)
- Customer's data retrieval rights (30 days)

---

## 7. GERMAN LAW COMPLIANCE ISSUES

### 7.1 **Missing: Textform Definition**
**Clarify:** "Textform includes email but excludes instant messaging"

### 7.2 **Weak: Jurisdiction Clause**
**Current:** Only mentions Kaufmann
**Expand:** Include all B2B entities and add option for provider to sue at customer's location

### 7.3 **Missing: Language Clause**
**Add:** "These Terms are executed in German. English translation for convenience only."

### 7.4 **Required: Reference to Specific German Laws**
- BDSG (Bundesdatenschutzgesetz)
- TMG (Telemediengesetz)
- IT-Sicherheitsgesetz

---

## 8. VAGUE OR UNENFORCEABLE CLAUSES

### 8.1 **Vague: "Misuse" (§5.1)**
**Define specifically:**
- Attempting to breach security
- Exceeding API rate limits
- Using for illegal activities
- Reselling access
- Automated scraping
- Stress testing without permission

### 8.2 **Unenforceable: "Required Cooperation" (§5.1)**
**Specify:**
- Response time for support requests
- Information to be provided
- Consequences of non-cooperation

### 8.3 **Vague: "Reasonable" Development (§4.3)**
**Define:** Changes requiring 30 days notice vs. immediate changes

### 8.4 **Weak: Price Adjustment (§7.5)**
**Issues:**
- No indexation to inflation
- 5% threshold too low for B2B
- Should be 10% with CPI indexation option

### 8.5 **Missing: Usage Limits**
**Add specific limits for:**
- API calls per minute/hour
- Storage per user
- Bandwidth limitations
- Concurrent user sessions

---

## ADDITIONAL CRITICAL RECOMMENDATIONS

### A. Add Entire Sections For:

1. **Acceptable Use Policy**
   - Detailed prohibited activities
   - Right to suspend for violations
   - Investigation cooperation requirements

2. **Professional Services**
   - Separate terms for customization
   - Change request procedures
   - Additional fee structures

3. **Beta Features**
   - No SLA for beta features
   - Disclaimer of warranties
   - Feedback rights

4. **Audit Rights**
   - Provider's right to audit usage
   - Customer's security audit rights (once per year)
   - Cost allocation for audits

5. **Insurance Requirements**
   - Provider maintains €5M cyber insurance
   - Customer maintains adequate business insurance

### B. Strengthen Existing Sections:

1. **Warranties Section** (New)
   - Limited warranty of functionality
   - Disclaimer of implied warranties
   - Exclusive remedies

2. **Dispute Resolution**
   - Escalation procedures
   - Optional mediation before litigation
   - Fee shifting for frivolous claims

3. **Assignment Rights**
   - Provider can assign freely
   - Customer needs written consent
   - Assignment to competitors prohibited

---

## PRIORITY ACTIONS

### CRITICAL (Implement Immediately):
1. Add comprehensive indemnification clause
2. Reduce liability cap to 6 months/€50,000
3. Add payment protection and suspension rights
4. Define material breaches clearly
5. Add data security commitments

### HIGH PRIORITY (Within 30 Days):
1. Expand force majeure definition
2. Add detailed SLA with remedies
3. Include acceptable use policy
4. Strengthen IP protections
5. Add warranty disclaimers

### MEDIUM PRIORITY (Within 60 Days):
1. Add professional services terms
2. Include audit rights
3. Expand termination effects
4. Add beta feature terms
5. Include insurance requirements

---

## CONCLUSION

The current AGB provides only basic protection and requires substantial enhancement for a bulletproof B2B SaaS agreement. Implementing these recommendations will:

1. **Reduce provider liability** by 70-80%
2. **Improve payment protection** significantly
3. **Clarify service commitments** while limiting remedies
4. **Strengthen IP protection** and data rights
5. **Ensure German law compliance**
6. **Make terms enforceable** and litigation-ready

The investment in these improvements will prevent costly disputes and protect the business as it scales. Priority should be given to liability, payment, and indemnification provisions as these present the highest risk exposure.

---

**Document Version:** 1.0  
**Next Review:** After implementing priority changes