import React, { useState } from 'react';
import InversionTable from './InversionTable';

interface InversionModeProps {
  materialId: string;
  userId: string;
  filename: string;
  backendUrl: string;
  onBack: () => void;
}

const InversionMode: React.FC<InversionModeProps> = ({
  materialId,
  userId,
  filename,
  backendUrl,
  onBack
}) => {
  const [processing, setProcessing] = useState(false);
  const [inversionsReady, setInversionsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startInversionProcessing = async () => {
    setProcessing(true);
    setError(null);

    try {
      const response = await fetch(
        `${backendUrl}/api/inversion/process/${materialId}?user_id=${userId}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error:', errorText);
        throw new Error(`Server returned ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Inversions created:', data);
      setInversionsReady(true);
    } catch (err) {
      console.error('Error processing inversions:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to create inversions: ${errorMessage}\n\nThis might mean the backend is still deploying. Please wait a minute and try again.`);
    } finally {
      setProcessing(false);
    }
  };

  // Check if inversions already exist
  React.useEffect(() => {
    const checkExistingInversions = async () => {
      try {
        const response = await fetch(
          `${backendUrl}/api/inversion/${materialId}/paragraphs?user_id=${userId}`
        );
        const data = await response.json();
        if (data.inversions && data.inversions.length > 0) {
          setInversionsReady(true);
        }
      } catch (err) {
        console.error('Error checking inversions:', err);
      }
    };

    checkExistingInversions();
  }, [materialId, userId, backendUrl]);

  if (inversionsReady) {
    return (
      <InversionTable
        materialId={materialId}
        userId={userId}
        backendUrl={backendUrl}
      />
    );
  }

  return (
    <div className="upload-container">
      <div className="upload-card">
        <div className="upload-icon">
          <svg
            width="80"
            height="80"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </div>

        <h2>Dialectical Learning Mode</h2>
        <p className="upload-subtitle">
          Ready to process <strong>{filename}</strong> for paragraph inversion.
          <br />
          This mode will create logical opposites for each paragraph and help you identify gaps.
        </p>

        {error && (
          <div style={{
            padding: '1rem',
            background: '#fee2e2',
            border: '2px solid #ef4444',
            borderRadius: '8px',
            marginBottom: '1rem',
            color: '#991b1b',
            whiteSpace: 'pre-wrap',
            fontSize: '0.95rem',
            lineHeight: '1.5'
          }}>
            {error}
          </div>
        )}

        <div className="guarantee">
          <p>How it works:</p>
          <ul>
            <li>Each paragraph is inverted to create its logical opposite</li>
            <li>Compare original vs inverted side-by-side</li>
            <li>AI identifies logical gaps and inconsistencies</li>
            <li>Create patches to reconcile opposites</li>
            <li>Build deeper understanding through dialectical thinking</li>
          </ul>
        </div>

        <button
          className="button button-primary"
          onClick={startInversionProcessing}
          disabled={processing}
          style={{ marginTop: '1.5rem' }}
        >
          {processing ? 'Creating Inversions...' : 'Start Inversion Mode'}
        </button>

        <button
          className="button button-secondary"
          onClick={onBack}
          style={{ marginTop: '1rem' }}
        >
          Back to Upload
        </button>

        {processing && (
          <div className="processing" style={{ marginTop: '2rem' }}>
            <div className="spinner"></div>
            <div className="processing-text">Processing paragraphs...</div>
            <p className="processing-detail">
              Creating logical inversions using AI
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default InversionMode;
