import React, { useState } from "react";

const TaxComplianceUI = ({ onAgreeAll, isLoading }) => {
	const [hasAgreed, setHasAgreed] = useState(false);

	const handleAgreeAll = () => {
		setHasAgreed(true);
		onAgreeAll();
	};

	return (
		<div className="tax-compliance-container">
			<div className="compliance-info">
				<div className="policy-item">
					<div className="policy-header">
						<span className="policy-icon">🎁</span>
						<strong>Gift Policy Compliance Certification</strong>
					</div>
					<p className="policy-description">
						I certify that this expense complies with company gift
						policy guidelines
					</p>
				</div>

				<div className="policy-item">
					<div className="policy-header">
						<span className="policy-icon">🏛️</span>
						<strong>IRS T&E Tax Policy Certification</strong>
					</div>
					<p className="policy-description">
						I certify that this expense complies with IRS Travel &
						Entertainment tax policies
					</p>
				</div>
			</div>

			<div className="compliance-actions">
				<button
					onClick={handleAgreeAll}
					disabled={isLoading || hasAgreed}
					className={`compliance-btn primary ${
						hasAgreed ? "agreed" : ""
					}`}
				>
					<span className="btn-icon">{hasAgreed ? "✅" : "✓"}</span>
					<span>
						{hasAgreed
							? "Agreed to Both Policies"
							: "I Agree to Both Policies"}
					</span>
				</button>
			</div>

			{!hasAgreed && (
				<div className="compliance-warning">
					⚠️ You must agree to both policies to proceed with creating
					the expense report
				</div>
			)}
		</div>
	);
};

export default TaxComplianceUI;
