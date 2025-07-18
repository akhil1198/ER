import React from "react";

const LoadingSpinner = ({ message = "Processing..." }) => {
	return (
		<div className="message assistant">
			<div className="message-content">
				<p>🔍 {message}</p>
				<div className="typing-indicator">
					<span></span>
					<span></span>
					<span></span>
				</div>
			</div>
		</div>
	);
};

export default LoadingSpinner;
