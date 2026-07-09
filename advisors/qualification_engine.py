"""
Module 5: Qualification Insights Business Rules Engine

This module evaluates customer data against business rules and generates:
- Risk Band (Low/Moderate/High)
- Confidence Score (based on data completeness)
- Insights (triggered rules)
"""

from decimal import Decimal


class QualificationEngine:
    """Rule-based qualification insights generator"""

    def __init__(self, customer):
        self.customer = customer
        self.triggered_rules = []
        self.insights = []
        self.risk_factors = 0
        self.total_data_points = 0

    def evaluate(self):
        """
        Main evaluation method - runs all business rules and generates insights
        Returns: {risk_band, confidence, insights, triggered_rules}
        """
        self._check_high_age()
        self._check_family_added()
        self._check_ped_declared()
        self._check_low_existing_cover()
        self._check_premium_budget()
        self._calculate_data_completeness()

        risk_band = self._determine_risk_band()
        confidence = self._calculate_confidence()

        return {
            "risk_band": risk_band,
            "confidence": round(confidence, 2),
            "insights": self.insights,
            "triggered_rules": self.triggered_rules,
        }

    # ============ BUSINESS RULES ============

    def _check_high_age(self):
        """
        Rule: High Age
        If age > 55:
        Suggest asking:
        - Medical history
        - Current medication
        - Hospitalization history
        - Existing cover
        """
        if self.customer.age > 55:
            self.triggered_rules.append("High Age (>55)")
            self.insights.append("Customer is above 55 years of age.")
            self.insights.append(
                "Medical history, current medication, and hospitalization details are important for risk assessment."
            )
            self.risk_factors += 1

        self.total_data_points += 1

    def _check_family_added(self):
        """
        Rule: Family Added
        If spouse or children exist:
        Suggest asking:
        - Floater coverage
        - Individual coverage
        - Dependent requirements
        """
        family_members = self.customer.family_members.all()

        if family_members.exists():
            self.triggered_rules.append("Family Members Present")
            self.insights.append("Family members identified.")
            self.insights.append(
                "Floater coverage and individual coverage options should be discussed to protect dependents."
            )
            self.risk_factors += 1

        self.total_data_points += 1

    def _check_ped_declared(self):
        """
        Rule: PED Declared
        If a disease is declared:
        Suggest asking:
        - Duration
        - Medication
        - Complications
        - Recent reports
        """
        medical_disclosures = self.customer.medical_disclosures.all()

        if medical_disclosures.exists():
            diseases = [md.disease_name for md in medical_disclosures]
            self.triggered_rules.append("Pre-existing Disease(s) Declared")
            self.insights.append(
                f"Pre-existing disease(s) declared: {', '.join(diseases)}."
            )
            self.insights.append(
                "Duration of disease, current medications, and recent medical reports are crucial for underwriting."
            )
            self.risk_factors += 2  # Higher weight for PED

        self.total_data_points += 1

    def _check_low_existing_cover(self):
        """
        Rule: Low Existing Cover
        If existing coverage is low (< ₹5,00,000):
        Suggest asking:
        - Desired coverage amount
        - Super top-up requirement
        - Portability options
        """
        insurance_covers = self.customer.insurance_covers.all()
        total_existing_cover = sum(
            cover.coverage_amount for cover in insurance_covers
        )

        COVERAGE_THRESHOLD = Decimal("500000")  # ₹5,00,000

        if total_existing_cover < COVERAGE_THRESHOLD:
            self.triggered_rules.append("Low Existing Cover")
            self.insights.append(
                f"Current coverage appears low (₹{total_existing_cover:,.0f}) compared to desired protection."
            )
            self.insights.append(
                "Desired coverage amount, super top-up options, and portability should be discussed."
            )
            self.risk_factors += 1

        self.total_data_points += 1

    def _check_premium_budget(self):
        """
        Rule: Budget Missing
        If premium_budget is not provided:
        Suggest asking:
        - Monthly premium comfort
        - Annual premium comfort
        """
        if not self.customer.premium_budget:
            self.triggered_rules.append("Premium Budget Not Specified")
            self.insights.append("Premium budget information is missing.")
            self.insights.append(
                "Customer's monthly and annual premium comfort levels should be identified."
            )
            self.risk_factors += 0.5  # Lower weight

        self.total_data_points += 1

    def _calculate_data_completeness(self):
        """
        Calculate how complete the customer profile is
        Influences confidence score
        """
        completeness_score = 0
        total_fields = 7  # Total possible fields to check

        # Check basic info
        if self.customer.age:
            completeness_score += 1
        if self.customer.occupation:
            completeness_score += 1
        if self.customer.annual_income:
            completeness_score += 1

        # Check family info
        if self.customer.family_members.exists():
            completeness_score += 1

        # Check medical info
        if self.customer.medical_disclosures.exists():
            completeness_score += 1

        # Check insurance info
        if self.customer.insurance_covers.exists():
            completeness_score += 1

        # Check budget
        if self.customer.premium_budget:
            completeness_score += 1

        self.data_completeness = completeness_score / total_fields

    def _determine_risk_band(self):
        """
        Determine risk band based on triggered rules
        Low: 0-1 risk factors
        Moderate: 1-2.5 risk factors
        High: 2.5+ risk factors
        """
        if self.risk_factors < 1:
            return "Low"
        elif self.risk_factors < 2.5:
            return "Moderate"
        else:
            return "High"

    def _calculate_confidence(self):
        """
        Calculate confidence score (0.0 to 1.0)
        Based on:
        - Data completeness (60% weight)
        - Number of triggered rules (40% weight)
        """
        # More complete data = higher confidence
        completeness_confidence = self.data_completeness * 0.6

        # More triggered rules = more patterns detected = higher confidence
        # (but capped at max 0.4)
        rules_triggered = min(len(self.triggered_rules) / 5, 1.0) * 0.4

        confidence = completeness_confidence + rules_triggered
        return min(confidence, 1.0)  # Cap at 1.0