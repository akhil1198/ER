export const formatFieldValue = (value) => {
	if (value === null || value === undefined) return "Not specified";
	if (typeof value === "boolean") return value ? "Yes" : "No";
	if (typeof value === "number") return value.toLocaleString();
	return value;
};

export const formatFieldName = (fieldName) => {
	return fieldName
		.replace(/_/g, " ")
		.replace(/\b\w/g, (l) => l.toUpperCase());
};

export const formatCurrency = (amount, currency = "USD") => {
	return new Intl.NumberFormat("en-US", {
		style: "currency",
		currency: currency,
	}).format(amount);
};

export const formatDate = (dateString) => {
	if (!dateString) return "Not specified";
	try {
		return new Date(dateString).toLocaleDateString();
	} catch {
		return dateString;
	}
};
