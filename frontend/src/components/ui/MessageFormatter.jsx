import React from "react";

const MessageFormatter = ({ content }) => {
	// Check if this is the welcome message and format it specially
	if (
		content.includes("Welcome to the Expense Assistant") &&
		content.includes("Upload a receipt")
	) {
		return (
			<div className="welcome-message-container">
				<div className="welcome-header">
					<h3 className="welcome-title">
						<span className="welcome-emoji">👋 </span> Welcome to
						the Expense Assistant!
					</h3>
				</div>
				<p className="welcome-description">
					I'm here to help you streamline your expense reporting
					process. Here's what I can do for you:
				</p>
				<div className="welcome-features">
					<div className="feature-item">
						<div className="feature-content">
							<span className="feature-icon"> 📷 </span>
							<strong>Upload a receipt</strong> and I'll extract
							expense details automatically
						</div>
					</div>
					<div className="feature-item">
						<div className="feature-content">
							<span className="feature-icon">📋 </span>
							<strong>Type 'show reports'</strong> to view your
							existing expense reports
						</div>
					</div>
					<div className="feature-item">
						<div className="feature-content">
							<span className="feature-icon">💬 </span>
							<strong>Type 'help'</strong> to see all available
							commands
						</div>
					</div>
				</div>
				<div className="welcome-cta">
					<p>What would you like to do?</p>
				</div>
			</div>
		);
	}

	// For all other messages, use the regular formatting
	const processedContent = content.replace(
		/\*\*([^*]+)\*\*/g,
		'<strong class="bold-text">$1</strong>'
	);

	const lines = processedContent.split("\n");
	const formattedLines = [];
	let inExampleSection = false;

	for (let i = 0; i < lines.length; i++) {
		let line = lines[i];

		if (!line.trim()) {
			formattedLines.push(<div key={i} style={{ height: "0.5rem" }} />);
			inExampleSection = false;
			continue;
		}

		if (line.includes("You can format it like this:")) {
			inExampleSection = true;
			formattedLines.push(
				<div
					key={i}
					className="message-line"
					dangerouslySetInnerHTML={{ __html: line }}
				/>
			);
			continue;
		}

		// Format headers (lines starting with emojis)
		if (line.match(/^[📋🎉👋❌✅⚠️💡📷🤖🔍📊💬❓🏛️]/)) {
			formattedLines.push(
				<div
					key={i}
					className="message-header"
					dangerouslySetInnerHTML={{ __html: line }}
				/>
			);
			inExampleSection = false;
		}
		// Format example lines
		else if (
			inExampleSection &&
			(line.includes("Report Name:") ||
				line.includes("Business Purpose:"))
		) {
			formattedLines.push(
				<div key={i} className="example-line">
					<span className="example-icon">📝</span>
					<span
						className="example-text"
						dangerouslySetInnerHTML={{ __html: line }}
					/>
				</div>
			);
		}
		// Format bullet points
		else if (line.trim().startsWith("•") || line.trim().startsWith("-")) {
			const bulletText = line.replace(/^[\s•-]+/, "");
			formattedLines.push(
				<div key={i} className="bullet-point">
					<span className="bullet">•</span>
					<span
						className="bullet-text"
						dangerouslySetInnerHTML={{ __html: bulletText }}
					/>
				</div>
			);
			inExampleSection = false;
		}
		// Format numbered lists
		else if (line.match(/^\s*\d+\./)) {
			const number = line.match(/^\s*(\d+)\./)[1];
			const text = line.replace(/^\s*\d+\.\s*/, "");
			formattedLines.push(
				<div key={i} className="numbered-item">
					<span className="number-badge">{number}</span>
					<span
						className="numbered-text"
						dangerouslySetInnerHTML={{ __html: text }}
					/>
				</div>
			);
			inExampleSection = false;
		}
		// Skip code blocks
		else if (line.includes("```") || line.includes("`")) {
			const cleanLine = line.replace(/```|`/g, "");
			if (cleanLine.trim()) {
				formattedLines.push(
					<div
						key={i}
						className="message-line"
						dangerouslySetInnerHTML={{ __html: cleanLine }}
					/>
				);
			}
		}
		// Format status lines
		else if (
			line.includes("ID:") ||
			line.includes("Status:") ||
			line.includes("Amount:") ||
			line.includes("Purpose:")
		) {
			const [label, ...valueParts] = line.split(":");
			const value = valueParts.join(":").trim();
			formattedLines.push(
				<div key={i}>
					<span> {label.trim()}:</span>
					<span dangerouslySetInnerHTML={{ __html: value }} />
				</div>
			);
			inExampleSection = false;
		}
		// Regular text
		else {
			formattedLines.push(
				<div
					key={i}
					className="message-line"
					dangerouslySetInnerHTML={{ __html: line }}
				/>
			);
			if (
				!line.includes("You can format it like this:") &&
				!line.includes("Or just tell me")
			) {
				inExampleSection = false;
			}
		}
	}

	return <div className="formatted-content">{formattedLines}</div>;
};

export default MessageFormatter;
