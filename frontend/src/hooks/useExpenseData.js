// frontend/src/hooks/useExpenseData.js - Updated for dynamic expense types

import { useState, useCallback } from "react";

export const useExpenseData = () => {
	const [currentExpense, setCurrentExpense] = useState(null);
	const [currentExpenseType, setCurrentExpenseType] = useState(null);
	const [currentExpenseTypeInfo, setCurrentExpenseTypeInfo] = useState(null);
	const [editingExpense, setEditingExpense] = useState(false);

	const updateExpenseData = useCallback((expenseData) => {
		setCurrentExpense(expenseData);
	}, []);

	const updateExpenseType = useCallback(
		(expenseTypeId, expenseTypeInfo = null) => {
			setCurrentExpenseType(expenseTypeId);
			if (expenseTypeInfo) {
				setCurrentExpenseTypeInfo(expenseTypeInfo);
			}
		},
		[]
	);

	const startEditing = useCallback(() => {
		setEditingExpense(true);
	}, []);

	const stopEditing = useCallback(() => {
		setEditingExpense(false);
	}, []);

	const saveExpenseChanges = useCallback((updatedData) => {
		setCurrentExpense(updatedData);
		setEditingExpense(false);
	}, []);

	const clearExpenseData = useCallback(() => {
		setCurrentExpense(null);
		setCurrentExpenseType(null);
		setCurrentExpenseTypeInfo(null);
		setEditingExpense(false);
	}, []);

	const validateExpenseData = useCallback(
		async (expenseTypeId, expenseData) => {
			try {
				const { apiService } = await import("../services/api");
				const response = await apiService.validateExpenseData(
					expenseTypeId,
					expenseData
				);
				return response;
			} catch (error) {
				console.error("Validation failed:", error);
				return {
					valid: false,
					validation_errors: [
						{ field: "general", message: "Validation failed" },
					],
				};
			}
		},
		[]
	);

	const mapDataToExpenseType = useCallback(
		async (expenseTypeId, extractedData) => {
			try {
				const { apiService } = await import("../services/api");
				const response = await apiService.mapDataToExpenseType(
					expenseTypeId,
					extractedData
				);
				return response;
			} catch (error) {
				console.error("Mapping failed:", error);
				throw error;
			}
		},
		[]
	);

	return {
		// State
		currentExpense,
		currentExpenseType,
		currentExpenseTypeInfo,
		editingExpense,

		// Actions
		updateExpenseData,
		updateExpenseType,
		startEditing,
		stopEditing,
		saveExpenseChanges,
		clearExpenseData,

		// API helpers
		validateExpenseData,
		mapDataToExpenseType,
	};
};
