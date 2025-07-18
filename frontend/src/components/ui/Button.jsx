import React from "react";

const Button = ({
	children,
	onClick,
	disabled = false,
	variant = "primary",
	size = "medium",
	icon,
	className = "",
	...props
}) => {
	const baseClasses = "btn";
	const variantClasses = {
		primary: "btn-primary",
		secondary: "btn-secondary",
		outline: "btn-outline",
	};
	const sizeClasses = {
		small: "btn-small",
		medium: "btn-medium",
		large: "btn-large",
	};

	const classes = [
		baseClasses,
		variantClasses[variant],
		sizeClasses[size],
		className,
	]
		.filter(Boolean)
		.join(" ");

	return (
		<button
			className={classes}
			onClick={onClick}
			disabled={disabled}
			{...props}
		>
			{icon && <span className="btn-icon">{icon}</span>}
			<span className="btn-text">{children}</span>
		</button>
	);
};

export default Button;
