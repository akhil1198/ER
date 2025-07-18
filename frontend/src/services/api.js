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

	async processReceipt(file) {
		const formData = new FormData();
		formData.append("file", file);

		return this.makeApiCall("/api/process-receipt", {
			method: "POST",
			body: formData,
		});
	}

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
