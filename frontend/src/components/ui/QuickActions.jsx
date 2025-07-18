import React from "react";

const QuickActions = ({ actions = [], isLoading = false }) => {
	if (!actions.length) return null;

	return (
		<div className="quick-actions-container">
			<div className="quick-actions-label">Choose an option:</div>
			<div className="quick-actions-buttons">
				{actions.map((action, index) => (
					<button
						key={index}
						onClick={action.onClick}
						disabled={isLoading}
						className={`quick-action-btn ${
							action.variant || "primary"
						}`}
					>
						<span className="btn-icon">{action.icon}</span>
						<span className="btn-text">{action.label}</span>
					</button>
				))}
			</div>
		</div>
	);
};

export default QuickActions;
