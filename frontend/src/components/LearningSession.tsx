import { useState, useEffect, useRef } from 'react'
import { WS_URL } from '../config'

interface LearningSessionProps {
  sessionId: string
  filename: string
  totalConcepts: number
  onComplete: () => void
}

interface Question {
  type: 'question'
  mode: string
  concept_name: string
  question: string
  difficulty: number
  data: any
}

interface Feedback {
  type: 'feedback'
  correct: boolean
  explanation: string
  mastered: boolean
  concept_name: string
}

interface ModeSwitch {
  type: 'mode_switch'
  new_mode: string
  reason: string
}

interface SessionComplete {
  type: 'session_complete'
  stats: {
    duration_minutes: number
    total_questions: number
    total_correct: number
    accuracy: number
    concepts_mastered: number
    total_concepts: number
  }
}

interface Hint {
  type: 'hint'
  hint: string
}

interface Peek {
  type: 'peek'
  answer: string
}

type Message = Question | Feedback | ModeSwitch | SessionComplete | Hint | Peek

function LearningSession({ sessionId, filename, totalConcepts, onComplete }: LearningSessionProps) {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [hint, setHint] = useState<string | null>(null)
  const [peekedAnswer, setPeekedAnswer] = useState<string | null>(null)
  const [stats, setStats] = useState({
    answered: 0,
    correct: 0,
    mastered: 0
  })
  const [_startTime, setStartTime] = useState<number>(Date.now())
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now())
  const [firstKeystrokeTime, setFirstKeystrokeTime] = useState<number | null>(null)

  const answerInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket(`${WS_URL}/ws/${sessionId}`)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
      setStartTime(Date.now())
    }

    websocket.onmessage = (event) => {
      const message: Message = JSON.parse(event.data)
      handleMessage(message)
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [sessionId])

  const handleMessage = (message: Message) => {
    switch (message.type) {
      case 'question':
        setCurrentQuestion(message)
        setAnswer('')
        setShowFeedback(false)
        setFeedback(null)
        setHint(null)
        setPeekedAnswer(null)
        setQuestionStartTime(Date.now())
        setFirstKeystrokeTime(null)
        setTimeout(() => answerInputRef.current?.focus(), 100)
        break

      case 'feedback':
        setFeedback(message)
        setShowFeedback(true)
        setStats(prev => ({
          answered: prev.answered + 1,
          correct: prev.correct + (message.correct ? 1 : 0),
          mastered: prev.mastered + (message.mastered ? 1 : 0)
        }))
        break

      case 'hint':
        setHint(message.hint)
        break

      case 'peek':
        setPeekedAnswer(message.answer)
        break

      case 'mode_switch':
        console.log(`Mode switched to ${message.new_mode}: ${message.reason}`)
        break

      case 'session_complete':
        console.log('Session complete!', message.stats)
        onComplete()
        break

      default:
        console.log('Unknown message type:', message)
    }
  }

  const handleAnswerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!firstKeystrokeTime) {
      setFirstKeystrokeTime(Date.now())
    }
    setAnswer(e.target.value)
  }

  const handleSubmit = () => {
    if (!ws || !answer.trim()) return

    const responseTime = Date.now() - questionStartTime
    const hesitationTime = firstKeystrokeTime ? firstKeystrokeTime - questionStartTime : 0

    ws.send(JSON.stringify({
      type: 'answer',
      answer: answer.trim(),
      response_time_ms: responseTime,
      hesitation_ms: hesitationTime
    }))
  }

  const handleSkip = () => {
    if (!ws) return

    ws.send(JSON.stringify({
      type: 'skip'
    }))

    // Wait for response, then get next question
  }

  const handlePeek = () => {
    if (!ws) return

    ws.send(JSON.stringify({
      type: 'peek'
    }))
  }

  const handleHint = () => {
    if (!ws) return

    ws.send(JSON.stringify({
      type: 'hint'
    }))
  }

  const handleNextQuestion = () => {
    setShowFeedback(false)
    setFeedback(null)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !showFeedback) {
      handleSubmit()
    } else if (e.key === 'Enter' && showFeedback) {
      handleNextQuestion()
    }
  }

  if (!connected) {
    return (
      <div className="session-container">
        <div className="session-card">
          <div className="spinner"></div>
          <p>Connecting to learning engine...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="session-container">
      <div className="session-header">
        <div className="session-info">
          <h2>{filename}</h2>
          <p>{totalConcepts} concepts to master</p>
        </div>

        <div className="session-stats">
          <div className="stat">
            <span className="stat-value">{stats.answered}</span>
            <span className="stat-label">Answered</span>
          </div>
          <div className="stat">
            <span className="stat-value">{stats.answered > 0 ? Math.round((stats.correct / stats.answered) * 100) : 0}%</span>
            <span className="stat-label">Accuracy</span>
          </div>
          <div className="stat">
            <span className="stat-value">{stats.mastered}/{totalConcepts}</span>
            <span className="stat-label">Mastered</span>
          </div>
        </div>
      </div>

      {currentQuestion && (
        <div className="question-card">
          <div className="question-header">
            <span className="mode-badge">{currentQuestion.mode.replace(/_/g, ' ')}</span>
            <span className="concept-name">{currentQuestion.concept_name}</span>
          </div>

          <div className="question-content">
            <p className="question-text">{currentQuestion.question}</p>
          </div>

          {!showFeedback ? (
            <div className="answer-section">
              <input
                ref={answerInputRef}
                type="text"
                className="answer-input"
                placeholder="Type your answer..."
                value={answer}
                onChange={handleAnswerChange}
                onKeyPress={handleKeyPress}
                autoFocus
              />

              {hint && (
                <div style={{
                  padding: '10px',
                  margin: '10px 0',
                  background: '#fff3cd',
                  border: '1px solid #ffc107',
                  borderRadius: '5px',
                  color: '#856404'
                }}>
                  <strong>💡 Hint:</strong> {hint}
                </div>
              )}

              {peekedAnswer && (
                <div style={{
                  padding: '10px',
                  margin: '10px 0',
                  background: '#d1ecf1',
                  border: '1px solid #bee5eb',
                  borderRadius: '5px',
                  color: '#0c5460'
                }}>
                  <strong>👁️ Answer:</strong> {peekedAnswer}
                </div>
              )}

              <div className="action-buttons">
                <button
                  onClick={handleSubmit}
                  disabled={!answer.trim()}
                  className="button button-primary"
                >
                  Submit Answer
                </button>

                <button
                  onClick={handleHint}
                  className="button button-hint"
                  title="Get a hint"
                >
                  Hint
                </button>

                <button
                  onClick={handlePeek}
                  className="button button-peek"
                  title="Peek at answer"
                >
                  Peek
                </button>

                <button
                  onClick={handleSkip}
                  className="button button-skip"
                  title="Skip this question"
                >
                  Skip
                </button>
              </div>
            </div>
          ) : feedback && (
            <div className={`feedback-section ${feedback.correct ? 'correct' : 'incorrect'}`}>
              <div className="feedback-header">
                {feedback.correct ? (
                  <div className="feedback-icon correct">✓</div>
                ) : (
                  <div className="feedback-icon incorrect">✗</div>
                )}
                <h3>{feedback.correct ? 'Correct!' : 'Not Quite'}</h3>
              </div>

              <p className="feedback-text">{feedback.explanation}</p>

              {feedback.mastered && (
                <div className="mastery-alert">
                  <div className="mastery-icon">★</div>
                  <p><strong>Concept Mastered!</strong> You've achieved mastery of: {feedback.concept_name}</p>
                </div>
              )}

              <button
                onClick={handleNextQuestion}
                className="button button-primary"
                autoFocus
              >
                Next Question →
              </button>
            </div>
          )}
        </div>
      )}

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${(stats.mastered / totalConcepts) * 100}%` }}
        />
      </div>
    </div>
  )
}

export default LearningSession
