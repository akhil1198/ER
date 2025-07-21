// frontend/src/components/chat/Message.jsx - Updated for dynamic expense types

import React from "react";
import MessageFormatter from "../ui/MessageFormatter";
import ExpenseDataCard from "../expense/ExpenseDataCard";
import TaxComplianceUI from "../expense/TaxComplianceUI";
import QuickActions from "../ui/QuickActions";
import TemplateButtons from "../ui/TemplateButtons";
import ExpenseTypeSelector from "../expense/ExpenseTypeSelector";

const Message = ({
	message,
	onSendCommand,
	isLoading,
	onEditExpense,
	editingExpense,
	onSaveExpense,
	onCancelExpense,
}) => {
	const isUser = message.type === "user" || message.type === "image";

	// Quick action configurations
	const getQuickActions = () => {
		if (
			message.type === "assistant" &&
			message.content.includes("What would you like to do next") &&
			message.content.includes("Create a new expense report") &&
			message.content.includes("Add to an existing report") &&
			!message.needs_tax_compliance
		) {
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
		}
		return [];
	};

	// Template configurations
	const getTemplates = () => {
		if (
			message.type === "assistant" &&
			message.content.includes("Report Name") &&
			message.content.includes("Business Purpose") &&
			!message.needs_tax_compliance
		) {
			return [
				{
					name: "Office Supplies",
					content: `Report Name: Office Supplies - ${new Date().toLocaleDateString()}\nBusiness Purpose: Monthly office supplies and equipment`,
					icon: "🏢",
				},
				{
					name: "Travel Expenses",
					content: `Report Name: Travel Expenses - ${new Date().toLocaleDateString()}\nBusiness Purpose: Business travel and transportation`,
					icon: "✈️",
				},
				{
					name: "Client Meals",
					content: `Report Name: Client Meals - ${new Date().toLocaleDateString()}\nBusiness Purpose: Client entertainment and meals`,
					icon: "🍽️",
				},
			];
		}
		return [];
	};

	// Tax compliance response handler
	const handleTaxCompliance = () => {
		const complianceMessage = `Gift Policy Compliance: ✓\nIRS Tax Policy Compliance: ✓`;
		onSendCommand(complianceMessage);
	};

	// Expense type change handler
	const handleExpenseTypeChange = (newExpenseTypeId) => {
		onSendCommand(`Change expense type to ${newExpenseTypeId}`);
	};

	return (
		<div
			className={`message ${isUser ? "user" : "assistant"} ${
				message.type
			}`}
		>
			<div className="message-content">
				{/* Image Message */}
				{message.type === "image" && message.image_url && (
					<div className="image-message">
						<img
							src={message.image_url}
							alt="Receipt"
							className="receipt-image"
						/>
						<p>{message.content}</p>
					</div>
				)}

				{/* Enhanced Expense Data Message with Dynamic Support */}
				{message.type === "expense_data" && message.expense_data && (
					<div className="expense-data-message">
						<div className="expense-intro">
							<MessageFormatter content={message.content} />
						</div>

						{/* Show expense type detection info if available */}
						{message.expense_type_info &&
							message.expense_type_info.confidence < 0.9 && (
								<div className="expense-type-suggestion">
									<div className="suggestion-header">
										<span className="suggestion-icon">
											🎯
										</span>
										<h5>Expense Type Detection</h5>
									</div>
									<div className="suggestion-content">
										<p>
											<strong>Detected:</strong>{" "}
											{message.expense_type_info.name}
										</p>
										<p>
											<strong>Confidence:</strong>{" "}
											{(
												message.expense_type_info
													.confidence * 100
											).toFixed(0)}
											%
										</p>
										{message.expense_type_info.confidence <
											0.8 && (
											<div className="low-confidence-warning">
												<span className="warning-icon">
													⚠️
												</span>
												<span>
													Low confidence - you may
													want to verify the expense
													type
												</span>
											</div>
										)}
									</div>
								</div>
							)}

						<ExpenseDataCard
							expenseData={message.expense_data}
							expenseTypeInfo={message.expense_type_info}
							nextAction={message.next_action}
							onSendCommand={onSendCommand}
							isLoading={isLoading}
							onEditExpense={onEditExpense}
							editingExpense={editingExpense}
							onSaveExpense={onSaveExpense}
							onCancelExpense={onCancelExpense}
							validationErrors={message.validation_errors || []}
						/>
					</div>
				)}

				{/* Regular Text Message */}
				{(message.type === "user" ||
					message.type === "assistant" ||
					message.type === "reports") &&
					!message.expense_data &&
					!message.image_url && (
						<div className="formatted-message">
							<MessageFormatter content={message.content} />

							{/* Tax Compliance UI */}
							{message.type === "assistant" &&
								message.needs_tax_compliance && (
									<TaxComplianceUI
										onAgreeAll={handleTaxCompliance}
										isLoading={isLoading}
									/>
								)}

							{/* Quick Actions */}
							<QuickActions
								actions={getQuickActions()}
								isLoading={isLoading}
							/>

							{/* Template Buttons */}
							<TemplateButtons
								templates={getTemplates()}
								onSelectTemplate={onSendCommand}
								isLoading={isLoading}
							/>

							{/* Success Highlight */}
							{message.type === "assistant" &&
								(message.content.includes("✅") ||
									message.content.includes(
										"created successfully"
									)) && (
									<div className="success-highlight">
										<div className="success-icon">🎉</div>
										<div className="success-message">
											Action completed successfully!
										</div>
									</div>
								)}
						</div>
					)}

				<div className="message-time">
					{new Date(message.timestamp).toLocaleTimeString()}
				</div>
			</div>
		</div>
	);
};

export default Message;
