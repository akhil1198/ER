import { useState, useCallback } from "react";
import { apiService } from "../services/api";

export const useFileUpload = () => {
	const [dragActive, setDragActive] = useState(false);
	const [isUploading, setIsUploading] = useState(false);

	const handleDragEvents = useCallback((e) => {
		e.preventDefault();
		e.stopPropagation();
		setDragActive(e.type === "dragenter" || e.type === "dragover");
	}, []);

	const uploadFile = useCallback(
		async (file) => {
			if (!file || isUploading) return null;

			if (!file.type.startsWith("image/")) {
				throw new Error("Invalid file type. Please upload an image.");
			}

			setIsUploading(true);

			try {
				const data = await apiService.processReceipt(file);
				return data;
			} catch (error) {
				console.error("Failed to upload file:", error);
				throw error;
			} finally {
				setIsUploading(false);
			}
		},
		[isUploading]
	);

	const handleDrop = useCallback(
		async (e) => {
			e.preventDefault();
			e.stopPropagation();
			setDragActive(false);

			const files = e.dataTransfer.files;
			if (files?.[0]?.type.startsWith("image/")) {
				return uploadFile(files[0]);
			}
			return null;
		},
		[uploadFile]
	);

	return {
		dragActive,
		isUploading,
		handleDragEvents,
		handleDrop,
		uploadFile,
		setDragActive,
	};
};
export default useFileUpload;
