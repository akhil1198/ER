import React, { useState, useEffect } from "react";
import "./App.css";

// Components
import Navbar from "./components/common/Navbar";
import Sidebar from "./components/layout/Sidebar";
import ChatContainer from "./components/chat/ChatContainer";

// Hooks
import { useChat } from "./hooks/useChat";
import { useFileUpload } from "./hooks/useFileUpload";
import { useExpenseData } from "./hooks/useExpenseData";

function App() {
	// ========================================
	// STATE MANAGEMENT
	// ========================================
	const [isMobile, setIsMobile] = useState(false);

	// Custom hooks
	const {
		messages,
		isLoading: chatLoading,
		sendMessage,
		sendQuickCommand,
		addMessage,
		initializeChat,
		setMessages,
	} = useChat();

	const {
		dragActive,
		isUploading,
		handleDragEvents,
		handleDrop,
		uploadFile,
	} = useFileUpload();

	const {
		currentExpense,
		editingExpense,
		updateExpenseData,
		startEditing,
		stopEditing,
		saveExpenseChanges,
	} = useExpenseData();

	const isLoading = chatLoading || isUploading;

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

	// Initialize chat
	useEffect(() => {
		initializeChat();
	}, [initializeChat]);

	// ========================================
	// EVENT HANDLERS
	// ========================================

	const handleFileUpload = async (file) => {
		if (!file || isLoading) return;

		// Create image URL for immediate display
		const imageUrl = URL.createObjectURL(file);

		// Add the image message immediately
		const imageMessage = {
			id: `image-${Date.now()}`,
			type: "image",
			content: `Uploaded receipt: ${file.name}`,
			timestamp: new Date().toISOString(),
			image_url: imageUrl,
		};

		addMessage(imageMessage);

		try {
			const data = await uploadFile(file);

			// Update current expense data
			updateExpenseData(data.expense_data);

			// Add processing response
			const responseMessage = {
				id: `response-${Date.now()}`,
				type: "expense_data",
				content: data.message,
				timestamp: new Date().toISOString(),
				expense_data: data.expense_data,
				next_action: data.next_action,
			};

			addMessage(responseMessage);

			// Clean up the temporary object URL
			URL.revokeObjectURL(imageUrl);
		} catch (error) {
			console.error("Failed to upload file:", error);

			// Remove the temporary image message and show error
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
		}
	};

	const handleDropEvent = async (e) => {
		const result = await handleDrop(e);
		if (result) {
			// Process the result similar to handleFileUpload
			handleFileUpload(result);
		}
	};

	const handleSaveExpenseChanges = (updatedExpenseData) => {
		saveExpenseChanges(updatedExpenseData);

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

		addMessage(updateMessage);
	};

	// ========================================
	// RENDER
	// ========================================

	return (
		<div
			className={`App chat-app ${dragActive ? "drag-active" : ""}`}
			onDragEnter={handleDragEvents}
			onDragLeave={handleDragEvents}
			onDragOver={handleDragEvents}
			onDrop={handleDropEvent}
		>
			{/* Navigation */}
			<Navbar />

			<div className="app-content">
				{/* Sidebar */}
				<Sidebar isMobile={isMobile} />

				{/* Main Chat Area */}
				<div className="chat-main">
					<ChatContainer
						messages={messages}
						onSendMessage={sendMessage}
						onSendCommand={sendQuickCommand}
						onFileUpload={handleFileUpload}
						isLoading={isLoading}
						dragActive={dragActive}
						onEditExpense={startEditing}
						editingExpense={editingExpense}
						onSaveExpense={handleSaveExpenseChanges}
						onCancelExpense={stopEditing}
					/>
				</div>
			</div>
		</div>
	);
}

export default App;
