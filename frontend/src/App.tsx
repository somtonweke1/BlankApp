import { useState } from 'react'
import { API_URL } from './config'
import Upload from './components/Upload'
import LearningSession from './components/LearningSession'
import Progress from './components/Progress'

type Screen = 'upload' | 'learning' | 'progress'

interface SessionInfo {
  sessionId: string
  materialId: string
  filename: string
  totalConcepts: number
}

function App() {
  const [screen, setScreen] = useState<Screen>('upload')
  const [userId, setUserId] = useState<string | null>(null)
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null)

  const handleUploadComplete = (materialId: string, _filename: string, _totalConcepts: number, uid: string) => {
    setUserId(uid)
    // Auto-start session after upload
    startSession(materialId, _filename, _totalConcepts, uid)
  }

  const startSession = async (materialId: string, _filename: string, _totalConcepts: number, uid: string) => {
    try {
      console.log('Starting session with:', { materialId, uid })
      const response = await fetch(`${API_URL}/api/sessions/start/${materialId}?user_id=${uid}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })

      if (!response.ok) {
        const errorText = await response.text()
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

  const handleRestart = () => {
    setSessionInfo(null)
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

        {screen === 'learning' && sessionInfo && (
          <LearningSession
            sessionId={sessionInfo.sessionId}
            filename={sessionInfo.filename}
            totalConcepts={sessionInfo.totalConcepts}
            onComplete={handleSessionComplete}
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
