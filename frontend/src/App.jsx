// App.js - Fixed version with stable component references
import React, { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";

// Constants
const API_BASE_URL = "http://localhost:8000";
const WS_BASE_URL = "ws://localhost:8000";

// Main App Component
function App() {
	// ========================================
	// STATE MANAGEMENT
	// ========================================
	const [sessionId, setSessionId] = useState(null);
	const [messages, setMessages] = useState([]);
	const [inputMessage, setInputMessage] = useState("");
	const [isConnected, setIsConnected] = useState(false);
	const [isUploading, setIsUploading] = useState(false);
	const [dragActive, setDragActive] = useState(false);
	const [chatMode, setChatMode] = useState("normal");
	const [sapRequirements, setSapRequirements] = useState({});
	const [isMobile, setIsMobile] = useState(false);

	// ========================================
	// REFS
	// ========================================
	const wsRef = useRef(null);
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
		return () => wsRef.current?.close();
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
	// API FUNCTIONS (Memoized with useCallback)
	// ========================================

	const initializeChat = useCallback(async () => {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/chat/create-session`,
				{
					method: "POST",
				}
			);
			const data = await response.json();
			setSessionId(data.session_id);
			await loadMessages(data.session_id);
			connectWebSocket(data.session_id);
		} catch (error) {
			console.error("Failed to initialize chat:", error);
		}
	}, []);

	const loadSapRequirements = useCallback(async () => {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/sap-concur/field-requirements`
			);
			const data = await response.json();
			setSapRequirements(data.fields);
		} catch (error) {
			console.error("Failed to load SAP requirements:", error);
		}
	}, []);

	const loadMessages = useCallback(async (sessionId) => {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/chat/${sessionId}/messages`
			);
			const data = await response.json();
			setMessages(data.messages);
			setChatMode(data.mode || "normal");
		} catch (error) {
			console.error("Failed to load messages:", error);
		}
	}, []);

	const sendMessage = useCallback(async () => {
		if (!inputMessage.trim() || !sessionId) return;

		try {
			await fetch(`${API_BASE_URL}/api/chat/${sessionId}/send-message`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ content: inputMessage }),
			});
			setInputMessage("");
		} catch (error) {
			console.error("Failed to send message:", error);
		}
	}, [inputMessage, sessionId]);

	const sendMessageDirectly = useCallback(
		async (content) => {
			if (!sessionId) return;

			try {
				await fetch(
					`${API_BASE_URL}/api/chat/${sessionId}/send-message`,
					{
						method: "POST",
						headers: { "Content-Type": "application/json" },
						body: JSON.stringify({ content }),
					}
				);
			} catch (error) {
				console.error("Failed to send message:", error);
			}
		},
		[sessionId]
	);

	const handleFileUpload = useCallback(
		async (file) => {
			if (!file || !sessionId) return;

			setIsUploading(true);
			try {
				const formData = new FormData();
				formData.append("file", file);
				await fetch(
					`${API_BASE_URL}/api/chat/${sessionId}/upload-receipt`,
					{
						method: "POST",
						body: formData,
					}
				);
			} catch (error) {
				console.error("Failed to upload file:", error);
			} finally {
				setIsUploading(false);
			}
		},
		[sessionId]
	);

	// ========================================
	// WEBSOCKET FUNCTIONS
	// ========================================

	const connectWebSocket = useCallback((sessionId) => {
		wsRef.current = new WebSocket(`${WS_BASE_URL}/ws/chat/${sessionId}`);

		wsRef.current.onopen = () => setIsConnected(true);
		wsRef.current.onclose = () => setIsConnected(false);
		wsRef.current.onerror = (error) => {
			console.error("WebSocket error:", error);
			setIsConnected(false);
		};
		wsRef.current.onmessage = (event) => {
			const message = JSON.parse(event.data);
			setMessages((prev) => [...prev, message]);

			// Update chat mode based on message type
			if (
				message.type === "system" &&
				message.content.includes("normal chat mode")
			) {
				setChatMode("normal");
			} else if (message.type === "expense_data") {
				setChatMode("expense");
			}
		};
	}, []);

	// ========================================
	// EVENT HANDLERS (Memoized with useCallback)
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
	// UTILITY FUNCTIONS (Memoized with useCallback)
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
							{isUploading && (
								<div className="message assistant">
									<div className="message-content">
										<div className="typing-indicator">
											<span></span>
											<span></span>
											<span></span>
										</div>
										<p>🔍 Processing your receipt...</p>
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

					{/* Input Area - Fixed to prevent re-rendering */}
					<div className="chat-input-container">
						<div className="input-row">
							<button
								className="attach-btn"
								onClick={() => fileInputRef.current?.click()}
								disabled={isUploading}
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
								disabled={isUploading}
							/>

							<button
								onClick={sendMessage}
								disabled={!inputMessage.trim() || isUploading}
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
