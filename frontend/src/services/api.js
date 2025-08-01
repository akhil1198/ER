// frontend/src/services/api.js - Updated with dynamic expense type endpoints

import { API_BASE_URL } from "../utils/constants";

class ApiService {
	async makeApiCall(url, options = {}) {
		try {
			const response = await fetch(`${API_BASE_URL}${url}`, options);

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error(`API call failed for ${url}:`, error);
			throw error;
		}
	}

	async sendChatMessage(content) {
		return this.makeApiCall("/api/chat", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ content }),
		});
	}

	// sending the receipt image to the backend for processing
	// This endpoint processes the receipt image and returns extracted data
	async processReceipt(file) {
		const formData = new FormData();
		formData.append("file", file);

		return this.makeApiCall("/api/process-receipt", {
			method: "POST",
			body: formData,
		});
	}

	// NEW: Dynamic expense type endpoints
	async getExpenseTypes(category = "meals") {
		return this.makeApiCall(`/api/expense-types?category=${category}`);
	}

	async getExpenseTypeForm(expenseTypeId) {
		return this.makeApiCall(`/api/expense-types/${expenseTypeId}/form`);
	}

	async getExpenseTypeFields(expenseTypeId) {
		return this.makeApiCall(`/api/expense-types/${expenseTypeId}/fields`);
	}

	async mapDataToExpenseType(expenseTypeId, extractedData) {
		return this.makeApiCall(
			`/api/expense-types/${expenseTypeId}/map-data`,
			{
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(extractedData),
			}
		);
	}

	async validateExpenseData(expenseTypeId, expenseData) {
		return this.makeApiCall("/api/validate-expense-data", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				expense_type_id: expenseTypeId,
				expense_data: expenseData,
			}),
		});
	}

	async createEnhancedExpenseEntry(expenseTypeId, expenseData, reportId) {
		return this.makeApiCall("/api/expense-entry/enhanced", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				expense_type_id: expenseTypeId,
				expense_data: expenseData,
				report_id: reportId,
			}),
		});
	}

	// Existing endpoints
	async getReports() {
		return this.makeApiCall("/api/reports");
	}

	async createReport(reportData) {
		return this.makeApiCall("/api/reports", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(reportData),
		});
	}

	async createExpenseEntry(expenseData) {
		return this.makeApiCall("/api/expense-entry", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(expenseData),
		});
	}

	async addExpenseToReport(reportId, expenseData) {
		return this.makeApiCall(
			`/api/add-expense-to-report?report_id=${reportId}`,
			{
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(expenseData),
			}
		);
	}

	async healthCheck() {
		return this.makeApiCall("/api/health");
	}
}

export const apiService = new ApiService();
