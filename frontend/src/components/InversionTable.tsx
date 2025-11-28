import React, { useState, useEffect } from 'react';
import '../styles.css';

interface Inversion {
  id: string;
  paragraph_number: number;
  page_number: number;
  original: string;
  inverted: string;
  gaps_identified: boolean;
  patch_created: boolean;
  gap_count: number;
  patch_count: number;
}

interface Gap {
  id: string;
  type: string;
  description: string;
  location: string;
  resolved: boolean;
}

interface Patch {
  id: string;
  patch_name: string;
  patch_description: string;
  patch_type: string;
  creativity_score: number | null;
  addresses_gaps: string[];
  created_at: string;
}

interface InversionTableProps {
  materialId: string;
  userId: string;
  backendUrl: string;
}

const InversionTable: React.FC<InversionTableProps> = ({ materialId, userId, backendUrl }) => {
  const [inversions, setInversions] = useState<Inversion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInversion, setSelectedInversion] = useState<Inversion | null>(null);
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [patches, setPatches] = useState<Patch[]>([]);
  const [showGapModal, setShowGapModal] = useState(false);
  const [showPatchModal, setShowPatchModal] = useState(false);
  const [identifyingGaps, setIdentifyingGaps] = useState(false);

  // Patch form state
  const [patchName, setPatchName] = useState('');
  const [patchDescription, setPatchDescription] = useState('');
  const [patchType, setPatchType] = useState('principle');
  const [creativityScore, setCreativityScore] = useState(5);

  useEffect(() => {
    loadInversions();
  }, [materialId, userId]);

  const loadInversions = async () => {
    try {
      const response = await fetch(
        `${backendUrl}/api/inversion/${materialId}/paragraphs?user_id=${userId}`
      );
      const data = await response.json();
      setInversions(data.inversions);
      setLoading(false);
    } catch (error) {
      console.error('Error loading inversions:', error);
      setLoading(false);
    }
  };

  const identifyGaps = async (inversion: Inversion) => {
    setIdentifyingGaps(true);
    try {
      const response = await fetch(`${backendUrl}/api/inversion/identify-gaps`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inversion_id: inversion.id })
      });
      const data = await response.json();
      setGaps(data.gaps);
      setSelectedInversion(inversion);
      setShowGapModal(true);
      loadInversions(); // Refresh to update gap counts
    } catch (error) {
      console.error('Error identifying gaps:', error);
    } finally {
      setIdentifyingGaps(false);
    }
  };

  const loadGaps = async (inversionId: string) => {
    try {
      const response = await fetch(`${backendUrl}/api/inversion/${inversionId}/gaps`);
      const data = await response.json();
      setGaps(data.gaps);
    } catch (error) {
      console.error('Error loading gaps:', error);
    }
  };

  const loadPatches = async (inversionId: string) => {
    try {
      const response = await fetch(`${backendUrl}/api/inversion/${inversionId}/patches`);
      const data = await response.json();
      setPatches(data.patches);
    } catch (error) {
      console.error('Error loading patches:', error);
    }
  };

  const openPatchModal = async (inversion: Inversion) => {
    setSelectedInversion(inversion);
    await loadGaps(inversion.id);
    await loadPatches(inversion.id);
    setShowPatchModal(true);
  };

  const createPatch = async () => {
    if (!selectedInversion || !patchDescription.trim()) {
      alert('Please provide a patch description');
      return;
    }

    try {
      const response = await fetch(
        `${backendUrl}/api/inversion/create-patch?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            inversion_id: selectedInversion.id,
            patch_name: patchName || 'Unnamed Patch',
            patch_description: patchDescription,
            patch_type: patchType,
            creativity_score: creativityScore,
            addresses_gaps: gaps.map(g => g.id)
          })
        }
      );
      await response.json();

      // Reset form
      setPatchName('');
      setPatchDescription('');
      setPatchType('principle');
      setCreativityScore(5);

      // Reload patches and inversions
      await loadPatches(selectedInversion.id);
      await loadInversions();

      alert('Patch created successfully!');
    } catch (error) {
      console.error('Error creating patch:', error);
      alert('Failed to create patch');
    }
  };

  if (loading) {
    return <div className="loading">Loading inversions...</div>;
  }

  return (
    <div className="inversion-container">
      <h2>Paragraph Inversion Table</h2>
      <p className="subtitle">
        Compare original paragraphs with their logical opposites. Spot gaps and create patches to reconcile them.
      </p>

      <div className="inversion-stats">
        <div className="stat-box">
          <div className="stat-number">{inversions.length}</div>
          <div className="stat-label">Total Paragraphs</div>
        </div>
        <div className="stat-box">
          <div className="stat-number">
            {inversions.filter(i => i.gaps_identified).length}
          </div>
          <div className="stat-label">Gaps Identified</div>
        </div>
        <div className="stat-box">
          <div className="stat-number">
            {inversions.filter(i => i.patch_created).length}
          </div>
          <div className="stat-label">Patches Created</div>
        </div>
      </div>

      <div className="inversion-table-wrapper">
        <table className="inversion-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Page</th>
              <th>Original Paragraph</th>
              <th>Inverted Paragraph</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {inversions.map((inv) => (
              <tr key={inv.id} className={inv.patch_created ? 'completed' : ''}>
                <td>{inv.paragraph_number + 1}</td>
                <td>{inv.page_number}</td>
                <td className="paragraph-cell">
                  <div className="paragraph-text">{inv.original}</div>
                </td>
                <td className="paragraph-cell inverted">
                  <div className="paragraph-text">{inv.inverted}</div>
                </td>
                <td className="actions-cell">
                  <div className="action-buttons">
                    <button
                      onClick={() => identifyGaps(inv)}
                      disabled={identifyingGaps}
                      className="btn-identify"
                    >
                      {inv.gaps_identified ? `View Gaps (${inv.gap_count})` : 'Identify Gaps'}
                    </button>
                    <button
                      onClick={() => openPatchModal(inv)}
                      className="btn-patch"
                      disabled={!inv.gaps_identified}
                    >
                      {inv.patch_created ? `View Patches (${inv.patch_count})` : 'Create Patch'}
                    </button>
                  </div>
                  {inv.patch_created && (
                    <div className="status-badge">✓ Complete</div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Gap Modal */}
      {showGapModal && selectedInversion && (
        <div className="modal-overlay" onClick={() => setShowGapModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Identified Gaps - Paragraph {selectedInversion.paragraph_number + 1}</h3>

            <div className="gap-comparison">
              <div className="gap-side">
                <h4>Original</h4>
                <p>{selectedInversion.original}</p>
              </div>
              <div className="gap-side">
                <h4>Inverted</h4>
                <p>{selectedInversion.inverted}</p>
              </div>
            </div>

            <div className="gaps-list">
              <h4>Logical Gaps Found:</h4>
              {gaps.length === 0 ? (
                <p>No gaps identified yet.</p>
              ) : (
                gaps.map((gap) => (
                  <div key={gap.id} className={`gap-item gap-${gap.type}`}>
                    <div className="gap-header">
                      <span className="gap-type">{gap.type}</span>
                      <span className="gap-location">{gap.location}</span>
                    </div>
                    <p className="gap-description">{gap.description}</p>
                  </div>
                ))
              )}
            </div>

            <div className="modal-actions">
              <button onClick={() => setShowGapModal(false)} className="btn-close">
                Close
              </button>
              <button
                onClick={() => {
                  setShowGapModal(false);
                  openPatchModal(selectedInversion);
                }}
                className="btn-next"
              >
                Create Patch →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Patch Modal */}
      {showPatchModal && selectedInversion && (
        <div className="modal-overlay" onClick={() => setShowPatchModal(false)}>
          <div className="modal patch-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Create Patch - Paragraph {selectedInversion.paragraph_number + 1}</h3>

            <div className="patch-context">
              <div className="context-section">
                <h4>Original vs Inverted</h4>
                <div className="side-by-side">
                  <div className="context-text">
                    <strong>Original:</strong>
                    <p>{selectedInversion.original}</p>
                  </div>
                  <div className="context-text">
                    <strong>Inverted:</strong>
                    <p>{selectedInversion.inverted}</p>
                  </div>
                </div>
              </div>

              <div className="context-section">
                <h4>Gaps to Address ({gaps.length})</h4>
                {gaps.map((gap) => (
                  <div key={gap.id} className="mini-gap">
                    <strong>{gap.type}:</strong> {gap.description}
                  </div>
                ))}
              </div>
            </div>

            <div className="patch-form">
              <h4>Your Patch</h4>
              <p className="form-hint">
                Create a function, rule, or principle that reconciles the opposites and addresses the gaps.
              </p>

              <div className="form-group">
                <label>Patch Name (optional)</label>
                <input
                  type="text"
                  value={patchName}
                  onChange={(e) => setPatchName(e.target.value)}
                  placeholder="e.g., 'Context-Dependent Truth Rule'"
                  className="patch-input"
                />
              </div>

              <div className="form-group">
                <label>Patch Type</label>
                <select
                  value={patchType}
                  onChange={(e) => setPatchType(e.target.value)}
                  className="patch-select"
                >
                  <option value="principle">Principle</option>
                  <option value="function">Function</option>
                  <option value="rule">Rule</option>
                  <option value="exception">Exception</option>
                  <option value="condition">Condition</option>
                </select>
              </div>

              <div className="form-group">
                <label>Patch Description *</label>
                <textarea
                  value={patchDescription}
                  onChange={(e) => setPatchDescription(e.target.value)}
                  placeholder="Describe your patch: How does it reconcile the original and inverted statements? What conditions make each true? What nuance does it add?"
                  className="patch-textarea"
                  rows={6}
                />
              </div>

              <div className="form-group">
                <label>Creativity Score (1-10)</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={creativityScore}
                  onChange={(e) => setCreativityScore(parseInt(e.target.value))}
                  className="creativity-slider"
                />
                <div className="slider-value">{creativityScore}/10</div>
              </div>
            </div>

            {patches.length > 0 && (
              <div className="existing-patches">
                <h4>Previous Patches</h4>
                {patches.map((patch) => (
                  <div key={patch.id} className="patch-card">
                    <div className="patch-card-header">
                      <strong>{patch.patch_name}</strong>
                      <span className="patch-type-badge">{patch.patch_type}</span>
                    </div>
                    <p>{patch.patch_description}</p>
                    <div className="patch-meta">
                      Score: {patch.creativity_score}/10 | {new Date(patch.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="modal-actions">
              <button onClick={() => setShowPatchModal(false)} className="btn-close">
                Close
              </button>
              <button
                onClick={createPatch}
                className="btn-create"
                disabled={!patchDescription.trim()}
              >
                Create Patch
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InversionTable;
