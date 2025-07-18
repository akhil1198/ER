import { useState, useCallback } from "react";

export const useExpenseData = () => {
	const [currentExpense, setCurrentExpense] = useState(null);
	const [editingExpense, setEditingExpense] = useState(false);

	const updateExpenseData = useCallback((expenseData) => {
		setCurrentExpense(expenseData);
	}, []);

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
		setEditingExpense(false);
	}, []);

	return {
		currentExpense,
		editingExpense,
		updateExpenseData,
		startEditing,
		stopEditing,
		saveExpenseChanges,
		clearExpenseData,
	};
};
