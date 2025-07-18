import React from "react";

const Navbar = () => {
	return (
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
					<button className="nav-item active">
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
	);
};

export default Navbar;
