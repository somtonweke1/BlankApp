import { useState, useRef } from 'react'
import { API_URL } from '../config'

interface UploadProps {
  onUploadComplete: (materialId: string, filename: string, totalConcepts: number, userId: string) => void
}

function Upload({ onUploadComplete }: UploadProps) {
  const [email, setEmail] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (!selectedFile.name.endsWith('.pdf')) {
        alert('Please select a PDF file')
        return
      }
      setFile(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!email || !file) {
      alert('Please enter email and select a file')
      return
    }

    setUploading(true)
    setProgress('Creating user account...')

    try {
      // Create user
      const userResponse = await fetch(`${API_URL}/api/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })

      if (!userResponse.ok) {
        throw new Error('Failed to create user')
      }

      const userData = await userResponse.json()
      const userId = userData.user_id

      setProgress('Uploading PDF...')

      // Upload file
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', userId)

      setProcessing(true)

      const uploadResponse = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData
      })

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file')
      }

      const uploadData = await uploadResponse.json()

      setProgress('Processing complete!')

      // Call completion callback
      onUploadComplete(
        uploadData.material_id,
        uploadData.filename,
        uploadData.total_concepts,
        userId
      )

    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
      setUploading(false)
      setProcessing(false)
      setProgress('')
    }
  }

  return (
    <div className="upload-container">
      <div className="upload-card">
        <div className="upload-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        <h2>Upload Your Study Material</h2>
        <p className="upload-subtitle">
          Upload any PDF and we'll help you master every concept through adaptive engagement
        </p>

        {!uploading ? (
          <>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="your.email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="file">Study Material (PDF)</label>
              <input
                ref={fileInputRef}
                id="file"
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="button button-secondary"
              >
                {file ? file.name : 'Choose PDF File'}
              </button>
            </div>

            <button
              onClick={handleUpload}
              disabled={!email || !file}
              className="button button-primary"
            >
              Upload and Start Learning
            </button>

            <div className="guarantee">
              <p>Our Guarantee:</p>
              <ul>
                <li>99% accuracy on all concepts</li>
                <li>95% recall probability after 1 week</li>
                <li>10 consecutive perfect answers per concept</li>
              </ul>
            </div>
          </>
        ) : (
          <div className="processing">
            <div className="spinner"></div>
            <p className="processing-text">{progress}</p>
            {processing && (
              <p className="processing-detail">
                Extracting concepts and generating adaptive questions...
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Upload
