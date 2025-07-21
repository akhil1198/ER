import React from "react";
import ExpenseFieldItem from "./ExpenseFieldItem";
import QuickActions from "../ui/QuickActions";
import MessageFormatter from "../ui/MessageFormatter";
import EnhancedEditableExpenseFields from "./EnhancedEditableExpenseFields";

const ExpenseDataCard = ({
	expenseData,
	nextAction,
	onSendCommand,
	isLoading,
	onEditExpense,
	editingExpense,
	onSaveExpense,
	onCancelExpense,
}) => {
	const importantFields = [
		"amount",
		"vendor",
		"transaction_date",
		"expense_category",
		"expense_type",
		"business_purpose",
	];

	const getNextActionButtons = () => {
		if (!nextAction) return [];

		return [
			{
				label: "Create New Report",
				onClick: () => onSendCommand("1"),
				variant: "primary",
				icon: "✨",
			},
			{
				label: "Add to Existing",
				onClick: () => onSendCommand("2"),
				variant: "secondary",
				icon: "📋",
			},
		];
	};

	// Show editing view if in edit mode
	if (editingExpense) {
		return (
			<EnhancedEditableExpenseFields
				expenseData={expenseData}
				onSave={onSaveExpense}
				onCancel={onCancelExpense}
				isLoading={isLoading}
			/>
		);
	}

	return (
		<div className="expense-data-card">
			<div className="expense-header">
				<h4>🧾 Extracted Expense Data</h4>
				<div className="expense-header-actions">
					<div className="extraction-status">
						<span className="status-badge success">
							✓ Extracted Successfully
						</span>
					</div>
					{onEditExpense && (
						<button
							onClick={onEditExpense}
							disabled={isLoading}
							className="edit-expense-btn"
							title="Edit expense details"
						>
							<span className="btn-icon">✏️</span>
							Edit
						</button>
					)}
				</div>
			</div>

			{/* Show current expense type selection if available */}
			{(expenseData.expense_category || expenseData.expense_type) && (
				<div className="current-selection">
					{expenseData.expense_category && (
						<div className="selection-item">
							<strong>Category:</strong>{" "}
							{expenseData.expense_category}
						</div>
					)}
					{expenseData.expense_type && (
						<div className="selection-item">
							<strong>Type:</strong> {expenseData.expense_type}
						</div>
					)}
					{expenseData.meal_type && (
						<div className="selection-item">
							<strong>Meal Type:</strong> {expenseData.meal_type}
						</div>
					)}
					{expenseData.attendees_count &&
						expenseData.attendees_count > 1 && (
							<div className="selection-item">
								<strong>Attendees:</strong>{" "}
								{expenseData.attendees_count}
							</div>
						)}
					{expenseData.client_prospect_name && (
						<div className="selection-item">
							<strong>Client/Prospect:</strong>{" "}
							{expenseData.client_prospect_name}
						</div>
					)}
				</div>
			)}

			<div className="expense-fields-grid">
				{Object.entries(expenseData).map(([key, value]) => {
					// Skip the fields shown in current selection above
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
							isImportant={importantFields.includes(key)}
						/>
					);
				})}
			</div>

			{nextAction && (
				<div className="next-action-container">
					<div className="action-header">
						<span className="action-icon">🚀</span>
						<span className="action-title">What's Next?</span>
					</div>
					<div className="action-content">
						<MessageFormatter content={nextAction} />
					</div>
					<QuickActions
						actions={getNextActionButtons()}
						isLoading={isLoading}
					/>
				</div>
			)}
		</div>
	);
};

export default ExpenseDataCard;
