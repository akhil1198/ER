// frontend/src/components/expense/DynamicExpenseForm.jsx - FIXED VERSION

import React, { useState, useEffect } from "react";
import { formatFieldName } from "../../utils/formatters";

const DynamicExpenseForm = ({
	expenseTypeId,
	initialData = {},
	onSave,
	onCancel,
	isLoading = false,
}) => {
	const [formData, setFormData] = useState(initialData);
	const [errors, setErrors] = useState({});
	const [hasChanges, setHasChanges] = useState(false);

	// Track changes
	useEffect(() => {
		const hasAnyChanges = Object.keys(formData).some(
			(key) => formData[key] !== initialData[key]
		);
		setHasChanges(hasAnyChanges);
	}, [formData, initialData]);

	const handleFieldChange = (fieldName, value) => {
		setFormData((prev) => ({ ...prev, [fieldName]: value }));

		// Clear error for this field
		if (errors[fieldName]) {
			setErrors((prev) => ({ ...prev, [fieldName]: null }));
		}
	};

	const validateForm = () => {
		const newErrors = {};

		// Basic validation for required fields
		const requiredFields = [
			"vendor_description",
			"amount",
			"transaction_date",
			"business_purpose",
		];

		requiredFields.forEach((field) => {
			if (!formData[field] || formData[field] === "") {
				newErrors[field] = `${formatFieldName(field)} is required`;
			}
		});

		// Amount validation
		if (
			formData.amount &&
			(isNaN(formData.amount) || parseFloat(formData.amount) <= 0)
		) {
			newErrors.amount = "Amount must be a valid number greater than 0";
		}

		setErrors(newErrors);
		return Object.keys(newErrors).length === 0;
	};

	const handleSave = () => {
		if (validateForm()) {
			onSave(formData);
		}
	};

	const renderField = (fieldName, fieldConfig) => {
		const value = formData[fieldName] || "";
		const hasError = errors[fieldName];

		const commonProps = {
			value,
			onChange: (e) => handleFieldChange(fieldName, e.target.value),
			className: `edit-field-input ${hasError ? "error" : ""}`,
			disabled: isLoading,
		};

		switch (fieldConfig.type) {
			case "dropdown":
			case "select":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select {fieldConfig.label}...</option>
						{fieldConfig.options?.map((option) => (
							<option key={option.value} value={option.value}>
								{option.label}
							</option>
						))}
					</select>
				);

			case "textarea":
				return (
					<textarea
						{...commonProps}
						rows={fieldConfig.rows || 3}
						maxLength={fieldConfig.maxLength}
						placeholder={fieldConfig.placeholder}
					/>
				);

			case "money":
			case "number":
				return (
					<input
						{...commonProps}
						type="number"
						step={fieldConfig.type === "money" ? "0.01" : "1"}
						min="0"
						placeholder="0.00"
					/>
				);

			case "date":
				return (
					<input
						{...commonProps}
						type="date"
						max={new Date().toISOString().split("T")[0]}
					/>
				);

			case "checkbox":
				return (
					<div className="checkbox-container">
						<input
							type="checkbox"
							checked={value === true || value === "yes"}
							onChange={(e) =>
								handleFieldChange(
									fieldName,
									e.target.checked ? "yes" : "no"
								)
							}
							disabled={isLoading}
							className="edit-field-checkbox"
						/>
						<label>{fieldConfig.label}</label>
					</div>
				);

			case "attendee_list":
				return (
					<AttendeeManager
						attendees={Array.isArray(value) ? value : []}
						onChange={(attendees) =>
							handleFieldChange(fieldName, attendees)
						}
						disabled={isLoading}
						required={fieldConfig.required}
					/>
				);

			default:
				return (
					<input
						{...commonProps}
						type="text"
						maxLength={fieldConfig.maxLength}
						placeholder={fieldConfig.placeholder}
					/>
				);
		}
	};

	const getFieldIcon = (fieldName) => {
		const icons = {
			vendor_description: "🏪",
			amount: "💰",
			transaction_date: "📅",
			business_purpose: "🎯",
			meal_type: "🍽️",
			payment_type: "💳",
			currency: "💱",
			city_of_purchase: "🏙️",
			comment: "💬",
			attendees: "👥",
			business_unit_allocation: "🏢",
			business_unit: "🏢",
		};
		return icons[fieldName] || "📝";
	};

	// Define field configurations (this could come from API in real implementation)
	const fieldConfigs = {
		vendor_description: {
			type: "text",
			label: "Vendor/Restaurant Name",
			required: true,
			placeholder: "Enter vendor name",
		},
		amount: {
			type: "money",
			label: "Amount",
			required: true,
			placeholder: "0.00",
		},
		transaction_date: {
			type: "date",
			label: "Transaction Date",
			required: true,
		},
		business_purpose: {
			type: "textarea",
			label: "Business Purpose",
			required: true,
			placeholder: "Describe the business purpose",
			rows: 3,
		},
		meal_type: {
			type: "dropdown",
			label: "Meal Type",
			options: [
				{ value: "breakfast", label: "Breakfast" },
				{ value: "lunch", label: "Lunch" },
				{ value: "dinner", label: "Dinner" },
				{ value: "snacks", label: "Snacks/Refreshments" },
			],
		},
		payment_type: {
			type: "dropdown",
			label: "Payment Type",
			options: [
				{ value: "personal_card", label: "Personal Credit Card" },
				{ value: "cash", label: "Cash" },
			],
		},
		currency: {
			type: "dropdown",
			label: "Currency",
			options: [
				{ value: "USD", label: "US Dollar (USD)" },
				{ value: "EUR", label: "Euro (EUR)" },
				{ value: "GBP", label: "British Pound (GBP)" },
			],
		},
		city_of_purchase: {
			type: "text",
			label: "City of Purchase",
			placeholder: "Enter city",
		},
		business_unit_allocation: {
			type: "dropdown",
			label: "Allocate to Another Business Unit?",
			options: [
				{ value: "no", label: "No" },
				{ value: "yes", label: "Yes" },
			],
		},
		business_unit: {
			type: "text",
			label: "Business Unit",
			placeholder: "Enter business unit",
		},
		comment: {
			type: "textarea",
			label: "Comment",
			placeholder: "Additional details or notes",
			rows: 2,
		},
		attendees: {
			type: "attendee_list",
			label: "Attendees",
			required: expenseTypeId?.includes("client"),
		},
	};

	// Group fields by sections
	const basicFields = [
		"vendor_description",
		"amount",
		"transaction_date",
		"business_purpose",
		"meal_type",
	];
	const paymentFields = ["payment_type", "currency", "city_of_purchase"];
	const additionalFields = [
		"business_unit_allocation",
		"business_unit",
		"comment",
	];
	const attendeeFields = ["attendees"];

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
				{/* Basic Information Section */}
				<div className="field-section">
					<h5 className="section-title">Basic Information</h5>
					{basicFields.map((fieldName) => {
						const fieldConfig = fieldConfigs[fieldName];
						if (!fieldConfig || !formData.hasOwnProperty(fieldName))
							return null;

						return (
							<div
								key={fieldName}
								className={`edit-field-item ${
									errors[fieldName] ? "has-error" : ""
								}`}
							>
								<div className="edit-field-label">
									<span className="field-icon">
										{getFieldIcon(fieldName)}
									</span>
									<span className="field-label-text">
										{fieldConfig.label}
										{fieldConfig.required && (
											<span className="required-indicator">
												*
											</span>
										)}
									</span>
								</div>
								<div className="edit-field-input-container">
									{renderField(fieldName, fieldConfig)}
									{errors[fieldName] && (
										<div className="field-error">
											<span className="error-icon">
												⚠️
											</span>
											{errors[fieldName]}
										</div>
									)}
								</div>
							</div>
						);
					})}
				</div>

				{/* Payment Information Section */}
				<div className="field-section">
					<h5 className="section-title">Payment Information</h5>
					{paymentFields.map((fieldName) => {
						const fieldConfig = fieldConfigs[fieldName];
						if (!fieldConfig || !formData.hasOwnProperty(fieldName))
							return null;

						return (
							<div
								key={fieldName}
								className={`edit-field-item ${
									errors[fieldName] ? "has-error" : ""
								}`}
							>
								<div className="edit-field-label">
									<span className="field-icon">
										{getFieldIcon(fieldName)}
									</span>
									<span className="field-label-text">
										{fieldConfig.label}
									</span>
								</div>
								<div className="edit-field-input-container">
									{renderField(fieldName, fieldConfig)}
								</div>
							</div>
						);
					})}
				</div>

				{/* Attendees Section (only for client meals) */}
				{(expenseTypeId?.includes("client") || formData.attendees) && (
					<div className="field-section">
						<h5 className="section-title">Attendees</h5>
						{attendeeFields.map((fieldName) => {
							const fieldConfig = fieldConfigs[fieldName];
							if (!fieldConfig) return null;

							return (
								<div
									key={fieldName}
									className={`edit-field-item ${
										errors[fieldName] ? "has-error" : ""
									}`}
								>
									<div className="edit-field-label">
										<span className="field-icon">
											{getFieldIcon(fieldName)}
										</span>
										<span className="field-label-text">
											{fieldConfig.label}
											{fieldConfig.required && (
												<span className="required-indicator">
													*
												</span>
											)}
										</span>
									</div>
									<div className="edit-field-input-container">
										{renderField(fieldName, fieldConfig)}
										{errors[fieldName] && (
											<div className="field-error">
												<span className="error-icon">
													⚠️
												</span>
												{errors[fieldName]}
											</div>
										)}
									</div>
								</div>
							);
						})}
					</div>
				)}

				{/* Additional Information Section */}
				<div className="field-section">
					<h5 className="section-title">Additional Information</h5>
					{additionalFields.map((fieldName) => {
						const fieldConfig = fieldConfigs[fieldName];
						if (!fieldConfig || !formData.hasOwnProperty(fieldName))
							return null;

						// Show business unit field only if allocation is 'yes'
						if (
							fieldName === "business_unit" &&
							formData.business_unit_allocation !== "yes"
						) {
							return null;
						}

						return (
							<div
								key={fieldName}
								className={`edit-field-item ${
									errors[fieldName] ? "has-error" : ""
								}`}
							>
								<div className="edit-field-label">
									<span className="field-icon">
										{getFieldIcon(fieldName)}
									</span>
									<span className="field-label-text">
										{fieldConfig.label}
									</span>
								</div>
								<div className="edit-field-input-container">
									{renderField(fieldName, fieldConfig)}
								</div>
							</div>
						);
					})}
				</div>
			</div>

			<div className="edit-actions">
				<button
					onClick={onCancel}
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

// Simplified Attendee Manager Component
const AttendeeManager = ({
	attendees = [],
	onChange,
	disabled = false,
	required = false,
}) => {
	const [showAddForm, setShowAddForm] = useState(false);
	const [newAttendee, setNewAttendee] = useState({
		name: "",
		type: "client",
		company: "",
	});

	const addAttendee = () => {
		if (newAttendee.name.trim()) {
			const updatedAttendees = [
				...attendees,
				{ ...newAttendee, id: Date.now() },
			];
			onChange(updatedAttendees);
			setNewAttendee({ name: "", type: "client", company: "" });
			setShowAddForm(false);
		}
	};

	const removeAttendee = (attendeeId) => {
		const updatedAttendees = attendees.filter(
			(att) => att.id !== attendeeId
		);
		onChange(updatedAttendees);
	};

	return (
		<div className="attendee-manager">
			<div className="attendee-list">
				{attendees.length === 0 ? (
					<div className="no-attendees">
						<span className="no-attendees-icon">👥</span>
						<p>No attendees added yet</p>
						{required && (
							<p className="attendees-required">
								At least 1 attendee required
							</p>
						)}
					</div>
				) : (
					attendees.map((attendee) => (
						<div key={attendee.id} className="attendee-item">
							<div className="attendee-info">
								<div className="attendee-name">
									{attendee.name}
								</div>
								<div className="attendee-details">
									<span className="attendee-type">
										{attendee.type}
									</span>
									{attendee.company && (
										<span className="attendee-company">
											• {attendee.company}
										</span>
									)}
								</div>
							</div>
							<button
								onClick={() => removeAttendee(attendee.id)}
								disabled={disabled}
								className="remove-attendee-btn"
								title="Remove attendee"
							>
								✕
							</button>
						</div>
					))
				)}
			</div>

			<div className="attendee-actions">
				{!showAddForm ? (
					<button
						onClick={() => setShowAddForm(true)}
						disabled={disabled}
						className="add-attendee-btn"
					>
						<span className="btn-icon">➕</span>
						Add Attendee
					</button>
				) : (
					<div className="add-attendee-form">
						<div className="add-form-fields">
							<input
								type="text"
								placeholder="Attendee name"
								value={newAttendee.name}
								onChange={(e) =>
									setNewAttendee((prev) => ({
										...prev,
										name: e.target.value,
									}))
								}
								className="attendee-input"
							/>
							<select
								value={newAttendee.type}
								onChange={(e) =>
									setNewAttendee((prev) => ({
										...prev,
										type: e.target.value,
									}))
								}
								className="attendee-input"
							>
								<option value="client">Client</option>
								<option value="employee">Employee</option>
								<option value="prospect">Prospect</option>
								<option value="supplier">Supplier</option>
							</select>
							<input
								type="text"
								placeholder="Company (optional)"
								value={newAttendee.company}
								onChange={(e) =>
									setNewAttendee((prev) => ({
										...prev,
										company: e.target.value,
									}))
								}
								className="attendee-input"
							/>
						</div>
						<div className="add-form-actions">
							<button
								onClick={() => setShowAddForm(false)}
								className="form-btn secondary small"
							>
								Cancel
							</button>
							<button
								onClick={addAttendee}
								disabled={!newAttendee.name.trim()}
								className="form-btn primary small"
							>
								Add
							</button>
						</div>
					</div>
				)}
			</div>

			<div className="attendee-summary">
				<span className="attendee-count">
					{attendees.length} attendee
					{attendees.length !== 1 ? "s" : ""}
				</span>
			</div>
		</div>
	);
};

export default DynamicExpenseForm;
