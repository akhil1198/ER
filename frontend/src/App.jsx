// App.js - Enhanced React Chat Interface
import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const API_BASE_URL = "http://localhost:8000";
const WS_BASE_URL = "ws://localhost:8000";

function App() {
	const [sessionId, setSessionId] = useState(null);
	const [messages, setMessages] = useState([]);
	const [inputMessage, setInputMessage] = useState("");
	const [isConnected, setIsConnected] = useState(false);
	const [isUploading, setIsUploading] = useState(false);
	const [dragActive, setDragActive] = useState(false);
	const [chatMode, setChatMode] = useState("normal"); // 'normal' or 'expense'
	const [sapRequirements, setSapRequirements] = useState({});

	const wsRef = useRef(null);
	const messagesEndRef = useRef(null);
	const fileInputRef = useRef(null);

	// Initialize chat session and load SAP requirements
	useEffect(() => {
		initializeChat();
		loadSapRequirements();
		return () => {
			if (wsRef.current) {
				wsRef.current.close();
			}
		};
	}, []);

	// Auto-scroll to bottom when new messages arrive
	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	const initializeChat = async () => {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/chat/create-session`,
				{
					method: "POST",
				}
			);
			const data = await response.json();
			const newSessionId = data.session_id;
			setSessionId(newSessionId);

			await loadMessages(newSessionId);
			connectWebSocket(newSessionId);
		} catch (error) {
			console.error("Failed to initialize chat:", error);
		}
	};

	const loadSapRequirements = async () => {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/sap-concur/field-requirements`
			);
			const data = await response.json();
			setSapRequirements(data.fields);
		} catch (error) {
			console.error("Failed to load SAP requirements:", error);
		}
	};

	const connectWebSocket = (sessionId) => {
		wsRef.current = new WebSocket(`${WS_BASE_URL}/ws/chat/${sessionId}`);

		wsRef.current.onopen = () => {
			setIsConnected(true);
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

		wsRef.current.onclose = () => {
			setIsConnected(false);
		};

		wsRef.current.onerror = (error) => {
			console.error("WebSocket error:", error);
			setIsConnected(false);
		};
	};

	const loadMessages = async (sessionId) => {
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
	};

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	};

	const sendMessage = async () => {
		if (!inputMessage.trim() || !sessionId) return;

		try {
			await fetch(`${API_BASE_URL}/api/chat/${sessionId}/send-message`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ content: inputMessage }),
			});
			setInputMessage("");
		} catch (error) {
			console.error("Failed to send message:", error);
		}
	};

	const handleFileUpload = async (file) => {
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
	};

	const handleDragEvents = (e) => {
		e.preventDefault();
		e.stopPropagation();

		if (e.type === "dragenter" || e.type === "dragover") {
			setDragActive(true);
		} else if (e.type === "dragleave") {
			setDragActive(false);
		}
	};

	const handleDrop = (e) => {
		e.preventDefault();
		e.stopPropagation();
		setDragActive(false);

		const files = e.dataTransfer.files;
		if (files && files[0] && files[0].type.startsWith("image/")) {
			handleFileUpload(files[0]);
		}
	};

	const handleFileSelect = (e) => {
		const file = e.target.files?.[0];
		if (file) {
			handleFileUpload(file);
		}
	};

	const handleKeyPress = (e) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	};

	const formatFieldName = (fieldName) => {
		const field = sapRequirements[fieldName];
		return field
			? field.name
			: fieldName
					.replace(/_/g, " ")
					.replace(/\b\w/g, (l) => l.toUpperCase());
	};

	const formatFieldValue = (value, fieldName) => {
		if (value === null || value === undefined) return "Not specified";
		if (typeof value === "boolean") return value ? "Yes" : "No";
		if (typeof value === "number") return value.toLocaleString();
		return value;
	};

	const isFieldRequired = (fieldName) => {
		return sapRequirements[fieldName]?.required || false;
	};

	const isFieldValid = (fieldName, value) => {
		const field = sapRequirements[fieldName];
		if (!field) return true;

		// Check if required field is missing
		if (
			field.required &&
			(value === null || value === undefined || value === "")
		) {
			return false;
		}

		// Check valid values
		if (
			value !== null &&
			field.valid_values &&
			!field.valid_values.includes(String(value))
		) {
			return false;
		}

		return true;
	};

	const getFieldStatus = (fieldName, value) => {
		if (!isFieldValid(fieldName, value)) {
			return "invalid";
		}
		if (value === null || value === undefined || value === "") {
			return isFieldRequired(fieldName)
				? "missing-required"
				: "missing-optional";
		}
		return "valid";
	};

	const exitExpenseMode = () => {
		sendMessageDirectly("stop");
	};

	const sendMessageDirectly = async (content) => {
		if (!sessionId) return;

		try {
			await fetch(`${API_BASE_URL}/api/chat/${sessionId}/send-message`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ content }),
			});
		} catch (error) {
			console.error("Failed to send message:", error);
		}
	};

	const renderExpenseField = (fieldName, value) => {
		const status = getFieldStatus(fieldName, value);
		const field = sapRequirements[fieldName];

		return (
			<div key={fieldName} className={`expense-field ${status}`}>
				<div className="field-info">
					<span className="field-label">
						{formatFieldName(fieldName)}
						{isFieldRequired(fieldName) && (
							<span className="required-indicator">*</span>
						)}
					</span>
					<span className={`field-value ${status}`}>
						{formatFieldValue(value, fieldName)}
					</span>
				</div>
				{status === "invalid" && field && (
					<div className="field-hint">
						{field.valid_values
							? `Must be one of: ${field.valid_values.join(", ")}`
							: field.description}
					</div>
				)}
				{status === "missing-required" && (
					<div className="field-hint error">
						This field is required for SAP Concur
					</div>
				)}
			</div>
		);
	};

	const renderMessage = (message) => {
		const isUser = message.type === "user" || message.type === "image";

		return (
			<div
				key={message.id}
				className={`message ${isUser ? "user" : "assistant"} ${
					message.type
				}`}
			>
				<div className="message-content">
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

					{message.type === "expense_data" &&
						message.expense_data && (
							<div className="expense-data-message">
								<p className="expense-intro">
									{message.content}
								</p>
								<div className="expense-data-card">
									<div className="expense-header">
										<h4>🧾 SAP Concur Expense Data</h4>
										<div className="mode-indicator">
											<span className="mode-badge expense">
												Expense Mode
											</span>
										</div>
									</div>

									<div className="expense-fields">
										{Object.entries(
											message.expense_data
										).map(([key, value]) =>
											renderExpenseField(key, value)
										)}
									</div>

									<div className="expense-actions">
										<button
											className="action-btn secondary"
											onClick={() =>
												setInputMessage("Change the ")
											}
										>
											✏️ Make Changes
										</button>
										<button className="action-btn primary">
											📊 Create SAP Concur Report
										</button>
										<button
											className="action-btn tertiary"
											onClick={exitExpenseMode}
										>
											❌ Exit Expense Mode
										</button>
									</div>

									<div className="quick-corrections">
										<p className="quick-corrections-title">
											💡 Quick corrections:
										</p>
										<div className="correction-examples">
											<span
												className="correction-example"
												onClick={() =>
													setInputMessage(
														"Change the business purpose to "
													)
												}
											>
												"Change the business purpose to
												client meeting"
											</span>
											<span
												className="correction-example"
												onClick={() =>
													setInputMessage(
														"Set the amount to "
													)
												}
											>
												"Set the amount to $50.00"
											</span>
											<span
												className="correction-example"
												onClick={() =>
													setInputMessage(
														"The vendor should be "
													)
												}
											>
												"The vendor should be Starbucks"
											</span>
										</div>
									</div>
								</div>
							</div>
						)}

					{message.type === "system" && (
						<div className="system-message">
							<span className="system-icon">🔄</span>
							<p>{message.content}</p>
						</div>
					)}

					{(message.type === "user" ||
						message.type === "assistant") &&
						message.type !== "image" &&
						message.type !== "system" && <p>{message.content}</p>}

					<div className="message-time">
						{new Date(message.timestamp).toLocaleTimeString()}
					</div>
				</div>
			</div>
		);
	};

	const getModeInfo = () => {
		if (chatMode === "expense") {
			return {
				title: "🧾 Expense Processing Mode",
				description: "Analyzing receipts for SAP Concur",
				color: "#667eea",
			};
		}
		return {
			title: "💬 Normal Chat Mode",
			description: "General AI assistant",
			color: "#28a745",
		};
	};

	if (!sessionId) {
		return (
			<div className="App loading-app">
				<div className="loading-spinner"></div>
				<p>Initializing chat...</p>
			</div>
		);
	}

	const modeInfo = getModeInfo();

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
			{/* Header */}
			<header
				className="chat-header"
				style={{
					background: `linear-gradient(135deg, ${modeInfo.color} 0%, #764ba2 100%)`,
				}}
			>
				<div className="header-content">
					<div className="header-left">
						<h1>{modeInfo.title}</h1>
						<p className="mode-description">
							{modeInfo.description}
						</p>
					</div>
					<div className="header-right">
						<div className="connection-status">
							<div
								className={`status-indicator ${
									isConnected ? "connected" : "disconnected"
								}`}
							></div>
							<span>
								{isConnected ? "Connected" : "Disconnected"}
							</span>
						</div>
						{chatMode === "expense" && (
							<button
								className="exit-mode-btn"
								onClick={exitExpenseMode}
							>
								Exit Expense Mode
							</button>
						)}
					</div>
				</div>
			</header>

			{/* Chat Messages */}
			<div className="chat-container">
				<div className="messages-container">
					{messages.map(renderMessage)}
					{isUploading && (
						<div className="message assistant">
							<div className="message-content">
								<div className="typing-indicator">
									<span></span>
									<span></span>
									<span></span>
								</div>
								<p>
									🔍 Processing your receipt for SAP Concur...
								</p>
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
						disabled={isUploading}
						title="Upload receipt"
					>
						📎
					</button>

					<textarea
						value={inputMessage}
						onChange={(e) => setInputMessage(e.target.value)}
						onKeyPress={handleKeyPress}
						placeholder={
							chatMode === "expense"
								? "Make corrections like 'Change vendor to Starbucks' or type 'stop' to exit expense mode..."
								: "Type a message... or drag & drop a receipt image to process expenses"
						}
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
						📤
					</button>
				</div>

				<input
					ref={fileInputRef}
					type="file"
					accept="image/*"
					onChange={handleFileSelect}
					style={{ display: "none" }}
				/>

				<div className="input-hint">
					{chatMode === "expense" ? (
						<span>
							💡 Make corrections: "Change the amount to $25.50" •
							"Set business purpose to client meeting" • Type
							"stop" to exit
						</span>
					) : (
						<span>
							💡 Upload receipt images for expense processing, or
							chat about anything!
						</span>
					)}
				</div>
			</div>
		</div>
	);
}

export default App;
