import { useState } from 'react'
import { API_URL } from './config'
import Upload from './components/Upload'
import LearningSession from './components/LearningSession'
import Progress from './components/Progress'
import InversionMode from './components/InversionMode'

type Screen = 'upload' | 'mode-select' | 'learning' | 'inversion' | 'progress'

interface SessionInfo {
  sessionId: string
  materialId: string
  filename: string
  totalConcepts: number
}

interface MaterialInfo {
  materialId: string
  filename: string
  totalConcepts: number
}

function App() {
  const [screen, setScreen] = useState<Screen>('upload')
  const [userId, setUserId] = useState<string | null>(null)
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null)
  const [materialInfo, setMaterialInfo] = useState<MaterialInfo | null>(null)

  const handleUploadComplete = (materialId: string, _filename: string, _totalConcepts: number, uid: string) => {
    setUserId(uid)
    setMaterialInfo({
      materialId,
      filename: _filename,
      totalConcepts: _totalConcepts
    })
    // Show mode selection instead of auto-starting
    setScreen('mode-select')
  }

  const startSession = async (materialId: string, _filename: string, _totalConcepts: number, uid: string) => {
    try {
      console.log('Starting session with:', { materialId, uid })

      // Retry logic for Render free tier cold starts
      let response
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 60000)

          response = await fetch(`${API_URL}/api/sessions/start/${materialId}?user_id=${uid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal
          })

          clearTimeout(timeoutId)
          break
        } catch (error) {
          if (attempt === 3) throw error
          console.log(`Retry ${attempt}/3...`)
          await new Promise(resolve => setTimeout(resolve, 2000))
        }
      }

      if (!response || !response.ok) {
        const errorText = response ? await response.text() : 'No response'
        console.error('Session start failed:', errorText)
        throw new Error(`Failed to start session: ${errorText}`)
      }

      const data = await response.json()
      console.log('Session started:', data)

      setSessionInfo({
        sessionId: data.session_id,
        materialId: data.material_id,
        filename: data.filename,
        totalConcepts: data.total_concepts
      })

      setScreen('learning')
    } catch (error) {
      console.error('Failed to start session:', error)
      alert(`Failed to start learning session: ${error}`)
    }
  }

  const handleSessionComplete = () => {
    setScreen('progress')
  }

  const handleSelectQuestionMode = () => {
    if (materialInfo && userId) {
      startSession(materialInfo.materialId, materialInfo.filename, materialInfo.totalConcepts, userId)
    }
  }

  const handleSelectInversionMode = () => {
    setScreen('inversion')
  }

  const handleRestart = () => {
    setSessionInfo(null)
    setMaterialInfo(null)
    setScreen('upload')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Mastery Machine</h1>
        <p className="tagline">Upload. Engage. Master. Guaranteed.</p>
      </header>

      <main className="app-main">
        {screen === 'upload' && (
          <Upload onUploadComplete={handleUploadComplete} />
        )}

        {screen === 'mode-select' && materialInfo && (
          <div className="upload-container">
            <div className="upload-card">
              <h2>Choose Learning Mode</h2>
              <p className="upload-subtitle">
                Material uploaded: <strong>{materialInfo.filename}</strong>
                <br />
                Select how you want to engage with this content.
              </p>

              <div style={{ display: 'grid', gap: '1rem', marginTop: '2rem' }}>
                <div
                  style={{
                    padding: '2rem',
                    background: '#f7fafc',
                    borderRadius: '12px',
                    cursor: 'pointer',
                    border: '2px solid transparent',
                    transition: 'all 0.2s'
                  }}
                  onClick={handleSelectQuestionMode}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.border = '2px solid #667eea'
                    e.currentTarget.style.background = '#edf2f7'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.border = '2px solid transparent'
                    e.currentTarget.style.background = '#f7fafc'
                  }}
                >
                  <h3 style={{ color: '#2d3748', marginBottom: '0.5rem' }}>
                    Question-Based Learning
                  </h3>
                  <p style={{ color: '#718096', margin: 0 }}>
                    Adaptive Q&A across 12 engagement modes. System guarantees mastery through
                    continuous assessment and difficulty adjustment.
                  </p>
                </div>

                <div
                  style={{
                    padding: '2rem',
                    background: '#fef3c7',
                    borderRadius: '12px',
                    cursor: 'pointer',
                    border: '2px solid transparent',
                    transition: 'all 0.2s'
                  }}
                  onClick={handleSelectInversionMode}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.border = '2px solid #f59e0b'
                    e.currentTarget.style.background = '#fde68a'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.border = '2px solid transparent'
                    e.currentTarget.style.background = '#fef3c7'
                  }}
                >
                  <h3 style={{ color: '#2d3748', marginBottom: '0.5rem' }}>
                    Dialectical Learning (Inversion Mode)
                  </h3>
                  <p style={{ color: '#78350f', margin: 0 }}>
                    Transform boring material into an active engagement game. Each paragraph is
                    inverted, you spot gaps, and create patches. Force creativity and deep
                    understanding through dialectical thinking.
                  </p>
                </div>
              </div>

              <button
                className="button button-secondary"
                onClick={handleRestart}
                style={{ marginTop: '2rem' }}
              >
                Back to Upload
              </button>
            </div>
          </div>
        )}

        {screen === 'learning' && sessionInfo && (
          <LearningSession
            sessionId={sessionInfo.sessionId}
            filename={sessionInfo.filename}
            totalConcepts={sessionInfo.totalConcepts}
            onComplete={handleSessionComplete}
          />
        )}

        {screen === 'inversion' && materialInfo && userId && (
          <InversionMode
            materialId={materialInfo.materialId}
            userId={userId}
            filename={materialInfo.filename}
            backendUrl={API_URL}
            onBack={handleRestart}
          />
        )}

        {screen === 'progress' && userId && (
          <Progress userId={userId} onRestart={handleRestart} />
        )}
      </main>

      <footer className="app-footer">
        <p>99% Accuracy • 95% Predicted Recall • Guaranteed Mastery</p>
      </footer>
    </div>
  )
}

export default App
