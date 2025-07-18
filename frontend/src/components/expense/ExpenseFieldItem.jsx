import React from "react";
import { formatFieldValue, formatFieldName } from "../../utils/formatters";

const ExpenseFieldItem = ({ fieldKey, value, isImportant = false }) => {
	const getFieldIcon = (field) => {
		const icons = {
			expense_type: "🏷️",
			transaction_date: "📅",
			business_purpose: "🎯",
			vendor: "🏪",
			city: "🏙️",
			country: "🌍",
			payment_type: "💳",
			amount: "💰",
			currency: "💱",
			comment: "💬",
		};
		return icons[field] || "📝";
	};

	const displayValue = formatFieldValue(value);

	return (
		<div className={`expense-field-item ${isImportant ? "important" : ""}`}>
			<div className="field-label-container">
				<span className="field-icon">{getFieldIcon(fieldKey)}</span>
				<span className="field-label-text">
					{formatFieldName(fieldKey)}
				</span>
			</div>
			<div className="field-value-container">
				<span className="field-value-text">{displayValue}</span>
				{value && <span className="field-check">✓</span>}
			</div>
		</div>
	);
};

export default ExpenseFieldItem;
