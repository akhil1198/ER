// Enhanced EditableExpenseFields.jsx - Compatible with Enhanced Expense Data
import React, { useState, useEffect } from "react";

// Constants for dropdown options
const EXPENSE_CATEGORIES = [
	"Meals & Entertainment",
	"Transportation",
	"Lodging",
	"Office Supplies",
	"Travel",
	"Other",
];

const EXPENSE_TYPE_OPTIONS = {
	"Meals & Entertainment": [
		"Meals Employee(s) Only - In Town",
		"Meals Employee(s) Only - Out of Town",
		"Meals with Carrier(s)",
		"Meals with Client Prospect(s)",
		"Meals with Client(s) - In Town",
		"Meals with Client(s) - Out of Town",
		"Meals with M&A Prospect(s)",
	],
	Transportation: [
		"Airfare",
		"Car Rental",
		"Gas/Fuel",
		"Parking",
		"Taxi/Rideshare",
		"Train",
	],
	Lodging: ["Hotel", "Lodging"],
	"Office Supplies": ["Office Supplies", "Software"],
	Travel: ["Travel Expense", "Conference", "Training"],
	Other: ["Other Expense"],
};

const PAYMENT_TYPES = [
	"Cash",
	"Personal Credit Card",
	"Corporate Credit Card",
	"Bank Transfer",
	"Check",
	"Other",
];

const CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"];
const MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Other"];

const EnhancedEditableExpenseFields = ({
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

		// Clear error for this field when user starts typing
		if (errors[field]) {
			setErrors((prev) => ({ ...prev, [field]: null }));
		}

		// Handle category change - reset expense type
		if (field === "expense_category") {
			setEditedData((prev) => ({
				...prev,
				expense_category: value,
				expense_type: "", // Reset expense type when category changes
			}));
		}
	};

	// Validation
	const validateFields = () => {
		const newErrors = {};

		// Required fields
		if (!editedData.vendor?.trim()) {
			newErrors.vendor = "Vendor is required";
		}

		if (!editedData.amount || editedData.amount <= 0) {
			newErrors.amount = "Valid amount is required";
		}

		if (!editedData.transaction_date) {
			newErrors.transaction_date = "Date is required";
		}

		if (!editedData.expense_category) {
			newErrors.expense_category = "Expense category is required";
		}

		if (!editedData.expense_type) {
			newErrors.expense_type = "Expense type is required";
		}

		// Meal-specific validations
		if (editedData.expense_category === "Meals & Entertainment") {
			if (!editedData.meal_type) {
				newErrors.meal_type = "Meal type is required for meals";
			}

			if (!editedData.business_purpose?.trim()) {
				newErrors.business_purpose =
					"Business purpose is required for meals";
			}

			if (editedData.attendees_count && editedData.attendees_count < 1) {
				newErrors.attendees_count =
					"Attendees count must be at least 1";
			}

			// Check if client/prospect name is needed
			if (
				editedData.expense_type &&
				(editedData.expense_type.includes("Client") ||
					editedData.expense_type.includes("Prospect"))
			) {
				if (!editedData.client_prospect_name?.trim()) {
					newErrors.client_prospect_name =
						"Client/Prospect name is required for client meals";
				}
			}
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

	// Format field name for display
	const formatFieldName = (fieldName) => {
		const fieldNames = {
			expense_category: "Expense Category",
			expense_type: "Expense Type",
			meal_type: "Meal Type",
			attendees_count: "Number of Attendees",
			client_prospect_name: "Client/Prospect Name",
			transaction_date: "Transaction Date",
			business_purpose: "Business Purpose",
			vendor: "Vendor",
			city: "City",
			country: "Country",
			payment_type: "Payment Type",
			amount: "Amount",
			currency: "Currency",
			comment: "Comment",
		};
		return (
			fieldNames[fieldName] ||
			fieldName
				.replace(/_/g, " ")
				.replace(/\b\w/g, (l) => l.toUpperCase())
		);
	};

	// Get field icon
	const getFieldIcon = (field) => {
		const icons = {
			expense_category: "📂",
			expense_type: "🏷️",
			meal_type: "🍽️",
			attendees_count: "👥",
			client_prospect_name: "🏢",
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
			case "expense_category":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select category...</option>
						{EXPENSE_CATEGORIES.map((category) => (
							<option key={category} value={category}>
								{category}
							</option>
						))}
					</select>
				);

			case "expense_type":
				const availableTypes =
					EXPENSE_TYPE_OPTIONS[editedData.expense_category] || [];
				return (
					<select
						{...commonProps}
						value={value || ""}
						disabled={!editedData.expense_category}
					>
						<option value="">Select type...</option>
						{availableTypes.map((type) => (
							<option key={type} value={type}>
								{type}
							</option>
						))}
					</select>
				);

			case "meal_type":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select meal type...</option>
						{MEAL_TYPES.map((type) => (
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

			case "attendees_count":
				return (
					<input
						{...commonProps}
						type="number"
						min="1"
						placeholder="1"
						onChange={(e) =>
							handleFieldChange(
								field,
								parseInt(e.target.value) || 1
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

	// Determine which fields to show
	const getFieldsToShow = () => {
		const baseFields = [
			"expense_category",
			"expense_type",
			"transaction_date",
			"vendor",
			"amount",
			"currency",
			"payment_type",
			"business_purpose",
			"city",
			"country",
			"comment",
		];

		// Add meal-specific fields if it's a meal
		if (editedData.expense_category === "Meals & Entertainment") {
			const mealFields = ["meal_type", "attendees_count"];

			// Add client/prospect field if it's a client meal
			if (
				editedData.expense_type &&
				(editedData.expense_type.includes("Client") ||
					editedData.expense_type.includes("Prospect"))
			) {
				mealFields.push("client_prospect_name");
			}

			// Insert meal fields after expense_type
			const typeIndex = baseFields.indexOf("expense_type");
			baseFields.splice(typeIndex + 1, 0, ...mealFields);
		}

		return baseFields;
	};

	const fieldsToShow = getFieldsToShow();
	const isMealsCategory =
		editedData.expense_category === "Meals & Entertainment";
	const isClientMeal =
		editedData.expense_type &&
		(editedData.expense_type.includes("Client") ||
			editedData.expense_type.includes("Prospect"));

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
				{fieldsToShow.map((field) => {
					const value = editedData[field];
					return (
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
										"expense_category",
										"expense_type",
										...(isMealsCategory
											? ["meal_type", "business_purpose"]
											: []),
										...(isClientMeal
											? ["client_prospect_name"]
											: []),
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
					);
				})}
			</div>

			{/* Helpful hints for meal expenses */}
			{isMealsCategory && (
				<div className="meal-hints">
					<div className="hint-item">
						<span className="hint-icon">💡</span>
						<span>
							For client meals, ensure you provide the
							client/prospect company name
						</span>
					</div>
					<div className="hint-item">
						<span className="hint-icon">📝</span>
						<span>
							Business purpose should clearly explain the reason
							for the meal
						</span>
					</div>
				</div>
			)}

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

export default EnhancedEditableExpenseFields;
