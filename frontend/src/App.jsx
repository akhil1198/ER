// frontend/src/App.jsx - Updated for dynamic expense types

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
		currentExpenseType,
		editingExpense,
		updateExpenseData,
		updateExpenseType,
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

			// Update current expense data with enhanced information
			updateExpenseData(data.expense_data);
			if (data.expense_type_info) {
				updateExpenseType(
					data.expense_type_info.id,
					data.expense_type_info
				);
			}

			// Add processing response with enhanced data
			const responseMessage = {
				id: `response-${Date.now()}`,
				type: "expense_data",
				content: data.message,
				timestamp: new Date().toISOString(),
				expense_data: data.expense_data,
				expense_type_info: data.expense_type_info,
				validation_errors: data.validation_errors,
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

	const handleSaveExpenseChanges = async (updatedExpenseData) => {
		try {
			// Save the changes
			saveExpenseChanges(updatedExpenseData);

			// Update the expense data in the most recent expense message
			setMessages((prevMessages) => {
				return prevMessages.map((message) => {
					if (
						message.type === "expense_data" &&
						message.expense_data
					) {
						return {
							...message,
							expense_data: updatedExpenseData,
							// Clear validation errors after successful save
							validation_errors: [],
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
		} catch (error) {
			console.error("Failed to save expense changes:", error);

			// Show error message
			const errorMessage = {
				id: `error-${Date.now()}`,
				type: "assistant",
				content: `❌ Failed to save changes: ${error.message}. Please try again.`,
				timestamp: new Date().toISOString(),
			};

			addMessage(errorMessage);
		}
	};

	const handleExpenseTypeChange = async (newExpenseTypeId) => {
		try {
			// Call API to re-map data to new expense type
			const response = await fetch(
				`/api/expense-types/${newExpenseTypeId}/map-data`,
				{
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify(currentExpense),
				}
			);

			if (response.ok) {
				const result = await response.json();

				// Update expense data and type
				updateExpenseData(result.mapped_data);
				updateExpenseType(newExpenseTypeId, result.expense_type_config);

				// Update the most recent expense message
				setMessages((prevMessages) => {
					return prevMessages.map((message) => {
						if (
							message.type === "expense_data" &&
							message.expense_data
						) {
							return {
								...message,
								expense_data: result.mapped_data,
								expense_type_info: {
									...message.expense_type_info,
									id: newExpenseTypeId,
									...result.expense_type_config,
								},
								validation_errors:
									result.validation_errors || [],
							};
						}
						return message;
					});
				});

				// Add confirmation message
				const changeMessage = {
					id: `type-change-${Date.now()}`,
					type: "assistant",
					content: `✅ **Expense type changed successfully!**\n\nYour data has been remapped to: **${result.expense_type_config.name}**\n\nPlease review the updated fields and continue with your expense submission.`,
					timestamp: new Date().toISOString(),
				};

				addMessage(changeMessage);
			}
		} catch (error) {
			console.error("Failed to change expense type:", error);

			const errorMessage = {
				id: `error-${Date.now()}`,
				type: "assistant",
				content: `❌ Failed to change expense type: ${error.message}. Please try again.`,
				timestamp: new Date().toISOString(),
			};

			addMessage(errorMessage);
		}
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
						onExpenseTypeChange={handleExpenseTypeChange}
						currentExpenseType={currentExpenseType}
					/>
				</div>
			</div>
		</div>
	);
}

export default App;
