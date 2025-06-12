import React, { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://localhost:8000";

function App() {
	const [selectedFile, setSelectedFile] = useState(null);
	const [loading, setLoading] = useState(false);
	const [result, setResult] = useState(null);
	const [error, setError] = useState(null);
	const [dragActive, setDragActive] = useState(false);

	const handleFileSelect = (file) => {
		if (file && file.type.startsWith("image/")) {
			setSelectedFile(file);
			setError(null);
			setResult(null);
		} else {
			setError("Please select a valid image file (JPEG, PNG, GIF)");
		}
	};

	const handleDrag = (e) => {
		e.preventDefault();
		e.stopPropagation();
		if (e.type === "dragenter" || e.type === "dragover") {
			setDragActive(true);
		} else if (e.type === "dragleave") {
			setDragActive(false);
		}
	};

	const handleDrop = (e) => {
		e.preventDefault();
		e.stopPropagation();
		setDragActive(false);

		if (e.dataTransfer.files && e.dataTransfer.files[0]) {
			handleFileSelect(e.dataTransfer.files[0]);
		}
	};

	const handleFileChange = (e) => {
		if (e.target.files && e.target.files[0]) {
			handleFileSelect(e.target.files[0]);
		}
	};

	const processReceipt = async () => {
		if (!selectedFile) {
			setError("Please select a file first");
			return;
		}

		setLoading(true);
		setError(null);
		setResult(null);

		try {
			const formData = new FormData();
			formData.append("file", selectedFile);

			const response = await fetch(
				`${API_BASE_URL}/api/process-receipt`,
				{
					method: "POST",
					body: formData,
				}
			);

			const data = await response.json();

			if (data.success) {
				setResult(data);
			} else {
				setError(data.error || "Processing failed");
			}
		} catch (err) {
			setError(
				"Failed to connect to server. Make sure the backend is running."
			);
		} finally {
			setLoading(false);
		}
	};

	const formatFieldName = (fieldName) => {
		return fieldName
			.replace(/_/g, " ")
			.replace(/\b\w/g, (l) => l.toUpperCase());
	};

	const formatFieldValue = (value) => {
		if (value === null || value === undefined) return "Not specified";
		if (typeof value === "boolean") return value ? "Yes" : "No";
		if (typeof value === "number") return value.toLocaleString();
		return value;
	};

	return (
		<div className="App">
			<header className="App-header">
				<h1>🧾 Expense Reporting MVP</h1>
				<p>
					Upload a receipt to extract expense information
					automatically
				</p>
			</header>

			<main className="App-main">
				{/* File Upload Section */}
				<div className="upload-section">
					<div
						className={`upload-area ${
							dragActive ? "drag-active" : ""
						}`}
						onDragEnter={handleDrag}
						onDragLeave={handleDrag}
						onDragOver={handleDrag}
						onDrop={handleDrop}
					>
						<input
							type="file"
							id="file-input"
							accept="image/*"
							onChange={handleFileChange}
							style={{ display: "none" }}
						/>
						<label htmlFor="file-input" className="upload-label">
							<div className="upload-content">
								<div className="upload-icon">📁</div>
								<p>
									{selectedFile
										? `Selected: ${selectedFile.name}`
										: "Click to select or drag & drop your receipt image"}
								</p>
								<small>
									Supports JPEG, PNG, GIF (max 10MB)
								</small>
							</div>
						</label>
					</div>

					<button
						onClick={processReceipt}
						disabled={!selectedFile || loading}
						className="process-button"
					>
						{loading ? "Processing..." : "Process Receipt"}
					</button>
				</div>

				{/* Loading Indicator */}
				{loading && (
					<div className="loading-section">
						<div className="spinner"></div>
						<p>Analyzing receipt with AI...</p>
					</div>
				)}

				{/* Error Display */}
				{error && (
					<div className="error-section">
						<h3>❌ Error</h3>
						<p>{error}</p>
					</div>
				)}

				{/* Results Display */}
				{result && result.success && (
					<div className="results-section">
						<h3>✅ Expense Data Extracted</h3>
						<div className="processing-info">
							<small>
								Processing time:{" "}
								{result.processing_time?.toFixed(2)}s
							</small>
						</div>

						<div className="expense-data">
							<h4>Extracted Information:</h4>
							<div className="expense-grid">
								{Object.entries(result.expense_data).map(
									([key, value]) => (
										<div
											key={key}
											className="expense-field"
										>
											<label>
												{formatFieldName(key)}:
											</label>
											<span
												className={
													value
														? "has-value"
														: "no-value"
												}
											>
												{formatFieldValue(value)}
											</span>
										</div>
									)
								)}
							</div>
						</div>

						<div className="action-buttons">
							<button
								className="secondary-button"
								onClick={() => {
									setResult(null);
									setSelectedFile(null);
								}}
							>
								Process Another Receipt
							</button>
							<button className="primary-button">
								Create Expense Report
							</button>
						</div>
					</div>
				)}
			</main>
		</div>
	);
}

export default App;
