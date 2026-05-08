import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiFolder, FiArrowLeft, FiTrash2, FiClock, FiRefreshCw } from 'react-icons/fi';
import apiClient from '../api/axiosInstance';
import ThemeToggle from '../components/ThemeToggle';
import '../App.css';

interface Folder {
    id: number;
    name: string;
    created_at: string;
    scheduled_for: string | null;
    status: string;
    document_count: number;
}

interface Document {
    id: number;
    filename: string;
    status: string;
    submitted_at: string;
    completed_at: string | null;
    error_message: string | null;
    has_output: boolean;
    target_language: string;
}

const Workspace: React.FC = () => {
    const [folders, setFolders] = useState<Folder[]>([]);
    const [activeFolderId, setActiveFolderId] = useState<number | null>(null);
    const [folderDetails, setFolderDetails] = useState<{ folder: Folder, documents: Document[] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [theme, setTheme] = useState<'dark' | 'light'>('dark');

    // Create folder form
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newFolderName, setNewFolderName] = useState('');

    // Schedule modal
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [scheduleTime, setScheduleTime] = useState('');
    const [targetLanguage, setTargetLanguage] = useState('Turkmen');
    const [processMode, setProcessMode] = useState<'parallel' | 'sequential'>('parallel');

    // ZIP upload ref
    const zipInputRef = useRef<HTMLInputElement>(null);

    const LANGUAGES = [
        'Turkmen', 'Russian', 'English', 'Chinese', 'Arabic',
        'Turkish', 'German', 'French', 'Spanish', 'Japanese',
        'Korean', 'Portuguese', 'Italian', 'Polish', 'Ukrainian',
        'Persian', 'Uzbek', 'Kazakh', 'Azerbaijani',
    ];

    // Check if folder has completed documents with output for ZIP download
    const hasDocumentsWithOutput = folderDetails?.documents.some(doc => doc.has_output) ?? false;

    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load user theme preference on mount
    useEffect(() => {
        const loadUserTheme = async () => {
            try {
                const response = await apiClient.get('/user/dashboard');
                const userTheme = response.data.user_info?.theme || 'dark';
                
                // Apply theme
                setTheme(userTheme as 'dark' | 'light');
                applyTheme(userTheme);
            } catch (error) {
                console.error('Failed to load theme preference:', error);
            }
        };
        loadUserTheme();
    }, []);

    // Apply theme class to document
    const applyTheme = (themeName: string) => {
        if (themeName === 'light') {
            document.documentElement.classList.add('light-theme');
        } else {
            document.documentElement.classList.remove('light-theme');
        }
    };

    // Handle theme change
    const handleThemeChange = (newTheme: 'dark' | 'light') => {
        setTheme(newTheme);
        applyTheme(newTheme);
    };

    useEffect(() => {
        if (activeFolderId) {
            fetchFolderDetails(activeFolderId);
        } else {
            fetchFolders();
        }
    }, [activeFolderId]);

    const fetchFolders = async () => {
        setLoading(true);
        try {
            const res = await apiClient.get('/workspace/');
            setFolders(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const fetchFolderDetails = async (id: number) => {
        setLoading(true);
        try {
            const res = await apiClient.get(`/workspace/${id}`);
            setFolderDetails(res.data);
        } catch (e) {
            console.error(e);
            setActiveFolderId(null);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateFolder = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newFolderName.trim()) return;
        try {
            await apiClient.post('/workspace/', { name: newFolderName });
            setShowCreateModal(false);
            setNewFolderName('');
            fetchFolders();
        } catch (e) {
            console.error(e);
            alert('Failed to create folder');
        }
    };

    const handleScheduleFolder = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!activeFolderId) return;

        try {
            if (processMode === 'sequential') {
                setShowScheduleModal(false);
                setLoading(true);
                const response = await apiClient.post(`/workspace/${activeFolderId}/process-sequential`, {
                    target_language: targetLanguage
                });
                alert(`Sequential processing: ${response.data.completed} completed, ${response.data.failed} failed`);
                fetchFolderDetails(activeFolderId);
            } else {
                let payload: any = { scheduled_for: null, target_language: targetLanguage };
                if (scheduleTime) {
                    payload.scheduled_for = new Date(scheduleTime).toISOString();
                }
                await apiClient.post(`/workspace/${activeFolderId}/schedule`, payload);
                setShowScheduleModal(false);
                setScheduleTime('');
                fetchFolderDetails(activeFolderId);
                alert(scheduleTime ? 'Folder scheduled successfully.' : 'Translation started immediately.');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to schedule folder');
        }
    };

    const handleDeleteFolder = async (id: number) => {
        if (!window.confirm('Are you sure you want to delete this folder and all its documents?')) return;
        try {
            await apiClient.delete(`/workspace/${id}`);
            if (activeFolderId === id) setActiveFolderId(null);
            else fetchFolders();
        } catch (e) {
            console.error(e);
            alert('Failed to delete folder');
        }
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0 || !activeFolderId) return;

        const formData = new FormData();
        for (let i = 0; i < e.target.files.length; i++) {
            formData.append('files', e.target.files[i]);
        }
        formData.append('target_language', targetLanguage);

        try {
            setLoading(true);
            await apiClient.post(`/workspace/${activeFolderId}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            // Refresh folder details after upload
            fetchFolderDetails(activeFolderId);
        } catch (err: any) {
            console.error(err);
            alert(err.response?.data?.detail || 'Failed to upload documents');
        } finally {
            if (fileInputRef.current) fileInputRef.current.value = '';
            setLoading(false);
        }
    };

    const handleDownloadZip = async (id: number) => {
        try {
            // Use axios with responseType blob and proper error handling
            const response = await apiClient.get(`/workspace/${id}/download`, {
                responseType: 'blob',
                timeout: 60000, // 60 second timeout for large files
            });
            
            // Axios returns the blob in response.data
            const blob = new Blob([response.data], { type: 'application/zip' });
            
            // Check if response has content
            if (blob.size > 0) {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `folder_${id}_translations.zip`);
                document.body.appendChild(link);
                link.click();
                link.parentNode?.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                alert('No completed documents to download.');
            }
        } catch (e: any) {
            console.error('Download failed', e);
            // Check if there's a response with error detail
            if (e.response?.data) {
                try {
                    const errorBlob = e.response.data;
                    const errorText = await new Response(errorBlob).text();
                    alert(errorText || 'Download failed');
                } catch {
                    alert(e.response.data?.detail || 'Download failed');
                }
            } else {
                alert('No completed documents to download, or an error occurred.');
            }
        }
    };

    const handleDownloadDoc = async (id: number, filename: string) => {
        try {
            const response = await apiClient.get(`/translate/download/${id}`, {
                responseType: 'blob',
                timeout: 60000,
            });
            
            const blob = new Blob([response.data], {
                type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            });
            
            if (blob.size > 0) {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                const baseName = filename.replace(/\.[^/.]+$/, '');
                link.setAttribute('download', `translated_${baseName}.docx`);
                document.body.appendChild(link);
                link.click();
                link.parentNode?.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                alert('Failed to download the document - empty response.');
            }
        } catch (e: any) {
            console.error('Download failed', e);
            if (e.response?.data) {
                try {
                    const errorBlob = e.response.data;
                    const errorText = await new Response(errorBlob).text();
                    alert(errorText || 'Download failed');
                } catch {
                    alert(e.response.data?.detail || 'Download failed');
                }
            } else {
                alert('Failed to download the document.');
            }
        }
    };

    const handleRetryDoc = async (id: number) => {
        try {
            await apiClient.post(`/workspace/document/${id}/retry`);
            fetchFolderDetails(activeFolderId!);
        } catch (e) {
            console.error('Retry failed', e);
            alert('Failed to retry the document translation.');
        }
    };

    const handleZipUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0 || !activeFolderId) return;
        
        const formData = new FormData();
        formData.append('file', e.target.files[0]);
        formData.append('target_language', targetLanguage);
        
        try {
            setLoading(true);
            const response = await apiClient.post(`/workspace/${activeFolderId}/upload-zip`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert(response.data.message);
            fetchFolderDetails(activeFolderId);
        } catch (err: any) {
            console.error(err);
            alert(err.response?.data?.detail || 'Failed to upload ZIP');
        } finally {
            if (zipInputRef.current) zipInputRef.current.value = '';
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-600 bg-green-100';
            case 'processing': return 'text-blue-600 bg-blue-100';
            case 'failed': return 'text-red-600 bg-red-100';
            case 'pending': return 'text-yellow-600 bg-yellow-100';
            default: return 'text-gray-600 bg-gray-100';
        }
    };

    if (loading && !folders.length && !folderDetails) {
        return <div className="dashboard-container">Loading Workspace...</div>;
    }

    return (
        <div className="dashboard-container" style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
            <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <div>
                    {activeFolderId ? (
                        <h1 className="dashboard-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <button onClick={() => setActiveFolderId(null)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '24px', display: 'flex', alignItems: 'center', color: 'var(--color-accent-dark)' }}><FiArrowLeft /></button>
                            {folderDetails?.folder.name}
                        </h1>
                    ) : (
                        <h1 className="dashboard-title">Translation Workspace</h1>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <ThemeToggle currentTheme={theme} onThemeChange={handleThemeChange} />
                    {!activeFolderId && (
                        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)} style={{ background: 'var(--gradient-primary)', color: 'white', padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', cursor: 'pointer' }}>
                            + New Folder
                        </button>
                    )}
                    {activeFolderId && folderDetails && (
                        <>
                            <input
                                type="file"
                                multiple
                                style={{ display: 'none' }}
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                accept="image/jpeg,image/png,image/jpg"
                            />
                            <input
                                type="file"
                                style={{ display: 'none' }}
                                ref={zipInputRef}
                                onChange={handleZipUpload}
                                accept=".zip"
                            />
                            <button className="btn" onClick={() => fileInputRef.current?.click()} style={{ background: 'var(--color-accent-dark)', color: 'white', padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', cursor: 'pointer' }}>
                                Upload Images
                            </button>
                            <button className="btn" onClick={() => zipInputRef.current?.click()} style={{ background: 'var(--color-accent-medium)', color: 'white', padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', cursor: 'pointer' }}>
                                Upload ZIP
                            </button>
                            <button className="btn" onClick={() => setShowScheduleModal(true)} style={{ background: 'var(--color-accent-primary)', color: 'white', padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', cursor: 'pointer' }}>
                                Start / Schedule
                            </button>
                            <button 
                                className="btn" 
                                onClick={() => handleDownloadZip(activeFolderId)} 
                                disabled={!hasDocumentsWithOutput}
                                style={{ 
                                    background: hasDocumentsWithOutput ? 'var(--color-success)' : 'var(--color-bg-medium)', 
                                    color: hasDocumentsWithOutput ? 'white' : 'var(--color-text-muted)', 
                                    padding: '0.5rem 1rem', 
                                    borderRadius: '0.375rem', 
                                    border: 'none', 
                                    cursor: hasDocumentsWithOutput ? 'pointer' : 'not-allowed',
                                    opacity: hasDocumentsWithOutput ? 1 : 0.5
                                }}
                            >
                                Download ZIP
                            </button>
                        </>
                    )}
                    <button className="btn" onClick={() => navigate('/client')} style={{ background: 'var(--color-bg-medium)', color: 'var(--color-text-primary)', padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', cursor: 'pointer' }}>
                        Dashboard
                    </button>
                </div>
            </div>

            {!activeFolderId ? (
                // Folders List View
                <div>
                    {folders.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '50px', color: 'var(--color-text-secondary)', background: 'var(--color-bg-subtle)', borderRadius: '12px', border: '2px dashed var(--color-border)' }}>
                            <h3 style={{ color: 'var(--color-text-primary)' }}>Your workspace is empty.</h3>
                            <p>Create a folder to start organizing and batching your translations.</p>
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px' }}>
                            {folders.map(folder => (
                                <div key={folder.id} style={{ border: '1px solid var(--color-border)', borderRadius: '12px', padding: '20px', background: 'var(--gradient-card)', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', boxShadow: 'var(--shadow-card)', transition: 'all 0.3s ease' }} onClick={() => setActiveFolderId(folder.id)}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}><FiFolder /> {folder.name}</h3>
                                        <button onClick={(e) => { e.stopPropagation(); handleDeleteFolder(folder.id); }} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', fontSize: '16px', display: 'flex', alignItems: 'center' }}><FiTrash2 /></button>
                                    </div>
                                    <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
                                        <span>{folder.document_count} items</span>
                                        <span className={`inline-px-2 py-1 rounded text-xs ${getStatusColor(folder.status)}`} style={{ padding: '2px 8px', borderRadius: '12px', display: 'inline-block', width: 'fit-content', textTransform: 'capitalize' }}>
                                            {folder.status}
                                        </span>
                                        {folder.scheduled_for && (
                                            <span style={{ fontSize: '12px', color: 'var(--color-warning)', display: 'flex', alignItems: 'center', gap: '4px' }}><FiClock /> {new Date(folder.scheduled_for).toLocaleString('tk-TM', { timeZone: 'Asia/Ashgabat' })}</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                // Folder Details View
                <div>
                    <div style={{ marginBottom: '20px', padding: '15px', background: 'rgba(255,219,187,0.2)', borderRadius: '10px', border: '1px solid var(--color-border)', display: 'flex', gap: '20px', alignItems: 'center' }}>
                        <div>
                            <span style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>Status:</span>
                            <span className={`ml-2 px-2 py-1 rounded text-xs ${getStatusColor(folderDetails?.folder?.status || '')}`} style={{ padding: '2px 8px', borderRadius: '12px', marginLeft: '8px', textTransform: 'capitalize' }}>
                                {folderDetails?.folder?.status}
                            </span>
                        </div>
                        {folderDetails?.folder?.scheduled_for && (
                            <div>
                                <span style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>Scheduled For:</span>
                                <strong style={{ marginLeft: '8px', color: 'var(--color-text-primary)' }}>{new Date(folderDetails.folder.scheduled_for).toLocaleString('tk-TM', { timeZone: 'Asia/Ashgabat' })}</strong>
                            </div>
                        )}
                        <div>
                            <button onClick={() => fetchFolderDetails(activeFolderId)} style={{ background: 'transparent', border: '1px solid var(--color-border)', borderRadius: '6px', padding: '4px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-primary)' }}><FiRefreshCw /> Refresh</button>
                        </div>
                    </div>

                    {folderDetails?.documents.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '50px', color: 'var(--color-text-secondary)', border: '2px dashed var(--color-border)', borderRadius: '10px' }}>
                            <p>No documents in this folder.</p>
                            <button onClick={() => fileInputRef.current?.click()} style={{ background: 'transparent', color: 'var(--color-accent-dark)', border: 'none', cursor: 'pointer', marginTop: '10px', textDecoration: 'underline', fontWeight: 600 }}>Upload some images</button>
                        </div>
                    ) : (
                        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
                            <thead>
                                <tr style={{ background: 'var(--gradient-primary)', textAlign: 'left' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid var(--color-border-strong)', color: 'white' }}>File</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid var(--color-border-strong)', color: 'white' }}>Target Language</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid var(--color-border-strong)', color: 'white' }}>Status</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid var(--color-border-strong)', color: 'white' }}>Submitted</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid var(--color-border-strong)', color: 'white' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {folderDetails?.documents.map((doc) => (
                                    <tr key={doc.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                        <td style={{ padding: '12px', color: 'var(--color-text-primary)' }}>{doc.filename}</td>
                                        <td style={{ padding: '12px', color: 'var(--color-text-secondary)', fontSize: '14px' }}>{doc.target_language}</td>
                                        <td style={{ padding: '12px' }}>
                                            <span className={`px-2 py-1 rounded text-xs ${getStatusColor(doc.status)}`} style={{ padding: '2px 8px', borderRadius: '12px', textTransform: 'capitalize' }}>
                                                {doc.status}
                                            </span>
                                            {doc.error_message && <div style={{ color: 'var(--color-danger)', fontSize: '12px', marginTop: '4px' }}>{doc.error_message}</div>}
                                        </td>
                                        <td style={{ padding: '12px', color: 'var(--color-text-secondary)', fontSize: '14px' }}>{new Date(doc.submitted_at).toLocaleString('tk-TM', { timeZone: 'Asia/Ashgabat' })}</td>
                                        <td style={{ padding: '12px' }}>
                                            {doc.status === 'completed' && doc.has_output && (
                                                <button onClick={() => handleDownloadDoc(doc.id, doc.filename)} style={{ background: 'transparent', border: 'none', color: 'var(--color-accent-dark)', textDecoration: 'underline', fontWeight: 600, cursor: 'pointer', padding: 0, marginRight: '10px' }}>Download Doc</button>
                                            )}
                                            {(doc.status === 'failed' || doc.status === 'pending' || (doc.status === 'completed' && !doc.has_output)) && (
                                                <button onClick={() => handleRetryDoc(doc.id)} style={{ background: 'transparent', border: 'none', color: 'var(--color-warning)', textDecoration: 'underline', fontWeight: 600, cursor: 'pointer', padding: 0 }}>{doc.status === 'pending' ? 'Retry' : 'Retry Translation'}</button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}

            {/* Create Folder Modal */}
            {showCreateModal && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div style={{ background: 'var(--color-bg-medium)', padding: '30px', borderRadius: '16px', width: '100%', maxWidth: '400px', boxShadow: '0 20px 60px rgba(0,0,0,0.5)', border: '1px solid var(--color-border)' }}>
                        <h2 style={{ marginTop: 0, marginBottom: '20px', fontSize: '20px', color: 'var(--color-text-heading)' }}>Create New Folder</h2>
                        <form onSubmit={handleCreateFolder}>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Folder Name *</label>
                                <input
                                    type="text"
                                    value={newFolderName}
                                    onChange={(e) => setNewFolderName(e.target.value)}
                                    style={{ width: '100%', padding: '10px 14px', border: '1px solid var(--color-border)', borderRadius: '8px', background: 'var(--color-bg-light)', color: 'var(--color-text-primary)', outline: 'none', boxSizing: 'border-box' }}
                                    required
                                    placeholder="e.g. Project Alpha Translations"
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                                <button type="button" onClick={() => setShowCreateModal(false)} style={{ background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border)', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', color: 'var(--color-text-primary)', fontWeight: 500 }}>Cancel</button>
                                <button type="submit" style={{ background: 'var(--gradient-primary)', color: 'white', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>Create</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Schedule Folder Modal */}
            {showScheduleModal && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div style={{ background: 'var(--color-bg-medium)', padding: '30px', borderRadius: '16px', width: '100%', maxWidth: '400px', boxShadow: '0 20px 60px rgba(0,0,0,0.5)', border: '1px solid var(--color-border)' }}>
                        <h2 style={{ marginTop: 0, marginBottom: '20px', fontSize: '20px', color: 'var(--color-text-heading)' }}>Start Translations</h2>
                        <form onSubmit={handleScheduleFolder}>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Target Language *</label>
                                <select
                                    value={targetLanguage}
                                    onChange={(e) => setTargetLanguage(e.target.value)}
                                    style={{ width: '100%', padding: '10px 14px', border: '1px solid var(--color-border)', borderRadius: '8px', background: 'var(--color-bg-light)', color: 'var(--color-text-primary)', outline: 'none', boxSizing: 'border-box' }}
                                >
                                    {LANGUAGES.map(lang => (
                                        <option key={lang} value={lang}>{lang}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Processing Mode *</label>
                                <select
                                    value={processMode}
                                    onChange={(e) => setProcessMode(e.target.value as 'parallel' | 'sequential')}
                                    style={{ width: '100%', padding: '10px 14px', border: '1px solid var(--color-border)', borderRadius: '8px', background: 'var(--color-bg-light)', color: 'var(--color-text-primary)', outline: 'none', boxSizing: 'border-box' }}
                                >
                                    <option value="parallel">Parallel (all at once)</option>
                                    <option value="sequential">Sequential (one by one)</option>
                                </select>
                            </div>
                            <div style={{ marginBottom: '25px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Schedule Start Time (Optional)</label>
                                <input
                                    type="datetime-local"
                                    value={scheduleTime}
                                    onChange={(e) => setScheduleTime(e.target.value)}
                                    style={{ width: '100%', padding: '10px 14px', border: '1px solid var(--color-border)', borderRadius: '8px', background: 'var(--color-bg-light)', color: 'var(--color-text-primary)', outline: 'none', boxSizing: 'border-box' }}
                                />
                                <small style={{ color: 'var(--color-text-secondary)', display: 'block', marginTop: '5px' }}>Leave empty to start translations immediately.</small>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                                <button type="button" onClick={() => setShowScheduleModal(false)} style={{ background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border)', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', color: 'var(--color-text-primary)', fontWeight: 500 }}>Cancel</button>
                                <button type="submit" style={{ background: 'var(--gradient-primary)', color: 'white', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>{scheduleTime ? 'Schedule' : 'Start Now'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Workspace;
