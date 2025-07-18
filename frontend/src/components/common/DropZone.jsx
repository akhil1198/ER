import React from "react";

const DropZone = ({ active }) => {
	if (!active) return null;

	return (
		<div className="drop-overlay">
			<div className="drop-content">
				<div className="drop-icon">🧾</div>
				<h3>Drop your receipt here</h3>
				<p>
					I'll extract expense data automatically and help you add it
					to SAP Concur
				</p>
			</div>
		</div>
	);
};

export default DropZone;
