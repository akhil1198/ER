import React from "react";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import DropZone from "../common/DropZone";

const ChatContainer = ({
	messages,
	onSendMessage,
	onSendCommand,
	onFileUpload,
	isLoading,
	dragActive,
	onEditExpense,
	editingExpense,
	onSaveExpense,
	onCancelExpense,
}) => {
	return (
		<div className="chat-container">
			<MessageList
				messages={messages}
				onSendCommand={onSendCommand}
				isLoading={isLoading}
				onEditExpense={onEditExpense}
				editingExpense={editingExpense}
				onSaveExpense={onSaveExpense}
				onCancelExpense={onCancelExpense}
			/>

			<MessageInput
				onSendMessage={onSendMessage}
				onFileSelect={onFileUpload}
				isLoading={isLoading}
			/>

			<DropZone active={dragActive} />
		</div>
	);
};

export default ChatContainer;
