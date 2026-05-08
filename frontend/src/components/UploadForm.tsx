// src/components/UploadForm.tsx
import React, { useState, useEffect } from 'react';
import apiClient from '../api/axiosInstance';
import { useTranslation } from 'react-i18next';
import { FiCheckCircle, FiXCircle } from 'react-icons/fi';
import '../App.css';

interface UploadFormProps {
  onUploadSuccess?: () => void;
}

interface DocumentStatus {
  id: number;
  status: string;
  is_translated: boolean;
  submitted_at: string;
  completed_at: string | null;
  error_message: string | null;
}

const UploadForm: React.FC<UploadFormProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('Turkmen'); // Default to Turkmen
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [translationReady, setTranslationReady] = useState(false);
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [statusPolling, setStatusPolling] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<DocumentStatus | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    let pollInterval: ReturnType<typeof setInterval>;

    if (statusPolling && documentId) {
      pollInterval = setInterval(async () => {
        try {
          const response = await apiClient.get(`/translate/status/${documentId}`);
          const statusData: DocumentStatus = response.data;

          setCurrentStatus(statusData);

          if (statusData.status === 'completed') {
            setTranslationReady(true);
            setStatusPolling(false);

            if (onUploadSuccess) {
              onUploadSuccess();
            }
          } else if (statusData.status === 'failed') {
            alert(`Translation failed: ${statusData.error_message || 'Unknown error'}`);
            setStatusPolling(false);
          }
        } catch (error) {
          console.error('Error polling status:', error);
          setStatusPolling(false);
        }
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [statusPolling, documentId, onUploadSuccess]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);

      // Generate preview URL for image files
      if (selectedFile.type.startsWith('image/')) {
        const url = URL.createObjectURL(selectedFile);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }

      setTranslationReady(false);
      setDocumentId(null);
      setCurrentStatus(null);
    }
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLanguage(e.target.value);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_language', selectedLanguage); // Add selected language to form data

    setIsUploading(true);
    try {
      // Upload the file to create a document record
      const response = await apiClient.post('/translate/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const docId = response.data.document_id;
      setDocumentId(docId);

      // Start polling for status (translation starts automatically in background)
      setStatusPolling(true);

    } catch (err) {
      console.error('Upload or processing failed', err);
      alert('Upload failed: ' + (err as Error).message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async () => {
    if (documentId === null) return;

    try {
      const response = await apiClient.get(`/translate/download/${documentId}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `translated_document_${documentId}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed', err);
      alert('Download failed: ' + (err as Error).message);
    }
  };

  const handleReset = () => {
    setFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl); // Clean up the object URL
      setPreviewUrl(null);
    }
    setTranslationReady(false);
    setDocumentId(null);
    setCurrentStatus(null);
    setStatusPolling(false);
  };

  return (
    <div className="upload-form">
      {!translationReady && !documentId && (
        <form onSubmit={e => { e.preventDefault(); handleUpload(); }}>
          <div className="upload-input">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              disabled={isUploading}
              style={{ display: 'none' }}
              id="file-upload"
            />
            <label htmlFor="file-upload" className="upload-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16" className="upload-icon">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
                <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z" />
              </svg>
              <span className="upload-text">{file ? file.name : t('translate.choose_image_file')}</span>
            </label>
          </div>

          {/* Image Preview */}
          {previewUrl && (
            <div className="image-preview-container">
              <img src={previewUrl} alt="Preview" className="image-preview" />
            </div>
          )}

          {/* Language Selection Dropdown */}
          <div className="language-selection">
            <label htmlFor="language-select" className="language-label">{t('translate.select_target_language')}</label>
            <select
              id="language-select"
              value={selectedLanguage}
              onChange={handleLanguageChange}
              className="language-dropdown"
              disabled={isUploading}
            >
              <option value="Turkmen">Turkmen</option>
              <option value="Russian">Russian</option>
              <option value="English">English</option>
              <option value="German">German</option>
              <option value="French">French</option>
              <option value="Spanish">Spanish</option>
              <option value="Chinese">Chinese</option>
              <option value="Japanese">Japanese</option>
              <option value="Arabic">Arabic</option>
            </select>
          </div>

          <button
            type="submit"
            className={`upload-button ${isUploading ? 'uploading' : ''}`}
            disabled={!file || isUploading}
          >
            {isUploading ? (
              <span className="upload-animation">
                <span className="upload-spinner"></span>
                {t('translate.uploading')}
              </span>
            ) : (
              <span className="upload-animation">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" className="upload-icon-small">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
                  <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z" />
                </svg>
                {t('upload_button')}
              </span>
            )}
          </button>
        </form>
      )}

      {(isUploading || statusPolling) && !translationReady && documentId && (
        <div className="upload-status-container">
          <div className="upload-status-animation">
            <div className="status-spinner"></div>
          </div>
          <p className="upload-status-text">
            {isUploading ? (
              <span className="status-uploading">{t('translate.uploading')}</span>
            ) : (
              <span>
                <span className={`status-${currentStatus?.status || 'processing'}`}>
                  {currentStatus?.status || t('translate.waiting')}
                </span>
                {currentStatus?.error_message && `(Error: ${currentStatus.error_message})`}
              </span>
            )}
          </p>
          <div className="progress-bar">
            <div className="progress-fill"></div>
          </div>

          {/* Show preview during upload/processing if available */}
          {previewUrl && (
            <div className="image-preview-container processing">
              <img src={previewUrl} alt="Preview" className="image-preview processing" />
              <div className="processing-overlay">
                <div className="processing-text">{t('translate.processing')}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {translationReady && documentId && (
        <div className="upload-success-container">
          <div className="success-animation"><FiCheckCircle size={48} color="#10b981" /></div>
          <p className="upload-success-text">{t('translate.translation_completed')}</p>

          {/* Show preview after completion */}
          {previewUrl && (
            <div className="image-preview-container success">
              <img src={previewUrl} alt="Original" className="image-preview success" />
            </div>
          )}

          <div className="success-actions">
            <button className="upload-button success-download" onClick={handleDownload}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" className="upload-icon-small">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
                <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z" />
              </svg>
              {t('translate.download_file')}
            </button>
            <button className="upload-button success-reset" onClick={handleReset}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" className="upload-icon-small">
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z" />
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z" />
              </svg>
              {t('translate.new_translation')}
            </button>
          </div>
        </div>
      )}

      {!translationReady && documentId && !isUploading && !statusPolling && (
        <div className="upload-error-container">
          <div className="error-animation"><FiXCircle size={48} color="#ef4444" /></div>
          <p className="upload-error-text">{t('translate.translation_failed')}</p>

          {/* Show preview even when error occurs */}
          {previewUrl && (
            <div className="image-preview-container error">
              <img src={previewUrl} alt="Original" className="image-preview error" />
              <div className="error-overlay">
                <div className="error-text">{t('translate.error_occurred')}</div>
              </div>
            </div>
          )}

          <button className="upload-button error-reset" onClick={handleReset}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" className="upload-icon-small">
              <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z" />
              <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z" />
            </svg>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default UploadForm;
