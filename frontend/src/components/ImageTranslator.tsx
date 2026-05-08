import React, { useState, useRef } from 'react';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { useUser } from '../contexts/UserContext';

const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
  </svg>
);

const AlertCircleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
  </svg>
);

const ImageTranslator: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { state, dispatch } = useUser();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please select a valid image file');
    }
  };

  const handleTranslate = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    // Check if user has remaining translations
    if (state.usage && state.usage.remaining <= 0) {
      setError('You have reached your translation limit. Please upgrade your plan.');
      // Optionally, trigger the modal in the dashboard
      window.dispatchEvent(new CustomEvent('limitReached'));
      return;
    }

    setIsTranslating(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      // Call the backend translation endpoint
      const response = await fetch('/pricing/translate', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Translation failed');
      }

      const data = await response.json();
      setResult(data);
      
      // Update local usage count
      dispatch({ type: 'UPDATE_TRANSLATION_COUNT' });
    } catch (err: any) {
      setError(err.message || 'Translation failed');
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Translate Image</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/*"
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={!!(state.usage && state.usage.remaining <= 0)}
            >
              <UploadIcon />
              Select Image
            </Button>
            {selectedFile && (
              <span className="text-sm text-gray-600 truncate max-w-xs">
                {selectedFile.name}
              </span>
            )}
          </div>

          {error && (
            <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              <AlertCircleIcon />
              {error}
            </div>
          )}

          <Button
            onClick={handleTranslate}
            disabled={!selectedFile || isTranslating || !!(state.usage && state.usage.remaining <= 0)}
            className="w-full"
          >
            {isTranslating ? 'Translating...' : 'Translate Image'}
          </Button>

          {result && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
              <p className="text-green-700">Translation completed successfully!</p>
              <p className="text-sm mt-1">Current usage: {result.current_usage}, Remaining: {result.remaining}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ImageTranslator;