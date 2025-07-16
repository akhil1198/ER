// App.jsx - Enhanced Version with Editable Expense Fields
import React, { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";

// Constants
const API_BASE_URL = "http://localhost:8000";

// Predefined options for dropdowns
const EXPENSE_TYPES = [
	"Meals",
	"Travel",
	"Accommodation",
	"Transportation",
	"Office Supplies",
	"Software",
	"Entertainment",
	"Fuel",
	"Parking",
	"Other",
];

const PAYMENT_TYPES = [
	"Credit Card",
	"Cash",
	"Bank Transfer",
	"Check",
	"Other",
];

const CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"];

// Editable Expense Fields Component
const EditableExpenseFields = ({
	expenseData,
	onSave,
	onCancel,
	isLoading = false,
}) => {
	const [editedData, setEditedData] = useState(expenseData || {});
	const [errors, setErrors] = useState({});
	const [hasChanges, setHasChanges] = useState(false);

	// Track changes
	useEffect(() => {
		const hasAnyChanges = Object.keys(editedData).some(
			(key) => editedData[key] !== expenseData[key]
		);
		setHasChanges(hasAnyChanges);
	}, [editedData, expenseData]);

	// Field update handler
	const handleFieldChange = (field, value) => {
		setEditedData((prev) => ({ ...prev, [field]: value }));

		// Clear error for this field when user starts typing
		if (errors[field]) {
			setErrors((prev) => ({ ...prev, [field]: null }));
		}
	};

	// Validation
	const validateFields = () => {
		const newErrors = {};

		if (!editedData.vendor?.trim()) {
			newErrors.vendor = "Vendor is required";
		}

		if (!editedData.amount || editedData.amount <= 0) {
			newErrors.amount = "Valid amount is required";
		}

		if (!editedData.transaction_date) {
			newErrors.transaction_date = "Date is required";
		}

		if (!editedData.expense_type) {
			newErrors.expense_type = "Expense type is required";
		}

		setErrors(newErrors);
		return Object.keys(newErrors).length === 0;
	};

	// Save handler
	const handleSave = () => {
		if (validateFields()) {
			onSave(editedData);
		}
	};

	// Cancel handler
	const handleCancel = () => {
		setEditedData(expenseData);
		setErrors({});
		setHasChanges(false);
		onCancel();
	};

	// Format field name for display
	const formatFieldName = (fieldName) => {
		return fieldName
			.replace(/_/g, " ")
			.replace(/\b\w/g, (l) => l.toUpperCase());
	};

	// Get field icon
	const getFieldIcon = (field) => {
		const icons = {
			expense_type: "🏷️",
			transaction_date: "📅",
			business_purpose: "🎯",
			vendor: "🏪",
			city: "🏙️",
			country: "🌍",
			payment_type: "💳",
			amount: "💰",
			currency: "💱",
			comment: "💬",
		};
		return icons[field] || "📝";
	};

	// Render field input based on type
	const renderFieldInput = (field, value) => {
		const commonProps = {
			value: value || "",
			onChange: (e) => handleFieldChange(field, e.target.value),
			className: `edit-field-input ${errors[field] ? "error" : ""}`,
		};

		switch (field) {
			case "expense_type":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select type...</option>
						{EXPENSE_TYPES.map((type) => (
							<option key={type} value={type}>
								{type}
							</option>
						))}
					</select>
				);

			case "payment_type":
				return (
					<select {...commonProps} value={value || ""}>
						<option value="">Select payment...</option>
						{PAYMENT_TYPES.map((type) => (
							<option key={type} value={type}>
								{type}
							</option>
						))}
					</select>
				);

			case "currency":
				return (
					<select {...commonProps} value={value || "USD"}>
						{CURRENCIES.map((curr) => (
							<option key={curr} value={curr}>
								{curr}
							</option>
						))}
					</select>
				);

			case "amount":
				return (
					<input
						{...commonProps}
						type="number"
						step="0.01"
						min="0"
						placeholder="0.00"
						onChange={(e) =>
							handleFieldChange(
								field,
								parseFloat(e.target.value) || 0
							)
						}
					/>
				);

			case "transaction_date":
				return (
					<input
						{...commonProps}
						type="date"
						max={new Date().toISOString().split("T")[0]}
					/>
				);

			case "business_purpose":
			case "comment":
				return (
					<textarea
						{...commonProps}
						rows="3"
						placeholder={`Enter ${formatFieldName(
							field
						).toLowerCase()}...`}
					/>
				);

			default:
				return (
					<input
						{...commonProps}
						type="text"
						placeholder={`Enter ${formatFieldName(
							field
						).toLowerCase()}...`}
					/>
				);
		}
	};

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
				{Object.entries(editedData).map(([field, value]) => (
					<div
						key={field}
						className={`edit-field-item ${
							errors[field] ? "has-error" : ""
						}`}
					>
						<div className="edit-field-label">
							<span className="field-icon">
								{getFieldIcon(field)}
							</span>
							<span className="field-label-text">
								{formatFieldName(field)}
								{[
									"vendor",
									"amount",
									"transaction_date",
									"expense_type",
								].includes(field) && (
									<span className="required-indicator">
										*
									</span>
								)}
							</span>
						</div>

						<div className="edit-field-input-container">
							{renderFieldInput(field, value)}
							{errors[field] && (
								<div className="field-error">
									<span className="error-icon">⚠️</span>
									{errors[field]}
								</div>
							)}
						</div>
					</div>
				))}
			</div>

			<div className="edit-actions">
				<button
					onClick={handleCancel}
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

// Main App Component
function App() {
	// ========================================
	// STATE MANAGEMENT
	// ========================================
	const [messages, setMessages] = useState([]);
	const [inputMessage, setInputMessage] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [dragActive, setDragActive] = useState(false);
	const [currentExpense, setCurrentExpense] = useState(null);
	const [isMobile, setIsMobile] = useState(false);
	const [editingExpense, setEditingExpense] = useState(false); // New state for edit mode

	// ========================================
	// REFS
	// ========================================
	const messagesEndRef = useRef(null);
	const fileInputRef = useRef(null);
	const textareaRef = useRef(null);

	// ========================================
	// EFFECTS
	// ========================================

	// Mobile detection
	useEffect(() => {
		const checkIfMobile = () => setIsMobile(window.innerWidth <= 768);
		checkIfMobile();
		window.addEventListener("resize", checkIfMobile);
		return () => window.removeEventListener("resize", checkIfMobile);
	}, []);

	// Initialize with welcome message
	useEffect(() => {
		const welcomeMessage = {
			id: `welcome-${Date.now()}`,
			type: "assistant",
			content:
				"👋 **Welcome to the Expense Assistant!**\n\n **Upload a receipt** and I'll extract expense details automatically \n📋 **Type 'show reports'** to view your existing expense reports\n💬 **Type 'help'** to see all available commands\n\nWhat would you like to do?",
			timestamp: new Date().toISOString(),
		};
		setMessages([welcomeMessage]);
	}, []);

	// Auto-scroll messages
	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	// Auto-resize textarea
	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto";
			textareaRef.current.style.height =
				Math.min(textareaRef.current.scrollHeight, 120) + "px";
		}
	}, [inputMessage]);

	// ========================================
	// API FUNCTIONS
	// ========================================

	const makeApiCall = useCallback(async (url, options = {}) => {
		try {
			const response = await fetch(`${API_BASE_URL}${url}`, options);

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error(`API call failed for ${url}:`, error);
			throw error;
		}
	}, []);

	// ========================================
	// EXPENSE EDITING HANDLERS
	// ========================================

	const handleEditExpense = useCallback(() => {
		setEditingExpense(true);
	}, []);

	const handleSaveExpenseChanges = useCallback((updatedExpenseData) => {
		setCurrentExpense(updatedExpenseData);
		setEditingExpense(false);

		// Update the expense data in the most recent expense message
		setMessages((prevMessages) => {
			return prevMessages.map((message) => {
				if (message.type === "expense_data" && message.expense_data) {
					return {
						...message,
						expense_data: updatedExpenseData,
					};
				}
				return message;
			});
		});

		// Add a confirmation message
		const updateMessage = {
			id: `update-${Date.now()}`,
			type: "assistant",
			content:
				"✅ **Expense details updated successfully!**\n\nYour changes have been saved. What would you like to do next?\n\n**1** - Create a new expense report\n**2** - Add to an existing report",
			timestamp: new Date().toISOString(),
		};

		setMessages((prevMessages) => [...prevMessages, updateMessage]);
	}, []);

	const handleCancelExpenseEdit = useCallback(() => {
		setEditingExpense(false);
	}, []);

	// ========================================
	// EXISTING FUNCTIONS (keeping them the same)
	// ========================================

	const sendMessage = useCallback(async () => {
		if (!inputMessage.trim() || isLoading) return;

		// Add user message immediately to the UI
		const userMessage = {
			id: `user-${Date.now()}`,
			type: "user",
			content: inputMessage,
			timestamp: new Date().toISOString(),
		};

		// Update messages immediately and clear input
		setMessages((prevMessages) => [...prevMessages, userMessage]);
		const messageToSend = inputMessage;
		setInputMessage("");
		setIsLoading(true);

		try {
			const data = await makeApiCall("/api/chat", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ content: messageToSend }),
			});

			// Add assistant response
			const assistantMessage = {
				id: `assistant-${Date.now()}`,
				type: "assistant",
				content: data.message,
				timestamp: new Date().toISOString(),
				action: data.action,
				reports: data.reports,
				expense_data: data.expense_data,
				needs_tax_compliance: data.needs_tax_compliance,
			};

			setMessages((prevMessages) => [...prevMessages, assistantMessage]);

			// Update current expense if present
			if (data.expense_data) {
				setCurrentExpense(data.expense_data);
			}
		} catch (error) {
			console.error("Failed to send message:", error);

			// On error, add an error message
			const errorMessage = {
				id: `error-${Date.now()}`,
				type: "assistant",
				content: `❌ Failed to send message: ${error.message}. Please try again.`,
				timestamp: new Date().toISOString(),
			};

			setMessages((prevMessages) => [...prevMessages, errorMessage]);
		} finally {
			setIsLoading(false);
		}
	}, [inputMessage, isLoading, makeApiCall]);

	const sendQuickCommand = useCallback(
		(command) => {
			if (!command.trim() || isLoading) return;

			// Add user message immediately to the UI
			const userMessage = {
				id: `user-${Date.now()}`,
				type: "user",
				content: command,
				timestamp: new Date().toISOString(),
			};

			// Update messages immediately
			setMessages((prevMessages) => [...prevMessages, userMessage]);
			setIsLoading(true);

			// Send to backend
			makeApiCall("/api/chat", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ content: command }),
			})
				.then((data) => {
					// Add assistant response
					const assistantMessage = {
						id: `assistant-${Date.now()}`,
						type: "assistant",
						content: data.message,
						timestamp: new Date().toISOString(),
						action: data.action,
						reports: data.reports,
						expense_data: data.expense_data,
						needs_tax_compliance: data.needs_tax_compliance,
					};

					setMessages((prevMessages) => [
						...prevMessages,
						assistantMessage,
					]);

					// Update current expense if present
					if (data.expense_data) {
						setCurrentExpense(data.expense_data);
					}
				})
				.catch((error) => {
					console.error("Failed to send command:", error);
					// On error, add an error message
					const errorMessage = {
						id: `error-${Date.now()}`,
						type: "assistant",
						content: `❌ Failed to send message: ${error.message}. Please try again.`,
						timestamp: new Date().toISOString(),
					};

					setMessages((prevMessages) => [
						...prevMessages,
						errorMessage,
					]);
				})
				.finally(() => {
					setIsLoading(false);
				});
		},
		[isLoading, makeApiCall]
	);

	const sendTaxComplianceResponse = useCallback(
		(giftPolicy, irsPolicy) => {
			const complianceMessage = `Gift Policy Compliance: ${
				giftPolicy ? "✓" : "✗"
			}\nIRS Tax Policy Compliance: ${irsPolicy ? "✓" : "✗"}`;
			sendQuickCommand(complianceMessage);
		},
		[sendQuickCommand]
	);

	const handleFileUpload = useCallback(
		async (file) => {
			if (!file || isLoading) return;

			// Create image URL for immediate display
			const imageUrl = URL.createObjectURL(file);

			// Add the image message immediately to the UI
			const imageMessage = {
				id: `image-${Date.now()}`,
				type: "image",
				content: `Uploaded receipt: ${file.name}`,
				timestamp: new Date().toISOString(),
				image_url: imageUrl,
			};

			// Update messages immediately to show the uploaded image
			setMessages((prevMessages) => [...prevMessages, imageMessage]);
			setIsLoading(true);

			try {
				const formData = new FormData();
				formData.append("file", file);

				const data = await makeApiCall("/api/process-receipt", {
					method: "POST",
					body: formData,
				});

				// Update current expense data
				setCurrentExpense(data.expense_data);

				// Add processing response
				const responseMessage = {
					id: `response-${Date.now()}`,
					type: "expense_data",
					content: data.message,
					timestamp: new Date().toISOString(),
					expense_data: data.expense_data,
					next_action: data.next_action,
				};

				setMessages((prevMessages) => [
					...prevMessages,
					responseMessage,
				]);

				// Clean up the temporary object URL
				URL.revokeObjectURL(imageUrl);
			} catch (error) {
				console.error("Failed to upload file:", error);

				// On error, remove the temporary image message and show error
				setMessages((prevMessages) => {
					const filteredMessages = prevMessages.filter(
						(msg) => msg.id !== imageMessage.id
					);
					return [
						...filteredMessages,
						{
							id: `error-${Date.now()}`,
							type: "assistant",
							content: `❌ Failed to upload receipt: ${error.message}. Please try again.`,
							timestamp: new Date().toISOString(),
						},
					];
				});

				// Clean up the temporary object URL
				URL.revokeObjectURL(imageUrl);
			} finally {
				setIsLoading(false);
			}
		},
		[isLoading, makeApiCall]
	);

	// ========================================
	// EVENT HANDLERS
	// ========================================

	const handleDragEvents = useCallback((e) => {
		e.preventDefault();
		e.stopPropagation();
		setDragActive(e.type === "dragenter" || e.type === "dragover");
	}, []);

	const handleDrop = useCallback(
		(e) => {
			e.preventDefault();
			e.stopPropagation();
			setDragActive(false);

			const files = e.dataTransfer.files;
			if (files?.[0]?.type.startsWith("image/")) {
				handleFileUpload(files[0]);
			}
		},
		[handleFileUpload]
	);

	const handleFileSelect = useCallback(
		(e) => {
			const file = e.target.files?.[0];
			if (file) handleFileUpload(file);
		},
		[handleFileUpload]
	);

	const handleKeyPress = useCallback(
		(e) => {
			if (e.key === "Enter" && !e.shiftKey) {
				e.preventDefault();
				sendMessage();
			}
		},
		[sendMessage]
	);

	// ========================================
	// UTILITY FUNCTIONS
	// ========================================

	const scrollToBottom = useCallback(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, []);

	const formatFieldValue = useCallback((value) => {
		if (value === null || value === undefined) return "Not specified";
		if (typeof value === "boolean") return value ? "Yes" : "No";
		if (typeof value === "number") return value.toLocaleString();
		return value;
	}, []);

	const formatFieldName = useCallback((fieldName) => {
		return fieldName
			.replace(/_/g, " ")
			.replace(/\b\w/g, (l) => l.toUpperCase());
	}, []);

	// Tax Compliance Component
	const TaxComplianceUI = ({ message }) => {
		const [hasAgreed, setHasAgreed] = useState(false);

		const handleAgreeAll = () => {
			setHasAgreed(true);
			sendTaxComplianceResponse(true, true);
		};

		return (
			<div className="tax-compliance-container">
				<div className="compliance-info">
					<div className="policy-item">
						<div className="policy-header">
							<span className="policy-icon">🎁</span>
							<strong>
								Gift Policy Compliance Certification
							</strong>
						</div>
						<p className="policy-description">
							I certify that this expense complies with company
							gift policy guidelines
						</p>
					</div>

					<div className="policy-item">
						<div className="policy-header">
							<span className="policy-icon">🏛️</span>
							<strong>IRS T&E Tax Policy Certification</strong>
						</div>
						<p className="policy-description">
							I certify that this expense complies with IRS Travel
							& Entertainment tax policies
						</p>
					</div>
				</div>

				<div className="compliance-actions">
					<button
						onClick={handleAgreeAll}
						disabled={isLoading || hasAgreed}
						className={`compliance-btn primary ${
							hasAgreed ? "agreed" : ""
						}`}
					>
						<span className="btn-icon">
							{hasAgreed ? "✅" : "✓"}
						</span>
						<span>
							{hasAgreed
								? "Agreed to Both Policies"
								: "I Agree to Both Policies"}
						</span>
					</button>
				</div>

				{!hasAgreed && (
					<div className="compliance-warning">
						⚠️ You must agree to both policies to proceed with
						creating the expense report
					</div>
				)}
			</div>
		);
	};

	// Message formatting function for beautiful display
	const renderFormattedMessage = useCallback((content) => {
		// Check if this is the welcome message and format it specially
		if (
			content.includes("Welcome to the Expense Assistant") &&
			content.includes("Upload a receipt")
		) {
			return (
				<div className="welcome-message-container">
					<div className="welcome-header">
						<h3 className="welcome-title">
							<span className="welcome-emoji">👋 </span> Welcome
							to the Expense Assistant!
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
								<strong>Upload a receipt</strong> and I'll
								extract expense details automatically
							</div>
						</div>
						<div className="feature-item">
							<div className="feature-content">
								<span className="feature-icon">📋 </span>
								<strong>Type 'show reports'</strong> to view
								your existing expense reports
							</div>
						</div>
						<div className="feature-item">
							<div className="feature-content">
								<span className="feature-icon">💬 </span>
								<strong>Type 'help'</strong> to see all
								available commands
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
		// First, process the entire content to handle bold text globally
		const processedContent = content.replace(
			/\*\*([^*]+)\*\*/g,
			'<strong class="bold-text">$1</strong>'
		);

		// Split content into lines for processing
		const lines = processedContent.split("\n");
		const formattedLines = [];
		let inExampleSection = false;

		for (let i = 0; i < lines.length; i++) {
			let line = lines[i];

			// Skip empty lines but add spacing
			if (!line.trim()) {
				formattedLines.push(
					<div key={i} style={{ height: "0.5rem" }} />
				);
				inExampleSection = false;
				continue;
			}

			// Check if we're entering an example section
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
			// Format example lines when we're in an example section
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
			// Format bullet points (lines starting with •)
			else if (
				line.trim().startsWith("•") ||
				line.trim().startsWith("-")
			) {
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
			// Skip code block formatting entirely - just treat as regular text
			else if (line.includes("```") || line.includes("`")) {
				// Remove the backticks and treat as regular text
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
			// Format status lines (lines with specific patterns)
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
	}, []);

	// Main App Render
	return (
		<div
			className={`App chat-app ${dragActive ? "drag-active" : ""}`}
			onDragEnter={handleDragEvents}
			onDragLeave={handleDragEvents}
			onDragOver={handleDragEvents}
			onDrop={handleDrop}
		>
			{/* NavBar Component */}
			<nav className="gallagher-navbar">
				<div className="navbar-left">
					<a href="#" className="gallagher-logo">
						<img
							src="GallagherAI.png"
							alt="Gallagher AI"
							className="logo-image"
						/>
						<div className="logo-fallback">
							<div className="logo-icon">G</div>
							<span className="logo-text">
								Gallagher <span className="logo-ai">AI</span>
							</span>
						</div>
					</a>
				</div>

				<div className="navbar-right">
					<div className="navbar-center">
						<button className="nav-item active">
							<span className="nav-icon">💬</span>
							Chat
						</button>
						<button className="nav-item">
							<span className="nav-icon">📄</span>
							Document Workspaces
						</button>
						<button className="nav-item updates-badge">
							<span className="nav-icon">🔔</span>
							Updates
						</button>
						<div className="more-dropdown">
							<button className="dropdown-toggle">
								More <span className="nav-icon">▼</span>
							</button>
						</div>
					</div>
					<button className="user-profile">
						<div className="user-avatar">AS</div>
						<div className="user-info">
							<div className="user-name">Akhil Shridhar</div>
							<div className="user-location">
								<span className="location-flag">🇺🇸</span>U.S.
							</div>
						</div>
					</button>
				</div>
			</nav>

			<div className="app-content">
				{/* Sidebar */}
				{!isMobile && (
					<div className="chat-sidebar">
						<div className="sidebar-header">
							<button
								className="new-chat-btn"
								onClick={() => window.location.reload()}
							>
								➕ New Chat
							</button>
						</div>
					</div>
				)}

				<div className="chat-main">
					{/* Message Area */}
					<div className="chat-container">
						<div className="messages-container">
							{messages.map((message) => {
								const isUser =
									message.type === "user" ||
									message.type === "image";

								return (
									<div
										key={message.id}
										className={`message ${
											isUser ? "user" : "assistant"
										} ${message.type}`}
									>
										<div className="message-content">
											{/* Image Message */}
											{message.type === "image" &&
												message.image_url && (
													<div className="image-message">
														<img
															src={
																message.image_url
															}
															alt="Receipt"
															className="receipt-image"
														/>
														<p>{message.content}</p>
													</div>
												)}

											{/* Expense Data Message with Edit Capability */}
											{message.type === "expense_data" &&
												message.expense_data && (
													<div className="expense-data-message">
														<div className="expense-intro">
															{renderFormattedMessage(
																message.content
															)}
														</div>

														{/* Show either editable fields or read-only display */}
														{editingExpense ? (
															<EditableExpenseFields
																expenseData={
																	message.expense_data
																}
																onSave={
																	handleSaveExpenseChanges
																}
																onCancel={
																	handleCancelExpenseEdit
																}
																isLoading={
																	isLoading
																}
															/>
														) : (
															<div className="expense-data-card">
																<div className="expense-header">
																	<h4>
																		🧾
																		Extracted
																		Expense
																		Data
																	</h4>
																	<div className="expense-header-actions">
																		<div className="extraction-status">
																			<span className="status-badge success">
																				✓
																				Extracted
																				Successfully
																			</span>
																		</div>
																		<button
																			onClick={
																				handleEditExpense
																			}
																			disabled={
																				isLoading
																			}
																			className="edit-expense-btn"
																			title="Edit expense details"
																		>
																			<span className="btn-icon">
																				✏️
																			</span>
																			Edit
																		</button>
																	</div>
																</div>

																<div className="expense-fields-grid">
																	{Object.entries(
																		message.expense_data
																	).map(
																		([
																			key,
																			value,
																		]) => {
																			const displayValue =
																				formatFieldValue(
																					value
																				);
																			const isImportant =
																				[
																					"amount",
																					"vendor",
																					"transaction_date",
                                                                                    "expense_type",
                                                                                    "business_purpose",
                                                                                    "meals"
																				].includes(
																					key
																				);

																			return (
																				<div
																					key={
																						key
																					}
																					className={`expense-field-item ${
																						isImportant
																							? "important"
																							: ""
																					}`}
																				>
																					<div className="field-label-container">
																						<span className="field-icon">
																							{key ===
																								"expense_type" &&
																								"🏷️"}
																							{key ===
																								"transaction_date" &&
																								"📅"}
																							{key ===
																								"business_purpose" &&
																								"🎯"}
																							{key ===
																								"vendor" &&
																								"🏪"}
																							{key ===
																								"city" &&
																								"🏙️"}
																							{key ===
																								"country" &&
																								"🌍"}
																							{key ===
																								"payment_type" &&
																								"💳"}
																							{key ===
																								"amount" &&
																								"💰"}
																							{key ===
																								"currency" &&
																								"💱"}
																							{key ===
																								"comment" &&
																								"💬"}
																						</span>
																						<span className="field-label-text">
																							{formatFieldName(
																								key
																							)}
																						</span>
																					</div>
																					<div className="field-value-container">
																						<span className="field-value-text">
																							{
																								displayValue
																							}
																						</span>
																						{value && (
																							<span className="field-check">
																								✓
																							</span>
																						)}
																					</div>
																				</div>
																			);
																		}
																	)}
																</div>

																{message.next_action && (
																	<div className="next-action-container">
																		<div className="action-header">
																			<span className="action-icon">
																				🚀
																			</span>
																			<span className="action-title">
																				What's
																				Next?
																			</span>
																		</div>
																		<div className="action-content">
																			{renderFormattedMessage(
																				message.next_action
																			)}
																		</div>
																		<div className="quick-action-buttons">
																			<button
																				onClick={() =>
																					sendQuickCommand(
																						"1"
																					)
																				}
																				disabled={
																					isLoading
																				}
																				className="action-button primary"
																			>
																				<span className="btn-icon">
																					✨
																				</span>
																				<span>
																					Create
																					New
																					Report
																				</span>
																			</button>
																			<button
																				onClick={() =>
																					sendQuickCommand(
																						"2"
																					)
																				}
																				disabled={
																					isLoading
																				}
																				className="action-button secondary"
																			>
																				<span className="btn-icon">
																					📋
																				</span>
																				<span>
																					Add
																					to
																					Existing
																				</span>
																			</button>
																		</div>
																	</div>
																)}
															</div>
														)}
													</div>
												)}

											{/* Regular Text Message with Beautiful Formatting */}
											{(message.type === "user" ||
												message.type === "assistant" ||
												message.type === "reports") &&
												!message.expense_data &&
												!message.image_url && (
													<div className="formatted-message">
														{renderFormattedMessage(
															message.content
														)}

														{/* Tax Compliance UI */}
														{message.type ===
															"assistant" &&
															message.needs_tax_compliance && (
																<TaxComplianceUI
																	message={
																		message
																	}
																/>
															)}

														{/* Quick Action Buttons for Choices - ONLY show after expense extraction */}
														{message.type ===
															"assistant" &&
															message.content.includes(
																"What would you like to do next"
															) &&
															message.content.includes(
																"Create a new expense report"
															) &&
															message.content.includes(
																"Add to an existing report"
															) &&
															!message.needs_tax_compliance && (
																<div className="quick-actions-container">
																	<div className="quick-actions-label">
																		Choose
																		an
																		option:
																	</div>
																	<div className="quick-actions-buttons">
																		<button
																			onClick={() =>
																				sendQuickCommand(
																					"1"
																				)
																			}
																			disabled={
																				isLoading
																			}
																			className="quick-action-btn primary"
																		>
																			<span className="btn-icon">
																				✨
																			</span>
																			<span className="btn-text">
																				Create
																				New
																				Report
																			</span>
																		</button>
																		<button
																			onClick={() =>
																				sendQuickCommand(
																					"2"
																				)
																			}
																			disabled={
																				isLoading
																			}
																			className="quick-action-btn secondary"
																		>
																			<span className="btn-icon">
																				📋
																			</span>
																			<span className="btn-text">
																				Add
																				to
																				Existing
																			</span>
																		</button>
																	</div>
																</div>
															)}

														{/* Template Buttons for Report Creation */}
														{message.type ===
															"assistant" &&
															message.content.includes(
																"Report Name"
															) &&
															message.content.includes(
																"Business Purpose"
															) &&
															!message.needs_tax_compliance && (
																<div className="template-suggestions">
																	<div className="template-header">
																		<span className="template-icon">
																			💡
																		</span>
																		<span className="template-title">
																			Quick
																			Templates
																		</span>
																	</div>
																	<div className="template-list">
																		{[
																			{
																				name: "Office Supplies",
																				template: `Report Name: Office Supplies - ${new Date().toLocaleDateString()}\nBusiness Purpose: Monthly office supplies and equipment`,
																				icon: "🏢",
																			},
																			{
																				name: "Travel Expenses",
																				template: `Report Name: Travel Expenses - ${new Date().toLocaleDateString()}\nBusiness Purpose: Business travel and transportation`,
																				icon: "✈️",
																			},
																			{
																				name: "Client Meals",
																				template: `Report Name: Client Meals - ${new Date().toLocaleDateString()}\nBusiness Purpose: Client entertainment and meals`,
																				icon: "🍽️",
																			},
																		].map(
																			(
																				item,
																				index
																			) => (
																				<button
																					key={
																						index
																					}
																					onClick={() =>
																						sendQuickCommand(
																							item.template
																						)
																					}
																					disabled={
																						isLoading
																					}
																					className="template-btn"
																				>
																					<span className="template-btn-icon">
																						{
																							item.icon
																						}
																					</span>
																					<span className="template-btn-text">
																						{
																							item.name
																						}
																					</span>
																					<span className="template-btn-arrow">
																						→
																					</span>
																				</button>
																			)
																		)}
																	</div>
																</div>
															)}

														{/* Success/Completion Messages */}
														{message.type ===
															"assistant" &&
															(message.content.includes(
																"✅"
															) ||
																message.content.includes(
																	"created successfully"
																)) && (
																<div className="success-highlight">
																	<div className="success-icon">
																		🎉
																	</div>
																	<div className="success-message">
																		Action
																		completed
																		successfully!
																	</div>
																</div>
															)}
													</div>
												)}

											<div className="message-time">
												{new Date(
													message.timestamp
												).toLocaleTimeString()}
											</div>
										</div>
									</div>
								);
							})}

							{/* Loading Indicator */}
							{isLoading && (
								<div className="message assistant">
									<div className="message-content">
										<p>🔍 Processing...</p>
										<div className="typing-indicator">
											<span></span>
											<span></span>
											<span></span>
										</div>
									</div>
								</div>
							)}

							<div ref={messagesEndRef} />
						</div>

						{/* Drop Zone Overlay */}
						{dragActive && (
							<div className="drop-overlay">
								<div className="drop-content">
									<div className="drop-icon">🧾</div>
									<h3>Drop your receipt here</h3>
									<p>
										I'll extract expense data automatically
										and help you add it to SAP Concur
									</p>
								</div>
							</div>
						)}
					</div>

					{/* Input Area */}
					<div className="chat-input-container">
						<div className="input-row">
							<button
								className="attach-btn"
								onClick={() => fileInputRef.current?.click()}
								disabled={isLoading}
								title="Upload receipt"
							>
								📎
							</button>

							<textarea
								ref={textareaRef}
								value={inputMessage}
								onChange={(e) =>
									setInputMessage(e.target.value)
								}
								onKeyPress={handleKeyPress}
								placeholder="Ask me anything or upload a receipt..."
								className="message-input"
								rows="1"
								disabled={isLoading}
							/>

							<button
								onClick={sendMessage}
								disabled={!inputMessage.trim() || isLoading}
								className="send-btn"
								title="Send message"
							>
								➤
							</button>
						</div>

						<input
							ref={fileInputRef}
							type="file"
							accept="image/*"
							onChange={handleFileSelect}
							style={{ display: "none" }}
						/>
					</div>
				</div>
			</div>
		</div>
	);
}

export default App;
