import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Loader2, AlertCircle, Image, FileSpreadsheet } from 'lucide-react';
import { processFile, processText } from '../api';
import type { ProcessResponse } from '../types';

interface Props {
  onResult: (result: ProcessResponse) => void;
  onExtracting: () => void;
}

const ACCEPT_TYPES = {
  'application/pdf': ['.pdf'],
  'text/plain': ['.txt'],
  'text/csv': ['.csv'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
};

function FileTypeIcon({ filename }: { filename: string }) {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  if (['png','jpg','jpeg'].includes(ext)) return <Image size={32} className="file-icon" />;
  if (['xlsx','xls','csv'].includes(ext)) return <FileSpreadsheet size={32} className="file-icon" />;
  return <FileText size={32} className="file-icon" />;
}

export default function InputSection({ onResult, onExtracting }: Props) {
  const [mode, setMode] = useState<'upload' | 'text'>('upload');
  const [textInput, setTextInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) { setUploadedFile(accepted[0]); setError(''); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPT_TYPES, maxFiles: 1, maxSize: 20 * 1024 * 1024,
    onDropRejected: () => setError('File rejected. Max 20 MB. Supported: PDF, CSV, XLSX, DOCX, TXT, PNG, JPG'),
  });

  const handleSubmit = async () => {
    setError(''); setLoading(true); onExtracting();
    try {
      let result: ProcessResponse;
      if (mode === 'upload') {
        if (!uploadedFile) { setError('Please select a file first.'); setLoading(false); return; }
        result = await processFile(uploadedFile);
      } else {
        if (!textInput.trim()) { setError('Please enter some text.'); setLoading(false); return; }
        result = await processText(textInput);
      }
      onResult(result);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Processing failed. Please try again.';
      setError(msg); setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="section-title"><Upload size={20} /> Input Data</h2>
      <div className="tab-group">
        <button className={`tab-btn ${mode === 'upload' ? 'active' : ''}`} onClick={() => setMode('upload')}>
          <Upload size={15} /> Upload File
        </button>
        <button className={`tab-btn ${mode === 'text' ? 'active' : ''}`} onClick={() => setMode('text')}>
          <FileText size={15} /> Paste Text
        </button>
      </div>

      {mode === 'upload' ? (
        <div {...getRootProps()} className={`dropzone ${isDragActive ? 'drag-active' : ''} ${uploadedFile ? 'has-file' : ''}`}>
          <input {...getInputProps()} />
          {uploadedFile ? (
            <div className="file-info">
              <FileTypeIcon filename={uploadedFile.name} />
              <p className="file-name">{uploadedFile.name}</p>
              <p className="file-size">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
              <span className="change-hint">Click or drag to replace</span>
            </div>
          ) : (
            <div className="drop-hint">
              <Upload size={36} className="upload-icon" />
              <p className="drop-text">{isDragActive ? 'Drop your file here' : 'Drag & drop or click to upload'}</p>
              <p className="drop-sub">PDF · CSV · XLSX · DOCX · TXT · PNG · JPG — max 20 MB</p>
            </div>
          )}
        </div>
      ) : (
        <textarea className="text-input"
          placeholder="Paste invoice text, utility bill details, or any document with emissions-related data..."
          value={textInput} onChange={e => setTextInput(e.target.value)} rows={8} />
      )}

      {error && <div className="error-banner"><AlertCircle size={16} />{error}</div>}

      <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
        {loading ? <><Loader2 size={18} className="spin" /> Analyzing with AI...</> :
          <><Upload size={18} /> Analyze Emissions</>}
      </button>
    </div>
  );
}
