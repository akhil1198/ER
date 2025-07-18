import { useState, useCallback } from "react";
import { apiService } from "../services/api";

export const useChat = () => {
	const [messages, setMessages] = useState([]);
	const [isLoading, setIsLoading] = useState(false);

	const addMessage = useCallback((message) => {
		setMessages((prevMessages) => [...prevMessages, message]);
	}, []);

	const sendMessage = useCallback(
		async (content) => {
			if (!content.trim() || isLoading) return;

			// Add user message immediately
			const userMessage = {
				id: `user-${Date.now()}`,
				type: "user",
				content,
				timestamp: new Date().toISOString(),
			};

			addMessage(userMessage);
			setIsLoading(true);

			try {
				const data = await apiService.sendChatMessage(content);

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

				addMessage(assistantMessage);
				return data;
			} catch (error) {
				console.error("Failed to send message:", error);

				const errorMessage = {
					id: `error-${Date.now()}`,
					type: "assistant",
					content: `❌ Failed to send message: ${error.message}. Please try again.`,
					timestamp: new Date().toISOString(),
				};

				addMessage(errorMessage);
				throw error;
			} finally {
				setIsLoading(false);
			}
		},
		[isLoading, addMessage]
	);

	const sendQuickCommand = useCallback(
		(command) => {
			return sendMessage(command);
		},
		[sendMessage]
	);

	const initializeChat = useCallback(() => {
		const welcomeMessage = {
			id: `welcome-${Date.now()}`,
			type: "assistant",
			content:
				"👋 **Welcome to the Expense Assistant!**\n\n **Upload a receipt** and I'll extract expense details automatically \n📋 **Type 'show reports'** to view your existing expense reports\n💬 **Type 'help'** to see all available commands\n\nWhat would you like to do?",
			timestamp: new Date().toISOString(),
		};
		setMessages([welcomeMessage]);
	}, []);

	return {
		messages,
		isLoading,
		sendMessage,
		sendQuickCommand,
		addMessage,
		initializeChat,
		setMessages,
	};
};
