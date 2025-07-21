// Enhanced ExpenseTypeSelector.jsx
import React, { useState, useEffect } from "react";

const ExpenseTypeSelector = ({
	expenseData,
	onExpenseTypeChange,
	onSave,
	onCancel,
	isLoading = false,
}) => {
	const [selectedCategory, setSelectedCategory] = useState(
		expenseData.expense_category || ""
	);
	const [selectedType, setSelectedType] = useState(
		expenseData.expense_type || ""
	);
	const [mealType, setMealType] = useState(expenseData.meal_type || "");
	const [attendeesCount, setAttendeesCount] = useState(
		expenseData.attendees_count || 1
	);
	const [clientProspectName, setClientProspectName] = useState(
		expenseData.client_prospect_name || ""
	);
	const [businessPurpose, setBusinessPurpose] = useState(
		expenseData.business_purpose || ""
	);

	// Expense type options based on category
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
	};

	const MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Other"];

	const handleCategoryChange = (category) => {
		setSelectedCategory(category);
		setSelectedType(""); // Reset type when category changes

		// If not meals, clear meal-specific fields
		if (category !== "Meals & Entertainment") {
			setMealType("");
			setClientProspectName("");
			setAttendeesCount(1);
		}
	};

	const handleTypeChange = (type) => {
		setSelectedType(type);

		// Auto-suggest business purpose based on type
		if (type.includes("Client")) {
			setBusinessPurpose("Client meeting and discussion");
		} else if (type.includes("Employee")) {
			setBusinessPurpose("Team meeting and discussion");
		} else if (type.includes("Prospect")) {
			setBusinessPurpose("Prospect meeting and discussion");
		}
	};

	const handleSave = () => {
		const updatedData = {
			...expenseData,
			expense_category: selectedCategory,
			expense_type: selectedType,
			meal_type:
				selectedCategory === "Meals & Entertainment" ? mealType : null,
			attendees_count:
				selectedCategory === "Meals & Entertainment"
					? attendeesCount
					: 1,
			client_prospect_name:
				selectedType.includes("Client") ||
				selectedType.includes("Prospect")
					? clientProspectName
					: null,
			business_purpose: businessPurpose,
		};

		onExpenseTypeChange(updatedData);
		onSave(updatedData);
	};

	const isClientMeal =
		selectedType.includes("Client") || selectedType.includes("Prospect");
	const isMealsCategory = selectedCategory === "Meals & Entertainment";

	return (
		<div className="expense-type-selector-container">
			<div className="selector-header">
				<h4>🏷️ Select Expense Type</h4>
				<p className="ai-suggestion">
					AI detected: <strong>{expenseData.expense_category}</strong>{" "}
					- Please confirm or adjust the category and specific type
					below.
				</p>
			</div>

			{/* Category Selection */}
			<div className="field-group">
				<label className="field-label">
					<span className="field-icon">📂</span>
					Expense Category *
				</label>
				<select
					value={selectedCategory}
					onChange={(e) => handleCategoryChange(e.target.value)}
					className="category-select"
				>
					<option value="">Select category...</option>
					{Object.keys(EXPENSE_TYPE_OPTIONS).map((category) => (
						<option key={category} value={category}>
							{category}
						</option>
					))}
				</select>
			</div>

			{/* Type Selection */}
			{selectedCategory && (
				<div className="field-group">
					<label className="field-label">
						<span className="field-icon">🎯</span>
						Specific Expense Type *
					</label>
					<select
						value={selectedType}
						onChange={(e) => handleTypeChange(e.target.value)}
						className="type-select"
					>
						<option value="">Select type...</option>
						{EXPENSE_TYPE_OPTIONS[selectedCategory].map((type) => (
							<option key={type} value={type}>
								{type}
							</option>
						))}
					</select>
				</div>
			)}

			{/* Meals & Entertainment Specific Fields */}
			{isMealsCategory && (
				<>
					<div className="field-group">
						<label className="field-label">
							<span className="field-icon">🍽️</span>
							Meal Type *
						</label>
						<select
							value={mealType}
							onChange={(e) => setMealType(e.target.value)}
							className="meal-type-select"
						>
							<option value="">Select meal type...</option>
							{MEAL_TYPES.map((type) => (
								<option key={type} value={type}>
									{type}
								</option>
							))}
						</select>
					</div>

					<div className="field-group">
						<label className="field-label">
							<span className="field-icon">👥</span>
							Number of Attendees *
						</label>
						<input
							type="number"
							min="1"
							value={attendeesCount}
							onChange={(e) =>
								setAttendeesCount(parseInt(e.target.value) || 1)
							}
							className="attendees-input"
						/>
					</div>

					{isClientMeal && (
						<div className="field-group">
							<label className="field-label">
								<span className="field-icon">🏢</span>
								Client/Prospect Name *
							</label>
							<input
								type="text"
								value={clientProspectName}
								onChange={(e) =>
									setClientProspectName(e.target.value)
								}
								placeholder="Enter client or prospect company name"
								className="client-input"
							/>
						</div>
					)}
				</>
			)}

			{/* Business Purpose */}
			<div className="field-group">
				<label className="field-label">
					<span className="field-icon">📝</span>
					Business Purpose *
				</label>
				<textarea
					value={businessPurpose}
					onChange={(e) => setBusinessPurpose(e.target.value)}
					placeholder="Describe the business purpose of this expense"
					className="purpose-textarea"
					rows="3"
				/>
			</div>

			{/* Action Buttons */}
			<div className="selector-actions">
				<button
					onClick={onCancel}
					disabled={isLoading}
					className="cancel-btn"
				>
					Cancel
				</button>

				<button
					onClick={handleSave}
					disabled={
						isLoading ||
						!selectedCategory ||
						!selectedType ||
						(isMealsCategory && !mealType) ||
						(isClientMeal && !clientProspectName) ||
						!businessPurpose
					}
					className="save-btn primary"
				>
					{isLoading ? "Saving..." : "Confirm & Continue"}
				</button>
			</div>

			{/* Validation Hints */}
			<div className="validation-hints">
				<div className="hint-item">
					<span className="hint-icon">💡</span>
					<span>
						Choose the most specific expense type that matches your
						receipt
					</span>
				</div>
				{isMealsCategory && (
					<div className="hint-item">
						<span className="hint-icon">🍽️</span>
						<span>
							For meals with clients, ensure you provide the
							client/prospect name
						</span>
					</div>
				)}
			</div>
		</div>
	);
};

// Enhanced ExpenseDataCard with Type Selector
const EnhancedExpenseDataCard = ({
	expenseData,
	onExpenseTypeChange,
	onSave,
	isLoading,
}) => {
	const [showTypeSelector, setShowTypeSelector] = useState(false);
	const [currentData, setCurrentData] = useState(expenseData);

	const handleShowTypeSelector = () => {
		setShowTypeSelector(true);
	};

	const handleTypeSelectionComplete = (updatedData) => {
		setCurrentData(updatedData);
		setShowTypeSelector(false);
		onExpenseTypeChange(updatedData);
	};

	const handleFinalSave = () => {
		onSave(currentData);
	};

	if (showTypeSelector) {
		return (
			<ExpenseTypeSelector
				expenseData={currentData}
				onExpenseTypeChange={handleTypeSelectionComplete}
				onSave={handleTypeSelectionComplete}
				onCancel={() => setShowTypeSelector(false)}
				isLoading={isLoading}
			/>
		);
	}

	return (
		<div className="expense-data-card">
			<div className="expense-header">
				<h4>🧾 Extracted Expense Data</h4>
				<div className="expense-header-actions">
					<div className="ai-confidence">
						<span className="confidence-badge">
							🤖 AI Detected: {currentData.expense_category}
						</span>
					</div>
					<button
						onClick={handleShowTypeSelector}
						disabled={isLoading}
						className="select-type-btn"
					>
						<span className="btn-icon">🏷️</span>
						{currentData.expense_type
							? "Change Type"
							: "Select Type"}
					</button>
				</div>
			</div>

			{/* Display current expense type selection */}
			{currentData.expense_type && (
				<div className="current-selection">
					<div className="selection-item">
						<strong>Category:</strong>{" "}
						{currentData.expense_category}
					</div>
					<div className="selection-item">
						<strong>Type:</strong> {currentData.expense_type}
					</div>
					{currentData.meal_type && (
						<div className="selection-item">
							<strong>Meal Type:</strong> {currentData.meal_type}
						</div>
					)}
					{currentData.attendees_count > 1 && (
						<div className="selection-item">
							<strong>Attendees:</strong>{" "}
							{currentData.attendees_count}
						</div>
					)}
					{currentData.client_prospect_name && (
						<div className="selection-item">
							<strong>Client/Prospect:</strong>{" "}
							{currentData.client_prospect_name}
						</div>
					)}
				</div>
			)}

			{/* Rest of expense fields display */}
			<div className="expense-fields-grid">
				{Object.entries(currentData).map(([key, value]) => {
					// Skip the new fields as they're shown above
					if (
						[
							"expense_category",
							"expense_type",
							"meal_type",
							"attendees_count",
							"client_prospect_name",
						].includes(key)
					) {
						return null;
					}

					return (
						<ExpenseFieldItem
							key={key}
							fieldKey={key}
							value={value}
							isImportant={[
								"amount",
								"vendor",
								"transaction_date",
								"business_purpose",
							].includes(key)}
						/>
					);
				})}
			</div>

			{/* Action buttons */}
			<div className="expense-actions">
				{currentData.expense_type ? (
					<div className="next-steps">
						<p>✅ Expense type confirmed! Ready to proceed.</p>
						<div className="action-buttons">
							<button
								onClick={() => handleFinalSave()}
								disabled={isLoading}
								className="proceed-btn primary"
							>
								<span className="btn-icon">🚀</span>
								Create Expense Report
							</button>
						</div>
					</div>
				) : (
					<div className="type-selection-prompt">
						<p>⚠️ Please select the expense type to continue</p>
						<button
							onClick={handleShowTypeSelector}
							className="select-type-btn primary"
						>
							<span className="btn-icon">🏷️</span>
							Select Expense Type
						</button>
					</div>
				)}
			</div>
		</div>
	);
};

export default { ExpenseTypeSelector, EnhancedExpenseDataCard };
