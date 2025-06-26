// App.jsx - Simplified version without WebSocket complexity
import React, { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";

// Constants
const API_BASE_URL = "http://localhost:8000";

// Main App Component
function App() {
	// ========================================
	// STATE MANAGEMENT
	// ========================================
	const [sessionId, setSessionId] = useState(null);
	const [messages, setMessages] = useState([]);
	const [inputMessage, setInputMessage] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [dragActive, setDragActive] = useState(false);
	const [chatMode, setChatMode] = useState("normal");
	const [currentExpense, setCurrentExpense] = useState(null);
	const [sapRequirements, setSapRequirements] = useState({});
	const [isMobile, setIsMobile] = useState(false);

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

	// Initialize app
	useEffect(() => {
		initializeChat();
		loadSapRequirements();
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
			const response = await fetch(`${API_BASE_URL}${url}`, {
				headers: {
					"Content-Type": "application/json",
					...options.headers,
				},
				...options,
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error(`API call failed for ${url}:`, error);
			throw error;
		}
	}, []);

	const initializeChat = useCallback(async () => {
		try {
			const data = await makeApiCall("/api/chat/create-session", {
				method: "POST",
			});
			setSessionId(data.session_id);
			await loadMessages(data.session_id);
		} catch (error) {
			console.error("Failed to initialize chat:", error);
		}
	}, [makeApiCall]);

	const loadSapRequirements = useCallback(async () => {
		try {
			const data = await makeApiCall(
				"/api/sap-concur/field-requirements"
			);
			setSapRequirements(data.fields);
		} catch (error) {
			console.error("Failed to load SAP requirements:", error);
		}
	}, [makeApiCall]);

	const loadMessages = useCallback(
		async (sessionId) => {
			try {
				const data = await makeApiCall(
					`/api/chat/${sessionId}/messages`
				);
				setMessages(data.messages);
				setChatMode(data.mode || "normal");
				setCurrentExpense(data.current_expense || null);
			} catch (error) {
				console.error("Failed to load messages:", error);
			}
		},
		[makeApiCall]
	);

	const sendMessage = useCallback(async () => {
		if (!inputMessage.trim() || !sessionId || isLoading) return;

		// Add user message immediately to the UI
		const userMessage = {
			id: `temp-${Date.now()}`,
			type: "user",
			content: inputMessage,
			timestamp: new Date().toISOString(),
			expense_data: null,
			image_url: null,
		};

		// Update messages immediately and clear input
		setMessages((prevMessages) => [...prevMessages, userMessage]);
		const messageToSend = inputMessage;
		setInputMessage("");
		setIsLoading(true);

		try {
			const data = await makeApiCall(
				`/api/chat/${sessionId}/send-message`,
				{
					method: "POST",
					body: JSON.stringify({ content: messageToSend }),
				}
			);

			// Replace all messages with the backend response
			setMessages(data.messages);
			setChatMode(data.mode);
			setCurrentExpense(data.current_expense);
		} catch (error) {
			console.error("Failed to send message:", error);

			// On error, add an error message but keep the user message
			setMessages((prevMessages) => [
				...prevMessages,
				{
					id: `error-${Date.now()}`,
					type: "assistant",
					content: `❌ Failed to send message: ${error.message}. Please try again.`,
					timestamp: new Date().toISOString(),
					expense_data: null,
					image_url: null,
				},
			]);
		} finally {
			setIsLoading(false);
		}
	}, [inputMessage, sessionId, isLoading, makeApiCall]);

	const sendMessageDirectly = useCallback(
		async (content) => {
			if (!sessionId || isLoading) return;

			// Add user message immediately to the UI
			const userMessage = {
				id: `temp-${Date.now()}`,
				type: "user",
				content: content,
				timestamp: new Date().toISOString(),
				expense_data: null,
				image_url: null,
			};

			setMessages((prevMessages) => [...prevMessages, userMessage]);
			setIsLoading(true);

			try {
				const data = await makeApiCall(
					`/api/chat/${sessionId}/send-message`,
					{
						method: "POST",
						body: JSON.stringify({ content }),
					}
				);

				// Replace all messages with the backend response
				setMessages(data.messages);
				setChatMode(data.mode);
				setCurrentExpense(data.current_expense);
			} catch (error) {
				console.error("Failed to send message:", error);

				// On error, add an error message
				setMessages((prevMessages) => [
					...prevMessages,
					{
						id: `error-${Date.now()}`,
						type: "assistant",
						content: `❌ Failed to send message: ${error.message}. Please try again.`,
						timestamp: new Date().toISOString(),
						expense_data: null,
						image_url: null,
					},
				]);
			} finally {
				setIsLoading(false);
			}
		},
		[sessionId, isLoading, makeApiCall]
	);

	const handleFileUpload = useCallback(
		async (file) => {
			if (!file || !sessionId || isLoading) return;

			// Create image URL for immediate display
			const imageUrl = URL.createObjectURL(file);

			// Add the image message immediately to the UI
			const imageMessage = {
				id: `temp-${Date.now()}`,
				type: "image",
				content: `Uploaded receipt: ${file.name}`,
				timestamp: new Date().toISOString(),
				image_url: imageUrl,
				expense_data: null,
			};

			// Update messages immediately to show the uploaded image
			setMessages((prevMessages) => [...prevMessages, imageMessage]);
			setIsLoading(true);

			try {
				const formData = new FormData();
				formData.append("file", file);

				const response = await fetch(
					`${API_BASE_URL}/api/chat/${sessionId}/upload-receipt`,
					{
						method: "POST",
						body: formData,
					}
				);

				if (!response.ok) {
					throw new Error(`Upload failed: ${response.status}`);
				}

				const data = await response.json();

				// Replace all messages with the backend response
				// This will include the properly formatted image message plus processing results
				setMessages(data.messages);
				setChatMode(data.mode);
				setCurrentExpense(data.current_expense);

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
							expense_data: null,
							image_url: null,
						},
					];
				});

				// Clean up the temporary object URL
				URL.revokeObjectURL(imageUrl);
			} finally {
				setIsLoading(false);
			}
		},
		[sessionId, isLoading]
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

	const exitExpenseMode = useCallback(
		() => sendMessageDirectly("stop"),
		[sendMessageDirectly]
	);

	const formatFieldName = useCallback(
		(fieldName) => {
			const field = sapRequirements[fieldName];
			return field
				? field.name
				: fieldName
						.replace(/_/g, " ")
						.replace(/\b\w/g, (l) => l.toUpperCase());
		},
		[sapRequirements]
	);

	const formatFieldValue = useCallback((value) => {
		if (value === null || value === undefined) return "Not specified";
		if (typeof value === "boolean") return value ? "Yes" : "No";
		if (typeof value === "number") return value.toLocaleString();
		return value;
	}, []);

	const isFieldRequired = useCallback(
		(fieldName) => sapRequirements[fieldName]?.required || false,
		[sapRequirements]
	);

	const isFieldValid = useCallback(
		(fieldName, value) => {
			const field = sapRequirements[fieldName];
			if (!field) return true;

			if (
				field.required &&
				(value === null || value === undefined || value === "")
			) {
				return false;
			}

			if (
				value !== null &&
				field.valid_values &&
				!field.valid_values.includes(String(value))
			) {
				return false;
			}

			return true;
		},
		[sapRequirements]
	);

	const getFieldStatus = useCallback(
		(fieldName, value) => {
			if (!isFieldValid(fieldName, value)) return "invalid";
			if (value === null || value === undefined || value === "") {
				return isFieldRequired(fieldName)
					? "missing-required"
					: "missing-optional";
			}
			return "valid";
		},
		[isFieldRequired, isFieldValid]
	);

	// Loading State
	if (!sessionId) {
		return (
			<div className="App loading-app">
				<div className="loading-spinner"></div>
				<p>Initializing Gallagher AI...</p>
			</div>
		);
	}

	// Main App Render
	return (
		<div
			className={`App chat-app ${
				dragActive ? "drag-active" : ""
			} ${chatMode}`}
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
						<button
							className={`nav-item ${
								chatMode === "normal" ? "active" : ""
							}`}
						>
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

											{/* Expense Data Message */}
											{message.type === "expense_data" &&
												message.expense_data && (
													<div className="expense-data-message">
														<p className="expense-intro">
															{message.content}
														</p>
														<div className="expense-data-card">
															<div className="expense-header">
																<h4>
																	🧾 SAP
																	Concur
																	Expense Data
																</h4>
																<div className="mode-indicator">
																	<span className="mode-badge expense">
																		Expense
																		Mode
																	</span>
																</div>
															</div>

															<div className="expense-fields">
																{Object.entries(
																	message.expense_data
																).map(
																	([
																		key,
																		value,
																	]) => {
																		const status =
																			getFieldStatus(
																				key,
																				value
																			);
																		const field =
																			sapRequirements[
																				key
																			];

																		return (
																			<div
																				key={
																					key
																				}
																				className={`expense-field ${status}`}
																			>
																				<div className="field-info">
																					<span className="field-label">
																						{formatFieldName(
																							key
																						)}
																						{isFieldRequired(
																							key
																						) && (
																							<span className="required-indicator">
																								*
																							</span>
																						)}
																					</span>
																					<span
																						className={`field-value ${status}`}
																					>
																						{formatFieldValue(
																							value
																						)}
																					</span>
																				</div>
																				{status ===
																					"invalid" &&
																					field && (
																						<div className="field-hint">
																							{field.valid_values
																								? `Must be one of: ${field.valid_values.join(
																										", "
																								  )}`
																								: field.description}
																						</div>
																					)}
																				{status ===
																					"missing-required" && (
																					<div className="field-hint error">
																						This
																						field
																						is
																						required
																						for
																						SAP
																						Concur
																					</div>
																				)}
																			</div>
																		);
																	}
																)}
															</div>

															<div className="expense-actions">
																<button
																	className="action-btn secondary"
																	onClick={() =>
																		setInputMessage(
																			"Change the "
																		)
																	}
																>
																	✏️ Make
																	Changes
																</button>
																<button className="action-btn primary">
																	📊 Create
																	SAP Concur
																	Report
																</button>
																<button
																	className="action-btn tertiary"
																	onClick={
																		exitExpenseMode
																	}
																>
																	❌ Exit
																	Expense Mode
																</button>
															</div>

															<div className="quick-corrections">
																<p className="quick-corrections-title">
																	💡 Quick
																	corrections:
																</p>
																<div className="correction-examples">
																	{[
																		{
																			text: "Change the business purpose to client meeting",
																			prefix: "Change the business purpose to ",
																		},
																		{
																			text: "Set the amount to $50.00",
																			prefix: "Set the amount to ",
																		},
																		{
																			text: "The vendor should be Starbucks",
																			prefix: "The vendor should be ",
																		},
																	].map(
																		(
																			correction,
																			index
																		) => (
																			<span
																				key={
																					index
																				}
																				className="correction-example"
																				onClick={() =>
																					setInputMessage(
																						correction.prefix
																					)
																				}
																			>
																				"
																				{
																					correction.text
																				}

																				"
																			</span>
																		)
																	)}
																</div>
															</div>
														</div>
													</div>
												)}

											{/* System Message */}
											{message.type === "system" && (
												<div className="system-message">
													<span className="system-icon">
														🔄
													</span>
													<p>{message.content}</p>
												</div>
											)}

											{/* Error Message */}
											{message.content &&
												message.content.includes(
													"Sorry, I had trouble processing"
												) && (
													<div className="error-message">
														{message.content}
													</div>
												)}

											{/* Processing Message */}
											{message.content &&
												message.content.includes(
													"Analyzing your receipt"
												) && (
													<div className="processing-message">
														<p>{message.content}</p>
													</div>
												)}

											{/* Regular Text Message */}
											{(message.type === "user" ||
												message.type === "assistant") &&
												!["image", "system"].includes(
													message.type
												) &&
												!message.content.includes(
													"Sorry, I had trouble processing"
												) &&
												!message.content.includes(
													"Analyzing your receipt"
												) && <p>{message.content}</p>}

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
										I'll extract SAP Concur expense data
										automatically
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
								placeholder="Ask me anything..."
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
