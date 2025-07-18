import React, { useState, useEffect } from "react";
import {
	EXPENSE_TYPES,
	PAYMENT_TYPES,
	CURRENCIES,
} from "../../utils/constants";
import { formatFieldName } from "../../utils/formatters";

const EditableExpenseFields = ({
	expenseData,
	onSave,
	onCancel,
	isLoading = false,
}) => {
	const [editedData, setEditedData] = useState(expenseData || {});
	const [errors, setErrors] = useState({});
	const [hasChanges, setHasChanges] = useState(false);

	// Track changes
	useEffect(() => {
		const hasAnyChanges = Object.keys(editedData).some(
			(key) => editedData[key] !== expenseData[key]
		);
		setHasChanges(hasAnyChanges);
	}, [editedData, expenseData]);

	// Field update handler
	const handleFieldChange = (field, value) => {
		setEditedData((prev) => ({ ...prev, [field]: value }));

		// Clear error for this field
		if (errors[field]) {
			setErrors((prev) => ({ ...prev, [field]: null }));
		}
	};

	// Validation
	const validateFields = () => {
		const newErrors = {};

		if (!editedData.vendor?.trim()) {
			newErrors.vendor = "Vendor is required";
		}

		if (!editedData.amount || editedData.amount <= 0) {
			newErrors.amount = "Valid amount is required";
		}

		if (!editedData.transaction_date) {
			newErrors.transaction_date = "Date is required";
		}

		if (!editedData.expense_type) {
			newErrors.expense_type = "Expense type is required";
		}

		setErrors(newErrors);
		return Object.keys(newErrors).length === 0;
	};

	// Save handler
	const handleSave = () => {
		if (validateFields()) {
			onSave(editedData);
		}
	};

	// Cancel handler
	const handleCancel = () => {
		setEditedData(expenseData);
		setErrors({});
		setHasChanges(false);
		onCancel();
	};

	// Get field icon
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

	// Render field input based on type
	const renderFieldInput = (field, value) => {
		const commonProps = {
			value: value || "",
			onChange: (e) => handleFieldChange(field, e.target.value),
			className: `edit-field-input ${errors[field] ? "error" : ""}`,
		};

		switch (field) {
			case "expense_type":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select type...</option>
						{EXPENSE_TYPES.map((type) => (
							<option key={type} value={type}>
								{type}
							</option>
						))}
					</select>
				);

			case "payment_type":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select payment...</option>
						{PAYMENT_TYPES.map((type) => (
							<option key={type} value={type}>
								{type}
							</option>
						))}
					</select>
				);

			case "currency":
				return (
					<select {...commonProps} value={value || "USD"}>
						{CURRENCIES.map((curr) => (
							<option key={curr} value={curr}>
								{curr}
							</option>
						))}
					</select>
				);

			case "amount":
				return (
					<input
						{...commonProps}
						type="number"
						step="0.01"
						min="0"
						placeholder="0.00"
						onChange={(e) =>
							handleFieldChange(
								field,
								parseFloat(e.target.value) || 0
							)
						}
					/>
				);

			case "transaction_date":
				return (
					<input
						{...commonProps}
						type="date"
						max={new Date().toISOString().split("T")[0]}
					/>
				);

			case "business_purpose":
			case "comment":
				return (
					<textarea
						{...commonProps}
						rows="3"
						placeholder={`Enter ${formatFieldName(
							field
						).toLowerCase()}...`}
					/>
				);

			default:
				return (
					<input
						{...commonProps}
						type="text"
						placeholder={`Enter ${formatFieldName(
							field
						).toLowerCase()}...`}
					/>
				);
		}
	};

	return (
		<div className="editable-expense-container">
			<div className="edit-header">
				<div className="edit-title">
					<span className="edit-icon">✏️</span>
					<h4>Edit Expense Details</h4>
				</div>
				<div className="edit-status">
					{hasChanges && (
						<span className="changes-indicator">
							<span className="changes-dot"></span>
							Unsaved changes
						</span>
					)}
				</div>
			</div>

			<div className="edit-fields-grid">
				{Object.entries(editedData).map(([field, value]) => (
					<div
						key={field}
						className={`edit-field-item ${
							errors[field] ? "has-error" : ""
						}`}
					>
						<div className="edit-field-label">
							<span className="field-icon">
								{getFieldIcon(field)}
							</span>
							<span className="field-label-text">
								{formatFieldName(field)}
								{[
									"vendor",
									"amount",
									"transaction_date",
									"expense_type",
								].includes(field) && (
									<span className="required-indicator">
										*
									</span>
								)}
							</span>
						</div>

						<div className="edit-field-input-container">
							{renderFieldInput(field, value)}
							{errors[field] && (
								<div className="field-error">
									<span className="error-icon">⚠️</span>
									{errors[field]}
								</div>
							)}
						</div>
					</div>
				))}
			</div>

			<div className="edit-actions">
				<button
					onClick={handleCancel}
					disabled={isLoading}
					className="edit-btn secondary"
				>
					<span className="btn-icon">↩️</span>
					Cancel
				</button>

				<button
					onClick={handleSave}
					disabled={isLoading || !hasChanges}
					className="edit-btn primary"
				>
					<span className="btn-icon">💾</span>
					{isLoading ? "Saving..." : "Save Changes"}
				</button>
			</div>
		</div>
	);
};

export default EditableExpenseFields;
