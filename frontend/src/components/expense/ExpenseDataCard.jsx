import React from "react";
import ExpenseFieldItem from "./ExpenseFieldItem";
import QuickActions from "../ui/QuickActions";
import MessageFormatter from "../ui/MessageFormatter";

const ExpenseDataCard = ({
	expenseData,
	nextAction,
	onSendCommand,
	isLoading,
	onEditExpense,
	editingExpense,
	onSaveExpense,
	onCancelExpense,
	EditableExpenseFields,
}) => {
	const importantFields = [
		"amount",
		"vendor",
		"transaction_date",
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
	if (editingExpense && EditableExpenseFields) {
		return (
			<EditableExpenseFields
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

			<div className="expense-fields-grid">
				{Object.entries(expenseData).map(([key, value]) => (
					<ExpenseFieldItem
						key={key}
						fieldKey={key}
						value={value}
						isImportant={importantFields.includes(key)}
					/>
				))}
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
