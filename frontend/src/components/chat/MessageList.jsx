import React, { useRef, useEffect } from "react";
import Message from "./Message";
import LoadingSpinner from "../common/LoadingSpinner";

const MessageList = ({
	messages,
	onSendCommand,
	isLoading,
	onEditExpense,
	editingExpense,
	onSaveExpense,
	onCancelExpense,
}) => {
	const messagesEndRef = useRef(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	return (
		<div className="messages-container">
			{messages.map((message) => (
				<Message
					key={message.id}
					message={message}
					onSendCommand={onSendCommand}
					isLoading={isLoading}
					onEditExpense={onEditExpense}
					editingExpense={editingExpense}
					onSaveExpense={onSaveExpense}
					onCancelExpense={onCancelExpense}
				/>
			))}

			{isLoading && <LoadingSpinner />}

			<div ref={messagesEndRef} />
		</div>
	);
};

export default MessageList;
