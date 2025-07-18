import { useCallback } from "react";
import { apiService } from "../services/api";

export const useApiCall = () => {
	const makeApiCall = useCallback(async (url, options = {}) => {
		return apiService.makeApiCall(url, options);
	}, []);

	return { makeApiCall };
};
