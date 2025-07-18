import React from "react";

const TemplateButtons = ({
	templates = [],
	onSelectTemplate,
	isLoading = false,
}) => {
	if (!templates.length) return null;

	return (
		<div className="template-suggestions">
			<div className="template-header">
				<span className="template-icon">💡</span>
				<span className="template-title">Quick Templates</span>
			</div>
			<div className="template-list">
				{templates.map((template, index) => (
					<button
						key={index}
						onClick={() => onSelectTemplate(template.content)}
						disabled={isLoading}
						className="template-btn"
					>
						<span className="template-btn-icon">
							{template.icon}
						</span>
						<span className="template-btn-text">
							{template.name}
						</span>
						<span className="template-btn-arrow">→</span>
					</button>
				))}
			</div>
		</div>
	);
};

export default TemplateButtons;
