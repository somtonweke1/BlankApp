import { useState, useEffect } from 'react'
import { API_URL } from '../config'

interface ProgressProps {
  userId: string
  onRestart: () => void
}

interface UserProgress {
  user_id: string
  email: string
  total_concepts: number
  mastered: number
  learning: number
  struggling: number
  total_session_time_minutes: number
  mastery_rate: number
}

function Progress({ userId, onRestart }: ProgressProps) {
  const [progress, setProgress] = useState<UserProgress | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProgress()
  }, [userId])

  const fetchProgress = async () => {
    try {
      const response = await fetch(`${API_URL}/api/users/${userId}/progress`)
      const data = await response.json()
      setProgress(data)
    } catch (error) {
      console.error('Failed to fetch progress:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="progress-container">
        <div className="progress-card">
          <div className="spinner"></div>
          <p>Loading your progress...</p>
        </div>
      </div>
    )
  }

  if (!progress) {
    return (
      <div className="progress-container">
        <div className="progress-card">
          <p>Failed to load progress</p>
          <button onClick={onRestart} className="button button-primary">
            Start New Session
          </button>
        </div>
      </div>
    )
  }

  const masteryPercentage = Math.round(progress.mastery_rate * 100)

  return (
    <div className="progress-container">
      <div className="progress-card">
        <div className="celebration">
          {progress.mastery_rate === 1.0 ? (
            <>
              <div className="celebration-icon">🎉</div>
              <h2>Session Complete!</h2>
              <p className="celebration-text">
                Congratulations! You've mastered all concepts with our 99% accuracy and 95% recall guarantee.
              </p>
            </>
          ) : (
            <>
              <div className="celebration-icon">📊</div>
              <h2>Great Progress!</h2>
              <p className="celebration-text">
                Keep going! You're on your way to mastery.
              </p>
            </>
          )}
        </div>

        <div className="progress-stats">
          <div className="progress-stat-card">
            <div className="progress-stat-value">{masteryPercentage}%</div>
            <div className="progress-stat-label">Mastery Rate</div>
          </div>

          <div className="progress-stat-card">
            <div className="progress-stat-value">{progress.mastered}</div>
            <div className="progress-stat-label">Concepts Mastered</div>
          </div>

          <div className="progress-stat-card">
            <div className="progress-stat-value">{progress.learning}</div>
            <div className="progress-stat-label">In Progress</div>
          </div>

          <div className="progress-stat-card">
            <div className="progress-stat-value">{progress.struggling}</div>
            <div className="progress-stat-label">Need Review</div>
          </div>
        </div>

        <div className="progress-breakdown">
          <h3>Breakdown</h3>
          <div className="progress-bar-container">
            <div className="progress-bar-segment mastered" style={{ width: `${(progress.mastered / progress.total_concepts) * 100}%` }}>
              {progress.mastered > 0 && `${progress.mastered} Mastered`}
            </div>
            <div className="progress-bar-segment learning" style={{ width: `${(progress.learning / progress.total_concepts) * 100}%` }}>
              {progress.learning > 0 && `${progress.learning} Learning`}
            </div>
            <div className="progress-bar-segment struggling" style={{ width: `${(progress.struggling / progress.total_concepts) * 100}%` }}>
              {progress.struggling > 0 && `${progress.struggling} Review`}
            </div>
          </div>
        </div>

        <div className="time-stats">
          <p>
            Total study time: <strong>{progress.total_session_time_minutes} minutes</strong>
          </p>
          <p>
            Average per concept: <strong>{Math.round(progress.total_session_time_minutes / progress.total_concepts)} minutes</strong>
          </p>
        </div>

        <div className="guarantee-met">
          {progress.mastery_rate === 1.0 ? (
            <div className="guarantee-badge">
              <div className="guarantee-icon">✓</div>
              <div>
                <h4>Mastery Guarantee Met</h4>
                <ul>
                  <li>99% accuracy achieved</li>
                  <li>10 consecutive perfect answers per concept</li>
                  <li>95% predicted recall after 1 week</li>
                  <li>Format invariance tested</li>
                  <li>Speed and fluency validated</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="continue-message">
              <p>Continue your session to achieve full mastery with our guarantee.</p>
            </div>
          )}
        </div>

        <div className="action-buttons">
          {progress.mastery_rate < 1.0 ? (
            <button className="button button-primary" onClick={() => window.location.reload()}>
              Continue Learning
            </button>
          ) : (
            <button className="button button-primary" onClick={onRestart}>
              Upload New Material
            </button>
          )}

          <button className="button button-secondary" onClick={onRestart}>
            Start Over
          </button>
        </div>
      </div>
    </div>
  )
}

export default Progress
