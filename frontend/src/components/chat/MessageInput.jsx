import React, { useState, useRef, useEffect } from "react";

const MessageInput = ({
	onSendMessage,
	onFileSelect,
	isLoading = false,
	placeholder = "Ask me anything or upload a receipt...",
}) => {
	const [inputMessage, setInputMessage] = useState("");
	const textareaRef = useRef(null);
	const fileInputRef = useRef(null);

	// Auto-resize textarea
	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto";
			textareaRef.current.style.height =
				Math.min(textareaRef.current.scrollHeight, 120) + "px";
		}
	}, [inputMessage]);

	const handleSend = () => {
		if (!inputMessage.trim() || isLoading) return;
		onSendMessage(inputMessage);
		setInputMessage("");
	};

	const handleKeyPress = (e) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	};

	const handleFileClick = () => {
		fileInputRef.current?.click();
	};

	const handleFileChange = (e) => {
		const file = e.target.files?.[0];
		if (file) {
			onFileSelect(file);
		}
	};

	return (
		<div className="chat-input-container">
			<div className="input-row">
				<button
					className="attach-btn"
					onClick={handleFileClick}
					disabled={isLoading}
					title="Upload receipt"
				>
					📎
				</button>

				<textarea
					ref={textareaRef}
					value={inputMessage}
					onChange={(e) => setInputMessage(e.target.value)}
					onKeyPress={handleKeyPress}
					placeholder={placeholder}
					className="message-input"
					rows="1"
					disabled={isLoading}
				/>

				<button
					onClick={handleSend}
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
				onChange={handleFileChange}
				style={{ display: "none" }}
			/>
		</div>
	);
};

export default MessageInput;
