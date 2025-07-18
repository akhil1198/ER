import React from "react";

const Sidebar = ({ isMobile }) => {
	if (isMobile) return null;

	return (
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
	);
};

export default Sidebar;
